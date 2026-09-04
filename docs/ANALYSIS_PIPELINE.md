# 统一分析入口（手动提供证据）

本轮实现：历史数据校验 → 赛前截止过滤 → 比赛/证据字段检查 → 模型概率 → 输入快照与预测入库 → 赛果追加 → 复盘。
不是实时数据服务，不会自动浏览、取得授权数据、自动下注或修改伤停相关模型参数。

## 命令

```sh
PYTHONPATH=src python -m sports_lottery.pipeline analyze data/processed/top5_2016_2026 request.json --db analysis.sqlite3
PYTHONPATH=src python -m sports_lottery.pipeline record-result prediction-id result.json --db analysis.sqlite3
PYTHONPATH=src python -m sports_lottery.pipeline review --db analysis.sqlite3
```

路径与记录ID由调用者提供。analyze会创建数据库文件，但不自动创建其父目录。
预测重复ID拒绝覆写；结果记录单独追加。SQLite并非防篡改系统。

## request.json字段

必填：id、match_id、league、home、away、kickoff、created_at、fixture_source_url。
时间必须带时区；league与球队名须精确匹配历史数据。编号与来源仍须人工向官方核实，程序只检验结构。
evidence为数组；每条含kind、match_id、team、summary、status、source_url、published_at、observed_at。
kind可选fixture、injuries、lineup、xg、schedule、motivation；team为对阵球队之一或both。
status为confirmed、doubtful或unknown；程序无法认证提供者的确认是否真实。
一条confirmed记录也不等于相关领域信息完整。

## 数据不足时

缺项或过期记录列入missing，状态为incomplete_inputs；即使字段齐全也只标requires_manual_review。
没有自动“高信心”“稳胆”状态。消息只供核查，暂不改变模型数值。
同一UTC预测日期的比赛全部排除；原始赛果仅含日期，无法精确恢复当日开赛与完赛时点。
为了可复现，使用的历史行与请求完整保存在input_snapshot中，并计算SHA-256。
每次预测包含快照可能增加数据库体积；正式批量使用前应改为去重的快照表。

## result.json字段

status=final、period=90_minutes、home_goals、away_goals、source_url、observed_at。
杯赛只填90分钟比分，不填加时/点球结果；最终状态须人工核实。
复盘只提供所选胜平负方向命中与失误序列，不提供没有真实出票记录支撑的收益率。

## 尚未完成

实时官方比赛核验、真实伤停/首发/xG数据源、更多联赛导入、概率校准拟合仍未完成。
26项测试含合成数据的预测—入库—记录赛果—复盘闭环，测试不代表预测准确率。
