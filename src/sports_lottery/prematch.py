"""Timestamped pre-match dossier; contextual evidence does not alter probabilities."""
from datetime import date
from .match_context import aware_time, validate_evidence, team_context
from .team_names import normalize_team

CATEGORIES = ("injuries", "lineup", "rest", "transfers", "cup")


def dossier(rows, fixture, at):
    cutoff, kickoff = aware_time(at), aware_time(fixture["kickoff"])
    if cutoff >= kickoff:
        raise ValueError("Dossier must precede kickoff")
    teams = [normalize_team(fixture[k]) for k in ("home", "away")]
    if len(set(teams)) != 2:
        raise ValueError("Distinct teams required")
    result = {t: {c: {"status": "unknown", "records": []} for c in CATEGORIES} for t in teams}
    warnings = []
    for raw in fixture.get("prematch", []):
        if raw.get("source_id") != fixture["source_id"]:
            raise ValueError("Prematch evidence match mismatch")
        t, category = normalize_team(raw.get("team", "")), raw.get("category")
        if t not in result or category not in CATEGORIES:
            raise ValueError("Unknown evidence team/category")
        item = validate_evidence(raw, at, fixture["kickoff"])
        if not item.get("summary", "").strip():
            raise ValueError("Evidence summary required")
        if item.get("source_type") not in {"official", "secondary"}:
            raise ValueError("Evidence source type required")
        details = item.get("details", {})
        if not isinstance(details, dict):
            raise ValueError("Evidence details must be an object")
        if category == "lineup":
            if details.get("kind") not in {"expected", "announced", "unknown"}:
                raise ValueError("Lineup kind required")
            players = details.get("players", [])
            if not isinstance(players, list) or any(not isinstance(p, str) or not p.strip() for p in players):
                raise ValueError("Invalid lineup players")
            if details["kind"] == "announced" and (len(players) != 11 or len(set(players)) != 11
                    or item["status"] != "confirmed" or item["source_type"] != "official"):
                raise ValueError("Announced XI needs eleven distinct players and official confirmation")
        if category == "rest" and "previous_kickoff" in details:
            previous = aware_time(details["previous_kickoff"])
            if previous >= cutoff:
                raise ValueError("Previous match must precede prediction")
            item = dict(item, kickoff_gap_hours=(kickoff-previous).total_seconds()/3600)
        if category == "cup":
            if details.get("kind") not in {"league", "single_leg", "two_leg", "unknown"}:
                raise ValueError("Competition format required")
            score = details.get("first_leg_score")
            if score is not None and (details["kind"] != "two_leg" or not isinstance(score, list)
                    or len(score) != 2 or any(type(g) is not int or g < 0 for g in score)):
                raise ValueError("First-leg score must be [this team goals, opponent goals]")
        result[t][category]["records"].append(item)
    # Date-only histories exclude the prediction's entire UTC date, matching compare().
    past = [r for r in rows if r["date"] < cutoff.date().isoformat()]
    for team in teams:
        context = team_context(past, team, cutoff.date().isoformat())
        result[team]["form"] = context
        played = [date.fromisoformat(r["date"]) for r in past
                  if team in (normalize_team(r["home_team"]), normalize_team(r["away_team"]))]
        result[team]["rest"]["historical_calendar_gap_days"] = (
            (kickoff.date()-max(played)).days if played else None)
        result[team]["rest"]["scope"] = "Supplied competitions only; calendar gap is not exact recovery time"
        for category in CATEGORIES:
            slot = result[team][category]
            if slot["records"]:
                # Preserve contradictions and earlier reports; never silently choose one.
                slot["status"] = "reported_requires_review"
                slot["records"].sort(key=lambda r: r["published_at"])
            else:
                warnings.append(f"{team}: missing {category} evidence")
    return {"version": "prematch-v1", "as_of": cutoff.isoformat(), "teams": result,
            "warnings": warnings, "numeric_adjustment": False,
            "note": "Sources are recorded, not independently authenticated. Expected XI is not announced XI. No automatic injury or motivation probability adjustment."}
