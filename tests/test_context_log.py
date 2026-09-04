import sqlite3
import unittest
from sports_lottery.match_context import team_context, validate_evidence
from sports_lottery.prediction_log import connect, save_prediction, save_result, review
from sports_lottery.calibration import reliability


class ContextLogTests(unittest.TestCase):
    def test_context_past_only_alias(self):
        row = dict(date="2020-01-01", league="L", home_team="West Brom", away_team="Other", ft_home_goals="2", ft_away_goals="1")
        result = team_context([row, dict(row, date="2020-01-10")], "西布罗姆", "2020-01-10")
        self.assertEqual(result["last5"]["matches"], 1)
        self.assertEqual(result["days_since_last"], 9)
        self.assertIsNone(result["injuries"])

    def test_unknown_form(self):
        self.assertIsNone(team_context([], "X", "2020-01-01")["last5"]["points_per_game"])

    def test_evidence_time(self):
        item = dict(published_at="2020-01-01T10:00:00Z", observed_at="2020-01-01T11:00:00Z", source_url="https://example.org/report", status="unknown")
        self.assertEqual(validate_evidence(item, "2020-01-01T12:00:00Z", "2020-01-01T13:00:00Z")["status"], "unknown")
        with self.assertRaises(ValueError):
            validate_evidence(item, "2020-01-01T10:30:00Z", "2020-01-01T13:00:00Z")

    def test_log_immutable_and_results_separate(self):
        db = connect(":memory:")
        item = dict(id="p1", match_id="m1", model_version="test", input_snapshot_hash="testhash", source_urls=["https://example.org"], created_at="2020-01-01T10:00:00Z", kickoff="2020-01-01T13:00:00Z", probabilities=dict(H=.6,D=.2,A=.2))
        save_prediction(db, item)
        with self.assertRaises(sqlite3.IntegrityError):
            save_prediction(db, item)
        save_result(db, "p1", dict(status="final",period="90_minutes",home_goals=1,away_goals=0,source_url="https://example.org/result",observed_at="2020-01-01T16:00:00Z"))
        self.assertEqual(review(db)["accuracy"], 1)
        self.assertIsNone(review(db)["roi"])
        db.close()

    def test_calibration(self):
        result = reliability([dict(probability=.5,outcome=1),dict(probability=.5,outcome=0)])
        self.assertEqual(result["expected_calibration_error"], 0)
        self.assertIsNone(reliability([])["expected_calibration_error"])
