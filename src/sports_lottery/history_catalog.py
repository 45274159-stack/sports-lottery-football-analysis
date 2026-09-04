"""Load every validated historical-results batch as one deduplicated catalog."""
from __future__ import annotations

from pathlib import Path

from .history_quality import load_validated


ROOT = Path(__file__).resolve().parents[2]
DATASETS = (
    ROOT / "data/processed/top5_2016_2026",
    ROOT / "data/processed/expanded_leagues_2016_2026",
    ROOT / "data/processed/completed_gaps_2025_26",
    ROOT / "data/processed/current_season_2026_27",
    ROOT / "data/processed/openfootball_2016_2026",
)


def load_all_history() -> list[dict[str, str]]:
    """Return all audited results, rejecting invalid, duplicate or conflicting rows."""
    result: list[dict[str, str]] = []
    seen: dict[tuple[str, str, str, str], tuple[str, str]] = {}
    problems: list[str] = []
    for directory in DATASETS:
        rows, issues = load_validated(str(directory))
        problems.extend(f"{directory.name}: {issue}" for issue in issues)
        for row in rows:
            key = row["league"], row["date"], row["home_team"], row["away_team"]
            score = row["ft_home_goals"], row["ft_away_goals"]
            if key in seen:
                label = "conflicting" if seen[key] != score else "duplicate"
                problems.append(f"{label} result: {key}")
                continue
            seen[key] = score
            result.append(row)
    if problems:
        raise ValueError(problems)
    return sorted(result, key=lambda row: (row["date"], row["league"], row["home_team"], row["away_team"]))
