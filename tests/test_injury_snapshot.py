import json
import unittest
from pathlib import Path
from sports_lottery.injury_snapshot import attach_injuries
from sports_lottery.prematch import dossier

class InjurySnapshotTest(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((Path(__file__).parents[1]/'data/prematch/2026-09-04-injuries.json').read_text())
        self.at=self.data['observed_at']

    def test_all_fixtures_and_dossiers(self):
        self.assertEqual(len(self.data['fixtures']),14)
        for match in self.data['fixtures']:
            fixture={k:match[k] for k in ('source_id','home','away','kickoff','league')}
            enriched=attach_injuries(fixture,self.data,self.at)
            report=dossier([],enriched,self.at)
            self.assertFalse(report['numeric_adjustment'])
            self.assertEqual(attach_injuries(enriched,self.data,self.at),enriched)
            self.assertNotIn('prematch',fixture)

    def test_pre_observation_rejected(self):
        with self.assertRaises(ValueError):
            attach_injuries(self.data['fixtures'][0],self.data,'2026-09-04T00:00:00Z')

    def test_swapped_teams_rejected(self):
        fixture=dict(self.data['fixtures'][0])
        fixture['home'],fixture['away']=fixture['away'],fixture['home']
        with self.assertRaises(ValueError):
            attach_injuries(fixture,self.data,self.at)

    def test_unknown_not_healthy(self):
        fixture=self.data['fixtures'][0]
        result=attach_injuries(fixture,self.data,self.at)
        self.assertEqual(result['injury_coverage']['Hannover']['status'],'unknown')
        self.assertEqual(result['prematch'],[])

if __name__=='__main__': unittest.main()
