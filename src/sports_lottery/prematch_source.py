"""Auditable pre-match snapshots from Sporttery's public football endpoints.

The collector deliberately keeps provider values close to their source shape.  It
does not turn missing injuries into "healthy", and it never treats predicted or
scorer lists as an officially announced starting XI.
"""
from __future__ import annotations

import json
import time
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from .sporttery_source import LIST_API, fetch_json, flatten_matches, normalize_match


BASE_API = "https://webapi.sporttery.cn/gateway"
DETAIL_ENDPOINTS = {
    "fixed_bonus": "/uniform/football/getFixedBonusV1.qry",
    "injuries": "/uniform/football/getInjurySuspensionV1.qry",
    "feature": "/uniform/football/getMatchFeatureV1.qry",
    "recent_results": "/uniform/football/getMatchResultV1.qry",
    "tables": "/uniform/football/getMatchTablesV1.qry",
    "future_matches": "/uniform/football/getFutureMatchesV1.qry",
}

MARKET_FIELDS = {
    "had": ("h", "d", "a"),
    "hhad": ("goalLine", "h", "d", "a"),
    "ttg": tuple(f"s{i}" for i in range(8)),
    "hafu": ("hh", "hd", "ha", "dh", "dd", "da", "ah", "ad", "aa"),
}


def endpoint_url(endpoint: str, match_id: str) -> str:
    return BASE_API + DETAIL_ENDPOINTS[endpoint] + "?" + urllib.parse.urlencode(
        {"clientCode": "3001", "matchId": match_id}
    )


