# 中国体育彩票竞彩足球历史数据与分析系统

这是一个面向中国体育彩票竞彩足球的可审计数据项目，用来沉淀近十年赛程、比赛结果、官方编号、固定奖金和赛前信息，并生成可复现的分析报告。

项目不承诺命中，也不把赔率当作结论。模型输出仅用于研究和小额娱乐决策。

## 当前能力

- 标准化竞彩足球 CSV 数据格式；
- 校验比赛编号、日期、球队、比分和赔率；
- 使用 SQLite 去重入库并更新赛后结果；
- 严格只读取开赛前历史比赛，避免数据泄漏；
- 输出基础胜平负概率、预期进球和参考比分；
- 为后续十年历史数据、伤停、赛程强度和赔率快照扩展保留结构。
- 已收录2016/17至2025/26五大联赛17,937场标准化比赛数据；
- 已加入2016/17至2025/26欧冠1,372场比赛，当前合计19,309场；
- 已补充8个常见竞彩联赛21,348场历史结果，并单独加入2025/26尾段22场及
  2026/27七个联赛已完赛163场；当前跨14项赛事校验通过40,842场；
- 可一键复算十年主胜率、平局率、客胜率、进球和双方进球分布。
- 支持在可访问竞彩网的本地网络按日期采集官方编号与赛果，自动翻页、去重并保存原始证据。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .

sporttery validate data/templates/matches_template.csv
sporttery init-db
sporttery import data/templates/matches_template.csv
sporttery analyze --home 皇家社会 --away 塞尔塔 --kickoff 2026-09-04T03:00:00+08:00
sporttery review-history data/processed/top5_2016_2026
sporttery collect-sporttery --start 2026-09-01 --end 2026-09-03 --output data/raw/sporttery/2026-09-01_2026-09-03.json
```

Python模型需要读取全部已审计批次时，统一使用
`sports_lottery.history_catalog.load_all_history()`；它会在跨批次发现重复或冲突比分时拒绝继续。

## 目录

```text
data/templates/    标准导入模板
data/raw/          原始快照（默认不提交大文件）
data/processed/    SQLite、清洗结果及已审计的十年数据集
reports/           可复核的统计复盘报告
docs/              数据字典与分析方法
src/               校验、入库和分析代码
tests/             自动化测试
```

## 十年数据建设顺序

1. 先收集官方赛程、编号及赛果，并保存来源；
2. 建立球队别名表，解决历史改名和不同中文译名；
3. 补充每次开奖前的固定奖金快照，禁止用临场数据覆盖早盘；
4. 添加伤停、首发、休息天数、旅行距离和杯赛背景；
5. 按时间滚动回测，再决定哪些特征真正有效。

历史数据必须来自可核验来源。仓库不会为了“凑满十年”而生成虚假记录。

首批结果见 [五大联赛十赛季复盘](reports/top5_2016_2026_review.md)，当前覆盖与明确缺口见
[完整性审计](reports/history_completeness_20260904.md)。详细字段见 [数据字典](docs/DATA_DICTIONARY.md)，分析边界见 [方法说明](docs/METHODOLOGY.md)，来源等级见 [数据来源](docs/SOURCES.md)。

## 责任提示

足球比赛具有高度随机性。任何分析都可能错误；请将投注限制在能够完全承受损失的小额娱乐预算内，不追损、不借款、不翻倍。
