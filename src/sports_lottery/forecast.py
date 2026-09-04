"""Experimental regulation-time model; no odds or injury assumptions."""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict, deque
from datetime import date
from itertools import groupby

from .history_quality import load_validated


def markets(home_rate, away_rate):
    if not all(math.isfinite(x) and 0 < x <= 6 for x in (home_rate, away_rate)):
        raise ValueError("Goal rates must be finite and in (0, 6]")
    def poisson(rate):
        values = [math.exp(-rate)]
        for n in range(1, 41):
            values.append(values[-1] * rate / n)
        return values
    hp, ap = poisson(home_rate), poisson(away_rate)
    results = dict(H=0., D=0., A=0.)
    goals = {str(n): 0. for n in range(7)} | {"7+": 0.}
    scores = []
    for h, ph in enumerate(hp):
        for a, pa in enumerate(ap):
            p = ph * pa
            results["H" if h > a else "A" if h < a else "D"] += p
            goals[str(h+a) if h+a < 7 else "7+"] += p
            scores.append((f"{h}:{a}", p))
    mass = sum(results.values())
    return dict(result={k: v/mass for k, v in results.items()},
                total_goals={k: v/mass for k, v in goals.items()},
                scores=[(s, p/mass) for s, p in sorted(scores, key=lambda x: -x[1])[:5]],
                omitted_mass=max(0., 1-mass))


class ForecastModel:
    def __init__(self):
        self.leagues = defaultdict(list)
        self.venues = defaultdict(list)

    def observe(self, row):
        self.leagues[row["league"]].append(row)
        self.venues[(row["league"], row["home_team"], "H")].append(row)
        self.venues[(row["league"], row["away_team"], "A")].append(row)

    def predict(self, league, home, away, before):
        day = date.fromisoformat(before)
        prior = sorted((r for r in self.leagues[league] if r["date"] < before), key=lambda r: r["date"])[-500:]
        if len(prior) < 100:
            raise ValueError("Insufficient league history: need 100 earlier matches")
        base_h = sum(int(r["ft_home_goals"]) for r in prior)/len(prior)
        base_a = sum(int(r["ft_away_goals"]) for r in prior)/len(prior)
        def venue(team, side):
            rows = sorted((r for r in self.venues[(league, team, side)] if r["date"] < before), key=lambda r: r["date"])[-20:]
            # Fixed prior of five venue matches; older games decay by half in 180 days.
            weights = [2 ** (-(day-date.fromisoformat(r["date"])).days/180) for r in rows]
            denom = 5 + sum(weights)
            rate_h = (5*base_h + sum(w*int(r["ft_home_goals"]) for w,r in zip(weights, rows)))/denom
            rate_a = (5*base_a + sum(w*int(r["ft_away_goals"]) for w,r in zip(weights, rows)))/denom
            return rate_h, rate_a, len(rows), sum(weights)
        hh, ha, hn, he = venue(home, "H")
        ah, aa, an, ae = venue(away, "A")
        rate_h = min(6., max(.15, (hh+ah)/2))
        rate_a = min(6., max(.15, (ha+aa)/2))
        warnings = ["Injuries, lineups, travel and motivation not included", "Uncalibrated experimental model"]
        if min(he, ae) < 5:
            warnings.append("Insufficient recent venue sample; do not use as a confident selection")
        return dict(league=league, home=home, away=away, before=before,
                    expected_goals={"home": rate_h, "away": rate_a},
                    sample={"home": hn, "away": an, "home_effective": he, "away_effective": ae},
                    warnings=warnings, **markets(rate_h, rate_a))


def evaluate(rows, start="2024-07-01"):
    model = ForecastModel()
    totals = defaultdict(lambda: dict(n=0, correct=0, home_correct=0, log_loss=0.,
                                     brier=0., baseline_log_loss=0., score_correct=0, goals_correct=0))
    for day, batch in groupby(sorted(rows, key=lambda r: r["date"]), key=lambda r: r["date"]):
        batch = list(batch)
        for r in batch:
            if day < start or len(model.leagues[r["league"]]) < 100:
                continue
            p = model.predict(r["league"], r["home_team"], r["away_team"], day)
            prior = model.leagues[r["league"]][-500:]
            baseline = (1+sum(x["ft_result"] == r["ft_result"] for x in prior))/(3+len(prior))
            m = totals[r["league"]]
            actual = r["ft_result"]
            m["n"] += 1
            m["correct"] += max(p["result"], key=p["result"].get) == actual
            m["home_correct"] += actual == "H"
            m["log_loss"] -= math.log(max(p["result"][actual], 1e-15))
            m["baseline_log_loss"] -= math.log(baseline)
            m["brier"] += sum((p["result"][k]-(k==actual))**2 for k in "HDA")
            m["score_correct"] += p["scores"][0][0] == f'{r["ft_home_goals"]}:{r["ft_away_goals"]}'
            total = int(r["ft_home_goals"])+int(r["ft_away_goals"])
            m["goals_correct"] += max(p["total_goals"], key=p["total_goals"].get) == (str(total) if total < 7 else "7+")
        for r in batch:
            model.observe(r)
    return {league: {"matches": m["n"], **{k: v/m["n"] for k,v in m.items() if k != "n"}}
            for league,m in totals.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--start", default="2024-07-01")
    parser.add_argument("--home")
    parser.add_argument("--away")
    parser.add_argument("--league")
    parser.add_argument("--before")
    args = parser.parse_args()
    rows, issues = load_validated(args.directory)
    if issues:
        raise SystemExit("\n".join(issues))
    if any((args.home, args.away, args.league, args.before)):
        if not all((args.home, args.away, args.league, args.before)):
            parser.error("Prediction requires home, away, league and before")
        model = ForecastModel()
        for row in sorted(rows, key=lambda r: r["date"]):
            if row["date"] < args.before:
                model.observe(row)
        result = model.predict(args.league, args.home, args.away, args.before)
    else:
        date.fromisoformat(args.start)
        result = dict(evaluation_start=args.start, metrics=evaluate(rows, args.start),
                      roi=None, warning="Retrospective evaluation, not an untouched prospective test; no verified Sporttery odds")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
