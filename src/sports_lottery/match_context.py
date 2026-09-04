"""Past-only form features and timestamped evidence checks; no inferred injuries."""
from datetime import date, datetime, timezone
from .team_names import normalize_team


def aware_time(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timezone required")
    return result.astimezone(timezone.utc)


def team_context(rows, team, before, league=None):
    cutoff = date.fromisoformat(before)
    team = normalize_team(team)
    games = []
    for row in rows:
        if league is not None and row["league"] != league:
            continue
        played = date.fromisoformat(row["date"])
        if played >= cutoff:
            continue
        home, away = normalize_team(row["home_team"]), normalize_team(row["away_team"])
        if team not in (home, away):
            continue
        h, a = int(row["ft_home_goals"]), int(row["ft_away_goals"])
        gf, ga = (h, a) if home == team else (a, h)
        games.append(dict(date=played, home=home == team, gf=gf, ga=ga,
                          points=3 if gf > ga else 1 if gf == ga else 0))
    games.sort(key=lambda r: r["date"], reverse=True)
    def summarize(selected):
        n = len(selected)
        return dict(matches=n, goals_for=sum(r["gf"] for r in selected),
                    goals_against=sum(r["ga"] for r in selected),
                    points_per_game=sum(r["points"] for r in selected)/n if n else None)
    return dict(team=team, before=before, last5=summarize(games[:5]), last10=summarize(games[:10]),
                home10=summarize([r for r in games if r["home"]][:10]),
                away10=summarize([r for r in games if not r["home"]][:10]),
                days_since_last=(cutoff-games[0]["date"]).days if games else None,
                games_previous_7_days=sum((cutoff-r["date"]).days <= 7 for r in games),
                scope="supplied dataset only; missing competitions undercount workload",
                injuries=None, lineup=None, travel=None, motivation=None)


def validate_evidence(item, prediction_time, kickoff):
    """Reject post-prediction information, retain explicit unknown status."""
    prediction, start = aware_time(prediction_time), aware_time(kickoff)
    published, observed = aware_time(item["published_at"]), aware_time(item["observed_at"])
    if not published <= observed <= prediction < start:
        raise ValueError("Evidence unavailable at prediction time or prediction after kickoff")
    if not item.get("source_url", "").startswith("https://"):
        raise ValueError("HTTPS source URL required")
    if item.get("status") not in {"confirmed", "doubtful", "unknown"}:
        raise ValueError("Use explicit evidence status")
    return dict(item, age_hours=(prediction-published).total_seconds()/3600)
