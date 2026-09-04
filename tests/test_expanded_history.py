import importlib.util
import json
import unittest
from sports_lottery.expanded_history import ROOT, canonical_fixture, load_expanded_history, coverage_for_fixture

spec=importlib.util.spec_from_file_location('expansion_import',ROOT/'scripts/import_expansion_20260904.py')
imp=importlib.util.module_from_spec(spec);spec.loader.exec_module(imp)

class ExpandedHistoryTests(unittest.TestCase):
    def test_archive_validation(self):
        rows=load_expanded_history()
        audit=json.loads((ROOT/'reports/expansion_20260904.json').read_text())
        self.assertEqual(len(rows),audit['imported'])
        self.assertEqual(len({r['league'] for r in rows}),8)
        self.assertTrue(all(r['source_url'] and r['date']<'2026-09-04' for r in rows))

    def test_eight_fixture_names_resolve(self):
        fixtures=json.loads((ROOT/'data/prematch/2026-09-04-injuries.json').read_text())['fixtures']
        for f in fixtures:
            if f['number'][-3:] in ('001','003','004','005','006','007','013','014'):
                c=coverage_for_fixture(f)
                self.assertTrue(all(c['team_rows'].values()),c)
                self.assertFalse(c['model_ready'])

    def test_source_empty_score_never_zero(self):
        p={'format':'footballjson','path':'2025-26/de.2.json'}
        games=list(imp.records(p,json.dumps({'matches':[{'date':'2025-08-01','team1':'A','team2':'B','score':[]}]})))
        with self.assertRaises(ValueError):imp.score(games[0][1]['ft'])

    def test_txt_out_of_order_postponements(self):
        p={'format':'footballtxt','path':'netherlands/2020-21_nl2.txt'}
        t='Tue Jan 5 2021\n A   v B   1-0\nThu Dec 10\n C   v D   0-0\n'
        rs=list(imp.records(p,t))
        self.assertEqual([r['date'] for _,r in rs],['2021-01-05','2020-12-10'])

    def test_different_clubs_not_fuzzy_merged(self):
        a=canonical_fixture({'league':'Primeira Liga','home':'Aves','away':'AVS'})
        self.assertNotEqual(a['home'],a['away'])
