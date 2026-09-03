from pathlib import Path
import tempfile
import unittest

from sports_lottery.analysis import estimate_match
from sports_lottery.database import connect, import_rows
from sports_lottery.review import load_history
from sports_lottery.schema import validate_csv


HEADER = "match_id,lottery_date,match_no,competition,kickoff_time,home_team,away_team,home_score,away_score,handicap,spf_home_odds,spf_draw_odds,spf_away_odds,rqspf_home_odds,rqspf_draw_odds,rqspf_away_odds,source_url,collected_at\n"


class CoreTests(unittest.TestCase):
    def test_optional_columns_may_be_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "minimal.csv"
            csv_path.write_text(
                "match_id,lottery_date,match_no,competition,kickoff_time,home_team,away_team,home_score,away_score\n"
                "minimal-1,2026-01-01,周四001,测试联赛,2026-01-01T20:00:00+08:00,甲队,乙队,,\n",
                encoding="utf-8",
            )
            rows, issues = validate_csv(csv_path)
            self.assertFalse(issues)
            database = connect(Path(directory) / "test.sqlite3")
            self.assertEqual(import_rows(database, rows), 1)

    def test_validate_and_import(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "matches.csv"
            csv_path.write_text(
                HEADER
                + "20260101-001,2026-01-01,周四001,测试联赛,2026-01-01T20:00:00+08:00,甲队,乙队,2,0,0,1.80,3.20,4.00,,,,https://example.com,2026-01-01T19:00:00+08:00\n",
                encoding="utf-8",
            )
            rows, issues = validate_csv(csv_path)
            self.assertFalse(issues)
            database = connect(Path(directory) / "test.sqlite3")
            self.assertEqual(import_rows(database, rows), 1)
            self.assertEqual(database.execute("SELECT COUNT(*) FROM matches").fetchone()[0], 1)

    def test_estimate_uses_only_prior_matches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "matches.csv"
            csv_path.write_text(
                HEADER
                + "1,2026-01-01,周四001,测试联赛,2026-01-01T20:00:00+08:00,甲队,乙队,2,0,0,,,,,,,,\n"
                + "2,2026-01-02,周五001,测试联赛,2026-01-02T20:00:00+08:00,丙队,丁队,1,1,0,,,,,,,,\n",
                encoding="utf-8",
            )
            rows, issues = validate_csv(csv_path)
            self.assertFalse(issues)
            database = connect(Path(directory) / "test.sqlite3")
            import_rows(database, rows)
            estimate = estimate_match(database, "甲队", "丁队", "2026-01-03T20:00:00+08:00")
            self.assertTrue(0 < estimate.home_win < 1)
            self.assertAlmostEqual(estimate.home_win + estimate.draw + estimate.away_win, 1)
            self.assertEqual(len(estimate.top_scores), 5)

    def test_history_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            path.write_text(
                "league,ft_home_goals,ft_away_goals,ft_result\n"
                "英超,2,1,H\n"
                "英超,1,1,D\n"
                "西甲,0,1,A\n",
                encoding="utf-8",
            )
            total, leagues = load_history(directory)
            self.assertEqual(total.matches, 3)
            self.assertEqual(total.goals, 6)
            self.assertEqual(total.over_2_5, 1)
            self.assertEqual(leagues["英超"].both_score, 2)


if __name__ == "__main__":
    unittest.main()
