"""Import the cross-checked 2026-09-22 Sporttery result batch."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOTTERY_DATE = "2026-09-22"
OBSERVED = "2026-09-23T04:01:37Z"
CPBAO = "https://www.cpbao.com/jc/jcResult!getJczcResultNew.action?matchDate=20260922&playType=FSPF&t=1"
ZGZCW = "https://cp.zgzcw.com/dc/getKaijiangFootBall.action"
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
                    queue = {
                        "checked_at": OBSERVED,
                        "previous_pending_checked": 0,
                        "settled": [],
                        "conflicts": [],
                        "remaining_pending": [],
                    }
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
                conflict_report.write_text(
                    json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
            raise RuntimeError(f"refusing to overwrite differing confirmed artifact: {path}")
        return
    path.write_text(content, encoding="utf-8")


def dump(path: Path, payload: object, *, conflict_report: Path | None = None) -> None:
    write_checked(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        conflict_report=conflict_report,
    )


def result(number: int, league: str, kickoff: str, home: str, away: str,
           home_en: str, away_en: str, ht: tuple[int, int], ft: tuple[int, int]) -> dict:
    return {
        "match_key": f"{LOTTERY_DATE}-周二{number:03d}",
        "display_number": f"周二{number:03d}",
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
        "verification": "cpbao_zgzcw_agree",
        "source_urls": [CPBAO, ZGZCW],
    }


def main() -> None:
    pending_path = ROOT / "reports/pending_results_20260923.json"
    records = [
        result(1, "Asian Games Men", "2026-09-22T18:00:00+08:00", "韩国U23", "沙特阿拉伯U23", "South Korea U23", "Saudi Arabia U23", (0, 0), (2, 0)),
        result(2, "EFL Trophy", "2026-09-23T02:00:00+08:00", "米尔顿凯恩斯", "克劳利", "Milton Keynes Dons", "Crawley Town", (2, 0), (4, 1)),
        result(3, "EFL Trophy", "2026-09-23T02:00:00+08:00", "诺茨郡", "格里姆斯比", "Notts County", "Grimsby Town", (1, 0), (2, 1)),
        result(4, "EFL Trophy", "2026-09-23T02:00:00+08:00", "维冈竞技", "布莱克浦", "Wigan Athletic", "Blackpool", (1, 0), (3, 2)),
    ]

    dump(ROOT / "data/processed/results/2026-09-22.json", {
        "schema_version": 1,
        "lottery_date": LOTTERY_DATE,
        "record_type": "sourced_results_batch",
        "model_training_ingested": True,
        "official_number_verification": "China Sports Lottery returned access-control status 567 and Sporttery timed out. CPBao and ZGZCW agree on all four final matches.",
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
    dump(ROOT / "data/raw/results/2026-09-22/source_evidence.json", {
        "observed_at": OBSERVED,
        "lottery_date": LOTTERY_DATE,
        "sources": [
            {"url": OFFICIAL[0], "status": "access_restricted_567", "usable": False, "note": "Official source attempted first; no bypass."},
            {"url": OFFICIAL[1], "status": "timeout", "usable": False, "note": "Official source attempted first; no bypass."},
            {"url": CPBAO, "status": "http_200", "role": "lottery numbers, teams and 90-minute scores"},
            {"url": ZGZCW, "status": "http_200", "role": "kickoff times, halftime and 90-minute score cross-check"},
        ],
        "raw_source_rows": {
            "cpbao": [
                "周二001 亚运男足 韩国亚 2:0 沙特亚",
                "周二002 英锦标赛 米尔顿 4:1 克劳利",
                "周二003 英锦标赛 诺茨郡 2:1 格里姆",
                "周二004 英锦标赛 维冈 3:2 布莱克浦",
            ],
            "zgzcw": [
                "周二001 09-22 18:00 韩国U23 2:0 (0:0) 沙特阿拉伯U23",
                "周二002 09-23 02:00 米尔顿 4:1 (2:0) 克劳利",
                "周二003 09-23 02:00 诺茨郡 2:1 (1:0) 格里姆",
                "周二004 09-23 02:00 维冈竞技 3:2 (1:0) 布莱克浦",
            ],
        },
        "extracted_records": records,
        "pending_recheck": pending,
    }, conflict_report=pending_path)

    csv_path = ROOT / "data/processed/current_season_2026_27/sporttery_2026-09-22.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in records:
        ht_result = "H" if row["half_home_goals"] > row["half_away_goals"] else "D" if row["half_home_goals"] == row["half_away_goals"] else "A"
        writer.writerow({
                "source": "cpbao+zgzcw/result-crosscheck",
                "source_url": CPBAO,
                "source_revision": OBSERVED,
                "source_row": row["display_number"][-3:],
                "observed_at": OBSERVED,
                "league": row["league"],
                "season": "2026" if row["league"] == "Asian Games Men" else "2026/27",
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
    dump(ROOT / "reports/current_season_update_20260923.json", {
        "as_of": OBSERVED,
        "batches": [{"path": "data/processed/current_season_2026_27/sporttery_2026-09-22.csv", "rows": 4, "net_new_since_previous_commit": 4}],
        "completed_ingested": 4,
        "pending_not_ingested": 1,
        "pending_matches": [pending],
        "current_season_rows": 471,
        "unified_catalog_rows": 41150,
        "validation_issues": [],
        "duplicate_or_conflicting_keys": [],
        "official_source_gap": "China Sports Lottery returned access-control status 567 and Sporttery timed out; CPBao and ZGZCW agreed on all four imported rows.",
        "halftime_data_gap": None,
        "temporal_review": "not_scheduled_wednesday; auditable pre-kickoff archive missing and true prospective sample count is 0; production model unchanged",
    }, conflict_report=pending_path)

    report = f"""# 2026-09-22 竞彩足球赛果核验与复盘

