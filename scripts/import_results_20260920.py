"""Import the cross-checked 2026-09-20 Sporttery result batch."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOTTERY_DATE = "2026-09-20"
OBSERVED = "2026-09-21T04:01:39Z"
CPBAO = "https://www.cpbao.com/jc/jcResult!getJczcResultNew.action?matchDate=20260920&playType=FSPF&t=1"
ZGZCW = "https://cp.zgzcw.com/dc/getKaijiangFootBall.action"
OFFICIAL = ["https://www.lottery.gov.cn/jc/zqsgkj/", "https://m.sporttery.cn/"]


# number|league|Beijing kickoff|home CN|away CN|FT|HT|home canonical|away canonical
RAW = """
周日001|Asian Games Men|2026-09-20 13:00|伊朗U23|中国U23|0:0|0:0|Iran U23|China U23
周日002|J1 League|2026-09-20 16:00|町田泽维亚|柏太阳神|2:4|1:0|Machida Zelvia|Kashiwa Reysol
周日003|J1 League|2026-09-20 16:00|大阪钢巴|神户胜利船|0:1|0:0|Gamba Osaka|Vissel Kobe
周日004|K League 1|2026-09-20 18:00|仁川联|大田市民|1:1|1:0|Incheon United|Daejeon Hana Citizen
周日005|Asian Games Men|2026-09-20 18:30|吉尔吉斯斯坦U23|日本U23|0:7|0:3|Kyrgyzstan U23|Japan U23
周日006|Serie A|2026-09-20 18:30|佛罗伦萨|那不勒斯|1:1|0:1|Fiorentina|Napoli
周日007|Championship|2026-09-20 19:00|狼队|西布罗姆维奇|1:0|0:0|Wolverhampton Wanderers|West Bromwich Albion
周日008|La Liga|2026-09-20 20:00|赫塔费|马拉加|1:0|0:0|Getafe|Malaga
周日009|Eredivisie|2026-09-20 20:30|特温特|埃因霍温|3:2|1:2|Twente|PSV Eindhoven
周日010|Premier League|2026-09-20 21:00|利兹联|水晶宫|0:0|0:0|Leeds United|Crystal Palace
周日011|Premier League|2026-09-20 21:00|伯恩茅斯|利物浦|0:1|0:0|Bournemouth|Liverpool
周日012|Premier League|2026-09-20 21:00|曼城|桑德兰|5:3|3:2|Manchester City|Sunderland
周日013|Serie A|2026-09-20 21:00|帕尔马|热那亚|2:1|1:0|Parma|Genoa
周日014|Serie A|2026-09-20 21:00|弗洛西诺内|科莫|2:0|2:0|Frosinone|Como
周日015|Bundesliga|2026-09-20 21:30|勒沃库森|RB莱比锡|2:0|1:0|Bayer Leverkusen|RB Leipzig
周日016|La Liga|2026-09-20 22:15|马德里竞技|皇家马德里|2:1|0:0|Atletico Madrid|Real Madrid
周日017|Allsvenskan|2026-09-20 22:30|米亚尔比|盖斯|0:3|0:1|Mjallby|GAIS
周日018|Eliteserien|2026-09-20 23:00|维京|利勒斯特罗姆|3:0|2:0|Viking|Lillestrom
周日019|Ligue 1|2026-09-20 23:15|尼斯|里尔|2:1|1:0|Nice|Lille
周日020|Premier League|2026-09-20 23:30|富勒姆|曼联|1:1|0:0|Fulham|Manchester United
周日021|Bundesliga|2026-09-20 23:30|沙尔克04|埃弗斯堡|0:0|0:0|Schalke 04|Elversberg
周日022|Serie A|2026-09-21 00:00|尤文图斯|亚特兰大|2:0|1:0|Juventus|Atalanta
周日023|La Liga|2026-09-21 00:30|比利亚雷亚尔|莱万特|3:1|1:1|Villarreal|Levante
周日024|La Liga|2026-09-21 00:30|拉科鲁尼亚|贝蒂斯|1:1|0:1|Deportivo La Coruna|Real Betis
周日025|Bundesliga|2026-09-21 01:30|帕德博恩|霍芬海姆|3:1|2:0|Paderborn|Hoffenheim
周日026|Serie A|2026-09-21 02:45|AC米兰|莱切|3:0|1:0|AC Milan|Lecce
周日027|Ligue 1|2026-09-21 02:45|马赛|巴黎圣日耳曼|1:2|0:0|Marseille|Paris Saint-Germain
周日028|La Liga|2026-09-21 03:00|巴伦西亚|皇家社会|2:3|0:1|Valencia|Real Sociedad
周日029|Primeira Liga|2026-09-21 03:30|波尔图|本菲卡|3:1|1:0|Porto|Benfica
周日030|Brasileirao|2026-09-21 06:30|巴拉纳竞技|巴伊亚|2:1|1:1|Athletico Paranaense|Bahia
"""


FIELDS = ["source","source_url","source_revision","source_row","observed_at","league","season","date","home_team","away_team","ft_home_goals","ft_away_goals","ft_result","ht_home_goals","ht_away_goals","ht_result","round","score_period","home_team_raw","away_team_raw"]


def outcome(home: int, away: int) -> str:
    return "H" if home > away else "A" if home < away else "D"


def parse_rows() -> list[dict]:
    result = []
    for line in RAW.strip().splitlines():
        number, league, kickoff, home, away, ft, ht, home_en, away_en = line.split("|")
        fh, fa = map(int, ft.split(":")); hh, ha = map(int, ht.split(":"))
        result.append({"number":number,"league":league,"kickoff":kickoff,"home":home,"away":away,
                       "fh":fh,"fa":fa,"hh":hh,"ha":ha,"home_en":home_en,"away_en":away_en})
    return result


def season(league: str) -> str:
    calendar = {"Asian Games Men", "J1 League", "K League 1", "Allsvenskan", "Eliteserien", "Brasileirao"}
    return "2026" if league in calendar else "2026-27"


def record(row: dict) -> dict:
    kickoff_date = row["kickoff"][:10]
    return {
        "match_key":f'{LOTTERY_DATE}-{row["number"]}', "display_number":row["number"],
        "home":row["home"], "away":row["away"], "league":row["league"], "status":"final",
        "kickoff_beijing":row["kickoff"].replace(" ", "T") + ":00+08:00",
        "home_goals":row["fh"], "away_goals":row["fa"],
        "half_home_goals":row["hh"], "half_away_goals":row["ha"],
        "total_goals":row["fh"]+row["fa"], "result":outcome(row["fh"],row["fa"]),
        "score_period":"90_minutes", "extra_time":None, "penalties":None,
        "verification":"cpbao_zgzcw_agree",
        "source_urls":[CPBAO, f"{ZGZCW}?startTime={kickoff_date}&endTime={kickoff_date}"],
    }


def csv_row(row: dict) -> dict:
    return {
        "source":"cpbao+zgzcw/result-crosscheck", "source_url":CPBAO, "source_revision":OBSERVED,
        "source_row":row["number"][-3:], "observed_at":OBSERVED, "league":row["league"],
        "season":season(row["league"]), "date":row["kickoff"][:10], "home_team":row["home_en"],
        "away_team":row["away_en"], "ft_home_goals":row["fh"], "ft_away_goals":row["fa"],
        "ft_result":outcome(row["fh"],row["fa"]), "ht_home_goals":row["hh"],
        "ht_away_goals":row["ha"], "ht_result":outcome(row["hh"],row["ha"]), "round":"",
        "score_period":"90_minutes", "home_team_raw":row["home"], "away_team_raw":row["away"],
    }


def dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    rows = parse_rows(); records = [record(row) for row in rows]
    dump(ROOT / "data/processed/results/2026-09-20.json", {
        "schema_version":1, "lottery_date":LOTTERY_DATE, "record_type":"sourced_results_batch",
        "model_training_ingested":True,
        "official_number_verification":"Official pages timed out. CPBao lottery-date results and ZGZCW Beijing-date results agree on all 30 final rows.",
        "observed_at":OBSERVED, "records":records,
    })
    dump(ROOT / "data/raw/results/2026-09-20/source_evidence.json", {
        "observed_at":OBSERVED, "lottery_date":LOTTERY_DATE,
        "sources":[
            *[{"url":url,"status":"timeout","usable":False,"note":"Official source attempted first; no bypass."} for url in OFFICIAL],
            {"url":CPBAO,"status":"http_200","role":"lottery-number and 90-minute score source"},
            {"url":ZGZCW,"status":"http_200","query_dates":["2026-09-20","2026-09-21"],"role":"kickoff, score and halftime cross-check"},
        ],
        "extracted_records":records,
        "pending_recheck":{"match_key":"2026-09-16-周三014","display_number":"周三014","home":"莱万特","away":"毕尔巴鄂竞技","status":"still_blank_on_both_indexes"},
    })
    csv_path = ROOT / "data/processed/current_season_2026_27/sporttery_2026-09-20.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS,lineterminator="\n"); writer.writeheader(); writer.writerows(csv_row(r) for r in rows)

    counts=Counter(r["result"] for r in records); goals=sum(r["total_goals"] for r in records)
    labels={"H":"主胜","D":"平","A":"客胜"}
    table=["|编号|北京时间|对阵|半场|90分钟|赛果|","|---|---|---|---:|---:|---:|"]
    for r in records:
        table.append(f'|{r["display_number"]}|{r["kickoff_beijing"][5:16].replace("T"," ")}|{r["home"]}—{r["away"]}|{r["half_home_goals"]}:{r["half_away_goals"]}|{r["home_goals"]}:{r["away_goals"]}|{labels[r["result"]]}|')
    report=f"""# 2026-09-20 竞彩足球赛果核验与复盘

