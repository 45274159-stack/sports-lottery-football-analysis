"""Read separately sourced history without silently enabling incomplete models."""
import json
from copy import deepcopy
from pathlib import Path
from .history_quality import load_validated

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT/'data/processed/expanded_leagues_2016_2026'

def canonical_fixture(fixture):
    result=deepcopy(fixture)
    league={'Bundesliga 2':'2. Bundesliga'}.get(result['league'],result['league'])
    aliases=json.loads((ROOT/'data/config/expanded_team_aliases.json').read_text())
    extra={'Eliteserien':{'Bodo Glimt':'Bodo/Glimt'},'MLS':{'Nashville':'Nashville SC'}}
    result['league']=league
    for key in ('home','away'):
        result[key]=extra.get(league,{}).get(result[key],result[key])
        result[key]=aliases.get(league,{}).get(result[key],result[key])
    return result

def load_expanded_history():
    rows,issues=load_validated(str(DIRECTORY))
    if issues:raise ValueError(issues)
    return rows

def coverage_for_fixture(fixture):
    f=canonical_fixture(fixture)
    rows=[r for r in load_expanded_history() if r['league']==f['league']]
    teams={name:sum(r['home_team']==name or r['away_team']==name for r in rows) for name in (f['home'],f['away'])}
    return dict(fixture=f,history_rows=len(rows),team_rows=teams,
                earliest=min((r['date'] for r in rows),default=None),
                latest=max((r['date'] for r in rows),default=None),
                model_ready=False,
                reason='Partial coverage; current season and competition-stage/FT checks required before enabling forecasts')
