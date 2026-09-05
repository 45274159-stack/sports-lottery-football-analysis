import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from sports_lottery.prematch_source import (
    collect_match_list,
    collect_prematch,
    parse_fixed_bonus,
    parse_injuries,
    save_prematch_snapshot,
)


LIST = {"value": {"matchInfoList": [{"subMatchList": [{
    "matchId": 42, "matchDate": "2026-09-04", "matchTime": "20:00",
    "matchNumStr": "周五001", "leagueAbbName": "测试联赛",
    "homeTeamAbbName": "主队", "awayTeamAbbName": "客队",
}]}]}}


class PrematchSourceTests(unittest.TestCase):
    def test_fixed_bonus_preserves_every_timestamp_and_market(self):
        parsed = parse_fixed_bonus({"value": {"oddsHistory": {
            "hadList": [
                {"updateDate": "2026-09-04", "updateTime": "09:00", "h": "1.80", "d": "3.10", "a": "4.00"},
                {"updateDate": "2026-09-04", "updateTime": "18:00", "h": "1.72", "d": "3.20", "a": "4.20"},
            ],
            "hhadList": [{"goalLine": "-1", "h": "3.10", "d": "3.45", "a": "1.92"}],
            "ttgList": [{"s0": "9.00", "s1": "4.20", "s2": "3.10"}],
            "crsList": [{"s1s0": "6.50", "s2s0": "7.20", "winOther": "20.00"}],
            "hafuList": [{"hh": "2.40", "hd": "14.00", "aa": "8.00"}],
        }}})
        self.assertEqual(parsed["status"], "available")
        self.assertEqual(len(parsed["markets"]["had"]), 2)
        self.assertEqual(parsed["markets"]["had"][1]["h"], "1.72")
        self.assertEqual(parsed["markets"]["hhad"][0]["goalLine"], "-1")
        self.assertEqual(parsed["markets"]["crs"][0]["s1s0"], "6.50")

    def test_injury_empty_is_not_translated_to_healthy(self):
        checked = parse_injuries({"value": {"homeList": [], "awayList": []}})
        missing = parse_injuries({"value": None})
        self.assertEqual(checked["empty_means"], "provider_returned_no_listed_absence")
        self.assertEqual(missing["status"], "unavailable")

    def test_list_deduplicates_all_and_concern_and_stops_repeated_page(self):
        calls = []
        def request(url):
            calls.append(url)
            page = parse_qs(urlparse(url).query)["pageNo"][0]
            return LIST if page in {"1", "2"} else {"value": {"matchInfoList": []}}
        rows = collect_match_list(date(2026, 9, 4), request=request)
        self.assertEqual([row["matchId"] for row in rows], [42])
        self.assertEqual(len(calls), 4)

    def test_full_snapshot_never_promotes_player_data_to_lineup(self):
        def request(url):
            if "getMatchDataPageList" in url:
                page = parse_qs(urlparse(url).query)["pageNo"][0]
                return LIST if page == "1" else {"value": {"matchInfoList": []}}
            if "getFixedBonus" in url:
                return {"value": {"oddsHistory": {"hadList": [{"h": "1.80", "d": "3.20", "a": "4.00"}]}}}
            if "getInjurySuspension" in url:
                return {"value": {"homeList": [{"playerName": "甲", "reason": "腿伤"}], "awayList": []}}
            return {"value": {}}
        snapshot = collect_prematch(date(2026, 9, 4), request=request, delay=0)
        self.assertEqual(snapshot["fixture_count"], 1)
        fixture = snapshot["fixtures"][0]
        self.assertEqual(fixture["availability"]["home"][0]["player"], "甲")
        self.assertEqual(fixture["lineups"]["status"], "unavailable")
        self.assertEqual(fixture["lineups"]["announced"]["home"], [])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "snapshot.json"
            save_prematch_snapshot(output, snapshot)
            self.assertEqual(json.loads(output.read_text())["fixture_count"], 1)
            self.assertFalse(output.with_suffix(".json.tmp").exists())
            with self.assertRaises(FileExistsError):
                save_prematch_snapshot(output, snapshot)


if __name__ == "__main__":
    unittest.main()
