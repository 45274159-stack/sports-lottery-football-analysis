# 8个缺失联赛：历史数据补充（2026-09-04）

本次新增 **21,348场来源所报全场赛果**。不是“8个联赛十年全部补齐”，也没有重新发布预测。
标准化数据在 `data/processed/expanded_leagues_2016_2026/`；逐来源版本、数量、缺失比分隔离记录在 `reports/expansion_20260904.json`。

| 当日编号 | 联赛 | 已导入场数 | 覆盖赛季/年份 | 明确缺口 |
|---|---|---:|---|---|
| 001 | 德乙 | 3,006 | 2016/17—2025/26，10季 | 2025/26仅252场，未补齐 |
| 003 | 挪超 | 2,068 | 2016—2025，10年 | 2024仅92场、2025仅44场；旧年可能含附加赛 |
| 004 | 沙特联 | 734 | 2016/17、2024/25、2025/26，3季 | 中间7季缺失；2025/26仅246场 |
| 005 | 法乙 | 3,505 | 2016/17—2025/26，10季 | 2025/26仅261场，2022/23及2023/24各379场需复核 |
| 006 | 荷甲 | 2,982 | 2016/17—2025/26，10季 | 2025/26仅302场；2019/20特殊赛季不得硬凑场数 |
| 007 | 荷乙 | 2,249 | 2020/21—2025/26，6季 | 2016/17—2019/20缺失；2025/26仅349场 |
| 013 | 葡超 | 3,041 | 2016/17—2025/26，10季 | 2025/26仅287场 |
| 014 | 美职联 | 3,763 | 2016—2025，10年 | 2024仅234场、2025仅146场；季后赛/90分钟口径待复核 |

“十季覆盖”仅表示每季至少存在记录，不代表完整；新赛季2026/27、自然年2026尚未加入本批。
历史赛季总场数会受取消、腰斩、扩军、附加赛和赛制调整影响，不能用固定场数伪造缺失记录。

## 来源与使用限制

- FootballCSV cache，来源于 Football-Data：<https://github.com/footballcsv/cache.footballdata>，仓库CC0；本批截至2023/24及2024部分数据。
- OpenFootball JSON：<https://github.com/openfootball/football.json>，CC0。
- OpenFootball Europe：<https://github.com/openfootball/europe>，CC0。
- Saudi Professional League Datasets：<https://github.com/alioh/Saudi-Professional-League-Datasets>；未找到明确数据再许可，本次仅保存带出处的赛果事实，不将其声明为本项目原创或重新许可。
- Soccerway来源的第三方整理：<https://github.com/omarmohamed456/Football-Match-Outcome-Predictor>，仓库附AGPLv3；用于补充部分缺失结果，不采用其模型、爬虫或赛中统计作为赛前特征。保留作者和许可文件，数据来源权利不因代码许可自动改变。

所有来源固定到本次读取的Git树版本，保存逐文件来源URL、行号、采集时间及内容校验值。
原始文件存为 `data/archives/expansion_20260904_raw.tar.gz`；解包到仓库根目录可还原 `data/raw/expansion_20260904/`。
网络直接下载的权限未获批准，没有绕过；Football-Data网页工具读取CSV不支持/限流，未宣称已从该站取得最新全量文件。

## 清洗与安全边界

1. 采用白名单球队别名，保留原始队名；不做模糊匹配。尤其不把Aves与AVS等不同俱乐部合并。
2. 同联赛、同日期、同主客队且同比分的重复来源合并；冲突另行隔离。
3. 空比分、未知比分不填0:0；1011条无法确认全场比分记录及2条带特殊比赛说明记录隔离，共1013条。
4. 校验日期、非负比分、半场不超过全场、胜平负与比分一致。
5. FT字段目前为 `source_reported_FT`，不是对所有附加赛已认证的90分钟结果。MLS和挪超旧源缺少阶段标签，暂不自动接入下注模型。
6. 历史数据为今日取得的回填快照；没有当年的发布时间快照，不把本次采集时间伪装成历史可用时间。
7. 不覆盖此前赛前预测、伤停或赛果记录，不计算未验证的竞彩ROI。

## 读取与复现

```python
from sports_lottery.expanded_history import load_expanded_history, coverage_for_fixture
rows = load_expanded_history()
# coverage_for_fixture 会返回当前双方历史样本数，model_ready始终为False。
```

复现清洗：先解包原始文件，再运行 `PYTHONPATH=src python scripts/import_expansion_20260904.py`。
运行测试：`PYTHONPATH=src python -m unittest discover -s tests`。

下一步：补齐明确缺失赛季/轮次，核对比赛阶段及90分钟口径，补当季已完赛，之后才做逐时回测、概率校准和新预测。
