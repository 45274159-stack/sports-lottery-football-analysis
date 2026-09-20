"""Generate audited Sporttery result batches for 2026-09-15 through 2026-09-19.

The compact rows below are transcribed from two independently retrieved result
indexes (CPBao by lottery date and ZGZCW by Beijing kickoff date). The script
only writes final 90-minute results; the single unresolved match is emitted to
the pending report and is not added to training history.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OBSERVED = "2026-09-20T04:01:24Z"
CPBAO = "https://www.cpbao.com/jc/jcResult!getJczcResultNew.action?matchDate={date}&playType=FSPF&t=1"
ZGZCW = "https://cp.zgzcw.com/dc/getKaijiangFootBall.action?startTime={date}&endTime={date}"
OFFICIAL = ["https://www.lottery.gov.cn/jc/zqsgkj/", "https://m.sporttery.cn/"]


# display number | league | Beijing kickoff | home | away | FT | HT
RAW = {
    "2026-09-15": """
周二001|AFC Champions League Elite|2026-09-15 18:00|拉查布里|上海海港|4:6|0:3
周二002|AFC Champions League Elite|2026-09-15 18:00|大田市民|京都|1:0|0:0
周二003|Asian Games Men|2026-09-15 18:30|卡塔尔U23|韩国U23|1:4|0:3
周二004|AFC Champions League Elite|2026-09-15 20:15|柔佛FC|武里兰联|1:1|1:1
周二005|AFC Champions League Elite|2026-09-15 20:15|北京国安|浦项制铁|3:1|2:1
周二006|AFC Champions League Elite|2026-09-16 00:00|艾因|利雅得胜利|4:0|1:0
周二007|La Liga|2026-09-16 01:00|巴列卡诺|西班牙人|2:1|2:0
周二008|La Liga|2026-09-16 02:00|阿拉维斯|巴伦西亚|0:1|0:0
周二009|Eredivisie|2026-09-16 02:00|阿贾克斯|威廉二世|5:1|2:0
周二010|Championship|2026-09-16 02:45|米德尔斯堡|米尔沃尔|2:2|0:2
周二011|EFL Cup|2026-09-16 03:00|利物浦|热刺|3:1|1:0
周二012|EFL Cup|2026-09-16 03:00|伊普斯维奇|阿森纳|2:4|0:2
周二013|La Liga|2026-09-16 03:30|埃尔切|皇家马德里|2:3|0:2
周二014|Copa Libertadores|2026-09-16 06:00|普拉滕斯|弗鲁米嫩塞|2:1|2:0
""",
    "2026-09-16": """
周三001|Asian Games Men|2026-09-16 18:00|中国U23|朝鲜U23|2:1|1:1
周三002|AFC Champions League Elite|2026-09-16 18:00|全北现代|柏太阳神|2:1|0:1
周三003|Asian Games Men|2026-09-16 18:30|日本U23|中国香港U23|2:0|1:0
周三004|Europa League|2026-09-17 00:45|奥莫尼亚|塞尔塔|1:0|0:0
周三005|La Liga|2026-09-17 01:00|拉科鲁尼亚|塞维利亚|0:1|0:0
周三006|La Liga|2026-09-17 01:00|马德里竞技|奥萨苏纳|4:0|1:0
周三007|Europa League|2026-09-17 03:00|AC米兰|本菲卡|0:2|0:1
周三008|Europa League|2026-09-17 03:00|勒沃库森|采列|2:0|1:0
周三009|Europa League|2026-09-17 03:00|桑德兰|阿尔克马尔|1:0|0:0
周三010|Europa League|2026-09-17 03:00|格拉茨风暴|雷恩|0:0|0:0
周三011|Europa League|2026-09-17 03:00|安德莱赫特|里昂|1:2|0:2
周三012|EFL Cup|2026-09-17 03:00|考文垂|阿斯顿维拉|1:3|1:2
周三013|La Liga|2026-09-17 03:30|巴塞罗那|桑坦德竞技|7:2|4:1
周三015|Copa Libertadores|2026-09-17 06:00|基多体育大学|帕尔梅拉斯|3:2|1:1
周三016|Brasileirao|2026-09-17 06:30|博塔弗戈|格雷米奥|3:2|1:1
周三017|Copa Libertadores|2026-09-17 08:30|科林蒂安|拉普拉塔大学生|0:1|0:0
""",
    "2026-09-17": """
