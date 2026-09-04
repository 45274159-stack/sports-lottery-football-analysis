import unittest
from sports_lottery.season_form import season_form
from sports_lottery.prematch import dossier


class SeasonFormTests(unittest.TestCase):
    def setUp(self):
        self.r = dict(league="L", season="2627", date="2026-08-01", home_team="A", away_team="B",
                      ft_home_goals="2", ft_away_goals="0", ft_result="H")
    def test_venue_and_season_split(self):
        rows = [self.r, dict(self.r, date="2025-08-01", season="2526", home_team="B", away_team="A")]
        r = season_form(rows, "L", "A", "2026-09-04", "2627")
        self.assertEqual(r["current_season"]["overall"]["matches"], 1)
        self.assertEqual(r["historical"]["away"]["matches"], 1)
        self.assertEqual(r["current_season"]["home"]["points_per_game"], 3)
    def test_future_exclusion_and_same_day_batch(self):
        second = dict(self.r, home_team="C", away_team="A")
        rows = [self.r, second]
        a = season_form(rows, "L", "C", "2026-09-04", "2627")
        self.assertEqual(a["recent_matches"][0]["opponent_elo_before"], 1500)
        self.assertEqual(a, season_form(list(reversed(rows))+[dict(self.r,date="2026-09-04")], "L", "C", "2026-09-04", "2627"))
    def test_unknown_and_duplicates(self):
        r = season_form([self.r], "L", "A", "2026-09-04", "2728")
        self.assertEqual(r["season_status"], "missing")
        self.assertIsNone(r["current_season"]["overall"]["points_per_game"])
        with self.assertRaises(ValueError): season_form([self.r,self.r], "L", "A", "2026-09-04")
    def test_dossier_integration(self):
        f = dict(home="A",away="B",league="L",season="2627",kickoff="2026-09-05T00:00:00Z")
        r = dossier([self.r], f, "2026-09-04T10:00:00Z")
        self.assertEqual(r["teams"]["A"]["season_form"]["season_status"], "available")
