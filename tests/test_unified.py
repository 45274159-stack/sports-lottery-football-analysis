import sqlite3
import unittest
from datetime import date,timedelta
from sports_lottery.unified import connect,compare,record_outcome,report,fixture_record,MODELS


class UnifiedTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
        self.rows=[dict(league="L",date=(date(2020,1,1)+timedelta(days=i)).isoformat(),home_team="A" if i%2 else "B",away_team="B" if i%2 else "A",ft_home_goals="2",ft_away_goals="1",ft_result="H") for i in range(120)]
        self.fixture=dict(league="L",home="A",away="B",kickoff="2020-06-02T18:00:00Z",source_id="synthetic-1",source_url="https://example.org/synthetic")
        self.outcome=dict(period="90_minutes",status="final",home_goals=2,away_goals=1,source_url="https://example.org/synthetic",observed_at="2020-06-02T21:00:00Z")
    def tearDown(self):self.db.close()
    def test_complete_round_trip(self):
        result=compare(self.db,self.rows,self.fixture,"2020-06-01T12:00:00Z")
        self.assertTrue(all(x["status"]=="ok" for x in result["outputs"].values()))
        self.assertEqual(report(self.db)["pending"],1)
        record_outcome(self.db,result["fixture_id"],self.outcome)
        summary=report(self.db)
        self.assertEqual(len(summary["paired_metrics"]),3)
        self.assertTrue(all(m["n"]==1 for m in summary["paired_metrics"]))
        self.assertIsNone(next(m for m in summary["paired_metrics"] if m["model"]==MODELS[0])["score_accuracy"])
    def test_duplicate_prediction_and_result_rejected(self):
        result=compare(self.db,self.rows,self.fixture,"2020-06-01T12:00:00Z")
        with self.assertRaises(sqlite3.IntegrityError):compare(self.db,self.rows,self.fixture,"2020-06-01T12:00:00Z")
        record_outcome(self.db,result["fixture_id"],self.outcome)
        with self.assertRaises(sqlite3.IntegrityError):record_outcome(self.db,result["fixture_id"],self.outcome)
    def test_skips_retained(self):
        result=compare(self.db,[],self.fixture,"2020-06-01T12:00:00Z")
        record_outcome(self.db,result["fixture_id"],self.outcome)
        summary=report(self.db)
        self.assertEqual(len(summary["excluded_comparisons"]),1)
        self.assertEqual(summary["paired_metrics"],[])
        self.assertEqual(len(summary["attempts"]),3)
    def test_same_day_results_do_not_leak(self):
        first=compare(self.db,self.rows,self.fixture,"2020-06-01T12:00:00Z")
        other=connect(":memory:")
        try:
            second=compare(other,self.rows+[dict(self.rows[0],date="2020-06-01")],self.fixture,"2020-06-01T12:00:00Z")
            self.assertEqual(first["snapshot_hash"],second["snapshot_hash"])
        finally:other.close()
    def test_earliest_prediction_only(self):
        first=compare(self.db,self.rows,self.fixture,"2020-06-01T12:00:00Z")
        compare(self.db,self.rows,self.fixture,"2020-06-01T13:00:00Z")
        record_outcome(self.db,first["fixture_id"],self.outcome)
        self.assertEqual(report(self.db)["fixtures"],1)
    def test_timezone_identity(self):
        other=dict(self.fixture,kickoff="2020-06-03T02:00:00+08:00")
        self.assertEqual(fixture_record(self.fixture)["id"],fixture_record(other)["id"])
