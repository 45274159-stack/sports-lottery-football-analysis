"""Reproducible import of public historical results; no invented missing scores."""
import csv, io, json, re, hashlib
from pathlib import Path
from datetime import datetime, date
from collections import Counter, defaultdict
from sports_lottery.history_quality import load_validated, outcome

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/expansion_20260904'
OUT=ROOT/'data/processed/expanded_leagues_2016_2026'
REPORT=ROOT/'reports/expansion_20260904.json'
LEAGUES={'de.2':'2. Bundesliga','fr.2':'Ligue 2','nl.1':'Eredivisie','pt.1':'Primeira Liga',
         'no.1':'Eliteserien','us.1':'MLS','mls':'MLS','nl2':'Eerste Divisie','no1':'Eliteserien'}
FIELDS=['source','source_url','source_revision','source_row','observed_at','league','season','date',
        'home_team','away_team','ft_home_goals','ft_away_goals','ft_result',
        'ht_home_goals','ht_away_goals','ht_result','round','score_period','home_team_raw','away_team_raw']

def score(value):
    m=re.fullmatch(r'(\d+)-(\d+)',value.strip())
    if not m:raise ValueError('No unambiguous full-time score')
    return tuple(map(int,m.groups()))

def identify(p):
    if p['format']=='saudi':return 'Saudi Pro League','2016-17'
    if p['format']=='soccerway_secondary':
        name=Path(p['path']).stem
        keys={'saudi_saudi_pro_league':'Saudi Pro League','netherlands_eerste_divisie':'Eerste Divisie',
              'germany_2_bundesliga':'2. Bundesliga','france_ligue_2':'Ligue 2','netherlands_eredivisie':'Eredivisie'}
        league=next(v for k,v in keys.items() if name.startswith(k))
        s=re.search(r'(20\d\d)-(20\d\d)',name)
        return league,s[1]+'-'+s[2][-2:]
    if p['format']=='footballtxt':
        s,k=Path(p['path']).stem.split('_');return LEAGUES[k],s
    return LEAGUES[Path(p['path']).stem],p['path'].split('/')[0]

