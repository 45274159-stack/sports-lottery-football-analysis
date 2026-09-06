# 近十年历史缺口补档（2026-09-06）

十年主表原约 40,842 场。

## 已准备的补档（项目目录 `decade_gaps/`）

来源：Hugging Face `eatpizzanot/soccer-dataset` fixtures.parquet（SECONDARY）。

| 文件 | 场次 |
|---|---|
| eerste_divisie_2016_2020_gaps.csv | 1430 |
| saudi_2018_2024_gaps.csv | 1506 |
| eliteserien_2024_2026_more.csv | 308 |
| mls_2024_2026_more.csv | 1250 |
| eliteserien_2024_2025_gaps.csv（openfootball） | 164 |
| saudi_2017_18_gaps.csv（alioh） | 186 |

合计约 **4844** 场新行。放进 `data/processed/completed_gaps_decade/` 后由 `load_all_history()` 读取。

## 源内仍不满的

- 沙特 2019-20：176 / 240
- 荷乙 2019-20：290 / 380
