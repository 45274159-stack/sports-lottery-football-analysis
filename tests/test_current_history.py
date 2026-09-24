import json
import importlib.util
import inspect
import tempfile
import unittest
from pathlib import Path

from sports_lottery.history_quality import load_validated
from sports_lottery.history_catalog import load_all_history


ROOT = Path(__file__).resolve().parents[1]


class CurrentHistoryTests(unittest.TestCase):
    def test_daily_import_refuses_to_overwrite_different_content(self):
        script_path = ROOT / "scripts/import_results_20260923.py"
        spec = importlib.util.spec_from_file_location("import_results_20260923", script_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "write_checked"))
        self.assertIn("conflict_report", inspect.signature(module.write_checked).parameters)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            conflict_report = Path(directory) / "pending.json"
            module.write_checked(path, '{"score":"2:0"}\n')
            module.write_checked(path, '{"score":"2:0"}\n')
            with self.assertRaisesRegex(RuntimeError, "refusing to overwrite"):
                module.write_checked(path, '{"score":"3:0"}\n', conflict_report=conflict_report)
            self.assertEqual(path.read_text(), '{"score":"2:0"}\n')
            conflicts = json.loads(conflict_report.read_text())["conflicts"]
            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0]["target"], str(path))
            self.assertNotEqual(conflicts[0]["existing_sha256"], conflicts[0]["proposed_sha256"])

    def test_current_and_gap_batches_validate(self):
        current, current_issues = load_validated(str(ROOT / "data/processed/current_season_2026_27"))
        gaps, gap_issues = load_validated(str(ROOT / "data/processed/completed_gaps_2025_26"))
        self.assertEqual(current_issues, [])
        self.assertEqual(gap_issues, [])
        self.assertEqual(len(current), 474)
        self.assertEqual(len(gaps), 22)
        self.assertTrue(all(row["date"] <= "2026-09-23" for row in current))

    def test_completeness_report_matches_batches(self):
        report = json.loads((ROOT / "reports/history_completeness_20260904.json").read_text())
        self.assertEqual(report["new_current_season_matches"], 163)
        self.assertEqual(report["total_validated_rows"], 40842)
        self.assertEqual(report["validation_issues"], [])
        self.assertEqual(report["conflicts"], [])
        self.assertIn("not all world football", report["scope"])

    def test_unified_catalog_has_no_cross_batch_duplicates(self):
        rows = load_all_history()
        self.assertEqual(len(rows), 41153)
        self.assertEqual(len({(r["league"], r["date"], r["home_team"], r["away_team"]) for r in rows}), 41153)

    def test_latest_sourced_result_batches(self):
        friday = json.loads((ROOT / "data/processed/results/2026-09-04.json").read_text())
        saturday = json.loads((ROOT / "data/processed/results/2026-09-05.json").read_text())
        self.assertEqual(len(friday["records"]), 14)
        self.assertEqual(len(saturday["records"]), 29)
        self.assertTrue(all(row["status"] == "final" for row in friday["records"]))
        self.assertTrue(all(row["status"] == "final" for row in saturday["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in friday["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in saturday["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in saturday["records"]))
        sunday = json.loads((ROOT / "data/processed/results/2026-09-06.json").read_text())
        self.assertEqual(len(sunday["records"]), 24)
        self.assertTrue(all(row["status"] == "final" for row in sunday["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in sunday["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in sunday["records"]))
        monday = json.loads((ROOT / "data/processed/results/2026-09-07.json").read_text())
        self.assertEqual(len(monday["records"]), 9)
        self.assertTrue(all(row["status"] == "final" for row in monday["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in monday["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in monday["records"]))
        tuesday = json.loads((ROOT / "data/processed/results/2026-09-08.json").read_text())
        self.assertEqual(len(tuesday["records"]), 12)
        self.assertTrue(all(row["status"] == "final" for row in tuesday["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in tuesday["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in tuesday["records"]))
        wednesday = json.loads((ROOT / "data/processed/results/2026-09-09.json").read_text())
        self.assertEqual(len(wednesday["records"]), 15)
        self.assertTrue(all(row["status"] == "final" for row in wednesday["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in wednesday["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in wednesday["records"]))
        thursday = json.loads((ROOT / "data/processed/results/2026-09-10.json").read_text())
        self.assertEqual(len(thursday["records"]), 7)
        self.assertTrue(all(row["status"] == "final" for row in thursday["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in thursday["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in thursday["records"]))
        friday_latest = json.loads((ROOT / "data/processed/results/2026-09-11.json").read_text())
        self.assertEqual(len(friday_latest["records"]), 12)
        self.assertTrue(all(row["status"] == "final" for row in friday_latest["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in friday_latest["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in friday_latest["records"]))
        saturday_latest = json.loads((ROOT / "data/processed/results/2026-09-12.json").read_text())
        self.assertEqual(len(saturday_latest["records"]), 30)
        self.assertTrue(all(row["status"] == "final" for row in saturday_latest["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in saturday_latest["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in saturday_latest["records"]))
        sunday_latest = json.loads((ROOT / "data/processed/results/2026-09-13.json").read_text())
        self.assertEqual(len(sunday_latest["records"]), 24)
        self.assertTrue(all(row["status"] == "final" for row in sunday_latest["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in sunday_latest["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in sunday_latest["records"]))
        monday_latest = json.loads((ROOT / "data/processed/results/2026-09-14.json").read_text())
        self.assertEqual(len(monday_latest["records"]), 12)
        self.assertEqual(
            [row["display_number"] for row in monday_latest["records"]],
            [f"周一{number:03d}" for number in range(2, 13)] + ["周一014"],
        )
        self.assertTrue(all(row["status"] == "final" for row in monday_latest["records"]))
        self.assertTrue(all(row["result"] in "HDA" for row in monday_latest["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in monday_latest["records"]))
        self.assertTrue(all(row["extra_time"] is None for row in monday_latest["records"]))
        self.assertTrue(all(row["penalties"] is None for row in monday_latest["records"]))
        expected = {
            "2026-09-15": 14,
            "2026-09-16": 16,
            "2026-09-17": 11,
            "2026-09-18": 14,
            "2026-09-19": 30,
        }
        for lottery_date, count in expected.items():
            batch = json.loads((ROOT / f"data/processed/results/{lottery_date}.json").read_text())
            self.assertEqual(len(batch["records"]), count)
            self.assertTrue(all(row["status"] == "final" for row in batch["records"]))
            self.assertTrue(all(row["score_period"] == "90_minutes" for row in batch["records"]))
            self.assertTrue(all(row["extra_time"] is None for row in batch["records"]))
            self.assertTrue(all(row["penalties"] is None for row in batch["records"]))
            self.assertTrue(all(row["half_home_goals"] is not None for row in batch["records"]))
        latest = json.loads((ROOT / "data/processed/results/2026-09-20.json").read_text())
        self.assertEqual([row["display_number"] for row in latest["records"]], [f"周日{i:03d}" for i in range(1, 31)])
        self.assertTrue(all(row["status"] == "final" for row in latest["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in latest["records"]))
        self.assertTrue(all(row["extra_time"] is None for row in latest["records"]))
        self.assertTrue(all(row["penalties"] is None for row in latest["records"]))
        self.assertTrue(all(row["half_home_goals"] is not None for row in latest["records"]))
        latest_monday_path = ROOT / "data/processed/results/2026-09-21.json"
        self.assertTrue(latest_monday_path.exists())
        latest_monday = json.loads(latest_monday_path.read_text())
        self.assertEqual([row["display_number"] for row in latest_monday["records"]], ["周一001"])
        self.assertEqual(latest_monday["records"][0]["kickoff_beijing"], "2026-09-21T15:00:00+08:00")
        self.assertEqual(latest_monday["records"][0]["result"], "H")
        self.assertEqual(latest_monday["records"][0]["score_period"], "90_minutes")
        self.assertIsNone(latest_monday["records"][0]["extra_time"])
        self.assertIsNone(latest_monday["records"][0]["penalties"])
        latest_tuesday_path = ROOT / "data/processed/results/2026-09-22.json"
        self.assertTrue(latest_tuesday_path.exists())
        latest_tuesday = json.loads(latest_tuesday_path.read_text())
        self.assertEqual(
            [row["display_number"] for row in latest_tuesday["records"]],
            [f"周二{i:03d}" for i in range(1, 5)],
        )
        self.assertTrue(all(row["status"] == "final" for row in latest_tuesday["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in latest_tuesday["records"]))
        self.assertTrue(all(row["extra_time"] is None for row in latest_tuesday["records"]))
        self.assertTrue(all(row["penalties"] is None for row in latest_tuesday["records"]))
        self.assertTrue(all(row["half_home_goals"] is not None for row in latest_tuesday["records"]))
        latest_wednesday_path = ROOT / "data/processed/results/2026-09-23.json"
        self.assertTrue(latest_wednesday_path.exists())
        latest_wednesday = json.loads(latest_wednesday_path.read_text())
        self.assertEqual(
            [row["display_number"] for row in latest_wednesday["records"]],
            [f"周三{i:03d}" for i in range(1, 4)],
        )
        self.assertTrue(all(row["status"] == "final" for row in latest_wednesday["records"]))
        self.assertTrue(all(row["score_period"] == "90_minutes" for row in latest_wednesday["records"]))
        self.assertTrue(all(row["extra_time"] is None for row in latest_wednesday["records"]))
        self.assertTrue(all(row["penalties"] is None for row in latest_wednesday["records"]))
        self.assertTrue(all(row["half_home_goals"] is not None for row in latest_wednesday["records"]))
        pending = json.loads((ROOT / "reports/pending_results_20260924.json").read_text())
        self.assertEqual([row["display_number"] for row in pending["remaining_pending"]], ["周三014"])
        self.assertEqual(pending["remaining_pending"][0]["status"], "postponed_weather")
        update = json.loads((ROOT / "reports/current_season_update_20260924.json").read_text())
        self.assertEqual(update["unified_catalog_rows"], len(load_all_history()))


if __name__ == "__main__":
    unittest.main()
