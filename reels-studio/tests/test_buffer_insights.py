import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.post.buffer_insights import (  # noqa: E402
    INSIGHTS_QUERY,
    build_snapshot,
    query_sent_posts,
    render_report,
)


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, query, variables):
        self.calls.append((query, variables))
        return self.responses.pop(0)


class BufferInsightsTests(unittest.TestCase):
    def test_query_validates_against_saved_official_buffer_schema(self):
        try:
            from graphql import build_client_schema, parse, validate
        except ImportError:
            self.skipTest("graphql-core is an optional test dependency")
        schema_path = ROOT / "research/publishing/buffer-schema-2026-10-10.json"
        # Buffer's saved introspection has an unrelated interface deprecation mismatch; trust the introspection
        # structure, but still run GraphQL document validation against its actual field/argument types.
        schema = build_client_schema(json.loads(schema_path.read_text(encoding="utf-8")), assume_valid=True)
        errors = validate(schema, parse(INSIGHTS_QUERY))
        self.assertEqual(errors, [])

    def test_paginates_sent_posts_and_never_requests_a_mutation(self):
        client = FakeClient([
            {"posts": {"edges": [{"node": {"id": "p1", "channelId": "c1"}}],
                        "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"}}},
            {"posts": {"edges": [{"node": {"id": "p2", "channelId": "c1"}}],
                        "pageInfo": {"hasNextPage": False, "endCursor": None}}},
        ])
        settings = {"organization_id": "org", "channels": {"youtube": {"buffer_id": "c1"}}, "max_pages": 3}
        posts, pages = query_sent_posts(client, settings)
        self.assertEqual([p["id"] for p in posts], ["p1", "p2"])
        self.assertEqual(pages, 2)
        self.assertTrue(all("metrics" in q for q, _ in client.calls))
        self.assertTrue(all("mutation" not in q.lower() for q, _ in client.calls))
        self.assertEqual(client.calls[1][1]["after"], "cursor-1")

    def test_incomplete_pagination_fails_closed(self):
        client = FakeClient([{"posts": {"edges": [], "pageInfo": {"hasNextPage": True, "endCursor": "c1"}}}])
        settings = {"organization_id": "org", "channels": {"youtube": {"buffer_id": "c1"}}, "max_pages": 1}
        with self.assertRaisesRegex(Exception, "pagination did not complete"):
            query_sent_posts(client, settings)

    def test_joins_publication_receipts_and_video_assets_and_tracks_metric_freshness(self):
        pubs = {"records": {"one:youtube": {"state": "sent", "buffer_post_id": "p1", "video_id": "one",
                                               "platform": "youtube", "title": "One title"}}}
        posts = [
            {"id": "p1", "channelId": "c1", "_channel_alias": "youtube", "sentAt": "2026-10-10T12:00:00Z",
             "externalLink": "https://youtube.com/watch?v=1", "text": "caption one", "assets": [],
             "metrics": [{"type": "views", "name": "Views", "value": 120, "unit": "views"},
                         {"type": "averageTimeWatched", "name": "Average time watched", "value": 12.5, "unit": "seconds"}],
             "metricsUpdatedAt": "2026-10-14T11:30:00Z"},
            {"id": "p2", "channelId": "c1", "_channel_alias": "youtube", "sentAt": "2026-10-14T11:30:00Z",
             "text": "untracked clip", "assets": [{"mimeType": "video/mp4", "source": "https://cdn.example/video.mp4"}],
             "metrics": [], "metricsUpdatedAt": None},
        ]
        snapshot = build_snapshot(posts, publication_records=pubs, fetched_at="2026-10-14T12:00:00Z",
                                  expected_post_ids=["p1"], pages=1)
        self.assertTrue(snapshot["complete"])
        self.assertEqual(snapshot["video_post_count"], 2)
        self.assertEqual(snapshot["posts"]["p1"]["video_id"], "one")
        self.assertEqual(snapshot["posts"]["p1"]["metrics_status"], "fresh")
        self.assertEqual(snapshot["posts"]["p2"]["metrics_status"], "awaiting_buffer_refresh")
        self.assertEqual(snapshot["coverage_by_platform"]["youtube"]["fresh_metric_posts"], 1)

    def test_untracked_non_video_sent_post_keeps_zero_coverage_without_crashing(self):
        posts = [{"id": "text-1", "channelId": "c1", "_channel_alias": "youtube", "text": "text post",
                  "assets": [], "metrics": [], "metricsUpdatedAt": None}]
        snapshot = build_snapshot(posts, publication_records={"records": {}, "configured_channels": ["instagram"]},
                                  fetched_at="2026-10-14T12:00:00Z")
        self.assertEqual(snapshot["video_post_count"], 0)
        self.assertEqual(snapshot["coverage_by_platform"]["youtube"]["total_video_posts"], 0)
        self.assertEqual(snapshot["coverage_by_platform"]["instagram"]["total_video_posts"], 0)

    def test_facebook_likes_stay_distinct_and_percent_is_not_scaled_twice(self):
        pubs = {"records": {"one:facebook": {"state": "sent", "buffer_post_id": "p1", "video_id": "one",
                                               "platform": "facebook", "title": "Facebook demo"}}}
        post = {"id": "p1", "channelId": "c1", "_channel_alias": "facebook", "assets": [],
                "metrics": [{"type": "reactions", "name": "Reactions", "value": 8, "unit": "count"},
                            {"type": "likes", "name": "Likes", "value": 5, "unit": "count"},
                            {"type": "engagementRate", "name": "Engagement rate", "value": 0.8, "unit": "percentage"}],
                "metricsUpdatedAt": "2026-10-14T11:00:00Z"}
        snapshot = build_snapshot([post], publication_records=pubs, fetched_at="2026-10-14T12:00:00Z")
        report = render_report(snapshot)
        self.assertIn("Top by reactions", report)
        self.assertIn("Top by Facebook likes", report)
        self.assertIn("0.80%", report)
        self.assertNotIn("80.00%", report)

    def test_missing_sent_post_marks_snapshot_incomplete(self):
        pubs = {"records": {"one:youtube": {"state": "sent", "buffer_post_id": "expected", "video_id": "one", "platform": "youtube"}}}
        snapshot = build_snapshot([], publication_records=pubs, fetched_at="2026-10-14T12:00:00Z", expected_post_ids=["expected"])
        self.assertFalse(snapshot["complete"])
        self.assertEqual(snapshot["missing_expected_post_ids"], ["expected"])

    def test_history_is_bounded_and_report_keeps_channels_separate(self):
        pubs = {"records": {"one:youtube": {"state": "sent", "buffer_post_id": "p1", "video_id": "one", "platform": "youtube"}}}
        old = {"posts": {"p1": {"history": [{"fetched_at": f"2026-10-{i:02d}T12:00:00Z", "metrics_updated_at": None, "metrics": []}
                                                   for i in range(1, 40)]}}}
        posts = [{"id": "p1", "channelId": "c1", "_channel_alias": "youtube", "assets": [],
                  "metrics": [{"type": "views", "name": "Views", "value": 20, "unit": "views"}],
                  "metricsUpdatedAt": "2026-10-14T11:00:00Z"}]
        snapshot = build_snapshot(posts, publication_records=pubs, fetched_at="2026-10-14T12:00:00Z", previous=old)
        self.assertLessEqual(len(snapshot["posts"]["p1"]["history"]), 7)
        report = render_report(snapshot)
        self.assertIn("not compared across channels", report)
        self.assertIn("Buffer Insights refresh daily", report)


if __name__ == "__main__":
    unittest.main()
