# 新赛季更新状态（2026-09-04）

## 本次真实状态

- 本次新增真实赛果：0。不能将更新程序完成说成数据库完成。
- datasets/football-datasets 的 datasets/{premier-league,la-liga,serie-a,bundesliga,ligue-1}/season-2627.csv 本次均返回404。
- 直接下载渠道网络批准未完成，未绕过限制。
- 新增 season_update 模块：校验赛季、截止日、赛果一致性、重复及比分冲突；输出包含旧数据与新赛季数据的独立快照。
- 本次未重新训练、未修改既有预测档案、未启用定时下载。

## 使用方法

先取得经过核验的新赛季数据文件（上游字段 Date/HomeTeam/AwayTeam/FTHG/FTAG/FTR，日期 ISO 格式）。

```bash
PYTHONPATH=src python -m sports_lottery.season_update season-2627.csv \
  --league premier-league --season 2627 --through 2026-09-04 \
  --history data/processed/top5_2016_2026 \
  --output data/processed/combined_snapshot_01 \
  --source-url https://github.com/datasets/football-datasets/blob/main/datasets/premier-league/season-2627.csv
```

第二个联赛导入时，以前一个快照作为 --history，输出到新的目录。不要覆盖历史快照。
将统一比较命令的 directory 参数改为最后一个合并目录，三个模型才会使用同一份更新后的数据。
攻防模型须基于新快照重新拟合；既有静态模型文件不会因新增数据而自动更新。

## 尚需补齐

1. 新赛季真实结果，及非五大联赛的可靠历史与新赛季数据。
2. 官方竞彩编号、让球及玩法售卖状态（第三方联赛结果不能替代）。
3. 带采集时刻的伤停、首发、转会与教练变化，目前不能声称已数值化接入。
4. 杯赛90分钟/加时/点球区分、首回合比分；不要套用联赛导入器。
5. 滚动样本外校准、与基准比较、低有效样本警告。
6. 赛前预测存档和赛后复盘；今日采集到的历史更正不等同于当时已知信息。

本模块拒绝同一比赛的比分冲突，必须人工核验后处理。来源文件须单独保留；manifest提供合并数据摘要，不等同于保存了上游原始证据。
足球数据增多不保证预测更准确，更不保证盈利。
