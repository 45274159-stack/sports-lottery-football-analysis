# 模型库

模型库用于保存版本、赛事范围、玩法、训练截止日、数据指纹、固定参数、代码版本与验证指标。
它不保存神秘“投注技巧”，也不把回顾性成绩当作未来保证。

## 初始化

```sh
PYTHONPATH=src python scripts/bootstrap_model_library.py
PYTHONPATH=src python -m sports_lottery.model_library --db data/models/model_library.sqlite3 list
```

默认目录登记五个联赛的 venue-poisson-v1 模型，全部为 candidate。
catalog.json 可审查并纳入Git；SQLite运行文件不纳入Git。

## 生命周期

1. candidate：完成历史回测，但未满足启用标准。
2. accepted：经人工审核并至少拥有一条验证记录，才允许激活。
3. retired：停用保留，不删除历史。

activate会检查模型赛事和玩法范围；select只返回accepted且训练截止日早于开赛日期的激活模型。
同一赛事和玩法只能有一个激活模型。模型登记为追加式，同一ID或同版本重复登记会失败。
候选模型至少累计100场标记为前瞻的评估后，`status MODEL accepted` 才允许通过；随后才能activate。
accepted只能转为retired，退役时自动移除所有激活项，不能逆向恢复。

## 已登记模型

- Premier League、La Liga、Serie A、Bundesliga、Ligue 1各一个候选模型。
- 玩法：90分钟胜平负、精确比分、总进球。
- 参数：联赛500场窗口、主客各20场、5场先验、180天半衰期、独立泊松。
- 数据指纹：68d78f2a3331d180ec9bc26403379152d95e41eaa65709174cb6bfa658d868ab
- 回测区间：2024-07-01起，逐日预测后才录入当天结果。

局限：回测模型会随历史滚动更新，catalog中的trained_through表示初始回测切点，而不是固定权重模型文件。
代码仍以规则参数实时重建，不是序列化训练权重。实际使用还需把pipeline改为从激活模型读取参数。
尚无真实前瞻验证、官方固定奖金、伤停、首发、xG及投注收益，因此不能激活为生产模型。

## 验收门槛（待执行）

至少保留一个完整赛季的冻结前瞻预测；概率校准、对数损失和Brier优于基准；
逐联赛检查样本量和漂移；精确比分单独评估；数据与代码指纹可复现；
引入赔率后必须使用当时真实可得的固定奖金，才能计算ROI。
