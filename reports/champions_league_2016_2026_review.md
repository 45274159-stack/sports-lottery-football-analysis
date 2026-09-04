# 欧冠近十赛季复盘（修正版）

数据源：[OpenFootball Champions League](https://github.com/openfootball/champions-league)，CC0。2016/17—2025/26正赛，共1372场。

本轮修正14场包含加时或点球的记录，按源文件明确记载的90分钟比分统计。旧版统计已被本版替代。

| 指标 | 修正后 |
|---|---:|
| 主胜 | 639 |
| 平局 | 272 |
| 客胜 | 461 |
| 总进球 | 4283 |
| 场均进球 | 3.122 |

修正证据见 champions_league_score_corrections.json；回测见 quality_baseline_2026-09-04.json。结构校验不等于官方逐场核实。2024/25赛制变化、淘汰赛晋级形势需单独建模。无官方固定奖金，不计算竞彩ROI。
