"""Attach reviewed injury snapshots to future dossiers without backdating."""
from copy import deepcopy
from .match_context import aware_time
from .team_names import normalize_team


def attach_injuries(fixture, snapshot, at):
    """Preserve source claims; first observation is the conservative evidence clock.

    published_at is an adapter availability clock, NOT a claimed publication time.
    Real source publication metadata and this distinction are retained in details.
    """
    observed = snapshot['observed_at']
    if not aware_time(observed) <= aware_time(at) < aware_time(fixture['kickoff']):
        raise ValueError('Snapshot unavailable at prediction time or match started')
    matches = [m for m in snapshot['fixtures'] if m['source_id'] == fixture['source_id']]
    if len(matches) != 1:
        raise ValueError('Unique match ID required')
    match = matches[0]
    if any(normalize_team(match[k]) != normalize_team(fixture[k]) for k in ('home','away')):
        raise ValueError('Home/away mismatch')
    if aware_time(match['kickoff']) != aware_time(fixture['kickoff']):
        raise ValueError('Kickoff mismatch')
    result = deepcopy(fixture)
    evidence = result.setdefault('prematch', [])
    existing = {r.get('injury_record_id') for r in evidence}
    coverage = {}
    for team in match['teams']:
        coverage[team['team']] = {'status':team['coverage'], 'note':team['note']}
        for index, claim in enumerate(team['records']):
            source = snapshot['sources'][claim['source_key']]
            rid = f"{fixture['source_id']}:{observed}:{team['team']}:{index}"
            if rid in existing:
                continue
            availability = claim['availability']
            status = 'doubtful' if availability == 'doubtful' else 'unknown'
            if source['type'] == 'official' and availability != 'conflicting':
                status = 'confirmed' if availability != 'doubtful' else 'doubtful'
            evidence.append(dict(injury_record_id=rid, source_id=fixture['source_id'],
                team=team['team'], category='injuries', source_url=source['url'],
                source_type=source['type'], published_at=observed, observed_at=observed,
                status=status, summary=f"{claim['player']}: {availability}; {claim['reason']}",
                details={**claim, 'source_published_at':source['published_at'],
                    'source_published_date':source['published_date'],
                    'timestamp_basis':'first_observed_not_source_publication',
                    'numeric_adjustment':False}))
            existing.add(rid)
    result['injury_coverage'] = coverage
    return result
