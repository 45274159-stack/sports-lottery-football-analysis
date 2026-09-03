from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import exp, factorial
import sqlite3


@dataclass(frozen=True)
class TeamForm:
    matches: int
    points_per_game: float
    goals_for_per_game: float
    goals_against_per_game: float


@dataclass(frozen=True)
class MatchEstimate:
    expected_home_goals: float
    expected_away_goals: float
    home_win: float
    draw: float
    away_win: float
    top_scores: tuple[tuple[str, float], ...]


def _team_form(connection: sqlite3.Connection, team: str, before: str, limit: int = 8) -> TeamForm:
    rows = connection.execute(
        """
        SELECT home_team, away_team, home_score, away_score
        FROM matches
        WHERE kickoff_time < ? AND home_score IS NOT NULL
          AND (home_team = ? OR away_team = ?)
        ORDER BY kickoff_time DESC
        LIMIT ?
        """,
        (before, team, team, limit),
    ).fetchall()
    if not rows:
        return TeamForm(0, 1.0, 1.25, 1.25)

    points = goals_for = goals_against = 0
    for row in rows:
        home = row["home_team"] == team
        scored = row["home_score"] if home else row["away_score"]
        conceded = row["away_score"] if home else row["home_score"]
        goals_for += scored
        goals_against += conceded
        points += 3 if scored > conceded else 1 if scored == conceded else 0
    count = len(rows)
    return TeamForm(count, points / count, goals_for / count, goals_against / count)


def _poisson(goals: int, expected: float) -> float:
    return exp(-expected) * expected**goals / factorial(goals)


def estimate_match(
    connection: sqlite3.Connection,
    home_team: str,
    away_team: str,
    kickoff_time: str,
    form_matches: int = 8,
) -> MatchEstimate:
    """Create a transparent baseline estimate using only matches before kickoff."""
    datetime.fromisoformat(kickoff_time)
    home = _team_form(connection, home_team, kickoff_time, form_matches)
    away = _team_form(connection, away_team, kickoff_time, form_matches)

    # Conservative blend with a small home advantage and league-neutral priors.
    home_xg = max(0.25, min(3.5, 0.45 * home.goals_for_per_game + 0.35 * away.goals_against_per_game + 0.45))
    away_xg = max(0.20, min(3.2, 0.45 * away.goals_for_per_game + 0.35 * home.goals_against_per_game + 0.20))

    score_probs: list[tuple[str, float]] = []
    home_win = draw = away_win = 0.0
    for home_goals in range(8):
        for away_goals in range(8):
            probability = _poisson(home_goals, home_xg) * _poisson(away_goals, away_xg)
            score_probs.append((f"{home_goals}:{away_goals}", probability))
            if home_goals > away_goals:
                home_win += probability
            elif home_goals == away_goals:
                draw += probability
            else:
                away_win += probability

    total = home_win + draw + away_win
    ranked = tuple(sorted(score_probs, key=lambda item: item[1], reverse=True)[:5])
    return MatchEstimate(
        round(home_xg, 3),
        round(away_xg, 3),
        home_win / total,
        draw / total,
        away_win / total,
        ranked,
    )

