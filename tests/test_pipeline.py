import unittest
from datetime import date, timedelta
from sports_lottery.pipeline import build_analysis
from sports_lottery.prediction_log import connect, save_prediction, save_result, review


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(league="L", date=(date(2019,1,1)+timedelta(days=i)).isoformat(),home_team="H",away_team="A",ft_home_goals="1",ft_away_goals="0",ft_result="H") for i in range(120)]
        self.request = dict(id="demo-only",match_id="synthetic",league="L",home="H",away="A",created_at="2020-01-01T10:00:00Z",kickoff="2020-01-02T10:00:00Z",fixture_source_url="https://example.org/synthetic",evidence=[])

    def test_full_record_review_cycle(self):
        item = build_analysis(self.rows, self.request)
        self.assertEqual(item["status"], "incomplete_inputs")
        self.assertEqual(len(item["missing"]),12)
        db = connect(":memory:")
        save_prediction(db,item)
        save_result(db,item["id"],dict(status="final",period="90_minutes",home_goals=1,away_goals=0,source_url="https://example.org/synthetic",observed_at="2020-01-02T15:00:00Z"))
        self.assertEqual(review(db)["settled"],1)
        db.close()

    def test_same_day_and_future_do_not_change_snapshot(self):
        a = build_analysis(self.rows,self.request)
        extra = dict(self.rows[0],date="2020-01-01",ft_home_goals="9")
        b = build_analysis(self.rows+[extra],self.request)
        self.assertEqual(a["input_snapshot_hash"],b["input_snapshot_hash"])

    def test_unknown_team_rejected(self):
        with self.assertRaises(ValueError):
            build_analysis(self.rows,dict(self.request,home="missing"))

    def test_future_evidence_rejected(self):
        e = dict(kind="injuries",match_id="synthetic",team="H",summary="test",status="confirmed",published_at="2020-01-01T11:00:00Z",observed_at="2020-01-01T12:00:00Z",source_url="https://example.org/synthetic")
        with self.assertRaises(ValueError):
            build_analysis(self.rows,dict(self.request,evidence=[e]))
