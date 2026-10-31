"""Owner rules 2026-10-21: random 1–5 shorts/day; per-channel best times; k-th short → k-th best slot."""
import datetime as dt
import json
import random
import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

from tools.post import best_times as bt

NY = ZoneInfo("America/New_York")
CFG = json.loads((Path(__file__).resolve().parents[1] / "config" / "publishing.json").read_text())


def _post(platform, hour, views, day=10):
    stamp = dt.datetime(2026, 10, day, hour, 0, tzinfo=NY).astimezone(dt.timezone.utc)
    metric_type = bt.METRIC_TYPE[platform]
    return {"platform": platform, "metrics_status": "fresh", "sent_at": stamp.isoformat().replace("+00:00", "Z"),
            "metrics": [{"type": metric_type, "value": views}]}


class DailyCountTests(unittest.TestCase):
    def test_draw_is_between_one_and_five(self):
        with tempfile.TemporaryDirectory() as tmp:
            for n in range(20):
                count = bt.daily_count(dt.date(2026, 11, 1) + dt.timedelta(days=n), Path(tmp) / "c.json", random.Random(n))
                self.assertIn(count, range(1, 6))

    def test_draw_once_per_day_never_redrawn(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            first = bt.daily_count(dt.date(2026, 11, 2), path, random.Random(1))
            for seed in range(2, 12):  # different RNG seeds must not change the stored count
                self.assertEqual(bt.daily_count(dt.date(2026, 11, 2), path, random.Random(seed)), first)
            self.assertEqual(len(json.loads(path.read_text())["days"]), 1)


class BestTimeTests(unittest.TestCase):
    def setUp(self):
        self.insights = {}
        # YouTube: 13:00 is best, then 17:00, then 09:00 (3 posts each -> reliable).
        for i, (hour, views) in enumerate([(13, 900), (13, 800), (13, 700),
                                           (17, 500), (17, 450), (17, 400),
                                           (9, 300), (9, 200), (9, 100), (20, 50)]):
            self.insights[f"yt{i}"] = _post("youtube", hour, views)
        # Only two posts at 20:00 — below min_samples, so it is never ranked from data.

    def test_best_slot_comes_first(self):
        clocks, prov = bt.ranked_clocks(self.insights, "youtube", CFG["schedule"]["profiles"]["youtube"],
                                        CFG, 3, NY)
        self.assertEqual(clocks, ["13:00", "17:00", "09:00"])
        self.assertNotIn("20:00", prov["ranked_hours"])

    def test_ranked_slots_never_repeat_and_keep_gap(self):
        for channel in ("youtube", "instagram", "facebook"):
            profile = CFG["schedule"]["profiles"][channel]
            for want in range(1, 6):
                clocks, _ = bt.ranked_clocks(self.insights, channel, profile, CFG, want, NY)
                self.assertLessEqual(len(clocks), want)
                self.assertEqual(len(set(clocks)), len(clocks), f"{channel} repeated a time")
                mins = sorted(int(c[:2]) * 60 + int(c[3:]) for c in clocks)
                gaps = [b - a for a, b in zip(mins, mins[1:])]
                self.assertTrue(all(g >= CFG["schedule"]["minimum_gap_minutes"] for g in gaps), f"{channel} {clocks}")

    def test_no_data_uses_six_to_nine_pm_window(self):
        clocks, prov = bt.ranked_clocks({}, "instagram", CFG["schedule"]["profiles"]["instagram"], CFG, 2, NY)
        # 150-minute gap removed 30 Oct; the configured gap is 5 minutes, so 30-minute steps all fit
        self.assertEqual(clocks, ["18:00", "18:30"])
        self.assertEqual(prov["fallback_window"], ["18:00", "21:00"])
        for c in clocks:
            self.assertTrue("18:00" <= c <= "21:00")

    def test_window_cannot_exceed_gap_so_extra_shorts_wait(self):
        # 150-minute gap fits only two slots in 18:00–21:00; the rest is not forced into other hours.
        clocks, _ = bt.ranked_clocks({}, "facebook", CFG["schedule"]["profiles"]["facebook"], CFG, 5, NY)
        self.assertEqual(clocks, ["18:00", "18:30", "19:00", "19:30", "20:00"])

    def test_channels_rank_independently(self):
        for i, (hour, views) in enumerate([(7, 900), (7, 900), (7, 900)]):
            self.insights[f"ig{i}"] = {"platform": "instagram", "metrics_status": "fresh",
                                       "sent_at": _post("instagram", hour, views)["sent_at"],
                                       "metrics": [{"type": "views", "value": views}]}
        ig, _ = bt.ranked_clocks(self.insights, "instagram", CFG["schedule"]["profiles"]["instagram"], CFG, 1, NY)
        yt, _ = bt.ranked_clocks(self.insights, "youtube", CFG["schedule"]["profiles"]["youtube"], CFG, 1, NY)
        self.assertEqual(ig, ["07:00"])
        self.assertEqual(yt, ["13:00"])


if __name__ == "__main__":
    unittest.main()


class PlannerRuleTests(unittest.TestCase):
    def test_rules_enabled_in_live_config(self):
        rules = CFG["schedule"]["best_times"]
        self.assertTrue(rules["enabled"])
        self.assertEqual((rules["daily_count_min"], rules["daily_count_max"]), (1, 5))
        self.assertEqual(rules["min_samples_per_hour"], 3)

    def test_count_cap_is_five_even_with_override(self):
        # A dated override of 10 must not exceed the owner's 1–5 daily rule.
        with tempfile.TemporaryDirectory() as tmp:
            n = bt.daily_count(dt.date(2026, 12, 1), Path(tmp) / "c.json", random.Random(7))
        self.assertLessEqual(n, 5)


class CiNoDrawTests(unittest.TestCase):
    def test_ci_never_draws_an_unrecorded_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            self.assertIsNone(bt.daily_count(dt.date(2026, 11, 9), path, allow_draw=False))
            self.assertFalse(path.exists())  # nothing written on a throwaway runner
