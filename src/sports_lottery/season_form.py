"""Season coverage, venue form and chronological opponent-strength context.

Elo is an experimental descriptive feature, not a win/draw/loss probability.
"""
from collections import defaultdict
from itertools import groupby
from datetime import date
from .team_names import normalize_team


def season_form(rows, league, team, before, season=None):
    date.fromisoformat(before)
    team = normalize_team(team)
    games, seen = [], set()
    for raw in rows:
        if raw["league"] != league or raw["date"] >= before:
            continue
        r = dict(raw, home_team=normalize_team(raw["home_team"]),
                 away_team=normalize_team(raw["away_team"]))
        key = (r["date"], r["home_team"], r["away_team"])
        if key in seen:
            raise ValueError("Duplicate match in season form")
        seen.add(key)
        date.fromisoformat(r["date"])
        h, a = int(r["ft_home_goals"]), int(r["ft_away_goals"])
        if min(h, a) < 0 or r["home_team"] == r["away_team"]:
            raise ValueError("Invalid completed match")
        games.append(r)
    ratings = defaultdict(lambda: 1500.)
    records = []
    for _, batch in groupby(sorted(games, key=lambda r: (r["date"], r["home_team"], r["away_team"])),
                           key=lambda r: r["date"]):
        changes = defaultdict(float)
        for r in batch:
            home, away = r["home_team"], r["away_team"]
            h, a = int(r["ft_home_goals"]), int(r["ft_away_goals"])
            expected = 1 / (1 + 10 ** ((ratings[away]-ratings[home]-60)/400))
            actual = 1. if h > a else 0. if h < a else .5
            delta = 20*(actual-expected)
            changes[home] += delta; changes[away] -= delta
            if team in (home, away):
                is_home = team == home
                records.append(dict(date=r["date"], season=r.get("season"), home=is_home,
                    opponent=away if is_home else home,
                    goals_for=h if is_home else a, goals_against=a if is_home else h,
                    opponent_elo_before=ratings[away if is_home else home],
                    performance_above_expected=(actual-expected) * (1 if is_home else -1)))
        for name, delta in changes.items():
            ratings[name] += delta
    def stats(items):
        n = len(items)
        return dict(matches=n, goals_for=sum(r["goals_for"] for r in items),
            goals_against=sum(r["goals_against"] for r in items),
            points_per_game=sum(3 if r["goals_for"] > r["goals_against"] else
                                1 if r["goals_for"] == r["goals_against"] else 0 for r in items)/n if n else None,
            mean_opponent_elo_before=sum(r["opponent_elo_before"] for r in items)/n if n else None,
            mean_performance_above_expected=sum(r["performance_above_expected"] for r in items)/n if n else None)
    current = [r for r in records if r["season"] == season] if season is not None else []
    scope = lambda items: dict(overall=stats(items), home=stats([r for r in items if r["home"]]),
                               away=stats([r for r in items if not r["home"]]))
    warnings = ["Experimental Elo: initial 1500, home advantage 60, K20; not a calibrated probability",
                "League-specific; missing competitions and promoted teams limit comparability"]
    if season is None: warnings.append("Fixture season unspecified; new-season coverage unknown")
    elif not current: warnings.append("No supplied completed matches for this team/season; do not treat as zero form")
    elif len(current) < 5: warnings.append("Fewer than five new-season matches; do not over-weight early results")
    return dict(version="season-form-v1", team=team, league=league, before=before, season=season,
                season_status="unspecified" if season is None else "available" if current else "missing",
                current_season=scope(current), historical=scope(records),
                last10=scope(records[-10:]), current_elo=ratings[team] if records else None,
                latest_match=records[-1]["date"] if records else None,
                recent_matches=records[-10:], warnings=warnings)
