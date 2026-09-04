import unittest
from sports_lottery.team_names import normalize_team
from sports_lottery.history_quality import regulation_score, outcome, backtest


class HistoryQualityTests(unittest.TestCase):
    def test_aliases_and_unknown(self):
        self.assertEqual(normalize_team("尤尔加登"), normalize_team("佐加顿斯"))
        self.assertEqual(normalize_team("Unknown FC"), "Unknown FC")
    def test_shootout_is_not_regulation(self):
        self.assertEqual(regulation_score("4-2 pen. 1-0 a.e.t. (1-0, 1-0)"), (1, 0))

    def test_extra_time(self):
        self.assertEqual(regulation_score("4-2 a.e.t. (1-2, 0-0)"), (1, 2))

    def test_ambiguous_rejected(self):
        with self.assertRaises(ValueError):
            regulation_score("3-1 pen. 0-0 a.e.t. (0-0)")

    def test_numeric_result(self):
        self.assertEqual(outcome(10, 2), "H")

    def test_same_day_not_used(self):
        rows = [dict(date="2020-01-01", league="L", ft_result="H"),
                dict(date="2020-01-01", league="L", ft_result="A"),
                dict(date="2020-01-02", league="L", ft_result="D")]
        self.assertEqual(backtest(rows, 1)["L"]["evaluated"], 1)
        self.assertEqual(backtest(rows, 1), backtest(list(reversed(rows)), 1))


if __name__ == "__main__":
    unittest.main()
