# 当日伤停快照

2026-09-04：14场、28队。24队有局部具体报告，4队仍缺可核验名单；共84条球员状态记录，包含复训和互相矛盾的报道，**不等于84名伤员**。

数据：`data/prematch/2026-09-04-injuries.json`。球员名保留拉丁拼写，避免中文译名误合并；球队与比赛按 source_id 关联。

状态包括 out / suspended / doubtful / returned_training / rehabilitation / conflicting。官方与第三方分别标注，任何名单均不代表全队完整信息。汉诺威、卡尔斯鲁厄、格勒诺布尔、福伦丹此次仍 unknown。

## 用于后续分析

```python
import json
from sports_lottery.injury_snapshot import attach_injuries
from sports_lottery.prematch import dossier
snapshot = json.load(open('data/prematch/2026-09-04-injuries.json'))
fixture = snapshot['fixtures'][7]  # 008；也可使用已有、同ID/队名/时间的比赛对象
enriched = attach_injuries(fixture, snapshot, at=snapshot['observed_at'])
context = dossier(history_rows, enriched, snapshot['observed_at'])
# 也可将 enriched 传给 unified.compare。不会自动改变数值概率。
```

适配器可重复调用，不重复附加同一记录；不修改传入对象。验证比赛ID、主客队、开赛时间及采集时点。早于采集时点的预测禁止使用这些资料，不能回填已经保存的旧预测。

源发布时间不明确则保持 null。适配到旧版 dossier 时，published_at 保守取 first_observed，details.timestamp_basis 明确标记这不是来源实际发布时间；source_published_at/source_published_date 保留原始元数据。时间衰减不能把这个适配字段当新闻年龄。

## 已知问题与人工复核

- 摩纳哥官方称 Balogun/Diop 已恢复合练、Fati 部分复训；第三方仍列缺阵。保留双方记录，复训不等于入选比赛名单。
- Duranville 的缺阵/存疑表述不同；保留分歧。
- Sekou Fofana 同时出现在欧塞尔和波尔图的第三方报道中，球队归属冲突，全部 quarantined 为 conflicting，不计算伤员总数。
- 纳什维尔官网读取失败，搜索摘要另列 Applewhite，未核实暂不录作确认伤员。
- Hannover 摘要中出现 Ghita，但打开网页未能复现，不作为确定伤缺；Grenoble 社区名单混合伤病与新援，不采用。
- 官方体彩编号最终应再以终端核对；本次编号沿用当日已核对第三方赛程。

本次仅新增证据和读取适配器，未训练伤停权重、未校准概率、未改动旧预测与比赛结果。
