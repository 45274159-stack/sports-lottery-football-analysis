"""Versioned model registry and safe pre-kickoff model selection."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS models (
  model_id TEXT PRIMARY KEY,
  family TEXT NOT NULL,
  version TEXT NOT NULL,
  competition TEXT NOT NULL,
  markets_json TEXT NOT NULL,
  trained_through TEXT NOT NULL,
  training_data_hash TEXT NOT NULL,
  parameters_json TEXT NOT NULL,
  code_ref TEXT NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('candidate','accepted','retired')),
  notes TEXT NOT NULL,
  UNIQUE(family,version,competition)
);
CREATE TABLE IF NOT EXISTS evaluations (
  id INTEGER PRIMARY KEY,
  model_id TEXT NOT NULL REFERENCES models(model_id),
  split_name TEXT NOT NULL,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  matches INTEGER NOT NULL CHECK(matches>0),
  metrics_json TEXT NOT NULL,
  is_prospective INTEGER NOT NULL CHECK(is_prospective IN (0,1)),
  UNIQUE(model_id,split_name)
);
CREATE TABLE IF NOT EXISTS active_models (
  competition TEXT NOT NULL,
  market TEXT NOT NULL,
  model_id TEXT NOT NULL REFERENCES models(model_id),
  activated_at TEXT NOT NULL,
  PRIMARY KEY(competition,market)
);
"""


def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    return db


def _date(value):
    return date.fromisoformat(value).isoformat()


def _utc(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timezone required")
    return parsed.astimezone(timezone.utc).isoformat()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=False, allow_nan=False)


def _metrics(value):
    if not value or any(type(v) not in (int,float) or not math.isfinite(v) for v in value.values()):
        raise ValueError("Metrics must be a nonempty finite numeric object")
    return value


def register_model(db, spec):
    required = ("model_id","family","version","competition","markets","trained_through",
                "training_data_hash","parameters","code_ref","created_at","status","notes")
    if any(key not in spec for key in required):
        raise ValueError("Incomplete model specification")
    if not spec["markets"] or len(set(spec["markets"])) != len(spec["markets"]):
        raise ValueError("Markets must be a nonempty unique list")
    if spec["status"] not in {"candidate","accepted","retired"}:
        raise ValueError("Invalid status")
    if not spec["training_data_hash"] or not spec["code_ref"]:
        raise ValueError("Data hash and code reference required")
    row = (spec["model_id"],spec["family"],spec["version"],spec["competition"],
           _json(spec["markets"]),_date(spec["trained_through"]),spec["training_data_hash"],
           _json(spec["parameters"]),spec["code_ref"],_utc(spec["created_at"]),spec["status"],spec["notes"])
    with db:
        db.execute("INSERT INTO models VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",row)


def add_evaluation(db, model_id, evaluation):
    model = db.execute("SELECT 1 FROM models WHERE model_id=?",(model_id,)).fetchone()
    if not model:
        raise ValueError("Unknown model")
    start,end = _date(evaluation["start_date"]),_date(evaluation["end_date"])
    if start>end:
        raise ValueError("Evaluation dates reversed")
    with db:
        db.execute("INSERT INTO evaluations(model_id,split_name,start_date,end_date,matches,metrics_json,is_prospective) VALUES (?,?,?,?,?,?,?)",
                   (model_id,evaluation["split_name"],start,end,evaluation["matches"],
                    _json(_metrics(evaluation["metrics"])),int(evaluation["is_prospective"])))


def activate(db, model_id, competition, market, activated_at):
    model = db.execute("SELECT * FROM models WHERE model_id=?",(model_id,)).fetchone()
    if not model or model["competition"] != competition or market not in json.loads(model["markets_json"]):
        raise ValueError("Model scope does not match activation")
    if model["status"] != "accepted":
        raise ValueError("Only accepted models may be active")
    if not db.execute("SELECT 1 FROM evaluations WHERE model_id=?",(model_id,)).fetchone():
        raise ValueError("Evaluation required before activation")
    with db:
        db.execute("INSERT INTO active_models VALUES (?,?,?,?) ON CONFLICT(competition,market) DO UPDATE SET model_id=excluded.model_id,activated_at=excluded.activated_at",
                   (competition,market,model_id,_utc(activated_at)))


