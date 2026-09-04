"""Fitted regularized Poisson attack/defence model; dependency-free JSON artifacts."""
import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from .forecast import markets
from .history_quality import load_validated


def fit(rows, league, through, iterations=300, ridge=5., half_life=365.):
    cutoff = date.fromisoformat(through)
    selected = sorted((r for r in rows if r["league"] == league and r["date"] <= through),
                      key=lambda r: (r["date"],r["home_team"],r["away_team"]))
    if len(selected) < 100 or iterations < 1 or ridge <= 0 or half_life <= 0:
        raise ValueError("Need 100 matches and positive fit parameters")
    teams = sorted({r[k] for r in selected for k in ("home_team","away_team")})
    index = {t:i for i,t in enumerate(teams)}
    # Aggregate sufficient statistics for repeated pairings after time weighting.
    pairs = defaultdict(lambda: [0.,0.,0.])
    counts = Counter()
    for r in selected:
        w = 2**(-(cutoff-date.fromisoformat(r["date"])).days/half_life)
        cell = pairs[index[r["home_team"]],index[r["away_team"]]]
        cell[0] += w; cell[1] += w*int(r["ft_home_goals"]); cell[2] += w*int(r["ft_away_goals"])
        counts[r["home_team"]] += 1; counts[r["away_team"]] += 1
    n = len(teams); attack = [0.]*n; defence = [0.]*n
    weight = sum(c[0] for c in pairs.values())
    intercept_h = math.log(max(.1,sum(c[1] for c in pairs.values())/weight))
    intercept_a = math.log(max(.1,sum(c[2] for c in pairs.values())/weight))
    for _ in range(iterations):
        ga = [ridge*x for x in attack]; gd = [ridge*x for x in defence]
        ca = [ridge]*n; cd = [ridge]*n
        gh=gg=ch=cg=0.
        for (h,a),(w,yh,ya) in pairs.items():
            mh=w*math.exp(intercept_h+attack[h]+defence[a])
            ma=w*math.exp(intercept_a+attack[a]+defence[h])
            rh,ra=mh-yh,ma-ya
            ga[h]+=rh;gd[a]+=rh;ga[a]+=ra;gd[h]+=ra
            ca[h]+=mh;cd[a]+=mh;ca[a]+=ma;cd[h]+=ma
            gh+=rh;gg+=ra;ch+=mh;cg+=ma
        # Damped diagonal Newton updates. Ridge anchors the scale of team effects.
        attack=[x-.2*g/c for x,g,c in zip(attack,ga,ca)]
        defence=[x-.2*g/c for x,g,c in zip(defence,gd,cd)]
        intercept_h-=.2*gh/max(ch,1e-9);intercept_a-=.2*gg/max(cg,1e-9)
    digest=hashlib.sha256(json.dumps(selected,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return dict(schema_version=1,family="fitted-poisson-attack-defence",version="1.0.0",league=league,
                trained_through=through,training_matches=len(selected),latest_training_match=selected[-1]["date"],
                training_hash=digest,parameters=dict(iterations=iterations,ridge=ridge,half_life_days=half_life),
                intercept_home=intercept_h,intercept_away=intercept_a,
                teams={t:dict(attack_log=attack[i],defence_log=defence[i],matches=counts[t]) for t,i in index.items()},
                status="experimental",limitations=["Independent goals assumption", "No injuries, lineups, xG or odds",
                  "Structural input checks are not independent verification of source results", "No prospective validation or profit claim"])


def predict(model, home, away, before):
    if date.fromisoformat(before) <= date.fromisoformat(model["trained_through"]):
        raise ValueError("Prediction must follow training cutoff")
    if home == away or home not in model["teams"] or away not in model["teams"]:
        raise ValueError("Distinct known teams required; unknown teams must not silently use average strength")
    h,a=model["teams"][home],model["teams"][away]
    lh=math.exp(model["intercept_home"]+h["attack_log"]+a["defence_log"])
    la=math.exp(model["intercept_away"]+a["attack_log"]+h["defence_log"])
    if max(lh,la)>6:
        raise ValueError("Goal rate exceeds supported range; abstain")
    return dict(home=home,away=away,before=before,expected_goals=dict(home=lh,away=la),
                model_version=model["version"],trained_through=model["trained_through"],
                warnings=model["limitations"],**markets(lh,la))


def holdout(model, rows):
    test = [r for r in rows if r["league"] == model["league"] and r["date"]>model["trained_through"]]
    n=hits=score_hits=goal_hits=home_hits=skipped=0;loss=brier=0.
    for r in test:
        try:p=predict(model,r["home_team"],r["away_team"],r["date"])
        except ValueError:skipped+=1;continue
        actual=r["ft_result"];n+=1
        hits+=max(p["result"],key=p["result"].get)==actual
        home_hits+=actual=="H"
        score_hits+=p["scores"][0][0]==f'{r["ft_home_goals"]}:{r["ft_away_goals"]}'
        total=int(r["ft_home_goals"])+int(r["ft_away_goals"])
        goal_hits+=max(p["total_goals"],key=p["total_goals"].get)==(str(total) if total<7 else "7+")
        loss-=math.log(max(p["result"][actual],1e-15))
        brier+=sum((p["result"][k]-(actual==k))**2 for k in "HDA")
    return dict(eligible_matches=len(test),evaluated=n,skipped=skipped,
                accuracy=hits/n if n else None,always_home_accuracy=home_hits/n if n else None,
                score_accuracy=score_hits/n if n else None,total_goals_accuracy=goal_hits/n if n else None,
                log_loss=loss/n if n else None,brier=brier/n if n else None,
                protocol="Fixed trained parameters; later chronological holdout; not a new prospective trial",roi=None)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    train=sub.add_parser("train");train.add_argument("directory");train.add_argument("--through",required=True)
    infer=sub.add_parser("predict");infer.add_argument("bundle");infer.add_argument("--league",required=True)
    infer.add_argument("--home",required=True);infer.add_argument("--away",required=True);infer.add_argument("--before",required=True)
    args=parser.parse_args()
    if args.command=="train":
        rows,issues=load_validated(args.directory)
        if issues:raise SystemExit("\n".join(issues))
        models={l:fit(rows,l,args.through) for l in sorted({r["league"] for r in rows})}
        result=dict(models=models,evaluations={l:holdout(m,rows) for l,m in models.items()})
    else:
        bundle=json.loads(Path(args.bundle).read_text(encoding="utf-8"))
        result=predict(bundle["models"][args.league],args.home,args.away,args.before)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