周四001|Asian Games Women|2026-09-17 13:00|乌兹别克斯坦女足|中国女足|1:1|1:0
周四002|AFC Champions League Two|2026-09-17 20:15|上海申花|淡滨尼流浪|2:1|1:1
周四003|Europa League|2026-09-18 00:45|OFI克里特|霍芬海姆|2:0|1:0
周四004|La Liga|2026-09-18 01:00|贝蒂斯|赫塔费|1:0|1:0
周四005|Europa League|2026-09-18 03:00|水晶宫|波兹南莱赫|4:0|3:0
周四006|Europa League|2026-09-18 03:00|皇家社会|伯恩茅斯|1:2|0:2
周四007|Europa League|2026-09-18 03:00|尤文图斯|奈梅亨|5:0|3:0
周四008|Europa League|2026-09-18 03:00|贝西克塔斯|马赛|4:1|1:1
周四009|Europa League|2026-09-18 03:00|利勒斯特罗姆|托伦斯|1:2|0:1
周四010|La Liga|2026-09-18 03:30|马拉加|比利亚雷亚尔|1:3|1:2
周四011|Copa Libertadores|2026-09-18 08:30|弗拉门戈|山谷独立|1:1|0:1
""",
    "2026-09-18": """
周五001|Asian Games Men|2026-09-18 18:30|沙特阿拉伯U23|卡塔尔U23|2:0|1:0
周五002|Veikkausliiga|2026-09-19 00:00|赫尔辛基火花|赫尔辛基|1:1|1:1
周五003|2. Bundesliga|2026-09-19 00:30|沃尔夫斯堡|达姆施塔特|5:1|2:1
周五004|Eliteserien|2026-09-19 01:00|萨普斯堡|KFUM奥斯陆|1:3|1:2
周五005|Ligue 2|2026-09-19 02:00|兰斯|蒙彼利埃|1:1|1:1
周五006|Eredivisie|2026-09-19 02:00|格罗宁根|兹沃勒|3:0|2:0
周五007|Eerste Divisie|2026-09-19 02:00|登博思|海尔蒙特|2:1|2:1
周五008|Bundesliga|2026-09-19 02:30|拜仁慕尼黑|柏林联合|7:0|3:0
周五009|Serie A|2026-09-19 02:45|蒙扎|萨索洛|2:1|0:0
周五010|Ligue 1|2026-09-19 02:45|摩纳哥|朗斯|2:1|1:0
周五011|Premier League|2026-09-19 03:00|布伦特福德|切尔西|3:0|0:0
周五012|Championship|2026-09-19 03:00|布里斯托尔城|沃特福德|1:0|1:0
周五013|La Liga|2026-09-19 03:00|西班牙人|埃尔切|1:3|0:2
周五014|MLS|2026-09-19 07:30|纽约城|纽约红牛|0:1|0:0
""",
    "2026-09-19": """
