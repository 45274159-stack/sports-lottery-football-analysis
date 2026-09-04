"""Historical-data audit and date-batched, expanding-window baseline evaluation.

No betting returns: these files do not contain verified pre-kickoff Sporttery odds.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date
from itertools import groupby
from pathlib import Path


def regulation_score(text: str) -> tuple[int, int]:
    """Read Football.TXT score suffix, never interpret shootout as match goals.

    For a.e.t. require the explicit (90-minute, half-time) pair. Ambiguous
    single parenthesis is deliberately rejected, not inferred.
    """
    if "a.e.t." in text:
        match = re.search(r"a\.e\.t\.\s*\((\d+)-(\d+),\s*\d+-\d+\)", text)
    elif "pen." in text:
        raise ValueError("Shootout without explicit regulation score")
    else:
        match = re.match(r"\s*(\d+)-(\d+)", text)
    if not match:
        raise ValueError(f"Ambiguous score: {text}")
    return int(match[1]), int(match[2])


def outcome(home: int, away: int) -> str:
    return "H" if home > away else "A" if home < away else "D"


def load_validated(directory: str):
    rows, issues, seen = [], [], set()
    for path in sorted(Path(directory).glob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            for number, row in enumerate(csv.DictReader(stream), 2):
                try:
                    date.fromisoformat(row["date"])
                    h, a = int(row["ft_home_goals"]), int(row["ft_away_goals"])
                    if None in row:
                        raise ValueError("extra CSV columns")
                    for field, total in (("ht_home_goals", h), ("ht_away_goals", a)):
                        if row.get(field, "") not in ("", None):
                            if not 0 <= int(row[field]) <= total:
                                raise ValueError("invalid halftime score")
                    if min(h, a) < 0:
                        raise ValueError("negative goals")
                    if row["ft_result"] != outcome(h, a):
                        raise ValueError("result/score mismatch")
                    if not row["home_team"].strip() or not row["away_team"].strip():
                        raise ValueError("missing team")
                    if row["home_team"] == row["away_team"]:
                        raise ValueError("identical teams")
                    league = row.get("league") or path.stem
                    key = (league, row["date"], row["home_team"], row["away_team"])
                    if key in seen:
                        raise ValueError("duplicate match key")
                    seen.add(key)
                    rows.append(dict(row, league=league))
                except (KeyError, ValueError) as error:
                    issues.append(f"{path.name}:{number}: {error}")
    if not rows and not issues:
        issues.append("No match rows found")
    return rows, issues


def backtest(rows, warmup=100):
    """League-frequency baseline; all games on a date predicted before update.

    Laplace smoothing; fixed warmup; no optimization on test data. This is a
    benchmark, not a team-strength model. Dates must be comparable per league.
    """
    if warmup < 1:
        raise ValueError("warmup must be positive")
    history = defaultdict(Counter)
    totals = defaultdict(lambda: dict(n=0, correct=0, home_correct=0, log_loss=0., brier=0.))
    for day, batch in groupby(sorted(rows, key=lambda r: r["date"]), key=lambda r: r["date"]):
        batch = list(batch)
        for row in batch:
            counts = history[row["league"]]
            n = sum(counts.values())
            if n < warmup:
                continue
            probabilities = {k: (counts[k] + 1) / (n + 3) for k in "HDA"}
            actual = row["ft_result"]
            metric = totals[row["league"]]
            metric["n"] += 1
            metric["correct"] += max(probabilities, key=probabilities.get) == actual
            metric["home_correct"] += actual == "H"
            metric["log_loss"] -= math.log(probabilities[actual])
            metric["brier"] += sum((probabilities[k] - (k == actual)) ** 2 for k in "HDA")
        for row in batch:
            history[row["league"]][row["ft_result"]] += 1
    return {league: {"evaluated": m["n"], "accuracy": m["correct"] / m["n"],
                     "always_home_accuracy": m["home_correct"] / m["n"],
                     "log_loss": m["log_loss"] / m["n"], "brier": m["brier"] / m["n"]}
            for league, m in sorted(totals.items())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--warmup", type=int, default=100)
    args = parser.parse_args()
    rows, issues = load_validated(args.directory)
    result = {"rows": len(rows), "issues": issues,
              "baseline": {} if issues else backtest(rows, args.warmup),
              "roi": None, "note": "No verified historical Sporttery odds; ROI unavailable."}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
