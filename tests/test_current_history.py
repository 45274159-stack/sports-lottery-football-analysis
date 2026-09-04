import json
import unittest
from pathlib import Path

from sports_lottery.history_quality import load_validated
from sports_lottery.history_catalog import load_all_history


ROOT = Path(__file__).resolve().parents[1]


class CurrentHistoryTests(unittest.TestCase):
    def test_current_and_gap_batches_validate(self):
        current, current_issues = load_validated(str(ROOT / "data/processed/current_season_2026_27"))
        gaps, gap_issues = load_validated(str(ROOT / "data/processed/completed_gaps_2025_26"))
        self.assertEqual(current_issues, [])
        self.assertEqual(gap_issues, [])
        self.assertEqual(len(current), 163)
        self.assertEqual(len(gaps), 22)
        self.assertTrue(all(row["date"] < "2026-09-04" for row in current))

    def test_completeness_report_matches_batches(self):
        report = json.loads((ROOT / "reports/history_completeness_20260904.json").read_text())
        self.assertEqual(report["new_current_season_matches"], 163)
        self.assertEqual(report["total_validated_rows"], 40842)
        self.assertEqual(report["validation_issues"], [])
        self.assertEqual(report["conflicts"], [])
        self.assertIn("not all world football", report["scope"])

    def test_unified_catalog_has_no_cross_batch_duplicates(self):
        rows = load_all_history()
        self.assertEqual(len(rows), 40842)
        self.assertEqual(len({(r["league"], r["date"], r["home_team"], r["away_team"]) for r in rows}), 40842)


if __name__ == "__main__":
    unittest.main()
