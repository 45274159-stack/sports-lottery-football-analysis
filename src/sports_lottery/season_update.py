"""Validate a new season export and build a fresh, combined model input snapshot.

No network access, invented results, or mutation of old prediction archives.
Run with a verified datasets/football-datasets season CSV exported locally.
"""
import argparse
import csv
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from .history_quality import load_validated, outcome

LEAGUES = {"premier-league": "Premier League", "la-liga": "La Liga",
           "serie-a": "Serie A", "bundesliga": "Bundesliga", "ligue-1": "Ligue 1"}
FIELDS = ["source", "league", "season", "date", "home_team", "away_team",
          "ft_home_goals", "ft_away_goals", "ft_result"]


def convert(text, slug, season, through):
    if slug not in LEAGUES or len(season) != 4 or not season.isdigit():
        raise ValueError("Unknown league or invalid season")
    year = 2000 + int(season[:2])
    if int(season[2:]) != (year + 1) % 100:
        raise ValueError("Season must span consecutive years")
    cutoff = date.fromisoformat(through)
    reader = csv.DictReader(text.lstrip("\ufeff").splitlines())
    required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
    if not required <= set(reader.fieldnames or []):
        raise ValueError("Missing source columns")
    rows, seen = [], set()
    for n, r in enumerate(reader, 2):
        if not any(r.values()):
            continue
        if None in r:
            raise ValueError(f"Extra columns at line {n}")
        day = date.fromisoformat(r["Date"])
        if not date(year, 7, 1) <= day < date(year + 1, 7, 1) or day > cutoff:
            raise ValueError(f"Outside season/cutoff at line {n}")
        h, a = int(r["FTHG"]), int(r["FTAG"])
        home, away = r["HomeTeam"].strip(), r["AwayTeam"].strip()
        if min(h, a) < 0 or outcome(h, a) != r["FTR"] or not home or not away or home == away:
            raise ValueError(f"Invalid completed match at line {n}")
        key = (day.isoformat(), home, away)
        if key in seen:
            raise ValueError(f"Duplicate match at line {n}")
        seen.add(key)
        rows.append(dict(zip(FIELDS, ["football-datasets", LEAGUES[slug], season,
                                     day.isoformat(), home, away, str(h), str(a), r["FTR"]])))
    if not rows:
        raise ValueError("No completed matches; empty file is not an update")
    return rows


def build(history, incoming, output, source_url, through):
    if not source_url.startswith("https://"):
        raise ValueError("Source URL required")
    old, issues = load_validated(history)
    if issues:
        raise ValueError("; ".join(issues))
    cutoff = date.fromisoformat(through).isoformat()
    if any(r["date"] > cutoff for r in old + incoming):
        raise ValueError("History contains results beyond cutoff")
    merged = {}
    for r in old + incoming:
        key = tuple(r[k] for k in ("league", "date", "home_team", "away_team"))
        if key in merged:
            if any(merged[key][k] != r[k] for k in ("ft_home_goals", "ft_away_goals", "ft_result")):
                raise ValueError("Conflicting score: manual review required")
            continue
        merged[key] = r
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)  # snapshots never overwrite past inputs
    fields = sorted(set().union(*(r.keys() for r in merged.values())))
    with (root / "matches.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(merged.values(), key=lambda r: (r["date"], r["league"], r["home_team"])))
    manifest = {"collected_at": datetime.now(timezone.utc).isoformat(), "through": through,
                "source_url": source_url, "history_rows": len(old),
                "new_rows": len(merged) - len(old), "combined_rows": len(merged),
                "sha256": hashlib.sha256((root / "matches.csv").read_bytes()).hexdigest(),
                "note": "Third-party results, not official Sporttery IDs. Collection time is not historical availability time. New snapshots require model refitting; old forecasts remain unchanged."}
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_csv"); p.add_argument("--league", choices=LEAGUES, required=True)
    p.add_argument("--season", required=True); p.add_argument("--through", required=True)
    p.add_argument("--history", required=True); p.add_argument("--output", required=True)
    p.add_argument("--source-url", required=True)
    a = p.parse_args()
    rows = convert(Path(a.source_csv).read_text(encoding="utf-8-sig"), a.league, a.season, a.through)
    print(json.dumps(build(a.history, rows, a.output, a.source_url, a.through), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
