# 七项建设状态：按实际能力计，不把文档当完成

本表记录本轮追加后状态，七项均仍有缺口，不能声称全量建成。

| 项目 | 已实现 | 尚缺 |
|---|---|---|
| 1 官方竞彩历史 | 采集器、访问受限停止、来源分级 | 获准的历史编号、固定奖金、取消延期数据；目前未采集成功 |
| 2 球队统一 | 显式别名、Unicode清理，近期状态模块已使用 | 全赛事稳定球队ID与人工审查映射；主模型仍要求数据内原名 |
| 3 扩大赛事覆盖 | 五大联赛和欧冠，共19309条 | 英冠、日韩、北欧、巴西、美职联、国家队等；本轮未新增赛事数据 |
| 4 状态与赛程 | 近5/10场、主客各10场、距上一场天数、前7日场次；预测CLI已接入 | 跨赛事完整覆盖、旅行、对手强度、积分目标与杯赛战意 |
| 5 伤停与首发 | 带时区的证据时间校验、来源字段、confirmed/doubtful/unknown | 真实持续更新的数据源；尚未自动采集或影响模型参数 |
| 6 保存与复盘 | SQLite预测/结果分表、拒绝重复ID、哈希、命中率、最长连续失误；已有时间回测 | 日常预测自动落库、实际出票记录、收益与资金回撤；没有赔率则不算ROI |
| 7 概率模型 | 时间衰减、主客状态、泊松比分/进球数/胜平负、回测、分箱可靠性与ECE | 拟合校准变换、独立前瞻检验、伤停及对手强度模型 |

## 新增模块

- `match_context.team_context(rows, team, before, league=None)`：只统计截止日期前的输入赛果，未知字段保留None。
- `match_context.validate_evidence(item, prediction_time, kickoff)`：检验发布时间≤获取时间≤预测时间<开赛时间；日期必须含时区。
- `prediction_log.connect(path)`、`save_prediction`、`save_result`、`review`：可调用的记录与复盘接口，无自动投注。
- `calibration.reliability(records)`：对所选方向的概率做分箱诊断，非已完成的校准模型。

日志要求赛前记录含id、match_id、model_version、input_snapshot_hash、source_urls、created_at、kickoff、H/D/A probabilities。
赛后记录另存，要求final、90_minutes、整数比分、来源与获取时间。不支持将加时/点球比分混入。
当前记录器由调用方提供时间、来源和输入哈希，不能认证真实发布时间；哈希只帮助发现内容变化，不是第三方审计证明。
应用接口不允许覆写同ID，但SQLite文件持有人仍能直接修改数据库，不宣称防篡改。
休息天数按日期差计算，不代表准确休息小时；遗漏其他赛事会低估密集程度。

## 验证

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m sports_lottery.forecast data/processed/top5_2016_2026
```

所有概率是实验输出，不承诺准确或盈利。需要额外付费、账号权限或许可的数据不得擅自购买或绕过限制。