def change_status(db, model_id, new_status):
    row = db.execute("SELECT status FROM models WHERE model_id=?",(model_id,)).fetchone()
    if not row:
        raise ValueError("Unknown model")
    old = row["status"]
    if old == "candidate" and new_status == "accepted":
        prospective = db.execute("SELECT COALESCE(SUM(matches),0) AS n FROM evaluations WHERE model_id=? AND is_prospective=1",(model_id,)).fetchone()["n"]
        if prospective < 100:
            raise ValueError("Acceptance requires at least 100 prospective evaluations")
    elif not (old == "accepted" and new_status == "retired"):
        raise ValueError("Only candidate→accepted or accepted→retired transitions allowed")
    with db:
        db.execute("UPDATE models SET status=? WHERE model_id=?",(new_status,model_id))
        if new_status == "retired":
            db.execute("DELETE FROM active_models WHERE model_id=?",(model_id,))


def select_model(db, competition, market, kickoff):
    kickoff_date = _utc(kickoff)[:10]
    row = db.execute("SELECT m.* FROM active_models a JOIN models m ON m.model_id=a.model_id WHERE a.competition=? AND a.market=? AND m.status='accepted' AND m.trained_through<?",
                     (competition,market,kickoff_date)).fetchone()
    if not row:
        raise ValueError("No accepted pre-kickoff model for this scope")
    result = dict(row)
    for key in ("markets_json","parameters_json"):
        result[key[:-5]] = json.loads(result.pop(key))
    result["evaluations"] = [dict(r) for r in db.execute("SELECT split_name,start_date,end_date,matches,metrics_json,is_prospective FROM evaluations WHERE model_id=? ORDER BY start_date",(result["model_id"],))]
    for evaluation in result["evaluations"]:
        evaluation["metrics"] = json.loads(evaluation.pop("metrics_json"))
        evaluation["is_prospective"] = bool(evaluation["is_prospective"])
    return result


def data_fingerprint(paths):
    digest = hashlib.sha256()
    for path in sorted(map(Path,paths),key=lambda p:str(p)):
        digest.update(str(path).encode());digest.update(b"\0")
        with path.open("rb") as stream:
            while chunk:=stream.read(1024*1024): digest.update(chunk)
    return digest.hexdigest()


def list_models(db):
    return [dict(r) for r in db.execute("SELECT model_id,family,version,competition,trained_through,status,created_at FROM models ORDER BY competition,family,version")]


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--db",required=True)
    sub=parser.add_subparsers(dest="command",required=True)
    reg=sub.add_parser("register");reg.add_argument("spec_json")
    ev=sub.add_parser("evaluate");ev.add_argument("model_id");ev.add_argument("evaluation_json")
    ac=sub.add_parser("activate");ac.add_argument("model_id");ac.add_argument("competition");ac.add_argument("market");ac.add_argument("--at",required=True)
    st=sub.add_parser("status");st.add_argument("model_id");st.add_argument("new_status",choices=("accepted","retired"))
    se=sub.add_parser("select");se.add_argument("competition");se.add_argument("market");se.add_argument("--kickoff",required=True)
    sub.add_parser("list")
    args=parser.parse_args();Path(args.db).parent.mkdir(parents=True,exist_ok=True);db=connect(args.db)
    try:
        if args.command=="register": register_model(db,json.loads(Path(args.spec_json).read_text()))
        elif args.command=="evaluate": add_evaluation(db,args.model_id,json.loads(Path(args.evaluation_json).read_text()))
        elif args.command=="activate": activate(db,args.model_id,args.competition,args.market,args.at)
        elif args.command=="status": change_status(db,args.model_id,args.new_status)
        elif args.command=="select": print(json.dumps(select_model(db,args.competition,args.market,args.kickoff),ensure_ascii=False,indent=2))
        else: print(json.dumps(list_models(db),ensure_ascii=False,indent=2))
    finally: db.close()

if __name__=="__main__": main()