def records(p,text):
    league,season=identify(p)
    if p['format']=='soccerway_secondary':
        for i,r in enumerate(csv.DictReader(io.StringIO(text.lstrip('\ufeff'))),2):
            yield i,dict(date=datetime.strptime(r['date'],'%B %d, %Y').date().isoformat(),home=r['home_team'],
                         away=r['away_team'],ft=r['home_goals']+'-'+r['away_goals'],ht='?',round=r.get('round',''),
                         reported_result=r.get('result',''))
    elif p['format']=='footballcsv':
        for i,r in enumerate(csv.DictReader(io.StringIO(text.lstrip('\ufeff'))),2):
            yield i,dict(date=datetime.strptime(r['Date'],'%a %b %d %Y').date().isoformat(),
                         home=r['Team 1'],away=r['Team 2'],ft=r['FT'],ht=r.get('HT','?'),round='')
    elif p['format']=='footballjson':
        obj=json.loads(text)
        games=obj.get('matches')
        if games is None:games=[{**m,'round':r.get('name','')} for r in obj['rounds'] for m in r['matches']]
        for i,r in enumerate(games,1):
            sc=r.get('score',{})
            if not isinstance(sc,dict):sc={}
            ft=sc.get('ft');ht=sc.get('ht')
            # Never interpret an extra-time total as a regulation score.
            bad=any(sc.get(k) is not None for k in ['et','aet','p','pen'])
            yield i,dict(date=r.get('date',''),home=r['team1'],away=r['team2'],
                         ft='ambiguous-extra-time' if bad else '-'.join(map(str,ft or [])),
                         ht='-'.join(map(str,ht)) if ht else '?',round=r.get('round',''))
    elif p['format']=='saudi':
        for i,r in enumerate(csv.DictReader(io.StringIO(text.lstrip('\ufeff'))),2):
            dt=re.sub(r'\s+','',r['Date'])
            yield i,dict(date=datetime.strptime(dt,'%d.%m.%Y').date().isoformat(),home=r['Team1'],away=r['Team2'],
                         ft=r['Score1']+'-'+r['Score2'],ht='?',round=r.get('Round',''),note=r.get('Note',''))
    else:
        current=None;round_name='';year=int(season[:4]);cross='-' in season
        for i,line in enumerate(text.splitlines(),1):
            clean=line.strip()
            if clean.startswith('▪'):round_name=clean.lstrip('▪ ').strip()
            m=re.fullmatch(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) ([A-Z][a-z]{2}) (\d{1,2})(?: (\d{4}))?',clean)
            if m:
                mo=datetime.strptime(m[2],'%b').month
                yy=int(m[4]) if m[4] else year+int(cross and mo<7)
                current=date(yy,mo,int(m[3])).isoformat();continue
            if ' v ' not in line:continue
            m=re.match(r'^\s*(?:\d{1,2}:\d{2}\s+)?(.+?)\s+v\s+(.+?)\s{2,}(\d+-\d+)(?:\s+\((\d+-\d+)\))?\s*$',line)
            if not m:
                yield i,dict(date=current or '',home='?',away='?',ft='unparsed',ht='?',round=round_name);continue
            yield i,dict(date=current or '',home=m[1],away=m[2],ft=m[3],ht=m[4] or '?',round=round_name)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((RAW/'manifest.json').read_text());rows=defaultdict(list);errors=[];sources=[];seen={};duplicates=0
    alias_path=ROOT/'data/config/expanded_team_aliases.json'
    aliases=json.loads(alias_path.read_text()) if alias_path.exists() else {}
    for p in manifest:
        league,season=identify(p)
        raw=RAW/p['repo'].split('/')[1]/p['path'];text=raw.read_text(encoding='utf-8')
        accepted=0;rejected=0
        for i,r in records(p,text):
            try:
                day=date.fromisoformat(r['date'])
                if not date(2016,1,1)<=day<date(2026,9,4):raise ValueError('Outside date window or unfinished future match')
                h,a=score(r['ft']);ht=('', '') if r['ht'] in ('?','','-') else score(r['ht'])
                if r.get('reported_result') and r['reported_result']!=outcome(h,a):raise ValueError('Source result disagrees with goals')
                if ht[0]!='' and (ht[0]>h or ht[1]>a):raise ValueError('Halftime exceeds fulltime')
                if r.get('note'):raise ValueError('Special match note requires review: '+r['note'])
                home=' '.join(r['home'].split());away=' '.join(r['away'].split())
                home=aliases.get(league,{}).get(home,home);away=aliases.get(league,{}).get(away,away)
                if home==away:raise ValueError('Same team')
                key=(league,r['date'],home,away)
                if key in seen:
                    if seen[key]==r['ft']:
                        duplicates+=1;continue
                    raise ValueError('Conflicting duplicate score '+str(seen[key]))
                seen[key]=r['ft']
                row=dict(source=p['repo'],source_url=p['url'],source_revision=p['sha'],source_row=i,
                         observed_at=p['observed_at'],league=league,season=season,date=r['date'],home_team=home,
                         away_team=away,ft_home_goals=h,ft_away_goals=a,ft_result=outcome(h,a),
                         ht_home_goals=ht[0],ht_away_goals=ht[1],ht_result=outcome(*ht) if ht[0]!='' else '',
                         round=r['round'],score_period='source_reported_FT',home_team_raw=r['home'],away_team_raw=r['away'])
                rows[league].append(row);accepted+=1
            except (ValueError,TypeError) as e:
                errors.append(dict(source=p['path'],repo=p['repo'],row=i,reason=str(e),record=r));rejected+=1
        sources.append(dict(repo=p['repo'],path=p['path'],source_url=p['url'],revision=p['sha'],league=league,
                            season=season,accepted=accepted,rejected=rejected,sha256=hashlib.sha256(raw.read_bytes()).hexdigest()))
    summary={}
    for league,rs in rows.items():
        rs.sort(key=lambda r:(r['date'],r['home_team'],r['away_team']))
        filename=re.sub(r'[^a-z0-9]+','_',league.lower()).strip('_')+'.csv'
        with (OUT/filename).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rs)
        summary[league]=dict(rows=len(rs),seasons=dict(sorted(Counter(r['season'] for r in rs).items())),
                            first_date=rs[0]['date'],last_date=rs[-1]['date'],file=str((OUT/filename).relative_to(ROOT)))
    validated,issues=load_validated(str(OUT))
    payload=dict(as_of='2026-09-04',scope='2016-17 to 2025-26; calendar leagues 2016 to 2025',
                 imported=len(validated),validation_issues=issues,exact_duplicates_removed=duplicates,leagues=summary,quarantine=errors,sources=sources,
                 warning='Coverage is not completeness. Current season absent. MLS FT and stage need review before wagering-period use.')
    REPORT.write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps(dict(imported=len(validated),issues=issues,quarantined=len(errors),leagues=summary),ensure_ascii=False,indent=2))
    if issues:raise ValueError(issues)
if __name__=='__main__':main()
