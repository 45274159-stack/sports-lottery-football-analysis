"""Import the cross-checked 2026-09-21 Sporttery result batch."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOTTERY_DATE = "2026-09-21"
OBSERVED = "2026-09-22T03:59:11Z"
CPBAO = "https://www.cpbao.com/jc/jcResult!getJczcResultNew.action?matchDate=20260921&playType=FSPF&t=1"
MATCH_REPORT = "https://news.zhibo8.com/zuqiu/2026-09-21/match2113578date2026vnative.htm"
OFFICIAL = ["https://www.lottery.gov.cn/jc/zqsgkj/", "https://m.sporttery.cn/"]
POSTPONEMENT = "https://cadenaser.com/nacional/2026/09/17/temporal-alertas-y-partidos-laliga-explica-el-protocolo-que-se-siguio-con-levante-athletic-y-barca-racing-cadena-ser/"
PENDING_CPBAO = "https://www.cpbao.com/jc/jcResult!getJczcResultNew.action?matchDate=20260916&playType=FSPF&t=1"

FIELDS = ["source","source_url","source_revision","source_row","observed_at","league","season","date","home_team","away_team","ft_home_goals","ft_away_goals","ft_result","ht_home_goals","ht_away_goals","ht_result","round","score_period","home_team_raw","away_team_raw"]


def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    record = {
        "match_key": "2026-09-21-周一001",
        "display_number": "周一001",
        "home": "中国女足",
        "away": "菲律宾女足",
        "league": "Asian Games Women",
        "status": "final",
        "kickoff_beijing": "2026-09-21T15:00:00+08:00",
        "home_goals": 5,
        "away_goals": 1,
        "half_home_goals": 2,
        "half_away_goals": 0,
        "total_goals": 6,
        "result": "H",
        "score_period": "90_minutes",
        "extra_time": None,
        "penalties": None,
        "verification": "cpbao_match_report_agree",
        "source_urls": [CPBAO, MATCH_REPORT],
    }
    dump(ROOT / "data/processed/results/2026-09-21.json", {
        "schema_version": 1,
        "lottery_date": LOTTERY_DATE,
        "record_type": "sourced_results_batch",
        "model_training_ingested": True,
        "official_number_verification": "Official pages returned access-control page 567. CPBao and an independent match report agree on the only listed final match.",
        "observed_at": OBSERVED,
        "records": [record],
    })
    dump(ROOT / "data/raw/results/2026-09-21/source_evidence.json", {
        "observed_at": OBSERVED,
        "lottery_date": LOTTERY_DATE,
        "sources": [
            *[{"url": url, "status": "access_restricted_567", "usable": False, "note": "Official source attempted first; no bypass."} for url in OFFICIAL],
            {"url": CPBAO, "status": "http_200", "role": "lottery number, teams and 90-minute score"},
            {"url": MATCH_REPORT, "status": "http_200", "role": "kickoff, halftime and full-time cross-check"},
        ],
        "extracted_records": [record],
        "pending_recheck": {
            "match_key": "2026-09-16-周三014",
            "display_number": "周三014",
            "home": "莱万特",
            "away": "毕尔巴鄂竞技",
            "status": "postponed_weather",
            "reason": "Heavy rain and an unplayable pitch; no rescheduled final score available.",
            "source_urls": [PENDING_CPBAO, POSTPONEMENT],
        },
    })

    csv_path = ROOT / "data/processed/current_season_2026_27/sporttery_2026-09-21.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "source": "cpbao+match-report/result-crosscheck",
        "source_url": CPBAO,
        "source_revision": OBSERVED,
        "source_row": "001",
        "observed_at": OBSERVED,
        "league": "Asian Games Women",
        "season": "2026",
        "date": "2026-09-21",
        "home_team": "China Women",
        "away_team": "Philippines Women",
        "ft_home_goals": 5,
        "ft_away_goals": 1,
        "ft_result": "H",
        "ht_home_goals": 2,
        "ht_away_goals": 0,
        "ht_result": "H",
        "round": "Group G round 3",
        "score_period": "90_minutes",
        "home_team_raw": "中国女足",
        "away_team_raw": "菲律宾女足",
    }
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)

    pending = {
        "match_key": "2026-09-16-周三014",
        "display_number": "周三014",
        "league": "La Liga",
        "kickoff_beijing": "2026-09-17T03:30:00+08:00",
        "home": "莱万特",
        "away": "毕尔巴鄂竞技",
        "status": "postponed_weather",
        "reason": "Heavy rain left the pitch unplayable; rescheduled date not yet confirmed in checked sources.",
        "home_goals": None,
        "away_goals": None,
        "source_urls": [PENDING_CPBAO, POSTPONEMENT],
    }
    dump(ROOT / "reports/pending_results_20260922.json", {
        "checked_at": OBSERVED,
        "previous_pending_checked": 1,
        "settled": [],
        "conflicts": [],
        "remaining_pending": [pending],
        "note": "2026-09-16 周三014 was postponed because of heavy rain and remains without a final score; it was not ingested.",
    })
    dump(ROOT / "reports/current_season_update_20260922.json", {
        "as_of": OBSERVED,
        "batches": [{"path": "data/processed/current_season_2026_27/sporttery_2026-09-21.csv", "rows": 1, "net_new_since_previous_commit": 1}],
        "completed_ingested": 1,
        "pending_not_ingested": 1,
        "pending_matches": [pending],
        "current_season_rows": 467,
        "unified_catalog_rows": 41146,
        "validation_issues": [],
        "duplicate_or_conflicting_keys": [],
        "official_source_gap": "China Sports Lottery and Sporttery official pages returned access-control status 567; CPBao and an independent match report agreed on the only imported row.",
        "halftime_data_gap": None,
        "temporal_review": "not_scheduled_tuesday; auditable pre-kickoff archive missing and true prospective sample count is 0; production model unchanged",
    })

    report = f"""# 2026-09-21 竞彩足球赛果核验与复盘

体彩官方页面返回访问限制状态567；彩宝编号日赛果与独立赛后报道对唯一场次的编号、球队、开赛时间及90分钟比分一致。赛后报道同时确认半场2:0。该场没有加时或点球。

## 执行结果

- 应核验：1场
- 已核验：1场
- 新增入库：1场
- 重复：0场
- 冲突：0场
- 本编号日待补查：0场
- 历史待补查：1场（2026-09-16 周三014，暴雨延期）

|编号|北京时间|对阵|半场|90分钟|赛果|
|---|---|---|---:|---:|---:|
|周一001|09-21 15:00|中国女足—菲律宾女足|2:0|5:1|主胜|

本期主胜1场，总进球6个。中国女足以小组第一晋级亚运会女足八强；本场结果只作为历史赛果，不据此推断后续比赛必然走势。

## 预测复盘边界

仓库没有2026年9月21日开球前保存的统一预测档案，也没有可用的 `forecast_archive.sqlite`。Z1及其他模型真实可审计前瞻样本仍为0，因此不计算胜平负、比分、总进球命中率、Brier、log loss或收益率；生产模型未调整。

## 来源与限制

优先访问[中国体彩网赛果页]({OFFICIAL[0]})和[竞彩网]({OFFICIAL[1]})，均返回访问限制页面，没有绕过。[彩宝9月21日竞彩赛果]({CPBAO})与[独立赛后报道]({MATCH_REPORT})完成交叉核对。历史待补场经[赛事延期报道]({POSTPONEMENT})确认因暴雨延期，尚无重赛完场比分。逐行结构化证据保存在 `data/raw/results/2026-09-21/source_evidence.json`。
"""
    (ROOT / "reports/review_2026-09-21.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
