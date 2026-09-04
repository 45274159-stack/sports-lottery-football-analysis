from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


LIST_API = "https://webapi.sporttery.cn/gateway/uniform/fb/getMatchDataPageListV1.qry"
HEADERS = {
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://m.sporttery.cn/mjc/zqsj/?tab=result",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/134 Mobile Safari/537.36",
}


class SourceBlocked(RuntimeError):
    """Raised when the official site rejects the current network."""


def date_range(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content_type = response.headers.get_content_type()
            body = response.read()
    except urllib.error.HTTPError as error:
        if error.code in {403, 429, 567}:
            raise SourceBlocked(f"官方数据源拒绝当前网络：HTTP {error.code}") from error
        raise
    if content_type != "application/json" or body.lstrip().startswith(b"<"):
        raise SourceBlocked("官方数据源返回安全拦截页，而不是JSON")
    payload = json.loads(body)
    if payload.get("errorCode") not in {None, "0", "0000", "S0000"}:
        raise RuntimeError(f"官方接口返回错误：{payload.get('errorCode')} {payload.get('errorMessage', '')}")
    return payload


def flatten_matches(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload.get("value") or {}
    groups = value.get("matchInfoList") or []
    return [match for group in groups for match in (group.get("subMatchList") or [])]


def normalize_match(match: dict[str, Any], collected_at: str) -> dict[str, Any]:
    match_id = match.get("matchId") or match.get("match_id")
    return {
        "source_grade": "OFFICIAL",
        "source": "中国体育彩票竞彩网移动端公开赛果接口",
        "source_url": LIST_API,
        "collected_at": collected_at,
        "match_id": str(match_id) if match_id is not None else None,
        "match_date": match.get("matchDate"),
        "match_time": match.get("matchTime"),
        "match_num": match.get("matchNumStr") or match.get("matchNum"),
        "league": match.get("leagueAbbName") or match.get("leagueAllName"),
        "home_team": match.get("homeTeamAbbName") or match.get("homeTeamAllName"),
        "away_team": match.get("awayTeamAbbName") or match.get("awayTeamAllName"),
        "status": match.get("matchStatusName"),
        "half_score": match.get("sectionsNo1"),
        "full_score": match.get("sectionsNo999"),
        "raw": match,
    }


def collect_results(
    start: date,
    end: date,
    *,
    request: Callable[[str], dict[str, Any]] = fetch_json,
    delay: float = 0.4,
    page_limit: int = 100,
) -> list[dict[str, Any]]:
    collected_at = datetime.now(timezone.utc).isoformat()
    found: dict[str, dict[str, Any]] = {}
    for day in date_range(start, end):
        previous_ids: set[str] = set()
        for page in range(1, page_limit + 1):
            query = urllib.parse.urlencode({"method": "result", "matchDate": day.isoformat(), "pageNo": page})
            items = flatten_matches(request(f"{LIST_API}?{query}"))
            if not items:
                break
            page_ids = {str(item.get("matchId")) for item in items}
            if page_ids == previous_ids:
                break
            previous_ids = page_ids
            for item in items:
                row = normalize_match(item, collected_at)
                if row["match_id"]:
                    found[row["match_id"]] = row
            if delay:
                time.sleep(delay)
    return sorted(found.values(), key=lambda row: (row.get("match_date") or "", row.get("match_num") or ""))


def save_snapshot(path: str | Path, rows: list[dict[str, Any]], start: date, end: date) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "sporttery-official-results-1.0",
        "requested_range": {"start": start.isoformat(), "end": end.isoformat()},
        "count": len(rows),
        "matches": rows,
    }
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(destination)
