# 数据来源与可信度

## 分级

| 等级 | 定义 | 用途 |
|---|---|---|
| OFFICIAL | 中国体育彩票公开赛程、赛果与固定奖金接口 | 竞彩编号、让球、开奖、奖金回测 |
| OPEN_DATA | 明确开放许可并可追溯的数据集 | 球队状态、进球和联赛基线 |
| SECONDARY | 媒体或第三方数据页 | 仅用于交叉验证，不覆盖官方字段 |

## 当前来源

- 中国体育彩票赛果开奖页：<https://www.lottery.gov.cn/jc/zqsgkj/>
- 竞彩网移动端公开赛果接口：`getMatchDataPageListV1.qry`
- Football datasets：<https://github.com/datasets/football-datasets>（PDDL 1.0）
- OpenFootball Champions League：<https://github.com/openfootball/champions-league>（CC0 1.0）

## 采集纪律

1. 官方接口被安全策略拦截时立即停止，不轮换IP、不伪造令牌、不绕过验证。
2. 保存原始响应、来源URL、采集时间和来源等级。
3. `sectionsNo999`只作为90分钟全场比分；加时和点球不得混入竞彩足球赛果。
4. 开奖页展示的中奖项固定奖金不等于完整赛前赔率快照。
5. 赛后字段不能作为赛前预测特征，避免数据泄漏。
6. 无法核验的竞彩编号、奖金或伤停字段保留为空。