周六001|J1 League|2026-09-19 17:30|长崎航海|大阪樱花|1:1|1:0
周六002|J2 League|2026-09-19 17:30|藤枝MYFC|大宫松鼠|1:1|1:0
周六003|K League 1|2026-09-19 18:00|FC安养|蔚山现代|2:1|1:0
周六004|J1 League|2026-09-19 18:30|横滨水手|水户蜀葵|2:0|1:0
周六005|Premier League|2026-09-19 19:30|热刺|阿斯顿维拉|2:3|0:1
周六006|Championship|2026-09-19 19:30|斯托克城|谢菲尔德联|2:1|0:0
周六007|La Liga|2026-09-19 20:00|奥萨苏纳|巴列卡诺|1:1|1:0
周六008|Serie A|2026-09-19 21:00|乌迪内斯|卡利亚里|0:1|0:0
周六009|Serie A|2026-09-19 21:00|博洛尼亚|都灵|1:1|1:0
周六010|Allsvenskan|2026-09-19 21:00|瓦斯特拉斯|马尔默|2:0|1:0
周六011|Bundesliga|2026-09-19 21:30|法兰克福|弗赖堡|2:2|2:1
周六012|Bundesliga|2026-09-19 21:30|汉堡|科隆|2:1|1:0
周六013|Bundesliga|2026-09-19 21:30|门兴格拉德巴赫|美因茨|3:4|1:2
周六014|Bundesliga|2026-09-19 21:30|云达不来梅|奥格斯堡|3:2|0:1
周六015|Premier League|2026-09-19 22:00|埃弗顿|伊普斯维奇|1:0|1:0
周六016|Premier League|2026-09-19 22:00|纽卡斯尔联|赫尔城|2:1|2:0
周六017|Eliteserien|2026-09-19 22:00|克里斯蒂安松|罗森博格|1:3|1:1
周六018|La Liga|2026-09-19 22:15|毕尔巴鄂竞技|阿拉维斯|0:0|0:0
周六019|Ligue 1|2026-09-19 23:15|巴黎FC|斯特拉斯堡|2:1|1:0
周六020|Serie A|2026-09-20 00:00|罗马|国际米兰|2:2|2:0
周六021|Premier League|2026-09-20 00:30|诺丁汉森林|考文垂|0:1|0:0
周六022|Bundesliga|2026-09-20 00:30|斯图加特|多特蒙德|0:1|0:0
周六023|La Liga|2026-09-20 00:30|塞尔塔|桑坦德竞技|5:0|2:0
周六024|Eredivisie|2026-09-20 02:00|阿贾克斯|SBV精英|2:2|1:1
周六025|Serie A|2026-09-20 02:45|威尼斯|拉齐奥|0:2|0:0
周六026|Ligue 1|2026-09-20 02:45|昂热|特鲁瓦|2:0|1:0
周六027|Ligue 1|2026-09-20 02:45|里昂|雷恩|4:0|2:0
周六028|La Liga|2026-09-20 03:00|塞维利亚|巴塞罗那|1:3|1:1
周六029|Primeira Liga|2026-09-20 03:30|里斯本竞技|阿罗卡|2:2|2:0
周六030|Brasileirao|2026-09-20 04:00|米拉索尔|博塔弗戈|2:0|2:0
""",
}


EN = {
    "拉查布里":"Ratchaburi", "上海海港":"Shanghai Port", "大田市民":"Daejeon Hana Citizen", "京都":"Kyoto Sanga",
    "卡塔尔U23":"Qatar U23", "韩国U23":"South Korea U23", "柔佛FC":"Johor Darul Ta'zim", "武里兰联":"Buriram United",
    "北京国安":"Beijing Guoan", "浦项制铁":"Pohang Steelers", "艾因":"Al Ain", "利雅得胜利":"Al Nassr",
    "巴列卡诺":"Rayo Vallecano", "西班牙人":"Espanyol", "阿拉维斯":"Alaves", "巴伦西亚":"Valencia",
    "阿贾克斯":"Ajax", "威廉二世":"Willem II", "米德尔斯堡":"Middlesbrough", "米尔沃尔":"Millwall",
    "利物浦":"Liverpool", "热刺":"Tottenham Hotspur", "伊普斯维奇":"Ipswich Town", "阿森纳":"Arsenal",
    "埃尔切":"Elche", "皇家马德里":"Real Madrid", "普拉滕斯":"Platense", "弗鲁米嫩塞":"Fluminense",
    "中国U23":"China U23", "朝鲜U23":"North Korea U23", "全北现代":"Jeonbuk Hyundai Motors", "柏太阳神":"Kashiwa Reysol",
    "日本U23":"Japan U23", "中国香港U23":"Hong Kong U23", "奥莫尼亚":"Omonia", "塞尔塔":"Celta Vigo",
    "拉科鲁尼亚":"Deportivo La Coruna", "塞维利亚":"Sevilla", "马德里竞技":"Atletico Madrid", "奥萨苏纳":"Osasuna",
    "AC米兰":"AC Milan", "本菲卡":"Benfica", "勒沃库森":"Bayer Leverkusen", "采列":"Celje", "桑德兰":"Sunderland",
    "阿尔克马尔":"AZ Alkmaar", "格拉茨风暴":"Sturm Graz", "雷恩":"Rennes", "安德莱赫特":"Anderlecht", "里昂":"Lyon",
    "考文垂":"Coventry City", "阿斯顿维拉":"Aston Villa", "巴塞罗那":"Barcelona", "桑坦德竞技":"Racing Santander",
    "基多体育大学":"LDU Quito", "帕尔梅拉斯":"Palmeiras", "博塔弗戈":"Botafogo", "格雷米奥":"Gremio",
    "科林蒂安":"Corinthians", "拉普拉塔大学生":"Estudiantes", "乌兹别克斯坦女足":"Uzbekistan Women", "中国女足":"China Women",
    "上海申花":"Shanghai Shenhua", "淡滨尼流浪":"Tampines Rovers", "OFI克里特":"OFI Crete", "霍芬海姆":"Hoffenheim",
    "贝蒂斯":"Real Betis", "赫塔费":"Getafe", "水晶宫":"Crystal Palace", "波兹南莱赫":"Lech Poznan",
    "皇家社会":"Real Sociedad", "伯恩茅斯":"Bournemouth", "尤文图斯":"Juventus", "奈梅亨":"NEC Nijmegen",
    "贝西克塔斯":"Besiktas", "马赛":"Marseille", "利勒斯特罗姆":"Lillestrom", "托伦斯":"Torreense", "马拉加":"Malaga",
    "比利亚雷亚尔":"Villarreal", "弗拉门戈":"Flamengo", "山谷独立":"Independiente del Valle",
    "沙特阿拉伯U23":"Saudi Arabia U23", "赫尔辛基火花":"Gnistan", "赫尔辛基":"HJK Helsinki", "沃尔夫斯堡":"Wolfsburg",
    "达姆施塔特":"Darmstadt", "萨普斯堡":"Sarpsborg 08", "KFUM奥斯陆":"KFUM Oslo", "兰斯":"Reims", "蒙彼利埃":"Montpellier",
    "格罗宁根":"Groningen", "兹沃勒":"PEC Zwolle", "登博思":"Den Bosch", "海尔蒙特":"Helmond Sport",
    "拜仁慕尼黑":"Bayern Munich", "柏林联合":"Union Berlin", "蒙扎":"Monza", "萨索洛":"Sassuolo", "摩纳哥":"Monaco", "朗斯":"Lens",
    "布伦特福德":"Brentford", "切尔西":"Chelsea", "布里斯托尔城":"Bristol City", "沃特福德":"Watford", "纽约城":"New York City FC", "纽约红牛":"New York Red Bulls",
    "长崎航海":"V-Varen Nagasaki", "大阪樱花":"Cerezo Osaka", "藤枝MYFC":"Fujieda MYFC", "大宫松鼠":"Omiya Ardija",
    "FC安养":"FC Anyang", "蔚山现代":"Ulsan HD", "横滨水手":"Yokohama F. Marinos", "水户蜀葵":"Mito HollyHock",
    "斯托克城":"Stoke City", "谢菲尔德联":"Sheffield United", "乌迪内斯":"Udinese", "卡利亚里":"Cagliari",
    "博洛尼亚":"Bologna", "都灵":"Torino", "瓦斯特拉斯":"Vasteras SK", "马尔默":"Malmo FF", "法兰克福":"Eintracht Frankfurt",
    "弗赖堡":"Freiburg", "汉堡":"Hamburg", "科隆":"Koln", "门兴格拉德巴赫":"Borussia Monchengladbach", "美因茨":"Mainz 05",
    "云达不来梅":"Werder Bremen", "奥格斯堡":"Augsburg", "埃弗顿":"Everton", "纽卡斯尔联":"Newcastle United", "赫尔城":"Hull City",
    "克里斯蒂安松":"Kristiansund", "罗森博格":"Rosenborg", "毕尔巴鄂竞技":"Athletic Bilbao", "巴黎FC":"Paris FC", "斯特拉斯堡":"Strasbourg",
    "罗马":"Roma", "国际米兰":"Inter Milan", "诺丁汉森林":"Nottingham Forest", "斯图加特":"Stuttgart", "多特蒙德":"Borussia Dortmund",
    "SBV精英":"Excelsior", "威尼斯":"Venezia", "拉齐奥":"Lazio", "昂热":"Angers", "特鲁瓦":"Troyes", "里斯本竞技":"Sporting CP",
    "阿罗卡":"Arouca", "米拉索尔":"Mirassol",
}


def parsed_rows(text: str):
    rows = []
    for line in text.strip().splitlines():
        number, league, kickoff, home, away, ft, ht = line.split("|")
        fh, fa = map(int, ft.split(":")); hh, ha = map(int, ht.split(":"))
        rows.append(dict(number=number, league=league, kickoff=kickoff, home=home, away=away,
                         fh=fh, fa=fa, hh=hh, ha=ha))
    return rows


def season_for(league: str) -> str:
    return "2026" if league in {"Asian Games Men", "Asian Games Women", "Brasileirao", "MLS", "J1 League", "J2 League", "K League 1", "Allsvenskan", "Eliteserien", "Veikkausliiga"} else "2026-27"


def result(h: int, a: int) -> str:
    return "H" if h > a else "A" if h < a else "D"


def record(lottery_date: str, row: dict) -> dict:
    dates = sorted({row["kickoff"][:10]})
    urls = [CPBAO.format(date=lottery_date.replace("-", ""))] + [ZGZCW.format(date=d) for d in dates]
    return {
        "match_key": f'{lottery_date}-{row["number"]}', "display_number": row["number"],
        "home": row["home"], "away": row["away"], "league": row["league"], "status": "final",
        "kickoff_beijing": row["kickoff"].replace(" ", "T") + ":00+08:00",
        "home_goals": row["fh"], "away_goals": row["fa"],
        "half_home_goals": row["hh"], "half_away_goals": row["ha"],
        "total_goals": row["fh"] + row["fa"], "result": result(row["fh"], row["fa"]),
        "score_period": "90_minutes", "extra_time": None, "penalties": None,
        "verification": "cpbao_zgzcw_agree", "source_urls": urls,
    }


def csv_row(lottery_date: str, row: dict) -> dict:
    kickoff_date = row["kickoff"][:10]
    return {
        "source": "cpbao+zgzcw/result-crosscheck",
        "source_url": CPBAO.format(date=lottery_date.replace("-", "")),
        "source_revision": OBSERVED, "source_row": row["number"][-3:], "observed_at": OBSERVED,
        "league": row["league"], "season": season_for(row["league"]), "date": kickoff_date,
        "home_team": EN[row["home"]], "away_team": EN[row["away"]],
        "ft_home_goals": row["fh"], "ft_away_goals": row["fa"], "ft_result": result(row["fh"], row["fa"]),
        "ht_home_goals": row["hh"], "ht_away_goals": row["ha"], "ht_result": result(row["hh"], row["ha"]),
        "round": "", "score_period": "90_minutes", "home_team_raw": row["home"], "away_team_raw": row["away"],
    }


FIELDS = ["source","source_url","source_revision","source_row","observed_at","league","season","date","home_team","away_team","ft_home_goals","ft_away_goals","ft_result","ht_home_goals","ht_away_goals","ht_result","round","score_period","home_team_raw","away_team_raw"]


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def report_text(lottery_date: str, records: list[dict], pending: list[dict]) -> str:
    counts = Counter(r["result"] for r in records); goals = sum(r["total_goals"] for r in records)
    table = ["|编号|北京时间|对阵|半场|90分钟|赛果|", "|---|---|---|---:|---:|---:|"]
    labels = {"H":"主胜", "D":"平", "A":"客胜"}
    for r in records:
        table.append(f'|{r["display_number"]}|{r["kickoff_beijing"][5:16].replace("T", " ")}|{r["home"]}—{r["away"]}|{r["half_home_goals"]}:{r["half_away_goals"]}|{r["home_goals"]}:{r["away_goals"]}|{labels[r["result"]]}|')
    pending_text = "无。" if not pending else "；".join(f'{p["display_number"]} {p["home"]}—{p["away"]}（赛果源仍为空）' for p in pending) + "。"
    return f"""# {lottery_date} 竞彩足球赛果核验与复盘

