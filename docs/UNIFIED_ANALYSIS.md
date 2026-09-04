# 统一档案与同场模型对比

新入口 `sports_lottery.unified` 将比赛、赛前快照、三个模型输出及赛后结果放进同一SQLite档案。
不删除、不迁移已有数据或旧日志；新档案由使用者指定路径，旧记录尚未自动迁入。

## 可运行命令

```sh
PYTHONPATH=src python -m sports_lottery.unified --db unified.sqlite3 compare data/processed/top5_2016_2026 fixture.json --at 2026-09-04T10:00:00+08:00
PYTHONPATH=src python -m sports_lottery.unified --db unified.sqlite3 result FIXTURE_ID result.json
PYTHONPATH=src python -m sports_lottery.unified --db unified.sqlite3 report
```

fixture.json需要league、home、away、kickoff、source_url、source_id；比赛与来源由调用者核实。
kickoff、--at及结果observed_at都必须含时区。--at必须早于开赛。
result.json需要status=final、period=90_minutes、home_goals、away_goals、source_url、observed_at。
总进球和比分仅按90分钟结算，额外时间比分不得混入。财务结算未实现。

## 统一规则

- 档案ID由联赛、规范化队名、UTC开赛时刻确定，同一时刻的不同时区表示映射同一ID。
- 当前只有基础队名别名，比赛延期会产生新ID；延期/取消及旧ID关联须另行实现，不能称为完整官方比赛主数据。
- 相同比赛、相同预测时间禁止重复写入；不同时间预测完整保留。
- 所有算法收到同一截止日期前的赛果集合；当日数据因缺少完赛时刻全部排除。
- 三模型：历史胜平负频率、近期主客状态泊松、重新拟合的攻防泊松。
- 模型各有窗口和权重，公平指相同数据可得性，不是相同参数或必然相同训练子集。
- 攻防模型按本次截止时间重新拟合并把完整参数放入预测记录；未复用含未来信息的最新参数文件。
- 快照包含输入、来源、证据、模型版本和SHA-256。SQLite不是防篡改系统，提供者仍可能伪造时间，未实现第三方时间认证。
- 证据必须有匹配source_id及发布时间/获取时间；证据尚未影响模型数值，也未自动联网核验。
- 模型无足够数据、未知球队等情况标skipped；其他异常标failed，不消失于档案。

## 公平复盘

每场比赛默认只采用最早保存的一次预测，防止多次更新重复计入。
按联赛报告三模型共同成功且已完场的相同比赛子集，列明未完场和剔除的对比ID、跳过/失败次数。
统计胜平负命中率、对数损失、Brier；具备比分/进球输出的模型另统计首选比分及总进球档命中率。
频率基准不产生比分，因此其比分命中率为null，不能误写成0。
最早记录的选择不等于所有比赛相同的赛前提前量；进一步实验需预先固定预测时间窗口。
本工具不会自动运行当天比赛，不具备真实伤停、xG、官方实时赛程或报价接入。

## 验证

测试覆盖完整三模型预测—结果—对比、重复写入拒绝、失败保留、同日数据泄漏、最早快照和时区统一。
这些测试用合成数据验证程序，不代表新增真实赛前预测，也不代表盈利证明。
