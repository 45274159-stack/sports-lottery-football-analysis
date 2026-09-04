"""Unified fixture archive, shared-cutoff predictions and paired comparisons.

Manual fixture/result imports; no live feed or betting settlement.
"""
import argparse
import hashlib
import json
import math
import sqlite3
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path

from .history_quality import load_validated
from .forecast import ForecastModel
from .fitted_model import fit, predict
from .match_context import aware_time, validate_evidence
from .team_names import normalize_team
from .prematch import dossier

MODELS = ("league-frequency-v1", "venue-form-v1", "fitted-attack-defence-v1")


def encoded(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def connect(path):
    db=sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS fixtures(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS comparisons(
      id TEXT PRIMARY KEY, fixture_id TEXT NOT NULL REFERENCES fixtures(id),
      cutoff TEXT NOT NULL, snapshot_hash TEXT NOT NULL, snapshot TEXT NOT NULL,
      UNIQUE(fixture_id,cutoff));
    CREATE TABLE IF NOT EXISTS forecasts(
      comparison_id TEXT NOT NULL REFERENCES comparisons(id), model_id TEXT NOT NULL,
      status TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(comparison_id,model_id));
    CREATE TABLE IF NOT EXISTS outcomes(fixture_id TEXT PRIMARY KEY REFERENCES fixtures(id), payload TEXT NOT NULL);
    """)
    return db


def fixture_record(item):
    for key in ("league","home","away","kickoff","source_url","source_id"):
        if not item.get(key):raise ValueError(f"Missing fixture {key}")
    if not item["source_url"].startswith("https://"):raise ValueError("Source URL required")
    fixture=dict(item,home=normalize_team(item["home"]),away=normalize_team(item["away"]),
                 kickoff=aware_time(item["kickoff"]).isoformat())
    if fixture["home"]==fixture["away"]:raise ValueError("Identical teams")
    identity={k:fixture[k] for k in ("league","home","away","kickoff")}
    fixture["id"]=fingerprint(identity)
    return fixture


def compare(db, rows, fixture, created_at):
    fixture=fixture_record(fixture)
    created=aware_time(created_at)
    if created>=aware_time(fixture["kickoff"]):raise ValueError("Must predict before kickoff")
    cutoff=created.date().isoformat()
    history=[]
    seen=set()
    for r in rows:
        if r["league"]!=fixture["league"] or r["date"]>=cutoff:continue
        r=dict(r,home_team=normalize_team(r["home_team"]),away_team=normalize_team(r["away_team"]))
        key=(r["date"],r["home_team"],r["away_team"])
        if key in seen:raise ValueError("Duplicate match after name normalization")
        seen.add(key);history.append(r)
    history.sort(key=lambda r:(r["date"],r["home_team"],r["away_team"]))
    evidence=[]
    for item in fixture.get("evidence",[]):
        if item.get("source_id")!=fixture["source_id"]:raise ValueError("Evidence match mismatch")
        evidence.append(validate_evidence(item,created_at,fixture["kickoff"]))
    prematch=dossier(rows,fixture,created_at)
    snapshot=dict(history=history,evidence=evidence,prematch=prematch,fixture=fixture,cutoff=created.isoformat(),
                  method="UTC prediction-day matches excluded; all algorithms receive same rows",
                  model_versions=MODELS)
    comparison_id=fingerprint(dict(fixture_id=fixture["id"],cutoff=created.isoformat()))
    outputs={}
    for model_id in MODELS:
        try:
            if len(history)<100:raise ValueError("Fewer than 100 prior league matches")
            if model_id==MODELS[0]:
                counts=Counter(r["ft_result"] for r in history)
                output=dict(result={k:(counts[k]+1)/(len(history)+3) for k in "HDA"})
            elif model_id==MODELS[1]:
                known={r[k] for r in history for k in ("home_team","away_team")}
                if not {fixture["home"],fixture["away"]}<=known:raise ValueError("Unknown team")
                model=ForecastModel()
                for r in history:model.observe(r)
                output=model.predict(fixture["league"],fixture["home"],fixture["away"],cutoff)
            else:
                through=(created.date()-timedelta(days=1)).isoformat()
                model=fit(history,fixture["league"],through)
                output=predict(model,fixture["home"],fixture["away"],cutoff)
                output["fitted_artifact"]=model
            outputs[model_id]=dict(status="ok",prediction=output)
        except ValueError as error:
            outputs[model_id]=dict(status="skipped",reason=str(error))
        except Exception as error:
            outputs[model_id]=dict(status="failed",reason=f"{type(error).__name__}: {error}")
    with db:
        existing=db.execute("SELECT payload FROM fixtures WHERE id=?",(fixture["id"],)).fetchone()
        if existing is None:db.execute("INSERT INTO fixtures VALUES (?,?)",(fixture["id"],encoded(fixture)))
        db.execute("INSERT INTO comparisons VALUES (?,?,?,?,?)",(comparison_id,fixture["id"],created.isoformat(),fingerprint(snapshot),encoded(snapshot)))
        for name,output in outputs.items():
            db.execute("INSERT INTO forecasts VALUES (?,?,?,?)",(comparison_id,name,output["status"],encoded(output)))
    return dict(comparison_id=comparison_id,fixture_id=fixture["id"],snapshot_hash=fingerprint(snapshot),
                history_matches=len(history),outputs=outputs,prematch=prematch,
                warning="Shared input availability, different algorithms/windows; supplied evidence not incorporated numerically or verified automatically")


def record_outcome(db, fixture_id, outcome):
    row=db.execute("SELECT payload FROM fixtures WHERE id=?",(fixture_id,)).fetchone()
    if not row:raise ValueError("Unknown fixture")
    if outcome.get("period")!="90_minutes" or outcome.get("status")!="final":raise ValueError("Final regulation-time score required")
    for key in ("home_goals","away_goals"):
        if type(outcome.get(key)) is not int or outcome[key]<0:raise ValueError("Nonnegative integer goals required")
    if not outcome.get("source_url","").startswith("https://"):raise ValueError("Outcome source required")
    if aware_time(outcome["observed_at"])<=aware_time(json.loads(row[0])["kickoff"]):raise ValueError("Outcome observation must follow kickoff")
    with db:db.execute("INSERT INTO outcomes VALUES (?,?)",(fixture_id,encoded(outcome)))


def report(db):
    # Earliest recorded prediction per fixture avoids overweighting repeat updates.
    grouped=defaultdict(dict);details={};attempts=Counter();pending=0
    query="""SELECT c.id,f.payload,o.payload,p.model_id,p.status,p.payload FROM comparisons c
    JOIN fixtures f ON f.id=c.fixture_id LEFT JOIN outcomes o ON o.fixture_id=f.id
    JOIN forecasts p ON p.comparison_id=c.id
    WHERE c.cutoff=(SELECT MIN(c2.cutoff) FROM comparisons c2 WHERE c2.fixture_id=c.fixture_id)"""
    for cid,fixture,outcome,model,status,payload in db.execute(query):
        grouped[cid][model]=json.loads(payload);details[cid]=(json.loads(fixture),json.loads(outcome) if outcome else None)
        attempts[(model,status)]+=1
    metrics=defaultdict(lambda:dict(n=0,hits=0,log_loss=0.,brier=0.,score_n=0,score_hits=0,goals_n=0,goals_hits=0))
    excluded=[]
    for cid,outputs in grouped.items():
        fixture,outcome=details[cid]
        if not outcome:pending+=1;continue
        if any(outputs.get(m,{}).get("status")!="ok" for m in MODELS):excluded.append(cid);continue
        h,a=outcome["home_goals"],outcome["away_goals"]
        actual="H" if h>a else "A" if h<a else "D"
        for name,out in outputs.items():
            p=out["prediction"];v=metrics[(fixture["league"],name)];v["n"]+=1
            v["hits"]+=max(p["result"],key=p["result"].get)==actual
            v["log_loss"]-=math.log(max(p["result"][actual],1e-15))
            v["brier"]+=sum((p["result"][k]-(k==actual))**2 for k in "HDA")
            if p.get("scores"):
                v["score_n"]+=1;v["score_hits"]+=p["scores"][0][0]==f"{h}:{a}"
            if p.get("total_goals"):
                v["goals_n"]+=1;v["goals_hits"]+=max(p["total_goals"],key=p["total_goals"].get)==(str(h+a) if h+a<7 else "7+")
    return dict(fixtures=len(grouped),pending=pending,excluded_comparisons=excluded,
                attempts=[dict(model=m,status=s,n=n) for (m,s),n in sorted(attempts.items())],
                paired_metrics=[dict(league=l,model=m,n=v["n"],accuracy=v["hits"]/v["n"],
                    log_loss=v["log_loss"]/v["n"],brier=v["brier"]/v["n"],
                    score_accuracy=v["score_hits"]/v["score_n"] if v["score_n"] else None,
                    total_goals_accuracy=v["goals_hits"]/v["goals_n"] if v["goals_n"] else None)
                    for (l,m),v in sorted(metrics.items())],roi=None,
                protocol="Earliest snapshot per fixture; common successful settled cohort; no financial settlement")


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--db",required=True)
    sub=parser.add_subparsers(dest="command",required=True)
    run=sub.add_parser("compare");run.add_argument("directory");run.add_argument("fixture_json");run.add_argument("--at",required=True)
    result=sub.add_parser("result");result.add_argument("fixture_id");result.add_argument("result_json")
    sub.add_parser("report");args=parser.parse_args()
    if args.command!="compare" and not Path(args.db).is_file():raise SystemExit("Existing archive required")
    db=connect(args.db)
    try:
        if args.command=="compare":
            rows,issues=load_validated(args.directory)
            if issues:raise SystemExit("\n".join(issues))
            output=compare(db,rows,json.loads(Path(args.fixture_json).read_text()),args.at)
        else:
            if args.command=="result":record_outcome(db,args.fixture_id,json.loads(Path(args.result_json).read_text()))
            output=report(db)
        print(json.dumps(output,ensure_ascii=False,indent=2))
    finally:db.close()


if __name__=="__main__":main()
