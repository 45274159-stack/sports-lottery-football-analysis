"""Run six covered fixtures with traceable injury evidence, preserving old forecasts."""
import json
from datetime import datetime, timezone
from pathlib import Path
from sports_lottery.unified import connect, compare
from sports_lottery.history_quality import load_validated
from sports_lottery.injury_snapshot import attach_injuries

rows, issues = load_validated('data/processed/top5_2016_2026')
if issues:
    raise ValueError(issues)
snapshot = json.loads(Path('data/prematch/2026-09-04-injuries.json').read_text())
at = datetime.now(timezone.utc).isoformat()
previous = json.loads(Path('reports/model_run_20260904.json').read_text())
db = connect(':memory:')
results = []
for old in previous['results']:
    fixture = attach_injuries(old['fixture'], snapshot, at)
    comparison = compare(db, rows, fixture, at)
    results.append(dict(number=old['number'], fixture=fixture, comparison=comparison))
    print(old['number'], {k:v.get('prediction',{}).get('result') for k,v in comparison['outputs'].items()}, flush=True)
report = dict(created_at=at, history_rows=len(rows), injury_snapshot=snapshot['observed_at'],
              numeric_injury_adjustment=False, results=results)
Path('reports/model_run_20260904_injuries.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
