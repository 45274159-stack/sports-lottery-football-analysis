import json
import unittest
from datetime import date,timedelta
from sports_lottery.fitted_model import fit,predict,holdout

class FittedTests(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(league="L",date=(date(2020,1,1)+timedelta(days=i)).isoformat(),home_team="A" if i%2 else "B",away_team="B" if i%2 else "A",ft_home_goals="3" if i%2 else "0",ft_away_goals="0" if i%2 else "2",ft_result="H" if i%2 else "A") for i in range(120)]
    def test_fit_learns_and_serializes(self):
        m=fit(self.rows,"L","2020-06-01")
        self.assertGreater(m["teams"]["A"]["attack_log"],m["teams"]["B"]["attack_log"])
        p=predict(json.loads(json.dumps(m)),"A","B","2020-06-02")
        self.assertGreater(p["result"]["H"],p["result"]["A"])
        self.assertAlmostEqual(sum(p["result"].values()),1)
    def test_cutoff_excludes_future(self):
        m=fit(self.rows,"L","2020-06-01")
        self.assertEqual(m,fit(self.rows+[dict(self.rows[0],date="2021-01-01")],"L","2020-06-01"))
        with self.assertRaises(ValueError):predict(m,"A","B","2020-06-01")
        with self.assertRaises(ValueError):predict(m,"Unknown","B","2020-06-02")
    def test_empty_holdout(self):
        self.assertIsNone(holdout(fit(self.rows,"L","2020-06-01"),self.rows)["accuracy"])
