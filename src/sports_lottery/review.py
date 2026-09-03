from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ReviewStats:
    matches: int = 0
    home_wins: int = 0
    draws: int = 0
    away_wins: int = 0
    goals: int = 0
    over_2_5: int = 0
    both_score: int = 0

    def add(self, home_goals: int, away_goals: int, result: str) -> None:
        self.matches += 1
        self.goals += home_goals + away_goals
        self.home_wins += result == "H"
        self.draws += result == "D"
        self.away_wins += result == "A"
        self.over_2_5 += home_goals + away_goals >= 3
        self.both_score += home_goals > 0 and away_goals > 0

    def as_row(self, label: str) -> list[str]:
        if not self.matches:
            return [label, "0", "-", "-", "-", "-", "-", "-"]
        pct = lambda value: f"{value / self.matches:.1%}"
        return [
            label,
            str(self.matches),
            pct(self.home_wins),
            pct(self.draws),
            pct(self.away_wins),
            f"{self.goals / self.matches:.2f}",
            pct(self.over_2_5),
            pct(self.both_score),
        ]


def load_history(directory: str | Path) -> tuple[ReviewStats, dict[str, ReviewStats]]:
    root = Path(directory)
    total = ReviewStats()
    leagues: dict[str, ReviewStats] = {}
    files = sorted(root.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"目录中没有CSV：{root}")

    for path in files:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                league = row["league"]
                home_goals = int(row["ft_home_goals"])
                away_goals = int(row["ft_away_goals"])
                result = row["ft_result"]
                leagues.setdefault(league, ReviewStats()).add(home_goals, away_goals, result)
                total.add(home_goals, away_goals, result)
    return total, leagues


def render_review(directory: str | Path) -> str:
    total, leagues = load_history(directory)
    header = ["范围", "场次", "主胜", "平局", "客胜", "场均进球", "3球及以上", "双方进球"]
    rows = [total.as_row("总体")]
    rows.extend(stats.as_row(name) for name, stats in sorted(leagues.items()))
    widths = [max(len(row[index]) for row in [header, *rows]) for index in range(len(header))]
    line = lambda row: " | ".join(value.ljust(widths[index]) for index, value in enumerate(row))
    return "\n".join([line(header), line(["-" * width for width in widths]), *(line(row) for row in rows)])
