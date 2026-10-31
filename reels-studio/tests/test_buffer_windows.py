"""Buffer posting windows: parsing, freshness, and the best-times fallback that uses them. No network."""
import datetime as dt
import unittest
import zoneinfo
from pathlib import Path

from tools.post import best_times as bt
from tools.post import buffer_windows as bw

ROOT = Path(__file__).resolve().parents[1]
NY = zoneinfo.ZoneInfo("America/New_York")
NOW = dt.datetime(2026, 10, 31, 12, 0, tzinfo=dt.timezone.utc)
CFG = {"schedule": {"minimum_gap_minutes": 5, "best_times": {"min_samples_per_hour": 3, "fallback_window": ["18:00", "21:00"]},
                    "profiles": {}}}


def channel(service, slots, disconnected=False):
    return {"id": f"{service}-id", "name": service, "service": service, "timezone": "America/New_York",
            "isDisconnected": disconnected, "postingSchedule": slots}


SLOTS = [
    {"day": "monday", "paused": False, "times": ["09:00", "18:30"]},
    {"day": "tuesday", "paused": False, "times": ["09:00", "19:00"]},
    {"day": "wednesday", "paused": True, "times": ["23:00"]},
    {"day": "sunday", "paused": False, "times": ["bad", "07:15"]},
]


class Build(unittest.TestCase):
    def test_ranks_slots_by_use_and_skips_paused_days(self):
        report = bw.build([channel("youtube", SLOTS)], NOW)
        yt = report["platforms"]["youtube"]
        self.assertEqual(yt["clocks_by_use"][0], "09:00")          # used on two days
        self.assertNotIn("23:00", yt["clocks_by_use"])             # paused day does not count
        self.assertTrue(any("bad" in p for p in yt["problems"]))   # malformed time is reported, not used
        self.assertIn("07:15", yt["clocks_by_use"])

    def test_only_youtube_instagram_facebook_and_connected(self):
        report = bw.build([channel("tiktok", SLOTS), channel("facebook", SLOTS, disconnected=True),
                           channel("instagram", SLOTS)], NOW)
        self.assertEqual(sorted(report["platforms"]), ["instagram"])
        self.assertTrue(report["skipped"])

    def test_read_only_query_has_no_mutation(self):
        self.assertNotIn("mutation", bw.WINDOWS_QUERY.lower())
        self.assertIn("postingSchedule", bw.WINDOWS_QUERY)


class Freshness(unittest.TestCase):
    def test_missing_snapshot_is_not_fresh(self):
        self.assertFalse(bw.is_fresh(None, NOW)[0])

    def test_eight_day_limit(self):
        recent = {"fetched_at": "2026-10-27T12:00:00Z"}
        old = {"fetched_at": "2026-10-20T12:00:00Z"}
        self.assertTrue(bw.is_fresh(recent, NOW)[0])
        ok, why = bw.is_fresh(old, NOW)
        self.assertFalse(ok)
        self.assertIn("days old", why)


class FetchWithFakeClient(unittest.TestCase):
    def test_fetch_uses_the_org_and_returns_channels(self):
        class Fake:
            def request(self, query, variables=None, mutation=False):
                assert not mutation and variables == {"org": "org-1"}
                return {"channels": [channel("youtube", SLOTS)]}
        out = bw.fetch({"organization_id": "org-1"}, client=Fake())
        self.assertEqual(out[0]["service"], "youtube")


class BestTimesFallback(unittest.TestCase):
    def test_fresh_buffer_windows_replace_the_researched_window(self):
        report = bw.build([channel("youtube", SLOTS)], NOW)
        clocks, prov = bt.ranked_clocks({}, "youtube", {"timezone": "America/New_York"}, CFG, 2, NY,
                                        windows_report=report, now=NOW)
        self.assertEqual(clocks, ["09:00", "07:15"])  # most used first, ties by earlier time
        self.assertEqual(prov["fallback_source"], "buffer-windows")

    def test_stale_windows_fall_back_and_say_why(self):
        report = bw.build([channel("youtube", SLOTS)], NOW)
        report["fetched_at"] = "2026-10-01T00:00:00Z"
        clocks, prov = bt.ranked_clocks({}, "youtube", {"timezone": "America/New_York"}, CFG, 2, NY,
                                        windows_report=report, now=NOW)
        self.assertEqual(clocks, ["18:00", "18:30"])
        self.assertEqual(prov["fallback_source"], "researched-window")
        self.assertIn("days old", prov["fallback_note"])

    def test_no_snapshot_keeps_the_researched_window(self):
        clocks, prov = bt.ranked_clocks({}, "instagram", {"timezone": "America/New_York"}, CFG, 2, NY, now=NOW)
        self.assertEqual(clocks, ["18:00", "18:30"])
        self.assertEqual(prov["fallback_source"], "researched-window")



class WeeklyWorkflow(unittest.TestCase):
    """The refresh is only real if the schedule exists. These checks fail if someone removes it."""

    def test_weekly_schedule_and_read_only_script(self):
        import yaml
        path = ROOT.parent / ".github" / "workflows" / "buffer-windows.yml"
        wf = yaml.safe_load(path.read_text(encoding="utf-8"))
        crons = [s["cron"] for s in wf[True]["schedule"]] if True in wf else [s["cron"] for s in wf["on"]["schedule"]]
        self.assertIn("0 4 * * 1", crons)  # Mondays 04:00 UTC
        text = path.read_text(encoding="utf-8")
        self.assertIn("tools/post/buffer_windows.py", text)
        self.assertNotIn("post.yml", text)
        self.assertIn("BUFFER_API_KEY", text)


if __name__ == "__main__":
    unittest.main()