def _value(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("value")
    return value if isinstance(value, dict) else {}


def _compact(item: dict[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    # Keep strings exactly as published: Decimal conversion and rounding belong
    # in downstream analysis, not in the evidence layer.
    row = {key: item[key] for key in ("updateDate", "updateTime") if item.get(key) not in (None, "")}
    row.update({key: item[key] for key in fields if item.get(key) not in (None, "")})
    return row


def parse_fixed_bonus(payload: dict[str, Any]) -> dict[str, Any]:
    history = _value(payload).get("oddsHistory") or {}
    markets: dict[str, list[dict[str, Any]]] = {}
    for market, fields in MARKET_FIELDS.items():
        rows = history.get(f"{market}List") or []
        markets[market] = [_compact(row, fields) for row in rows if isinstance(row, dict)]

    crs_rows = []
    for item in history.get("crsList") or []:
        if not isinstance(item, dict):
            continue
        score_fields = sorted(
            key for key in item
            if (key.startswith("s") and key not in {"single"}) or key in {"winOther", "drawOther", "loseOther"}
        )
        crs_rows.append(_compact(item, score_fields))
    markets["crs"] = crs_rows
    return {
        "status": "available" if any(markets.values()) else "unavailable",
        "markets": markets,
        "note": "Each list is an ordered provider history; values are preserved without interpolation.",
    }


def _people(items: Any) -> list[dict[str, Any]]:
    rows = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        row = {
            "player": item.get("playerName") or item.get("name"),
            "position": item.get("positionName") or item.get("position"),
            "reason": item.get("injuryReason") or item.get("reason"),
            "status": item.get("status"),
        }
        if any(value not in (None, "") for value in row.values()):
            rows.append(row)
    return rows


def parse_injuries(payload: dict[str, Any]) -> dict[str, Any]:
    value = _value(payload)
    home, away = _people(value.get("homeList")), _people(value.get("awayList"))
    return {
        "status": "available" if "homeList" in value or "awayList" in value else "unavailable",
        "home": home,
        "away": away,
        "empty_means": "provider_returned_no_listed_absence" if "homeList" in value or "awayList" in value else "not_checked",
    }


def _team_block(value: dict[str, Any], side: str) -> dict[str, Any]:
    block = value.get(side) or value.get(f"{side}Team") or {}
    return block if isinstance(block, dict) else {}


def parse_technical_data(
    feature: dict[str, Any], recent_results: dict[str, Any], tables: dict[str, Any], future: dict[str, Any]
) -> dict[str, Any]:
    fv, rv, tv, uv = map(_value, (feature, recent_results, tables, future))
    return {
        "status": "available" if any((fv, rv, tv, uv)) else "unavailable",
        "scope": "current-season/provider match-detail data; not a ten-year aggregate",
        "feature": {
            "home": _team_block(fv, "home"),
            "away": _team_block(fv, "away"),
            "raw": fv,
        },
        "recent_results": {
            "home": _team_block(rv, "home"),
            "away": _team_block(rv, "away"),
            "raw": rv,
        },
        "tables": {
            "home": tv.get("homeTable") or [],
            "away": tv.get("awayTable") or [],
            "raw": tv,
        },
        "future_matches": {"raw": uv},
    }


def collect_match_list(
    match_date: date,
    *,
    request: Callable[[str], dict[str, Any]] = fetch_json,
    methods: tuple[str, ...] = ("all", "concern"),
    page_limit: int = 20,
) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for method in methods:
        previous: set[str] = set()
        for page in range(1, page_limit + 1):
            query = urllib.parse.urlencode(
                {"method": method, "matchDate": match_date.isoformat(), "pageNo": page}
            )
            items = flatten_matches(request(f"{LIST_API}?{query}"))
            if not items:
                break
            ids = {str(item.get("matchId")) for item in items if item.get("matchId") is not None}
            if ids == previous:
                break
            previous = ids
            for item in items:
                if item.get("matchId") is not None:
                    found[str(item["matchId"])] = item
    return sorted(found.values(), key=lambda row: (row.get("matchDate") or "", row.get("matchNumStr") or ""))


def _capture(
    endpoint: str,
    match_id: str,
    request: Callable[[str], dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    url = endpoint_url(endpoint, match_id)
    try:
        return request(url), {"status": "ok", "url": url}
    except Exception as error:  # one failed optional detail must not erase the fixture
        return {}, {"status": "error", "url": url, "error": f"{type(error).__name__}: {error}"}


def collect_prematch(
    match_date: date,
    *,
    request: Callable[[str], dict[str, Any]] = fetch_json,
    delay: float = 0.25,
) -> dict[str, Any]:
    captured_at = datetime.now(timezone.utc).isoformat()
    matches = collect_match_list(match_date, request=request)
    fixtures = []
    for raw_match in matches:
        normalized = normalize_match(raw_match, captured_at)
        match_id = normalized["match_id"]
        payloads: dict[str, dict[str, Any]] = {}
        provenance: dict[str, dict[str, Any]] = {}
        for endpoint in DETAIL_ENDPOINTS:
            payloads[endpoint], provenance[endpoint] = _capture(endpoint, match_id, request)
            if delay:
                time.sleep(delay)
        fixtures.append({
            "fixture": normalized,
            "fixed_bonus": parse_fixed_bonus(payloads["fixed_bonus"]),
            "availability": parse_injuries(payloads["injuries"]),
            "lineups": {
                "status": "unavailable",
                "expected": {"home": [], "away": []},
                "announced": {"home": [], "away": []},
                "note": "No official starting-XI endpoint was verified. Scorer/player pages are not lineups.",
            },
            "technical": parse_technical_data(
                payloads["feature"], payloads["recent_results"], payloads["tables"], payloads["future_matches"]
            ),
            "provenance": provenance,
            "raw_payloads": payloads,
        })
    return {
        "schema_version": "sporttery-prematch-snapshot-1.0",
        "match_date": match_date.isoformat(),
        "captured_at": captured_at,
        "timezone_note": "Match dates and times are preserved exactly as published by the provider.",
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
    }


def save_prematch_snapshot(path: str | Path, payload: dict[str, Any]) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite pre-match evidence: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(destination)
