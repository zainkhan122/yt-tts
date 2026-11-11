"""Tests for the three new topic-selection signal tools:
search_probe (searched), need_miner (needed), rerank_backlog (performance).

These run offline (no network) by using cached/stub data where possible.
"""
import json
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent


class SearchProbeTests(unittest.TestCase):
    def test_searched_score_empty_suggestions(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import search_probe as sp
        res = sp.searched_score("zzzznotrealtopic", suggestions=[])
        self.assertEqual(res["score"], 0)
        self.assertIn("note", res)

    def test_searched_score_with_high_intent(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import search_probe as sp
        sugg = ["capcut alternative", "capcut alternative free", "capcut alternative for pc",
                "capcut alternative for mac", "capcut alternative app"]
        res = sp.searched_score("capcut alternative", suggestions=sugg)
        self.assertGreater(res["score"], 50)
        self.assertGreater(len(res["high_intent"]), 0)

    def test_fetch_suggestions_cache_roundtrip(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import search_probe as sp
        # Mock the network so we don't hit it in tests
        with mock.patch.object(sp, "_google_suggest", return_value=["test q"]), \
             mock.patch.object(sp, "_ddg_suggest", return_value=["test q"]):
            r1 = sp.fetch_suggestions("test query", use_cache=False)
            self.assertEqual(r1, ["test q"])
            r2 = sp.fetch_suggestions("test query", use_cache=False)
            self.assertEqual(r2, ["test q"])


class NeedMinerTests(unittest.TestCase):
    def test_question_patterns(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import need_miner as nm
        self.assertTrue(nm.QUESTION.search("how do I run this locally?"))
        self.assertTrue(nm.QUESTION.search("is there a free alternative to X"))
        self.assertTrue(nm.QUESTION.search("can it work without an API key?"))
        self.assertTrue(nm.QUESTION.search("why doesn't this support Mac?"))
        # Non-questions should not match
        self.assertFalse(nm.QUESTION.search("great video, thanks!"))
        self.assertFalse(nm.QUESTION.search("subscribed and followed"))

    def test_top_comments_returns_list(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import need_miner as nm
        # top_comments should return a list (empty on failure, not raise)
        result = nm.top_comments("https://www.youtube.com/shorts/invalid")
        self.assertIsInstance(result, list)


class RerankBacklogTests(unittest.TestCase):
    def test_performance_bonus_buckets(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import rerank_backlog as rb
        self.assertEqual(rb.performance_bonus(100000), rb.BUMP_STRONG)
        self.assertEqual(rb.performance_bonus(20000), rb.BUMP_GOOD)
        self.assertEqual(rb.performance_bonus(5000), rb.BUMP_MEH)
        self.assertEqual(rb.performance_bonus(100), rb.DEMOTE)

    def test_load_tracker_returns_dict(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import rerank_backlog as rb
        result = rb.load_tracker(7)
        self.assertIsInstance(result, dict)

    def test_rerank_dry_run_no_write(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import rerank_backlog as rb
        res = rb.rerank(write=False)
        self.assertIn("report", res)
        self.assertFalse(res["written"])


if __name__ == "__main__":
    unittest.main()
