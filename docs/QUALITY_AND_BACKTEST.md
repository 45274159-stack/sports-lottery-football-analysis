# 数据质量与时间回测

本轮新增基础校验、欧冠90分钟比分解析、显式队名别名和时间回测基准。

## 运行

```sh
PYTHONPATH=src python -m sports_lottery.history_quality data/processed/top5_2016_2026
PYTHONPATH=src python -m sports_lottery.history_quality data/processed/openfootball_2016_2026
PYTHONPATH=src python -m unittest discover -s tests -v
```

校验日期、重复对阵、负进球、半场比分和全场比分关系、胜平负一致性及CSV列数。
校验失败时不输出回测，未知伤停及官方奖金不填造假默认值。

回测按日期分组：当天全部预测完成才录入当天结果，避免同日结果泄漏。
每项赛事至少100场历史后才开始评估；使用加一平滑的历史胜平负频率。
报告命中率、对数损失及三分类Brier分数，并对比始终主胜。
这是最简单的基准，不是训练好的球队实力模型，也不提供盈利承诺。
当前五大联赛基准命中率约41.7%—45.6%，未超过始终主胜。

## 欧冠修正

14场含加时/点球的记录按原始文件括号内的90分钟与半场比分修正。
不会将点球大战得分作为进球数；无法明确区分的记录拒绝解析。
原始来源：https://github.com/openfootball/champions-league （CC0）
修正证据：reports/champions_league_score_corrections.json。
这些校验只验证结构与源文件解析，不等同于逐场向官方独立核实。

## 队名与缺项

team_names.py 提供小型显式别名表；未知球队保持原名，不进行模糊自动合并。
该工具尚未自动改写已有数据库，需要扩充并审查后接入多源匹配。
官方历史固定奖金、伤停快照和实际投注单尚不完整，所以ROI保持缺失。
采集器目前整段完成才写快照，尚不支持断点续传。
后续优先：授权官方数据、覆盖率审计、球队级模型、独立留出集和概率校准。
