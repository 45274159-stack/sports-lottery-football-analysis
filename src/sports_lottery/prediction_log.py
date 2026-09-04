"""Append-only application-level prediction and result log (not tamper-proof).

No bet placement. Financial returns remain unavailable without verified tickets.
"""
import hashlib
import json
import math
import sqlite3
from .match_context import aware_time


def connect(path):
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS predictions (
      id TEXT PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS results (
      prediction_id TEXT PRIMARY KEY REFERENCES predictions(id), payload TEXT NOT NULL);
    """)
    return db


def save_prediction(db, item):
    for field in ("id", "match_id", "model_version", "input_snapshot_hash", "source_urls"):
        if not item.get(field):
            raise ValueError(f"Missing {field}")
    if aware_time(item["created_at"]) >= aware_time(item["kickoff"]):
        raise ValueError("Prediction must precede kickoff")
    probabilities = item["probabilities"]
    if set(probabilities) != {"H", "D", "A"}:
        raise ValueError("Only H/D/A probability records supported")
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities.values()):
        raise ValueError("Invalid probability")
    if abs(sum(probabilities.values())-1) > 1e-8:
        raise ValueError("Probabilities must sum to one")
    payload = json.dumps(item, sort_keys=True, ensure_ascii=False, allow_nan=False)
    with db:
        db.execute("INSERT INTO predictions VALUES (?,?,?)",
                   (item["id"], payload, hashlib.sha256(payload.encode()).hexdigest()))


def save_result(db, prediction_id, item):
    prediction = db.execute("SELECT payload FROM predictions WHERE id=?", (prediction_id,)).fetchone()
    if prediction is None:
        raise ValueError("Unknown prediction")
    if item.get("status") != "final" or item.get("period") != "90_minutes":
        raise ValueError("Only explicitly final regulation-time results supported")
    if not item.get("source_url", "").startswith("https://"):
        raise ValueError("Result source required")
    if aware_time(item["observed_at"]) <= aware_time(json.loads(prediction[0])["kickoff"]):
        raise ValueError("Result timestamp must follow kickoff")
    for key in ("home_goals", "away_goals"):
        if type(item.get(key)) is not int or item[key] < 0:
            raise ValueError("Nonnegative integer goals required")
    with db:
        db.execute("INSERT INTO results VALUES (?,?)", (prediction_id, json.dumps(item)))


def review(db):
    n = hits = streak = max_streak = 0
    pairs = [(json.loads(p), json.loads(r)) for p,r in db.execute("SELECT p.payload,r.payload FROM predictions p JOIN results r ON p.id=r.prediction_id")]
    for p, r in sorted(pairs, key=lambda pair: (aware_time(pair[0]["kickoff"]), pair[0]["id"])):
        actual = "H" if r["home_goals"] > r["away_goals"] else "A" if r["home_goals"] < r["away_goals"] else "D"
        correct = max(p["probabilities"], key=p["probabilities"].get) == actual
        n += 1
        hits += correct
        streak = 0 if correct else streak+1
        max_streak = max(max_streak, streak)
    return dict(settled=n, hits=hits, accuracy=hits/n if n else None,
                longest_incorrect_streak=max_streak, roi=None, monetary_drawdown=None,
                warning="No verified stakes, ticket combinations or fixed odds; no financial return calculation")
