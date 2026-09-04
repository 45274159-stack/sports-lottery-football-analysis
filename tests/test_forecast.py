import unittest
from sports_lottery.forecast import markets, ForecastModel


class ForecastTests(unittest.TestCase):
    def test_probability_mass(self):
        for h,a in [(1.5, 1.), (6.,6.), (.15,.15)]:
            p = markets(h,a)
            self.assertAlmostEqual(sum(p["result"].values()), 1.)
            self.assertAlmostEqual(sum(p["total_goals"].values()), 1.)
            self.assertLess(p["omitted_mass"], 1e-12)

    def test_symmetry(self):
        p = markets(1.2,1.2)
        self.assertAlmostEqual(p["result"]["H"], p["result"]["A"])

    def test_invalid_rates(self):
        for x in [0, -1, float("nan"), 7]:
            with self.assertRaises(ValueError):
                markets(x, 1)

    def test_future_history_excluded(self):
        model = ForecastModel()
        for _ in range(100):
            model.observe(dict(league="L",date="2020-01-01",home_team="H",away_team="A",ft_home_goals="1",ft_away_goals="0"))
        before = model.predict("L","H","A","2020-02-01")
        model.observe(dict(league="L",date="2020-03-01",home_team="H",away_team="A",ft_home_goals="9",ft_away_goals="9"))
        self.assertEqual(before, model.predict("L","H","A","2020-02-01"))

    def test_insufficient_history(self):
        with self.assertRaises(ValueError):
            ForecastModel().predict("L","H","A","2020-01-01")
