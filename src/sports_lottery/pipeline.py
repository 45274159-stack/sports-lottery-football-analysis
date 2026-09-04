"""Manual-input analysis pipeline. No live feed, automatic browsing or wagering."""
import argparse
import hashlib
import json
from pathlib import Path

from .forecast import ForecastModel
from .history_quality import load_validated
from .match_context import aware_time, team_context, validate_evidence
from .prediction_log import connect, save_prediction, save_result, review


def build_analysis(rows, request):
    required = ("id", "match_id", "league", "home", "away", "kickoff", "created_at", "fixture_source_url")
    for key in required:
        if not request.get(key):
            raise ValueError(f"Missing {key}")
    created, kickoff = aware_time(request["created_at"]), aware_time(request["kickoff"])
    if created >= kickoff:
        raise ValueError("Prediction must precede kickoff")
    if request["home"] == request["away"]:
        raise ValueError("Identical teams")
    if not request["fixture_source_url"].startswith("https://"):
        raise ValueError("Fixture source URL required")
    # Input dates have no uniform timezone. Exclude prediction-day games entirely.
    cutoff = created.date().isoformat()
    history = sorted([r for r in rows if r["league"] == request["league"] and r["date"] < cutoff],
                     key=lambda r: (r["date"], r["home_team"], r["away_team"]))
    known = {r[k] for r in history for k in ("home_team", "away_team")}
    if not {request["home"], request["away"]} <= known:
        raise ValueError("Team not found in selected league; resolve names or add history first")
    evidence = []
    kinds = {"injuries", "lineup", "xg", "schedule", "motivation", "fixture"}
    for item in request.get("evidence", []):
        if item.get("kind") not in kinds or item.get("match_id") != request["match_id"]:
            raise ValueError("Evidence kind or match identity invalid")
        if item.get("team") not in (request["home"], request["away"], "both"):
            raise ValueError("Evidence team invalid")
        if not item.get("summary"):
            raise ValueError("Evidence summary required")
        evidence.append(validate_evidence(item, request["created_at"], request["kickoff"]))
    missing = []
    # Freshness limits are conservative workflow choices, not learned accuracy claims.
    for kind, hours in (("fixture", 24), ("injuries", 48), ("lineup", 6), ("xg", 168), ("schedule", 48), ("motivation", 48)):
        for team in (request["home"], request["away"]):
            if not any(e["kind"] == kind and e["team"] in (team, "both") and
                       e["status"] == "confirmed" and e["age_hours"] <= hours for e in evidence):
                missing.append(f"{team}:{kind}")
    model = ForecastModel()
    for row in history:
        model.observe(row)
    forecast = model.predict(request["league"], request["home"], request["away"], cutoff)
    snapshot = dict(history=history, request=request)
    serialized = json.dumps(snapshot, sort_keys=True, ensure_ascii=False, allow_nan=False)
    warnings = forecast["warnings"] + [
        "Evidence is supplied by the caller; sources have not been automatically fetched or verified",
        "Evidence is displayed for review, not numerically incorporated in the model",
        "Dates only: games on the UTC prediction date are excluded to prevent leakage",
        "No verified odds or market availability; not a betting ticket",
    ]
    return dict(id=request["id"], match_id=request["match_id"],
                created_at=request["created_at"], kickoff=request["kickoff"],
                model_version="venue-poisson-v1-pipeline1", input_snapshot_hash=hashlib.sha256(serialized.encode()).hexdigest(),
                source_urls=sorted({request["fixture_source_url"], *(e["source_url"] for e in evidence)}),
                probabilities=forecast["result"], forecast=forecast,
                context={team: team_context(history, team, cutoff, request["league"]) for team in (request["home"], request["away"])},
                evidence=evidence, missing=missing, warnings=warnings,
                status="incomplete_inputs" if missing else "requires_manual_review",
                input_snapshot=snapshot)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("directory")
    analyze.add_argument("request_json")
    analyze.add_argument("--db", required=True)
    settle = sub.add_parser("record-result")
    settle.add_argument("prediction_id")
    settle.add_argument("result_json")
    settle.add_argument("--db", required=True)
    report = sub.add_parser("review")
    report.add_argument("--db", required=True)
    args = parser.parse_args()
    if args.command == "analyze":
        rows, issues = load_validated(args.directory)
        if issues:
            raise SystemExit("\n".join(issues))
        request = json.loads(Path(args.request_json).read_text(encoding="utf-8"))
        item = build_analysis(rows, request)
        db = connect(args.db)
        try:
            save_prediction(db, item)
        finally:
            db.close()
        print(json.dumps({k:v for k,v in item.items() if k != "input_snapshot"}, ensure_ascii=False, indent=2))
    else:
        if not Path(args.db).is_file():
            raise SystemExit("Existing database required")
        db = connect(args.db)
        try:
            if args.command == "record-result":
                save_result(db, args.prediction_id, json.loads(Path(args.result_json).read_text(encoding="utf-8")))
            print(json.dumps(review(db), ensure_ascii=False, indent=2))
        finally:
            db.close()


if __name__ == "__main__":
    main()
