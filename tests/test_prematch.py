import unittest
from sports_lottery.prematch import dossier
from sports_lottery.unified import compare, connect


class PrematchTests(unittest.TestCase):
    def setUp(self):
        self.at = "2026-09-04T10:00:00Z"
        self.fixture = dict(home="A", away="B", league="L", source_id="test",
                            source_url="https://example.org", kickoff="2026-09-05T00:00:00Z")
        self.e = dict(team="A", category="injuries", source_id="test", source_type="official",
                      source_url="https://example.org", summary="Test only", status="confirmed",
                      published_at="2026-09-04T08:00:00Z", observed_at="2026-09-04T09:00:00Z")

    def run_dossier(self, **changes):
        return dossier([], dict(self.fixture, prematch=[dict(self.e, **changes)]), self.at)

    def test_missing_is_unknown(self):
        r = dossier([], self.fixture, self.at)
        self.assertEqual(len(r["warnings"]), 10)
        self.assertEqual(r["teams"]["A"]["injuries"]["status"], "unknown")
        self.assertFalse(r["numeric_adjustment"])

    def test_wrong_team_match_and_future_rejected(self):
        for changes in (dict(team="C"), dict(source_id="other"),
                        dict(observed_at="2026-09-04T11:00:00Z")):
            with self.assertRaises(ValueError): self.run_dossier(**changes)

    def test_lineup_not_confused(self):
        self.run_dossier(category="lineup", details=dict(kind="expected", players=["P"]))
        with self.assertRaises(ValueError):
            self.run_dossier(category="lineup", details=dict(kind="announced", players=["P"]))
        self.run_dossier(category="lineup", details=dict(kind="announced", players=[str(i) for i in range(11)]))

    def test_rest_and_cup(self):
        r = self.run_dossier(category="rest", details=dict(previous_kickoff="2026-09-01T00:00:00Z"))
        self.assertEqual(r["teams"]["A"]["rest"]["records"][0]["kickoff_gap_hours"], 96)
        with self.assertRaises(ValueError):
            self.run_dossier(category="cup", details=dict(kind="league", first_leg_score=[1, 0]))

    def test_integrated_archive(self):
        import json
        db = connect(":memory:")
        try:
            r = compare(db, [], dict(self.fixture, prematch=[self.e]), self.at)
            saved = json.loads(db.execute("SELECT snapshot FROM comparisons").fetchone()[0])
            self.assertEqual(saved["prematch"], r["prematch"])
            self.assertEqual(r["prematch"]["teams"]["A"]["injuries"]["status"], "reported_requires_review")
        finally: db.close()
