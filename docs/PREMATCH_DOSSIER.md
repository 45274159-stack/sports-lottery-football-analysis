# 五类赛前资料

统一分析 compare() 现接受 fixture.prematch 列表，并返回 prematch 资料卡。
资料卡也进入 comparisons.snapshot 及其哈希；旧预测不修改。

每条资料必须有：team（与该场主客队一致）、category、source_id（与比赛一致）、source_url（HTTPS）、source_type（official/secondary）、published_at、observed_at（含时区）、status（confirmed/doubtful/unknown）、summary。details 是可选结构化对象。

| category | 内容 | details 约定 |
|---|---|---|
| injuries | 伤病、停赛、出场存疑 | player、availability、reason；必须明确消息范围，不能凭空断言全队无伤停 |
| lineup | 预计/官方首发 | kind 必须 expected/announced/unknown；players 名单；announced 须11个不重复球员、官方且确认状态 |
| rest | 前场比赛及休息间隔 | previous_kickoff 含时区；系统计算开球间隔小时，不等同于纯恢复时长 |
| transfers | 转入、转出、注册、教练变化 | player、direction、registration；转入不等于已获本场出场资格 |
| cup | 联赛或杯赛背景 | kind 必须 league/single_leg/two_leg/unknown；first_leg_score 为本队、对手顺序的首回合进球数组 |

示例（仅示意，不能作为真实证据）：

```json
{
  "team": "A",
  "category": "lineup",
  "source_id": "该场已有source_id",
  "source_url": "https://example.org/preview",
  "source_type": "secondary",
  "published_at": "2026-09-04T08:00:00Z",
  "observed_at": "2026-09-04T09:00:00Z",
  "status": "doubtful",
  "summary": "媒体预计首发，尚非官方公告",
  "details": {"kind": "expected", "players": []}
}
```

## 防误用

- 必须 发布时间 ≤ 采集时间 ≤ 预测时间 < 开球时间；赛后消息拒绝导入。
- 无资料显示 unknown，并列出缺口；有报道显示 reported_requires_review，不自动认定消息真实。
- 多份消息全部保留，不静默覆盖相互矛盾的说法；age_hours 提供时效判断。
- 历史休息天数从传入的所有赛事记录计算，整天排除预测当日结果。赛事缺失会低估负荷，日期间隔不能称为精确休息小时。
- 资料会进入统一输出和快照，但暂不数值调整概率；必须经过样本外验证后才能加入模型权重。
- 本次没有自动采集伤停网站、没有填写真实当日球队资料，也没有启用定时采集。

运行方式仍为原来的 sports_lottery.unified compare，只需在比赛JSON添加 prematch 数组；无需新数据库。
