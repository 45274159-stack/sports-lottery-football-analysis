"""Read-only chronological archive evaluation and held-out H/D/A calibration.

Uses earliest saved forecast per fixture; never overwrites original predictions.
"""
import argparse
import hashlib
import json
import math
import sqlite3
from collections import defaultdict
from pathlib import Path
from .match_context import aware_time
from .calibration import reliability


def probabilities(p):
    if set(p) != set("HDA") or any(not math.isfinite(v) or not 0 <= v <= 1 for v in p.values()) or abs(sum(p.values())-1) > 1e-8:
        raise ValueError("Invalid H/D/A probabilities")
    return p


def transform(p, temperature):
    probabilities(p)
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("Positive temperature required")
    logits = {k: math.log(max(v, 1e-15))/temperature for k,v in p.items()}
    maximum = max(logits.values())
    weights = {k: math.exp(v-maximum) for k,v in logits.items()}
    return {k: v/sum(weights.values()) for k,v in weights.items()}


def metrics(records):
    n = len(records)
    return dict(n=n,
        accuracy=sum(max(p,key=p.get)==y for p,y in records)/n if n else None,
        log_loss=-sum(math.log(max(p[y],1e-15)) for p,y in records)/n if n else None,
        brier=sum(sum((p[k]-(k==y))**2 for k in "HDA") for p,y in records)/n if n else None,
        class_reliability={k:reliability([dict(probability=p[k],outcome=int(k==y)) for p,y in records]) for k in "HDA"})


def evaluate_archive(db, split, end, minimum=30):
    split, end = aware_time(split), aware_time(end)
    if split >= end or type(minimum) is not int or minimum < 1:
        raise ValueError("Ordered split/end and positive minimum required")
    groups = defaultdict(lambda: dict(train=[], test=[], ids=[]))
    excluded = defaultdict(int)
    query = """SELECT c.id,c.cutoff,c.snapshot_hash,c.snapshot,f.payload,o.payload,p.model_id,p.status,p.payload
        FROM comparisons c JOIN fixtures f ON f.id=c.fixture_id
        JOIN forecasts p ON p.comparison_id=c.id LEFT JOIN outcomes o ON o.fixture_id=f.id
        WHERE c.cutoff=(SELECT MIN(x.cutoff) FROM comparisons x WHERE x.fixture_id=c.fixture_id)
        ORDER BY c.cutoff,c.id,p.model_id"""
    for cid,at,digest,snapshot,fixture,result,model,status,payload in db.execute(query):
        if hashlib.sha256(snapshot.encode()).hexdigest() != digest:
            raise ValueError("Input snapshot hash mismatch")
        f = json.loads(fixture); predicted = aware_time(at); kickoff = aware_time(f["kickoff"])
        if predicted >= kickoff: raise ValueError("Saved prediction is not pre-kickoff")
        if status != "ok": excluded["unsuccessful_model"] += 1; continue
        if result is None: excluded["unsettled"] += 1; continue
        r = json.loads(result); observed = aware_time(r["observed_at"])
        if r.get("status") != "final" or r.get("period") != "90_minutes" or observed <= kickoff:
            raise ValueError("Invalid saved outcome")
        if observed >= end: excluded["outcome_unavailable_by_end"] += 1; continue
        p = probabilities(json.loads(payload)["prediction"]["result"])
        h,a = r["home_goals"],r["away_goals"]
        y = "H" if h>a else "A" if h<a else "D"
        g = groups[(f["league"],model)]
        if observed < split and predicted < split:
            g["train"].append((p,y)); g["ids"].append(cid)
        elif split <= predicted < kickoff < end:
            g["test"].append((p,y))
        else: excluded["boundary_or_delayed_result"] += 1
    outputs=[]
    for (league,model),g in sorted(groups.items()):
        train,test=g["train"],g["test"]
        fitted=len(train)>=minimum and len({y for _,y in train})==3
        grid=(.5,.75,1.,1.25,1.5,2.,3.)
        t=min(grid,key=lambda t:sum(-math.log(max(transform(p,t)[y],1e-15)) for p,y in train)) if fitted else 1.
        raw=metrics(test); adjusted=metrics([(transform(p,t),y) for p,y in test]) if fitted else None
        outputs.append(dict(league=league,model=model,calibration_n=len(train),
            calibration_status="fitted" if fitted else "insufficient_samples_or_missing_class",
            temperature=t if fitted else None,calibration_ids=g["ids"],
            test_raw=raw,test_calibrated=adjusted,
            holdout_log_loss_improvement=raw["log_loss"]-adjusted["log_loss"] if fitted and test else None))
    return dict(split=split.isoformat(),end=end.isoformat(),minimum=minimum,groups=outputs,
        exclusions=dict(excluded),roi=None,
        protocol="Earliest forecast, per league/model; calibrator fitted on results observed strictly before split; untouched later prediction window; no original record changes",
        limitations=["Temperature scaling calibrates H/D/A only; score and total-goal markets unchanged",
                     "No automatic promotion of calibrated probabilities to live predictions",
                     "Archive timestamps are application claims, not tamper-proof proof of prospective prediction",
                     "Base-model training must already be past-only; empty archives cannot demonstrate accuracy"])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db",required=True);p.add_argument("--split",required=True)
    p.add_argument("--end",required=True);p.add_argument("--minimum",type=int,default=30)
    a=p.parse_args()
    path=Path(a.db).resolve()
    if not path.is_file():p.error("Existing archive required")
    db=sqlite3.connect(path.as_uri()+"?mode=ro",uri=True)
    try: print(json.dumps(evaluate_archive(db,a.split,a.end,a.minimum),ensure_ascii=False,indent=2))
    finally:db.close()


if __name__=="__main__":main()
