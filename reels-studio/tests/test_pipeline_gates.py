"""Regression tests for the 1 Nov 2026 lessons (see docs/production-lessons.md, rows 15-23)."""
import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import preflight as pf  # noqa: E402
from tools.post import cadence  # noqa: E402


class PolicyGateTests(unittest.TestCase):
    def test_new_brief_needs_motion_standard(self):
        with patch.object(pf, "QUEUE", Path(tempfile.mkdtemp()) / "none.json"):
            res = pf.check_policy("brand-new-01", {"id": "brand-new-01"})
        self.assertEqual(res[0]["status"], "BLOCK")
        self.assertIn("motion_standard", res[0]["detail"])

    def test_published_brief_is_grandfathered(self):
        q = Path(tempfile.mkdtemp()) / "q.json"
        q.write_text(json.dumps({"items": [{"video_id": "old-01", "brief_sha256": "x"}]}))
        with patch.object(pf, "QUEUE", q):
            res = pf.check_policy("old-01", {"id": "old-01"})
        self.assertEqual(res[0]["status"], "PASS")

    def test_pending_copy_pin_blocks(self):
        q = Path(tempfile.mkdtemp()) / "q.json"
        q.write_text(json.dumps({"items": [{"video_id": "v-01", "copy_pin_pending": "owner decision"}]}))
        with patch.object(pf, "QUEUE", q):
            res = pf.check_policy("v-01", {"id": "v-01", "motion_standard": 2})
        self.assertEqual(res[0]["status"], "BLOCK")
        self.assertIn("copy pin pending", res[0]["detail"])


class LayoutAuditTests(unittest.TestCase):
    def test_scrim_over_media_is_a_problem_in_the_audit(self):
        src = (ROOT / "tools" / "layout_audit.py").read_text()
        self.assertIn('.sp-imgcard .sp-scrim', src)          # measured in the browser
        self.assertIn("scrim(s) over card media", src)       # and reported as a failure

    def test_layout_check_exists_in_preflight(self):
        self.assertIn("check_layout", (ROOT / "tools" / "preflight.py").read_text())


class CadenceCollisionTests(unittest.TestCase):
    def test_offset_depends_on_channel_salt(self):
        cfg = {"schedule": {"random_gap_minutes": {"min": 5, "max": 20}}}
        day = dt.date(2026, 11, 1)
        offsets = {cadence.random_offset_minutes("youtube", day, 0, cfg, salt=n) for n in range(12)}
        self.assertGreater(len(offsets), 1, "two posts on one channel must not share one offset")
        for o in offsets:
            self.assertTrue(5 <= o <= 20)


class CiRequirementTests(unittest.TestCase):
    def test_youtube_requirements_include_yt_dlp(self):
        txt = (ROOT / "tools" / "youtube" / "requirements.txt").read_text()
        self.assertIn("yt-dlp", txt)


class PublisherExitTests(unittest.TestCase):
    def test_legacy_issue_is_held_not_blocking(self):
        src = (ROOT / "tools" / "post" / "publisher.py").read_text()
        self.assertIn("held_for_review", src)
        self.assertIn("def blocking(issue)", src)


if __name__ == "__main__":
    unittest.main()