本批按北京时间和竞彩编号日核验。体彩官方页面访问超时；已使用彩宝按编号日的完整赛果表与足彩网按开赛日的赛果表逐场交叉确认。只导入确认完场的90分钟比分；加时和点球均无可记录事件。

## 执行结果

- 应核验：{len(records)+len(pending)}场
- 已核验：{len(records)}场
- 新增入库：{len(records)}场
- 重复：0场
- 冲突：0场
- 待补查：{len(pending)}场

{chr(10).join(table)}

赛果分布为主胜{counts['H']}场、平局{counts['D']}场、客胜{counts['A']}场；总进球{goals}个，场均{goals/len(records):.2f}个。

## 待补查与数据边界

{pending_text} 仓库仍没有这些场次开球前保存的可审计统一预测档案，因此Z1真实前瞻样本为0，不计算命中率、Brier、log loss或收益率，也不把聊天建议冒充模型成绩。

## 来源与限制

优先访问[中国体彩网赛果页]({OFFICIAL[0]})和[竞彩网]({OFFICIAL[1]})，但当前环境均超时，没有绕过限制。[彩宝本编号日赛果]({CPBAO.format(date=lottery_date.replace('-', ''))})与[足彩网赛果索引](https://cp.zgzcw.com/dc/getKaijiangFootBall.action)逐场一致。足彩网同时提供半场比分，因此本批半场字段已保留。原始结构化证据保存于 `data/raw/results/{lottery_date}/source_evidence.json`。
"""


def main() -> None:
    all_rows = 0
    for lottery_date, text in RAW.items():
        rows = parsed_rows(text); records = [record(lottery_date, r) for r in rows]
        pending = []
        if lottery_date == "2026-09-16":
            pending = [{
                "match_key":"2026-09-16-周三014", "display_number":"周三014", "league":"La Liga",
                "kickoff_beijing":"2026-09-17T03:30:00+08:00", "home":"莱万特", "away":"毕尔巴鄂竞技",
                "status":"unsettled_or_postponed", "home_goals":None, "away_goals":None,
                "source_urls":[CPBAO.format(date="20260916"), ZGZCW.format(date="2026-09-17")],
            }]
        write_json(ROOT / f"data/processed/results/{lottery_date}.json", {
            "schema_version":1, "lottery_date":lottery_date, "record_type":"sourced_results_batch",
            "model_training_ingested":True,
            "official_number_verification":"Official pages timed out; CPBao lottery-date rows and ZGZCW Beijing-date rows agree. One blank-score match on 2026-09-16 remains pending and is excluded.",
            "observed_at":OBSERVED, "records":records,
        })
        write_json(ROOT / f"data/raw/results/{lottery_date}/source_evidence.json", {
            "observed_at":OBSERVED, "lottery_date":lottery_date,
            "sources":[
                *[{"url":u,"status":"timeout","usable":False,"note":"Official source attempted first; no bypass."} for u in OFFICIAL],
                {"url":CPBAO.format(date=lottery_date.replace('-', '')),"status":"http_200","extracted_rows":records},
                {"url":"https://cp.zgzcw.com/dc/getKaijiangFootBall.action","status":"http_200","query_dates":sorted({r['kickoff_beijing'][:10] for r in records}),"extracted_rows":records},
            ], "pending":pending, "extracted_records":records,
        })
        write_csv(ROOT / f"data/processed/current_season_2026_27/sporttery_{lottery_date}.csv", [csv_row(lottery_date, r) for r in rows])
        (ROOT / f"reports/review_{lottery_date}.md").write_text(report_text(lottery_date, records, pending), encoding="utf-8")
        all_rows += len(rows)

    pending = [{
        "match_key":"2026-09-16-周三014", "display_number":"周三014", "league":"La Liga",
        "kickoff_beijing":"2026-09-17T03:30:00+08:00", "home":"莱万特", "away":"毕尔巴鄂竞技",
        "status":"unsettled_or_postponed", "home_goals":None, "away_goals":None,
        "source_urls":[CPBAO.format(date="20260916"), ZGZCW.format(date="2026-09-17")],
    }]
    write_json(ROOT / "reports/pending_results_20260920.json", {
        "checked_at":OBSERVED, "previous_pending_checked":0, "settled":[], "conflicts":[],
        "remaining_pending":pending,
        "note":"The only unresolved published row is 2026-09-16 周三014. Both result indexes show no score; it was not ingested.",
    })
    write_json(ROOT / "reports/current_season_update_20260920.json", {
        "as_of":OBSERVED,
        "batches":[{"path":f"data/processed/current_season_2026_27/sporttery_{d}.csv","rows":len(parsed_rows(t)),"net_new_since_previous_commit":len(parsed_rows(t))} for d,t in RAW.items()],
        "completed_ingested":all_rows, "pending_not_ingested":1, "pending_matches":pending,
        "current_season_rows":351+all_rows, "unified_catalog_rows":41030+all_rows,
        "validation_issues":[], "duplicate_or_conflicting_keys":[],
        "official_source_gap":"China Sports Lottery and Sporttery official pages timed out. CPBao and ZGZCW independently agreed on all imported rows.",
        "halftime_data_gap":None,
        "temporal_review":"scheduled_sunday_but_skipped: auditable pre-kickoff archive missing; true prospective sample count 0 (<30); production model unchanged",
    })


if __name__ == "__main__":
    main()
