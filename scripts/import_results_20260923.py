"""Import the cross-checked 2026-09-23 Sporttery result batch."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOTTERY_DATE = "2026-09-23"
OBSERVED = "2026-09-24T03:58:34Z"
CPBAO = "https://www.cpbao.com/jc/jcResult!getJczcResultNew.action?matchDate=20260923&playType=FSPF&t=1"
ZGZCW = "https://cp.zgzcw.com/dc/getKaijiangFootBall.action"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard?dates=20260923"
MLS = "https://www.mlssoccer.com/competitions/mls-regular-season/2026/matches/seavsrsl-09-23-2026/"
OFFICIAL = ["https://www.lottery.gov.cn/jc/zqsgkj/", "https://m.sporttery.cn/"]
POSTPONEMENT = "https://cadenaser.com/nacional/2026/09/17/temporal-alertas-y-partidos-laliga-explica-el-protocolo-que-se-siguio-con-levante-athletic-y-barca-racing-cadena-ser/"
PENDING_CPBAO = "https://www.cpbao.com/jc/jcResult!getJczcResultNew.action?matchDate=20260916&playType=FSPF&t=1"

FIELDS = ["source", "source_url", "source_revision", "source_row", "observed_at", "league", "season", "date", "home_team", "away_team", "ft_home_goals", "ft_away_goals", "ft_result", "ht_home_goals", "ht_away_goals", "ht_result", "round", "score_period", "home_team_raw", "away_team_raw"]


def write_checked(path: Path, content: str, *, conflict_report: Path | None = None) -> None:
    """Create a batch artifact or accept an identical rerun, never overwrite."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != content:
            if conflict_report is not None:
                if conflict_report.exists():
                    queue = json.loads(conflict_report.read_text(encoding="utf-8"))
                else:
                    queue = {"checked_at": OBSERVED, "previous_pending_checked": 0, "settled": [], "conflicts": [], "remaining_pending": []}
                conflict = {
                    "target": str(path),
                    "existing_sha256": hashlib.sha256(existing.encode()).hexdigest(),
                    "proposed_sha256": hashlib.sha256(content.encode()).hexdigest(),
                    "detected_at": OBSERVED,
                    "status": "conflict_requires_review",
                }
                if conflict not in queue["conflicts"]:
                    queue["conflicts"].append(conflict)
                conflict_report.parent.mkdir(parents=True, exist_ok=True)
                conflict_report.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise RuntimeError(f"refusing to overwrite differing confirmed artifact: {path}")
        return
    path.write_text(content, encoding="utf-8")


