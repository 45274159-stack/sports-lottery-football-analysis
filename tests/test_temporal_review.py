import json
import unittest
from sports_lottery.unified import connect, encoded, fingerprint
from sports_lottery.temporal_review import evaluate_archive, transform


class TemporalReviewTests(unittest.TestCase):
    def setUp(self):self.db=connect(":memory:")
    def tearDown(self):self.db.close()
    def add(self,i,day,y,observed=None):
        ident=str(i); snap=dict(test=i)
        fixture=dict(league="L",kickoff=f"2026-08-{day:02}T18:00:00Z")
        result=dict(status="final",period="90_minutes",home_goals=1 if y=="H" else 0,
                    away_goals=1 if y=="A" else 0,observed_at=observed or f"2026-08-{day:02}T21:00:00Z")
        self.db.execute("INSERT INTO fixtures VALUES (?,?)",(ident,encoded(fixture)))
        self.db.execute("INSERT INTO comparisons VALUES (?,?,?,?,?)",(ident,ident,f"2026-08-{day:02}T10:00:00Z",fingerprint(snap),encoded(snap)))
        self.db.execute("INSERT INTO forecasts VALUES (?,?,?,?)",(ident,"test-model","ok",encoded(dict(prediction=dict(result=dict(H=.8,D=.1,A=.1))))))
        self.db.execute("INSERT INTO outcomes VALUES (?,?)",(ident,encoded(result)))
    def run_report(self):return evaluate_archive(self.db,"2026-08-10T00:00:00Z","2026-09-01T00:00:00Z",3)
    def test_transform(self):
        p=transform(dict(H=.8,D=.1,A=.1),2)
        self.assertAlmostEqual(sum(p.values()),1)
        self.assertLess(p["H"],.8)
        with self.assertRaises(ValueError):transform(dict(H=1,D=1,A=1),1)
    def test_split_immutable_and_no_test_label_leak(self):
        for i,y in enumerate("HDA",1):self.add(i,i,y)
        self.add(4,12,"A")
        before=list(self.db.execute("SELECT * FROM forecasts"))
        r=self.run_report()["groups"][0]
        self.assertEqual(r["calibration_n"],3);self.assertEqual(r["test_raw"]["n"],1)
        saved=json.loads(self.db.execute("SELECT payload FROM outcomes WHERE fixture_id='4'").fetchone()[0])
        saved.update(home_goals=1,away_goals=0)
        self.db.execute("UPDATE outcomes SET payload=? WHERE fixture_id='4'",(encoded(saved),))
        self.assertEqual(r["temperature"],self.run_report()["groups"][0]["temperature"])
        self.assertEqual(before,list(self.db.execute("SELECT * FROM forecasts")))
    def test_late_result_not_calibration(self):
        self.add(1,1,"H",observed="2026-08-11T00:00:00Z")
        r=self.run_report()
        self.assertEqual(r["exclusions"]["boundary_or_delayed_result"],1)
        self.assertEqual(r["groups"][0]["calibration_status"],"insufficient_samples_or_missing_class")
    def test_tamper_rejected(self):
        self.add(1,1,"H")
        self.db.execute("UPDATE comparisons SET snapshot='{}'")
        with self.assertRaises(ValueError):self.run_report()
    def test_empty(self):self.assertEqual(self.run_report()["groups"],[])