体彩官方页面访问超时；彩宝按竞彩编号日列出的30场赛果与足彩网按北京时间开赛日给出的赛果逐场一致。全部以90分钟比分入库；本批没有需要记录的加时或点球。

## 执行结果

- 应核验：30场
- 已核验：30场
- 新增入库：30场
- 重复：0场
- 冲突：0场
- 本编号日待补查：0场
- 历史待补查：1场（2026-09-16 周三014）

{chr(10).join(table)}

主胜{counts['H']}场、平局{counts['D']}场、客胜{counts['A']}场；总进球{goals}个，场均{goals/len(records):.2f}个。明显偏离强弱预期的赛果包括特温特3:2埃因霍温、弗洛西诺内2:0科莫、马德里竞技2:1皇家马德里及波尔图3:1本菲卡。

## 预测复盘边界

仓库没有2026年9月20日开球前保存的统一预测档案，也没有可用的 `forecast_archive.sqlite`。Z1及其他模型真实可审计前瞻样本仍为0，因此不计算胜平负、比分、总进球命中率、Brier、log loss或收益率；生产模型未调整。

## 来源与限制

优先访问[中国体彩网赛果页]({OFFICIAL[0]})和[竞彩网]({OFFICIAL[1]})，但当前环境均超时，没有绕过限制。[彩宝9月20日竞彩赛果]({CPBAO})与[足彩网赛果索引]({ZGZCW})完成交叉核对。足彩网提供的半场比分已保留。逐行结构化证据保存在 `data/raw/results/2026-09-20/source_evidence.json`。
"""
    (ROOT / "reports/review_2026-09-20.md").write_text(report,encoding="utf-8")

    pending={"match_key":"2026-09-16-周三014","display_number":"周三014","league":"La Liga","kickoff_beijing":"2026-09-17T03:30:00+08:00","home":"莱万特","away":"毕尔巴鄂竞技","status":"unsettled_or_postponed","home_goals":None,"away_goals":None,"source_urls":["https://www.cpbao.com/jc/jcResult!getJczcResultNew.action?matchDate=20260916&playType=FSPF&t=1",f"{ZGZCW}?startTime=2026-09-17&endTime=2026-09-17"]}
    dump(ROOT / "reports/pending_results_20260921.json", {"checked_at":OBSERVED,"previous_pending_checked":1,"settled":[],"conflicts":[],"remaining_pending":[pending],"note":"2026-09-16 周三014 remains blank on both indexes and was not ingested."})
    dump(ROOT / "reports/current_season_update_20260921.json", {
        "as_of":OBSERVED,"batches":[{"path":"data/processed/current_season_2026_27/sporttery_2026-09-20.csv","rows":30,"net_new_since_previous_commit":30}],
        "completed_ingested":30,"pending_not_ingested":1,"pending_matches":[pending],"current_season_rows":466,"unified_catalog_rows":41145,
        "validation_issues":[],"duplicate_or_conflicting_keys":[],
        "official_source_gap":"China Sports Lottery and Sporttery official pages timed out; CPBao and ZGZCW agreed on all 30 imported rows.",
        "halftime_data_gap":None,"temporal_review":"not_scheduled_monday; auditable pre-kickoff archive missing and true prospective sample count is 0; production model unchanged",
    })


if __name__ == "__main__":
    main()
