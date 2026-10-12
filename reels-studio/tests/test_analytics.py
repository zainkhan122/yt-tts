"""Analytics lane: 24 h / 7 d snapshots, own-history baselines, honest unavailability."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.post.state import Journal
from tools.youtube import analytics
from tools.youtube.api import ANALYTICS_REPORTS, YouTubeAPI, YouTubeError, validate_analytics_url

NOW = dt.datetime(2026, 10, 12, 12, 0, tzinfo=dt.timezone.utc)


def iso(delta_hours):
    return (NOW - dt.timedelta(hours=delta_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeAPI:
    """Data API stats + Analytics API rows, keyed by youtube id."""

    def __init__(self, stats=None, rows=None, analytics_error=None):
        self.stats, self.rows, self.analytics_error = stats or {}, rows, analytics_error
        self.calls = []

    def json(self, method, resource, params=None, cost=1):
        self.calls.append((method, resource, dict(params or {})))
        if resource == ANALYTICS_REPORTS:
            if self.analytics_error:
                raise self.analytics_error
            return {"rows": self.rows or []}
        ids = params["id"].split(",")
        return {"items": [{"id": i, "snippet": {"publishedAt": self.stats[i]["published_at"]},
                           "statistics": {"viewCount": str(self.stats[i]["views"]), "likeCount": str(self.stats[i]["likes"]),
                                          "commentCount": str(self.stats[i]["comments"])}} for i in ids if i in self.stats]}


def records():
    return {
        "news-a-01:youtube": {"video_id": "news-a-01", "platform": "youtube", "state": "sent",
                              "external_url": "https://www.youtube.com/watch?v=AAAAAAAAAAA"},
        "news-b-01:youtube": {"video_id": "news-b-01", "platform": "youtube", "state": "published_manual",
                              "external_url": "https://youtu.be/BBBBBBBBBBB"},
        "news-c-01:youtube": {"video_id": "news-c-01", "platform": "youtube", "state": "scheduled", "external_url": None},
    }


STATS = {"AAAAAAAAAAA": {"published_at": iso(30), "views": 1000, "likes": 80, "comments": 20},
         "BBBBBBBBBBB": {"published_at": iso(200), "views": 4000, "likes": 300, "comments": 100}}


class TargetingTests(unittest.TestCase):
    def test_targets_only_readable_sent_rows_with_ids(self):
        self.assertEqual(analytics.targets(records()), {"news-a-01": "AAAAAAAAAAA", "news-b-01": "BBBBBBBBBBB"})

    def test_due_windows_respect_age_and_already_taken(self):
        self.assertEqual(analytics.due_windows({"snapshots": []}, 30), ["24h"])
        self.assertEqual(analytics.due_windows({"snapshots": []}, 200), ["24h", "7d"])
        taken = {"snapshots": [{"window": "24h"}]}
        self.assertEqual(analytics.due_windows(taken, 200), ["7d"])
        self.assertEqual(analytics.due_windows({"snapshots": []}, 5), [])


class SnapshotTests(unittest.TestCase):
    def test_snapshot_is_idempotent_and_missing_analytics_is_explicit(self):
        store, recs = analytics.empty_store(), records()
        api = FakeAPI(stats=STATS, analytics_error=YouTubeError("YouTube HTTP 403: insufficient scope", "HTTP_403"))
        changed = analytics.snapshot(api, recs, store, NOW)
        self.assertIn("news-a-01@24h", changed)
        self.assertIn("news-b-01@24h", changed)
        self.assertIn("news-b-01@7d", changed)
        a24 = store["videos"]["news-a-01"]["snapshots"][0]
        self.assertEqual(a24["views"], 1000)
        self.assertEqual(a24["engagement_rate"], 0.1)
        self.assertIn("unavailable", a24["analytics"])
        self.assertIn("403", a24["analytics"]["unavailable"])
        # second run: nothing due again
        self.assertEqual(analytics.snapshot(FakeAPI(stats=STATS), recs, store, NOW), [])

    def test_available_analytics_metrics_are_stored(self):
        store = analytics.empty_store()
        api = FakeAPI(stats=STATS, rows=[[2500, 0.0432, 8.5, 61.2]])
        analytics.snapshot(api, records(), store, NOW)
        entry = store["videos"]["news-a-01"]["snapshots"][0]["analytics"]
        self.assertEqual(entry["impressions"], 2500)
        self.assertAlmostEqual(entry["ctr"], 0.0432)
        self.assertAlmostEqual(entry["avg_view_percentage"], 61.2)

    def test_empty_rows_read_as_freshness_not_zero(self):
        store = analytics.empty_store()
        analytics.snapshot(FakeAPI(stats=STATS, rows=[]), records(), store, NOW)
        entry = store["videos"]["news-a-01"]["snapshots"][0]["analytics"]
        self.assertIn("freshness", entry["unavailable"])


class ReportTests(unittest.TestCase):
    def test_baseline_needs_two_other_videos_and_names_them(self):
        store = analytics.empty_store()
        recs = records()
        recs["news-d-01:youtube"] = {"video_id": "news-d-01", "platform": "youtube", "state": "sent",
                                     "external_url": "https://www.youtube.com/watch?v=CCCCCCCCCCC"}
        stats = {**STATS, "CCCCCCCCCCC": {"published_at": iso(30), "views": 500, "likes": 10, "comments": 5}}
        analytics.snapshot(FakeAPI(stats=stats, rows=[[10, 0.02, 5, 50]]), recs, store, NOW)
        text = analytics.summarize(store)
        self.assertIn("median(n=2)", text)  # three videos: each is judged against the other two
        self.assertIn("CTR 2.00%", text)

    def test_single_video_report_says_baseline_is_missing(self):
        store = analytics.empty_store()
        recs = {k: v for k, v in records().items() if v["video_id"] == "news-a-01"}
        analytics.snapshot(FakeAPI(stats=STATS), recs, store, NOW)
        self.assertIn("needs 2+ other videos", analytics.summarize(store))

    def test_empty_store_report_does_not_pretend(self):
        self.assertIn("no snapshots yet", analytics.summarize(analytics.empty_store()))


class StoreTests(unittest.TestCase):
    def test_missing_store_bootstraps_and_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "analytics.json"
            self.assertEqual(analytics.load_store(path), analytics.empty_store())
            store = analytics.empty_store()
            analytics.snapshot(FakeAPI(stats=STATS), records(), store, NOW)
            path.write_text(json.dumps(store))
            self.assertEqual(analytics.load_store(path)["videos"]["news-a-01"]["snapshots"][0]["views"], 1000)


class EndpointTests(unittest.TestCase):
    def test_validator_accepts_only_the_exact_reports_url(self):
        self.assertEqual(validate_analytics_url(ANALYTICS_REPORTS), ANALYTICS_REPORTS)
        for bad in ("https://youtubeanalytics.googleapis.com/v2/reports?x=1",
                    "http://youtubeanalytics.googleapis.com/v2/reports",
                    "https://youtubeanalytics.googleapis.com/v2/other",
                    "https://evil.example.com/v2/reports"):
            with self.assertRaises(YouTubeError):
                validate_analytics_url(bad)

    def test_client_routes_the_reports_url_with_auth(self):
        class Session:
            def __init__(self):
                self.calls = []

            def request(self, method, url, **kw):
                self.calls.append((method, url, kw.get("params"), kw.get("headers")))

                class R:
                    status_code = 200
                    headers = {}

                    def json(self):
                        return {"rows": [[5, 0.1, 6.0, 40.0]]}
                return R()

        session = Session()
        with tempfile.TemporaryDirectory() as tmp:
            journal_path = Path(tmp) / "journal.json"
            journal_path.write_text(json.dumps({"records": {}, "quota": {}}))
            journal = Journal({"repository": "x/y", "branch": "main"}, remote=False, path=journal_path)
            cfg = json.loads((Path(__file__).resolve().parents[1] / "config/youtube.json").read_text())
            api = YouTubeAPI(cfg, journal, credentials={"client_id": "c", "client_secret": "s", "refresh_token": "r"},
                             session=session)
            api.token, api.expires = "fake-token", 10 ** 12
            with patch("tools.youtube.api.time"):
                body = api.json("GET", ANALYTICS_REPORTS, params={"ids": "channel==MINE"}, cost=1)
        self.assertEqual(body["rows"][0][0], 5)
        method, url, params, headers = session.calls[0]
        self.assertEqual((method, url), ("GET", ANALYTICS_REPORTS))
        self.assertEqual(params["ids"], "channel==MINE")
        self.assertEqual(headers["Authorization"], "Bearer fake-token")


if __name__ == "__main__":
    unittest.main()
