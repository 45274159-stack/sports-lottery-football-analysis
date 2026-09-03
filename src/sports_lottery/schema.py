from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv


REQUIRED_FIELDS = (
    "match_id",
    "lottery_date",
    "match_no",
    "competition",
    "kickoff_time",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
)

OPTIONAL_FIELDS = (
    "handicap",
    "spf_home_odds",
    "spf_draw_odds",
    "spf_away_odds",
    "rqspf_home_odds",
    "rqspf_draw_odds",
    "rqspf_away_odds",
    "source_url",
    "collected_at",
)


@dataclass(frozen=True)
class ValidationIssue:
    row: int
    field: str
    message: str


def _parse_int(value: str, field: str, row_number: int, issues: list[ValidationIssue]) -> int | None:
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        issues.append(ValidationIssue(row_number, field, "必须是整数"))
        return None


def _parse_float(value: str, field: str, row_number: int, issues: list[ValidationIssue]) -> float | None:
    if value == "":
        return None
    try:
        number = float(value)
    except ValueError:
        issues.append(ValidationIssue(row_number, field, "必须是数字"))
        return None
    if number <= 1:
        issues.append(ValidationIssue(row_number, field, "十进制赔率必须大于1"))
    return number


def validate_csv(path: str | Path) -> tuple[list[dict[str, object]], list[ValidationIssue]]:
    """Validate a normalized match CSV and return typed rows plus all issues."""
    source = Path(path)
    issues: list[ValidationIssue] = []
    typed_rows: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        for field in REQUIRED_FIELDS:
            if field not in headers:
                issues.append(ValidationIssue(1, field, "缺少必填列"))
        if issues:
            return [], issues

        for row_number, raw in enumerate(reader, start=2):
            row = {key: (value or "").strip() for key, value in raw.items()}
            for field in ("match_id", "lottery_date", "match_no", "competition", "kickoff_time", "home_team", "away_team"):
                if not row[field]:
                    issues.append(ValidationIssue(row_number, field, "不能为空"))

            match_id = row["match_id"]
            if match_id in seen_ids:
                issues.append(ValidationIssue(row_number, "match_id", "编号重复"))
            seen_ids.add(match_id)

            try:
                datetime.strptime(row["lottery_date"], "%Y-%m-%d")
            except ValueError:
                issues.append(ValidationIssue(row_number, "lottery_date", "格式应为YYYY-MM-DD"))
            try:
                datetime.fromisoformat(row["kickoff_time"])
            except ValueError:
                issues.append(ValidationIssue(row_number, "kickoff_time", "格式应为ISO 8601，如2026-09-04T03:00:00+08:00"))

            home_score = _parse_int(row["home_score"], "home_score", row_number, issues)
            away_score = _parse_int(row["away_score"], "away_score", row_number, issues)
            if (home_score is None) != (away_score is None):
                issues.append(ValidationIssue(row_number, "score", "主客比分必须同时填写或同时留空"))
            if home_score is not None and (home_score < 0 or away_score is not None and away_score < 0):
                issues.append(ValidationIssue(row_number, "score", "比分不能为负数"))

            typed: dict[str, object] = dict(row)
            typed["home_score"] = home_score
            typed["away_score"] = away_score
            typed["handicap"] = _parse_int(row.get("handicap", ""), "handicap", row_number, issues)
            for field in OPTIONAL_FIELDS:
                if field.endswith("_odds"):
                    typed[field] = _parse_float(row.get(field, ""), field, row_number, issues)
            typed_rows.append(typed)

    return typed_rows, issues

