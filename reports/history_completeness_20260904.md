# 足球历史数据完整性审计（2026-09-04）

- 当前校验通过：**40,842 场**
- 本次新增2026/27已完赛：**163 场**
- 范围：14 tracked competitions, not all world football

## 联赛覆盖

| 联赛 | 场次 | 首场 | 最新 | 赛季数 |
|---|---:|---|---|---:|
| 2. Bundesliga | 3,006 | 2016-08-05 | 2026-04-05 | 10 |
| Bundesliga | 3,069 | 2016-08-26 | 2026-08-30 | 11 |
| Eerste Divisie | 2,249 | 2020-08-28 | 2026-04-06 | 6 |
| Eliteserien | 2,068 | 2016-03-11 | 2025-05-04 | 10 |
| Eredivisie | 3,018 | 2016-08-05 | 2026-08-30 | 11 |
| La Liga | 3,830 | 2016-08-19 | 2026-08-31 | 11 |
| Ligue 1 | 3,495 | 2016-08-12 | 2026-08-30 | 11 |
| Ligue 2 | 3,505 | 2016-07-29 | 2026-04-06 | 10 |
| MLS | 3,763 | 2016-03-06 | 2025-05-04 | 10 |
| Premier League | 3,820 | 2016-08-13 | 2026-08-31 | 11 |
| Primeira Liga | 3,093 | 2016-08-12 | 2026-08-31 | 11 |
| Saudi Pro League | 734 | 2016-08-11 | 2026-04-08 | 3 |
| Serie A | 3,820 | 2016-08-20 | 2026-08-31 | 11 |
| champions_league | 1,372 | 2016-09-13 | 2026-05-30 | 10 |

## 已知缺口

- Eerste Divisie 2016-17 through 2019-20 absent
- Saudi Pro League 2017-18 through 2023-24 absent
- MLS 2024-2026 incomplete and phase/90-minute review pending
- Eliteserien 2024-2026 incomplete and phase/90-minute review pending
- 2026-27 second divisions and Saudi/MLS/Eliteserien not available in this source snapshot
- No global lower-league, youth, women, reserve, friendly, or every cup competition coverage

## 结论

当前库不是全球最近十年所有足球比赛的完整镜像。本报告只把可复现、带来源且比分明确的记录计为已入库；空比分不填0:0，未完赛不导入。
