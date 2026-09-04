# 赛前存档、赛后核对、时间切分与概率校准

## 已有存档复盘入口

```bash
PYTHONPATH=src python -m sports_lottery.unified --db data/processed/forecast_archive.sqlite compare data/processed/最终合并目录 fixture.json --at 2026-09-04T10:00:00Z
PYTHONPATH=src python -m sports_lottery.unified --db data/processed/forecast_archive.sqlite result 比赛fixture_id result.json
PYTHONPATH=src python -m sports_lottery.unified --db data/processed/forecast_archive.sqlite report
```

fixture/result 必须是真实核验数据；示例时间不能当作真实记录时间。compare 保存来源、原始概率、历史输入与赛前资料快照；result 仅接受注明 final 和 90_minutes 的比分、来源及采集时间。重复结果拒绝覆盖，每场复盘只取最早预测。数据库属于应用层追加记录，不是不可篡改审计系统。

## 新增时间切分校准评估

```bash
PYTHONPATH=src python -m sports_lottery.temporal_review \
  --db data/processed/forecast_archive.sqlite \
  --split 2026-08-01T00:00:00Z --end 2026-09-01T00:00:00Z --minimum 30
```

- 只读数据库，不改预测、不改赛果。
- 按联赛、模型分别处理。每场仍仅使用最早的预测。
- 校准集：预测及赛果采集时间严格早于 split。
- 验收集：预测时间在 split 之后，比赛及赛果采集时间在 end 之前。
- 跨分界迟到赛果、未结算、失败模型列入排除统计。
- 温度缩放在固定候选0.5/0.75/1/1.25/1.5/2/3中按校准集对数损失选择；至少30条且胜平负三类均出现才拟合。这只是最低保护，不代表样本足够可靠。
- 输出原始/校准后对数损失、Brier分数、准确率、三个类别的可靠性分箱和校准样本ID。
- 后段对数损失改善可能为负；不自动启用校准结果，更不能声称必然提升。
- 仅校准胜平负；比分、总进球概率不随之调整，因此不混合作为统一比分分布。

## 历史回测与真实前瞻分开

历史主客场模型已有按日期逐步更新的回测：

```bash
PYTHONPATH=src python -m sports_lottery.forecast data/processed/最终合并目录 --start 2024-07-01
```

该历史回测不等同于真实提前存档。temporal_review 接收的是统一存档中的预测，基础模型必须先满足只用更早资料的条件。不要将历史重新生成的预测标成真实赛前预测；输入日期过滤也不等于证明当时数据已公开。

## 本次验收边界

本次完成代码和合成测试，未生成真实比赛预测/赛果，未开启自动赛果抓取、未宣称完成实际新赛季校准。真实档案样本仍须积累；没有真实样本就没有可报告的命中率提升。无票据和历史固定奖金不计算收益率。
