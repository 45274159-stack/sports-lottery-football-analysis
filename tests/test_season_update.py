import tempfile
import unittest
from pathlib import Path
from sports_lottery.season_update import convert, build
from sports_lottery.history_quality import load_validated

HEADER = "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
SAMPLE = HEADER + "2026-08-20,Test Home,Test Away,2,1,H\n"


class SeasonUpdateTests(unittest.TestCase):
    def test_reject_invalid_and_future(self):
        for text in (HEADER, SAMPLE + SAMPLE.splitlines()[1], SAMPLE.replace(",H", ",A"),
                     SAMPLE.replace("2026-08-20", "2026-09-05")):
            with self.assertRaises(ValueError):
                convert(text, "premier-league", "2627", "2026-09-04")

    def test_merge_idempotency_and_conflict(self):
        rows = convert(SAMPLE, "premier-league", "2627", "2026-09-04")
        with tempfile.TemporaryDirectory() as tmp:
            history = Path(tmp) / "history"
            history.mkdir()
            import csv
            with (history / "old.csv").open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader(); w.writerows(rows)
            output = Path(tmp) / "snapshot"
            result = build(history, rows, output, "https://example.org/test", "2026-09-04")
            self.assertEqual(result["new_rows"], 0)
            self.assertEqual(load_validated(output)[1], [])
            with self.assertRaises(FileExistsError):
                build(history, rows, output, "https://example.org/test", "2026-09-04")
            with self.assertRaises(ValueError):
                build(history, [dict(rows[0], ft_home_goals="3")], Path(tmp)/"conflict",
                      "https://example.org/test", "2026-09-04")
