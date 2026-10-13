import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validate_dispatch import plan_dispatch  # noqa: E402


class DispatchPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.briefs = Path(self.tmp.name)
        (self.briefs / "one.json").write_text(json.dumps({
            "id": "one",
            "scenes": [{"id": "hook"}, {"id": "demo_1"}],
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, raw="one", **kwargs):
        return plan_dispatch(raw, briefs_root=self.briefs, today=datetime.date(2026, 10, 14), **kwargs)

    def test_valid_inputs_are_normalized_and_date_tag_is_deterministic(self):
        result = self.plan("briefs/one.json", quality="looks", crf="23")
        self.assertEqual(result["briefs"], ["one"])
        self.assertEqual(result["tag"], "renders-2026-10-14")
        self.assertEqual(result["crf"], 23)

    def test_implicit_daily_tag_uses_asia_karachi_calendar_date(self):
        fixed_local = datetime.datetime(2026, 10, 14, 0, 15)
        with patch("tools.validate_dispatch.datetime.datetime") as clock:
            clock.now.return_value = fixed_local
            result = plan_dispatch("one", briefs_root=self.briefs)
        self.assertEqual(result["tag"], "renders-2026-10-14")
        self.assertEqual(clock.now.call_args.args[0].key, "Asia/Karachi")

    def test_unknown_or_mismatched_brief_fails_before_dispatch(self):
        with self.assertRaisesRegex(ValueError, "unknown brief"):
            self.plan("missing")
        (self.briefs / "wrong.json").write_text(json.dumps({"id": "not-wrong"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ID mismatch"):
            self.plan("wrong")

    def test_duplicate_unsafe_or_oversized_batch_fails(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.plan("one one")
        with self.assertRaisesRegex(ValueError, "brief input"):
            self.plan("../one")
        with self.assertRaisesRegex(ValueError, "daily cap"):
            self.plan(" ".join(f"short-{i}" for i in range(11)))

    def test_invalid_quality_crf_and_tag_fail(self):
        with self.assertRaisesRegex(ValueError, "quality"):
            self.plan(quality="ultra")
        with self.assertRaisesRegex(ValueError, "CRF"):
            self.plan(crf="not-a-number")
        with self.assertRaisesRegex(ValueError, "CRF"):
            self.plan(crf=52)
        with self.assertRaisesRegex(ValueError, "invalid tag"):
            self.plan(tag="refs/heads/main")

    def test_scene_rebuild_requires_valid_unique_scene_ids_and_reason(self):
        with self.assertRaisesRegex(ValueError, "non-empty rebuild reason"):
            self.plan(rebuild_scenes="hook")
        with self.assertRaisesRegex(ValueError, "unknown scene"):
            self.plan(rebuild_scenes="not-a-scene", rebuild_reason="typo fix")
        with self.assertRaisesRegex(ValueError, "safe and unique"):
            self.plan(rebuild_scenes="hook hook", rebuild_reason="typo fix")
        result = self.plan(rebuild_scenes="hook,demo_1", rebuild_reason="fix labels", from_tag="renders-2026-10-10")
        self.assertEqual(result["rebuild_scenes"], ["hook", "demo_1"])


if __name__ == "__main__":
    unittest.main()