def dump(path: Path, payload: object, *, conflict_report: Path | None = None) -> None:
    write_checked(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n", conflict_report=conflict_report)


def result(number: int, league: str, kickoff: str, home: str, away: str,
           home_en: str, away_en: str, ht: tuple[int, int], ft: tuple[int, int],
           verification: str, source_urls: list[str]) -> dict:
    return {
        "match_key": f"{LOTTERY_DATE}-周三{number:03d}",
        "display_number": f"周三{number:03d}",
        "home": home,
        "away": away,
        "home_normalized": home_en,
        "away_normalized": away_en,
        "league": league,
        "status": "final",
        "kickoff_beijing": kickoff,
        "home_goals": ft[0],
        "away_goals": ft[1],
        "half_home_goals": ht[0],
        "half_away_goals": ht[1],
        "total_goals": sum(ft),
        "result": "H" if ft[0] > ft[1] else "D" if ft[0] == ft[1] else "A",
        "score_period": "90_minutes",
        "extra_time": None,
        "penalties": None,
        "verification": verification,
        "source_urls": source_urls,
    }


def main() -> None:
    pending_path = ROOT / "reports/pending_results_20260924.json"
    records = [
        result(1, "Asian Games Men", "2026-09-23T13:30:00+08:00", "中国U23", "阿联酋U23", "China U23", "United Arab Emirates U23", (0, 0), (0, 0), "cpbao_zgzcw_agree", [CPBAO, ZGZCW]),
        result(2, "Asian Games Men", "2026-09-23T18:30:00+08:00", "日本U23", "泰国U23", "Japan U23", "Thailand U23", (1, 0), (3, 0), "cpbao_zgzcw_agree", [CPBAO, ZGZCW]),
        result(3, "MLS", "2026-09-24T09:30:00+08:00", "西雅图", "盐湖城", "Seattle Sounders FC", "Real Salt Lake", (0, 0), (2, 0), "zgzcw_espn_mls_agree", [ZGZCW, ESPN, MLS]),
    ]

    dump(ROOT / "data/processed/results/2026-09-23.json", {
        "schema_version": 1,
        "lottery_date": LOTTERY_DATE,
        "record_type": "sourced_results_batch",
        "model_training_ingested": True,
        "official_number_verification": "China Sports Lottery and Sporttery both returned access-control status 567. CPBao and ZGZCW agree on matches 001-002; ZGZCW, ESPN and MLS agree on match 003.",
        "observed_at": OBSERVED,
        "records": records,
    }, conflict_report=pending_path)

    pending = {
        "match_key": "2026-09-16-周三014",
        "display_number": "周三014",
        "league": "La Liga",
        "kickoff_beijing": "2026-09-17T03:30:00+08:00",
        "home": "莱万特",
        "away": "毕尔巴鄂竞技",
        "status": "postponed_weather",
        "reason": "Heavy rain left the pitch unplayable; the checked lottery result page still has no final score.",
        "home_goals": None,
        "away_goals": None,
        "source_urls": [PENDING_CPBAO, POSTPONEMENT],
    }
    dump(ROOT / "data/raw/results/2026-09-23/source_evidence.json", {
        "observed_at": OBSERVED,
        "lottery_date": LOTTERY_DATE,
        "sources": [
            {"url": OFFICIAL[0], "status": "access_restricted_567", "usable": False, "note": "Official source attempted first; no bypass."},
            {"url": OFFICIAL[1], "status": "access_restricted_567", "usable": False, "note": "Official source attempted first; no bypass."},
            {"url": CPBAO, "status": "http_200", "role": "lottery numbers, teams and 90-minute scores for 001-002; 003 still blank at collection time"},
            {"url": ZGZCW, "status": "http_200", "role": "all lottery numbers, kickoff times, halftime and 90-minute score cross-check"},
            {"url": ESPN, "status": "http_200", "role": "Seattle 2-0 Real Salt Lake final score and UTC kickoff cross-check"},
            {"url": MLS, "status": "http_200", "role": "competition-official Seattle vs Real Salt Lake match page"},
        ],
        "raw_source_rows": {
            "cpbao": [
                "周三001 亚运男足 中国亚 0:0 阿联酋亚",
                "周三002 亚运男足 日本亚 3:0 泰国亚",
                "周三003 美职 西雅图 -:- 盐湖城（采集时未更新）",
            ],
            "zgzcw": [
                "周三001 09-23 13:30 中国U23 0:0 (0:0) 阿联酋U23",
                "周三002 09-23 18:30 日本U23 3:0 (1:0) 泰国U23",
                "周三003 09-24 09:30 西雅图 2:0 (0:0) 盐湖城",
            ],
            "espn": ["Real Salt Lake at Seattle Sounders FC; 2026-09-24T01:30Z; Full Time; Seattle 2, Real Salt Lake 0"],
        },
        "extracted_records": records,
        "pending_recheck": pending,
    }, conflict_report=pending_path)

    csv_path = ROOT / "data/processed/current_season_2026_27/sporttery_2026-09-23.csv"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in records:
        ht_result = "H" if row["half_home_goals"] > row["half_away_goals"] else "D" if row["half_home_goals"] == row["half_away_goals"] else "A"
        writer.writerow({
            "source": "crosschecked/result-import",
            "source_url": row["source_urls"][0],
            "source_revision": OBSERVED,
            "source_row": row["display_number"][-3:],
            "observed_at": OBSERVED,
            "league": row["league"],
            "season": "2026" if row["league"] == "Asian Games Men" else "2026",
            "date": LOTTERY_DATE,
            "home_team": row["home_normalized"],
            "away_team": row["away_normalized"],
            "ft_home_goals": row["home_goals"],
            "ft_away_goals": row["away_goals"],
            "ft_result": row["result"],
            "ht_home_goals": row["half_home_goals"],
            "ht_away_goals": row["half_away_goals"],
            "ht_result": ht_result,
            "round": "",
            "score_period": "90_minutes",
            "home_team_raw": row["home"],
            "away_team_raw": row["away"],
        })
    write_checked(csv_path, stream.getvalue(), conflict_report=pending_path)

    dump(pending_path, {
        "checked_at": OBSERVED,
        "previous_pending_checked": 1,
        "settled": [],
        "conflicts": [],
        "remaining_pending": [pending],
        "note": "2026-09-16 周三014 remains postponed and has no final score; it was not ingested.",
    })
    dump(ROOT / "reports/current_season_update_20260924.json", {
        "as_of": OBSERVED,
        "batches": [{"path": "data/processed/current_season_2026_27/sporttery_2026-09-23.csv", "rows": 3, "net_new_since_previous_commit": 3}],
        "completed_ingested": 3,
        "duplicate_existing": 0,
        "conflicts": 0,
        "pending_not_ingested": 1,
        "pending_matches": [pending],
        "current_season_rows": 474,
        "unified_catalog_rows": 41153,
        "validation_issues": [],
        "duplicate_or_conflicting_keys": [],
        "official_source_gap": "China Sports Lottery and Sporttery returned access-control status 567; secondary sources agreed on all imported rows, and the MLS row also has ESPN and competition-official support.",
        "halftime_data_gap": None,
        "temporal_review": "not_scheduled_thursday; auditable pre-kickoff archive missing and true prospective sample count is 0; production model unchanged",
    }, conflict_report=pending_path)

    report = f"""# 2026-09-23 竞彩足球赛果核验与复盘

体彩两个官方入口均返回访问限制状态567，未绕过限制。彩宝与足彩网对周三001—002的编号、球队和90分钟比分一致；周三003由足彩网、ESPN及MLS官方比赛页交叉确认。本批全部为90分钟完场，没有加时或点球。

## 执行结果

- 应核验：3场
- 已核验：3场
- 新增入库：3场
- 重复：0场
- 冲突：0场
- 本编号日待补查：0场
- 历史待补查：1场（2026-09-16 周三014，暴雨延期）

|编号|北京时间|对阵|半场|90分钟|赛果|
|---|---|---|---:|---:|---:|
|周三001|09-23 13:30|中国U23—阿联酋U23|0:0|0:0|平|
|周三002|09-23 18:30|日本U23—泰国U23|1:0|3:0|主胜|
|周三003|09-24 09:30|西雅图—盐湖城|0:0|2:0|主胜|

本期主胜2场、平局1场、客胜0场；总进球5个，场均1.67个。

## 预测复盘边界

仓库没有2026年9月23日开球前保存的统一预测档案，也没有可用的 `forecast_archive.sqlite`。Z1及其他模型真实可审计前瞻样本仍为0，因此不计算胜平负、比分、总进球命中率、Brier、log loss或收益率；生产模型未调整。

## 来源与限制

优先访问[中国体彩网赛果页]({OFFICIAL[0]})和[竞彩网]({OFFICIAL[1]})，均受访问限制。[彩宝9月23日竞彩赛果]({CPBAO})与[足彩网赛果]({ZGZCW})核对001—002；003经[ESPN赛果接口]({ESPN})和[MLS官方比赛页]({MLS})补充交叉确认。历史待补场在[彩宝9月16日赛果]({PENDING_CPBAO})仍无比分，并经[赛事延期报道]({POSTPONEMENT})确认因暴雨延期，故继续待补、不入库。逐行证据保存在 `data/raw/results/2026-09-23/source_evidence.json`。
"""
    write_checked(ROOT / "reports/review_2026-09-23.md", report, conflict_report=pending_path)


if __name__ == "__main__":
    main()
