"""Import verified scored matches from a pinned OpenFootball snapshot.

The importer deliberately excludes scoreless *records* only when the source has
no score field. A reported 0-0 remains a valid match. Fixtures on or after the
as-of date are excluded so a scheduled game cannot leak into a forecast.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from sports_lottery.history_quality import load_validated, outcome


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/openfootball_20260904"
CURRENT = ROOT / "data/processed/current_season_2026_27"
EXPANDED = ROOT / "data/processed/expanded_leagues_2016_2026"
GAPS = ROOT / "data/processed/completed_gaps_2025_26"
REPORT_JSON = ROOT / "reports/history_completeness_20260904.json"
REPORT_MD = ROOT / "reports/history_completeness_20260904.md"
AS_OF = date(2026, 9, 4)
OBSERVED_AT = "2026-09-04T23:33:53Z"
REVISION = "8aa4cd0ce0410b21037f063eeb4edd981081d85d"

LEAGUES = {
    "en.1": "Premier League", "de.1": "Bundesliga", "es.1": "La Liga",
    "fr.1": "Ligue 1", "it.1": "Serie A", "nl.1": "Eredivisie",
    "pt.1": "Primeira Liga",
}

# Explicit, reviewable aliases. Unknown names remain unchanged.
ALIASES = {
    "Premier League": {
        "AFC Bournemouth": "Bournemouth", "Arsenal FC": "Arsenal",
        "Aston Villa FC": "Aston Villa", "Brighton & Hove Albion FC": "Brighton",
        "Chelsea FC": "Chelsea", "Crystal Palace FC": "Crystal Palace",
        "Everton FC": "Everton", "Fulham FC": "Fulham", "Hull City AFC": "Hull",
        "Ipswich Town FC": "Ipswich", "Leeds United FC": "Leeds",
        "Liverpool FC": "Liverpool", "Manchester City FC": "Man City",
        "Manchester United FC": "Man United", "Newcastle United FC": "Newcastle",
        "Nottingham Forest FC": "Nott'm Forest", "Sunderland AFC": "Sunderland",
        "Tottenham Hotspur FC": "Tottenham", "AFC Coventry City": "Coventry",
        "Coventry City FC": "Coventry", "Brentford FC": "Brentford",
    },
    "Bundesliga": {
        "FC Bayern München": "Bayern Munich", "Borussia Dortmund": "Dortmund",
        "VfB Stuttgart": "Stuttgart", "1. FC Köln": "FC Koln",
        "1. FSV Mainz 05": "Mainz", "RB Leipzig": "RB Leipzig",
        "Bayer 04 Leverkusen": "Leverkusen", "Eintracht Frankfurt": "Ein Frankfurt",
        "SC Freiburg": "Freiburg", "FC Augsburg": "Augsburg",
        "VfL Wolfsburg": "Wolfsburg", "Werder Bremen": "Werder Bremen",
        "TSG 1899 Hoffenheim": "Hoffenheim", "1. FC Union Berlin": "Union Berlin",
        "Borussia Mönchengladbach": "M'gladbach", "Hamburger SV": "Hamburg",
        "FC St. Pauli": "St Pauli", "SC Paderborn 07": "Paderborn",
        "FC Schalke 04": "Schalke 04", "SV 07 Elversberg": "Elversberg",
        "SV Werder Bremen": "Werder Bremen",
    },
    "La Liga": {
        "Real Madrid CF": "Real Madrid", "FC Barcelona": "Barcelona",
        "Club Atlético de Madrid": "Ath Madrid", "Real Betis Balompié": "Betis",
        "Athletic Club": "Ath Bilbao", "Real Sociedad": "Sociedad",
        "Valencia CF": "Valencia", "Sevilla FC": "Sevilla", "Villarreal CF": "Villarreal",
        "RC Celta de Vigo": "Celta", "CA Osasuna": "Osasuna", "Getafe CF": "Getafe",
        "RCD Espanyol": "Espanol", "RCD Mallorca": "Mallorca", "Girona FC": "Girona",
        "Rayo Vallecano de Madrid": "Vallecano", "Deportivo Alavés": "Alaves",
        "Levante UD": "Levante", "Málaga CF": "Malaga", "UD Almería": "Almeria",
        "Elche CF": "Elche", "RC Deportivo La Coruña": "La Coruna",
        "RCD Espanyol de Barcelona": "Espanol",
        "Real Racing Club de Santander": "Santander",
        "Real Sociedad de Fútbol": "Sociedad",
    },
    "Ligue 1": {
        "Olympique Lyonnais": "Lyon", "Paris Saint-Germain FC": "Paris SG",
        "AS Monaco FC": "Monaco", "Olympique de Marseille": "Marseille",
        "LOSC Lille": "Lille", "AJ Auxerre": "Auxerre", "RC Strasbourg Alsace": "Strasbourg",
        "RC Lens": "Lens", "Toulouse FC": "Toulouse", "Stade Rennais FC 1901": "Rennes",
        "OGC Nice": "Nice", "FC Nantes": "Nantes", "Angers SCO": "Angers",
        "FC Lorient": "Lorient", "Stade Brestois 29": "Brest", "Paris FC": "Paris FC",
        "Le Havre AC": "Le Havre", "ES Troyes AC": "Troyes",
        "Le Mans FC": "Le Mans", "Lille OSC": "Lille",
        "Racing Club de Lens": "Lens",
    },
    "Serie A": {
        "AC Milan": "Milan", "FC Internazionale Milano": "Inter", "Juventus FC": "Juventus",
        "AS Roma": "Roma", "SSC Napoli": "Napoli", "SS Lazio": "Lazio",
        "ACF Fiorentina": "Fiorentina", "Atalanta BC": "Atalanta", "Bologna FC 1909": "Bologna",
        "Torino FC": "Torino", "Genoa CFC": "Genoa", "Como 1907": "Como",
        "Udinese Calcio": "Udinese", "US Lecce": "Lecce", "Parma Calcio 1913": "Parma",
        "Cagliari Calcio": "Cagliari", "US Sassuolo Calcio": "Sassuolo",
        "Hellas Verona FC": "Verona", "Venezia FC": "Venezia", "AC Monza": "Monza",
        "Frosinone Calcio": "Frosinone",
    },
    "Eredivisie": {
        "ADO Den Haag": "Den Haag", "SC Cambuur-Leeuwarden": "Cambuur",
    },
    "Primeira Liga": {
        "CS Marítimo": "Maritimo", "Académico de Viseu FC": "Viseu",
    },
}

FIELDS = ["source", "source_url", "source_revision", "source_row", "observed_at", "league",
          "season", "date", "home_team", "away_team", "ft_home_goals", "ft_away_goals",
          "ft_result", "ht_home_goals", "ht_away_goals", "ht_result", "round", "score_period",
          "home_team_raw", "away_team_raw"]


def scored_match(record):
    value = record.get("score")
    if isinstance(value, list) and len(value) == 2:
        return value, None
    if isinstance(value, dict) and isinstance(value.get("ft"), list) and len(value["ft"]) == 2:
        return value["ft"], value.get("ht")
    return None


def standard_name(league, name):
    expanded = json.loads((ROOT / "data/config/expanded_team_aliases.json").read_text())
    return ALIASES.get(league, {}).get(name, expanded.get(league, {}).get(name, name))


def rows_from(code, season):
    league = LEAGUES[code]
    path = RAW / season / f"{code}.json"
    payload = json.loads(path.read_text())
    url = f"https://raw.githubusercontent.com/openfootball/football.json/{REVISION}/{season}/{code}.json"
    accepted, rejected = [], []
    for number, match in enumerate(payload["matches"], 1):
        parsed = scored_match(match)
        if parsed is None:
            continue
        try:
            day = date.fromisoformat(match["date"])
            if day >= AS_OF:
                raise ValueError("on/after as-of date")
            ft, ht = parsed
            h, a = map(int, ft)
            if min(h, a) < 0:
                raise ValueError("negative goals")
            if ht is not None:
                hh, ha = map(int, ht)
                if not (0 <= hh <= h and 0 <= ha <= a):
                    raise ValueError("halftime exceeds fulltime")
            else:
                hh = ha = ""
            home_raw, away_raw = match["team1"], match["team2"]
            home, away = standard_name(league, home_raw), standard_name(league, away_raw)
            accepted.append(dict(
                source="openfootball/football.json", source_url=url, source_revision=REVISION,
                source_row=number, observed_at=OBSERVED_AT, league=league, season=season,
                date=day.isoformat(), home_team=home, away_team=away,
                ft_home_goals=h, ft_away_goals=a, ft_result=outcome(h, a),
                ht_home_goals=hh, ht_away_goals=ha,
                ht_result=outcome(hh, ha) if hh != "" else "", round=match.get("round", ""),
                score_period="source_reported_FT", home_team_raw=home_raw, away_team_raw=away_raw,
            ))
        except (KeyError, TypeError, ValueError) as error:
            rejected.append({"source_row": number, "reason": str(error), "record": match})
    return accepted, rejected, path, url


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(rows)


def write_completed_2025_gaps():
    additions, conflicts = {}, []
    for code in ("nl.1", "pt.1"):
        league = LEAGUES[code]
        new, rejected, _, _ = rows_from(code, "2025-26")
        target = EXPANDED / ("eredivisie.csv" if code == "nl.1" else "primeira_liga.csv")
        with target.open(encoding="utf-8", newline="") as stream:
            old = list(csv.DictReader(stream))
        index = {(r["date"], r["home_team"], r["away_team"]): r for r in old}
        gap_rows = []
        for row in new:
            key = row["date"], row["home_team"], row["away_team"]
            if key in index:
                prior = index[key]
                if (str(row["ft_home_goals"]), str(row["ft_away_goals"])) != (prior["ft_home_goals"], prior["ft_away_goals"]):
                    conflicts.append({"league": league, "key": key, "old": prior, "new": row})
                continue
            gap_rows.append(row); index[key] = row
        gap_rows.sort(key=lambda r: (r["date"], r["home_team"], r["away_team"]))
        write_csv(GAPS / ("eredivisie.csv" if code == "nl.1" else "primeira_liga.csv"), gap_rows)
        additions[league] = {"added": len(gap_rows), "original_total": len(old), "rejected": len(rejected)}
    return additions, conflicts


def audit():
    datasets = [
        ("top5", ROOT / "data/processed/top5_2016_2026"),
        ("expanded", EXPANDED), ("completed_gaps", GAPS), ("current", CURRENT),
        ("champions_league", ROOT / "data/processed/openfootball_2016_2026"),
    ]
    coverage, total, issues = {}, 0, []
    for label, directory in datasets:
        rows, found = load_validated(str(directory))
        issues.extend(f"{label}: {x}" for x in found)
        total += len(rows)
        for league in sorted({r["league"] for r in rows}):
            subset = [r for r in rows if r["league"] == league]
            entry = coverage.setdefault(league, {"rows": 0, "seasons": Counter(), "first_date": None, "last_date": None})
            entry["rows"] += len(subset)
            entry["seasons"].update(r.get("season", "unknown") for r in subset)
            dates = [r["date"] for r in subset]
            entry["first_date"] = min(filter(None, [entry["first_date"], min(dates)]))
            entry["last_date"] = max(filter(None, [entry["last_date"], max(dates)]))
    for value in coverage.values(): value["seasons"] = dict(sorted(value["seasons"].items()))
    return total, coverage, issues


def main():
    CURRENT.mkdir(parents=True, exist_ok=True)
    imported, quarantine, sources = 0, [], []
    for code, league in LEAGUES.items():
        rows, rejected, path, url = rows_from(code, "2026-27")
        write_csv(CURRENT / f"{code.replace('.', '_')}.csv", rows)
        imported += len(rows); quarantine.extend({"league": league, **x} for x in rejected)
        sources.append({"league": league, "path": str(path.relative_to(ROOT)), "url": url,
                        "revision": REVISION, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "accepted": len(rows), "rejected": len(rejected)})
    additions, conflicts = write_completed_2025_gaps()
    total, coverage, issues = audit()
    payload = {
        "as_of": AS_OF.isoformat(), "scope": "14 tracked competitions, not all world football",
        "new_current_season_matches": imported, "completed_2025_26_additions": additions,
        "total_validated_rows": total, "coverage": coverage, "validation_issues": issues,
        "conflicts": conflicts, "quarantine": quarantine, "sources": sources,
        "known_gaps": [
            "Eerste Divisie 2016-17 through 2019-20 absent",
            "Saudi Pro League 2017-18 through 2023-24 absent",
            "MLS 2024-2026 incomplete and phase/90-minute review pending",
            "Eliteserien 2024-2026 incomplete and phase/90-minute review pending",
            "2026-27 second divisions and Saudi/MLS/Eliteserien not available in this source snapshot",
            "No global lower-league, youth, women, reserve, friendly, or every cup competition coverage",
        ],
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    lines = ["# 足球历史数据完整性审计（2026-09-04）", "",
             f"- 当前校验通过：**{total:,} 场**", f"- 本次新增2026/27已完赛：**{imported} 场**",
             f"- 范围：{payload['scope']}", "", "## 联赛覆盖", "",
             "| 联赛 | 场次 | 首场 | 最新 | 赛季数 |", "|---|---:|---|---|---:|"]
    for league, item in sorted(coverage.items()):
        lines.append(f"| {league} | {item['rows']:,} | {item['first_date']} | {item['last_date']} | {len(item['seasons'])} |")
    lines += ["", "## 已知缺口", ""] + [f"- {x}" for x in payload["known_gaps"]]
    lines += ["", "## 结论", "", "当前库不是全球最近十年所有足球比赛的完整镜像。"
              "本报告只把可复现、带来源且比分明确的记录计为已入库；空比分不填0:0，未完赛不导入。"]
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"new": imported, "total": total, "issues": issues,
                      "additions_2025_26": additions, "conflicts": len(conflicts)}, ensure_ascii=False, indent=2))
    if issues or conflicts:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
