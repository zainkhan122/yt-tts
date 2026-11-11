import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.post.performance import (  # noqa: E402
    analyze,
    build_video_records,
    classify_hook,
    percentile_ranks,
    render_report,
    topic_advice,
    dimension_findings,
)

NOW = dt.datetime(2026, 10, 16, 12, 0, tzinfo=dt.timezone.utc)


def make_post(pid, vid, platform, sent_at, views, history=None):
    metrics = [{"type": "views", "name": "Views", "value": views, "unit": "count"},
               {"type": "comments", "name": "Comments", "value": 2, "unit": "count"},
               {"type": "engagementRate", "name": "Eng. Rate", "value": 1.5, "unit": "percentage"}]
    return {"post_id": pid, "video_id": vid, "platform": platform, "sent_at": sent_at,
            "external_url": f"https://example.com/{pid}", "metrics": metrics,
            "metrics_updated_at": "2026-10-16T10:00:00Z", "metrics_status": "fresh",
            "history": history or []}


def make_snapshot(posts):
    return {"fetched_at": "2026-10-16T08:00:00Z", "complete": True,
            "posts": {p["post_id"]: p for p in posts}}


def write_brief(root: Path, vid, hook="A plain statement hook.", cta=True, category="model"):
    scenes = [{"id": "hook", "say": hook, "heading": "HOOK"},
              {"id": "cta", "say": "Comment KEY for the link." if cta else "Follow for more."}]
    (root / f"{vid}.json").write_text(json.dumps(
        {"id": vid, "title": f"Title {vid}", "template": "tool-spotlight",
         "production_category": category, "niche": "niche", "scenes": scenes}), encoding="utf-8")


class PerformanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.briefs = Path(self.tmp.name)
        self.queue = {"items": []}

    def tearDown(self):
        self.tmp.cleanup()

    def test_percentile_ranks_handles_ties(self):
        ranks = percentile_ranks({"a": 10, "b": 10, "c": 30})
        self.assertEqual(ranks["c"], 100.0)
        self.assertEqual(ranks["a"], ranks["b"])
        self.assertLess(ranks["a"], 50.0)

    def test_classify_hook(self):
        self.assertEqual(classify_hook("What if your phone ran this?"), "question")
        self.assertEqual(classify_hook("Meet the new model."), "introducing")
        self.assertEqual(classify_hook("This tool edits video."), "statement")

    def _videos(self, specs):
        """specs: (vid, sent_at, views) -> joined records on youtube."""
        posts, queue_items = [], []
        for vid, sent, views in specs:
            write_brief(self.briefs, vid)
            posts.append(make_post(f"p-{vid}", vid, "youtube", sent, views))
            queue_items.append({"video_id": vid, "category": "tool"})
        videos = build_video_records(make_snapshot(posts), self.briefs, {"items": queue_items}, NOW)
        return videos

    def test_early_posts_are_never_judged(self):
        videos = self._videos([
            ("old-good", "2026-10-01T12:00:00Z", 1000),
            ("old-bad", "2026-10-01T12:00:00Z", 10),
            ("new-viral", "2026-10-16T06:00:00Z", 99999),  # 6h old: huge but too early
        ])
        old = [("old-good", 1000), ("old-mid1", 30), ("old-mid2", 20), ("old-bad", 10)]
        result = analyze(make_snapshot(
            [make_post(f"p-{v}", v, "youtube", "2026-10-01T12:00:00Z", views) for v, views in old] +
            [make_post("p-new-viral", "new-viral", "youtube", "2026-10-16T06:00:00Z", 99999)],
        ), self.briefs, {"items": [{"video_id": v, "category": "tool"} for v, _ in old] +
                        [{"video_id": "new-viral", "category": "tool"}]}, [], now=NOW)
        self.assertEqual(result["counts"]["early"], 1)
        report = render_report(result)
        self.assertIn("Too early to judge", report)
        self.assertIn("`new-viral`", report.split("Too early to judge")[1])
        winners_line = report.split("Winners (≥75th percentile):")[1].split("\n")[0]
        self.assertIn("old-good", winners_line)
        self.assertNotIn("new-viral", winners_line)

    def test_dimension_recommendation_needs_evidence_floor(self):
        specs = [(f"tool-win-{i}", "2026-10-01T12:00:00Z", 900 - i) for i in range(3)]
        specs += [("repo-mid", "2026-10-01T12:00:00Z", 100)]
        posts = []
        queue_items = []
        for vid, sent, views in specs:
            write_brief(self.briefs, vid, category="repo" if vid.startswith("repo") else "model")
            posts.append(make_post(f"p-{vid}", vid, "youtube", sent, views))
            queue_items.append({"video_id": vid, "category": "repo" if vid.startswith("repo") else "tool"})
        result = analyze(make_snapshot(posts), self.briefs, {"items": queue_items}, [], now=NOW)
        # only 3 'tool' videos judged -> below n>=4, so no Prioritise recommendation
        self.assertFalse(any("Prioritise" in r["action"] for r in result["recommendations"]))

    def test_dimension_recommendation_fires_at_floor(self):
        specs = [(f"tool-win-{i}", "2026-10-01T12:00:00Z", 900 - 10 * i) for i in range(4)]
        specs += [("repo-low", "2026-10-01T12:00:00Z", 50), ("news-low", "2026-10-01T12:00:00Z", 40)]
        posts, queue_items = [], []
        cats = {"tool-win": "tool", "repo-low": "repo", "news-low": "news"}
        for vid, sent, views in specs:
            cat = next(v for k, v in cats.items() if vid.startswith(k))
            write_brief(self.briefs, vid)
            posts.append(make_post(f"p-{vid}", vid, "youtube", sent, views))
            queue_items.append({"video_id": vid, "category": cat})
        result = analyze(make_snapshot(posts), self.briefs, {"items": queue_items}, [], now=NOW)
        self.assertTrue(any("Prioritise" in r["action"] and "'tool'" in r["action"]
                            for r in result["recommendations"]))

    def test_velocity_uses_last_two_history_points(self):
        hist = [{"fetched_at": "2026-10-14T08:00:00Z", "metrics_updated_at": "x",
                 "metrics": [{"type": "views", "name": "Views", "value": 100, "unit": "count"}]},
                {"fetched_at": "2026-10-16T08:00:00Z", "metrics_updated_at": "y",
                 "metrics": [{"type": "views", "name": "Views", "value": 300, "unit": "count"}]}]
        write_brief(self.briefs, "vel-1")
        snap = make_snapshot([make_post("p-vel-1", "vel-1", "youtube", "2026-10-05T12:00:00Z", 300, history=hist)])
        result = analyze(snap, self.briefs, {"items": [{"video_id": "vel-1", "category": "tool"}]}, [], now=NOW)
        entry = result["videos"][0]["platforms"]["youtube"]
        self.assertEqual(entry["views_per_day_recent"], 100.0)

    def test_slot_buckets_use_eastern_time(self):
        # 20:00Z in October = 16:00 ET -> evening
        specs = [(f"slot-{i}", "2026-10-05T20:00:00Z", 500) for i in range(3)]
        posts, queue_items = [], []
        for vid, sent, views in specs:
            write_brief(self.briefs, vid)
            posts.append(make_post(f"p-{vid}", vid, "youtube", sent, views))
            queue_items.append({"video_id": vid, "category": "tool"})
        result = analyze(make_snapshot(posts), self.briefs, {"items": queue_items}, [], now=NOW)
        evening = [s for s in result["slot_findings"] if s["daypart"] == "evening"]
        self.assertEqual(len(evening), 1)
        self.assertEqual(evening[0]["n"], 3)

    def test_topic_advice_blocks_risk_and_penalises_duplicates(self):
        videos = {}
        dims = dimension_findings(videos)
        rows = [
            {"status": "idea", "topic": "Great New Vision Model That Runs On Phones", "type": "model-spotlight",
             "url": "https://example.com/a", "score": "80", "trend_signal": "rising", "risk_flags": ""},
            {"status": "idea", "topic": "Risky Bypass Tool", "type": "repo-spotlight",
             "url": "https://example.com/b", "score": "90", "trend_signal": "", "risk_flags": "ToS bypass"},
            {"status": "sent", "topic": "Already done", "type": "news", "url": "", "score": "70",
             "trend_signal": "", "risk_flags": ""},
        ]
        advice = topic_advice(rows, videos, dims)
        topics = [c["topic"] for c in advice["top_candidates"]]
        self.assertIn("Great New Vision Model That Runs On Phones", topics)
        self.assertEqual([b["topic"] for b in advice["blocked_by_risk_flags"]], ["Risky Bypass Tool"])


if __name__ == "__main__":
    unittest.main()