体彩官方页面分别返回访问限制状态567和超时，未绕过限制。彩宝编号日赛果与足彩网赛果对周二001—004的编号、球队和90分钟比分一致；足彩网同时提供开赛时间及半场比分。本批全部为90分钟完场，没有加时或点球。

## 执行结果

- 应核验：4场
- 已核验：4场
- 新增入库：4场
- 重复：0场
- 冲突：0场
- 本编号日待补查：0场
- 历史待补查：1场（2026-09-16 周三014，暴雨延期）

|编号|北京时间|对阵|半场|90分钟|赛果|
|---|---|---|---:|---:|---:|
|周二001|09-22 18:00|韩国U23—沙特阿拉伯U23|0:0|2:0|主胜|
|周二002|09-23 02:00|米尔顿凯恩斯—克劳利|2:0|4:1|主胜|
|周二003|09-23 02:00|诺茨郡—格里姆斯比|1:0|2:1|主胜|
|周二004|09-23 02:00|维冈竞技—布莱克浦|1:0|3:2|主胜|

本期主胜4场、平局0场、客胜0场；总进球15个，场均3.75个。

## 预测复盘边界

仓库没有2026年9月22日开球前保存的统一预测档案，也没有可用的 `forecast_archive.sqlite`。Z1及其他模型真实可审计前瞻样本仍为0，因此不计算胜平负、比分、总进球命中率、Brier、log loss或收益率；生产模型未调整。

## 来源与限制

优先访问[中国体彩网赛果页]({OFFICIAL[0]})和[竞彩网]({OFFICIAL[1]})，分别受访问限制和超时。[彩宝9月22日竞彩赛果]({CPBAO})与[足彩网赛果]({ZGZCW})完成交叉核对。历史待补场在[彩宝9月16日赛果]({PENDING_CPBAO})仍无比分，并经[赛事延期报道]({POSTPONEMENT})确认因暴雨延期，故继续待补、不入库。逐行证据保存在 `data/raw/results/2026-09-22/source_evidence.json`。
"""
    write_checked(ROOT / "reports/review_2026-09-22.md", report, conflict_report=pending_path)


if __name__ == "__main__":
    main()
