"""Package a pinned repository data snapshot, not a claim of worldwide completeness."""
import csv, io, json, hashlib, zipfile
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
OVERRIDE=ROOT.parent/'bundle-source-20260904'
PLAN=ROOT/'data/snapshots/20260904-upload-plan.json'
ARCHIVE=ROOT/'data/archives/football_data_available_2016_to_20260904.zip'
INDEX=ROOT/'data/snapshots/20260904-upload-manifest.json'

def blob_sha(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def main():
    plan=json.loads(PLAN.read_text());files={};checks=[];counts=Counter();dates=[]
    for e in plan['entries']:
        candidates=[OVERRIDE/e['path'],ROOT/e['path']];data=None
        for p in candidates:
            if not p.is_file():continue
            b=p.read_bytes()
            for candidate in [b,b[:-1] if b.endswith(b'\n') else b]:
                if blob_sha(candidate)==e['sha']:
                    data=candidate;break
            if data is not None:break
        if data is None:raise ValueError('Cannot reproduce pinned blob: '+e['path'])
        files[e['path']]=data
        checks.append(dict(path=e['path'],bytes=len(data),git_blob_sha=e['sha'],sha256=hashlib.sha256(data).hexdigest()))
        if e['path'].endswith('.csv') and '/processed/' in e['path']:
            for r in csv.DictReader(io.StringIO(data.decode('utf-8-sig'))):
                league=r.get('league') or ('Champions League' if 'champions_league.csv' in e['path'] else None)
                if not league:raise ValueError('Unknown competition '+e['path'])
                counts[league]+=1;dates.append(r['date'])
    injury=json.loads(files['data/prematch/2026-09-04-injuries.json'])
    today=dict(lottery_date='2026-09-04',source_observed_at=injury['observed_at'],
               scope='14 fixtures from the existing Sporttery-day snapshot, not all global football',
               official_number_verification=injury['official_number_verification'],
               fixtures=[{k:m[k] for k in ('source_id','number','league','kickoff','home','away')} for m in injury['fixtures']],
               result_policy='No match outcomes added; fixture schedule is not live-reverified during packaging')
    files['today/2026-09-04-fixtures.json']=json.dumps(today,ensure_ascii=False,indent=2).encode()
    result_batch=json.loads(files['data/processed/results/2026-09-03.json'])
    prediction=json.loads(files['reports/model_run_20260904_injuries.json'])
    summary=dict(created_at=datetime.now(timezone.utc).isoformat(),source_commit=plan['source_commit'],
                 scope='All data and reports present in the pinned project snapshot; not worldwide comprehensive data',
                 history_rows=sum(counts.values()),history_by_competition=dict(sorted(counts.items())),
                 earliest_date=min(dates),latest_history_date=max(dates),source_files=len(checks),
                 today_fixture_count=len(today['fixtures']),injury_records=sum(len(t['records']) for m in injury['fixtures'] for t in m['teams']),
                 archived_forecast_fixtures=len(prediction['results']),
                 separately_archived_results=len(result_batch['records']),
                 separately_archived_results_lottery_date='2026-09-03',
                 results_added_for_20260904=False,
                 files=checks,
                 limitations=['Missing seasons and rounds remain. See reports/expansion_20260904.json.',
                              'No complete worldwide fixtures or ten-year injury/lineup/SP archive.',
                              'History FT and competition phases retain existing verification limitations.',
                              'No new training, calibration or forecast was performed by packaging.'])
    readme=f'''# 足球数据整包（截至2026-09-04已收集资料）

这是现有项目数据的版本备份，不是全球所有足球比赛的完整十年数据库。

- 历史CSV记录：{sum(counts.values()):,}场，{len(counts)}个赛事类别。
- 今天已收集竞彩足球：14场赛程、84条球员状态记录、6场模型预测。
- 另存9月3日竞彩批次赛果：{len(result_batch['records'])}场；原文件注明尚未进入训练。
- 今天赛程批次未新增任何赛果，不把预测比分当作实际结果。
- 来源仓库版本：{plan['source_commit']}。

## 内容

data/processed：五大联赛、欧冠、补充8联赛、单独赛果批次。
data/prematch：今天的伤停快照（包含复训、停赛、存疑，不等于84名伤员）。
data/models：模型目录与已拟合参数。
data/config：明确的球队别名映射。
data/archives：补充数据原始来源压缩包（含许可说明）。
reports：质量、回测、校准观察、复盘和预测记录。
today：从已保存快照提取的14场赛程，不是本次重新抓取的全球赛程。
MANIFEST.json：逐文件SHA256、Git blob校验值和范围说明。

## 必须保留的缺口

德乙、挪超、法乙、荷甲、葡超、美职联虽然覆盖10个赛季/年份，部分赛季缺场。
荷乙目前6季，沙特联目前3季；不能称为十年已齐。
新赛季数据、全部伤停首发、历史竞彩奖金仍不完整。模型未因打包而升级。
保留各来源自己的许可与归属，不将第三方数据声明为本项目原创。
'''
    files['README_数据范围.txt']=readme.encode('utf-8')
    files['MANIFEST.json']=json.dumps(summary,ensure_ascii=False,indent=2).encode()
    ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):z.writestr(name,data)
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None
        assert all(z.read(k)==v for k,v in files.items())
    summary['archive']=dict(path=str(ARCHIVE.relative_to(ROOT)),bytes=ARCHIVE.stat().st_size,
                            sha256=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),members=len(files))
    INDEX.write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='files'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
