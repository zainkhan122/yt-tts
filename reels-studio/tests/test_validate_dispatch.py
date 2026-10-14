import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validate_dispatch import _brief_id, main, plan_dispatch  # noqa: E402


class ValidateDispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.brief_root = self.root / "reels-studio/briefs"
        self.brief_root.mkdir(parents=True)
        for brief_id in ("one", "two"):
            brief = {
                "id": brief_id,
                "voice_seed": 0,
                "scenes": [{"id": "hook"}, {"id": "demo_1"}],
            }
            (self.brief_root / f"{brief_id}.json").write_text(json.dumps(brief), encoding="utf-8")
        self.receipt_summary = {
            "briefs": {
                brief_id: {
                    "asset_manifest_sha256": "a" * 64,
                    "asset_files_sha256": "b" * 64,
                    "capture_id": f"cap-{brief_id}",
                }
                for brief_id in ("one", "two")
            }
        }

    def tearDown(self):
        self.tmp.cleanup()

    def _make_attempts(self):
        return [{"fingerprint": "c" * 64}]

    def test_valid_full_render_normalizes_paths_and_verifies_batch_receipt(self):
        with patch("tools.validate_dispatch.production_gate.validate_receipt", return_value=self.receipt_summary) as receipt:
            with patch("tools.validate_dispatch.render_attempts.make_attempts", return_value=self._make_attempts()):
                plan = plan_dispatch(
                    "briefs/one.json two",
                    tag="renders-2026-10-14",
                    quality="looks",
                    crf="23",
                    production_receipt="reels-studio/research/production/receipts/daily.json",
                    repo_root=self.root,
                )
        self.assertEqual(plan["briefs"], ["one", "two"])
        self.assertEqual(plan["crf"], 23)
        self.assertEqual(plan["attempts"], self._make_attempts())
        receipt.assert_called_once()
        self.assertEqual(receipt.call_args.args[1:3],
                         ("reels-studio/research/production/receipts/daily.json", ["one", "two"]))

    def test_duplicate_unsafe_or_oversized_brief_inputs_are_rejected(self):
        for value, message in (
            ("one one", "duplicate brief IDs"),
            ("../briefs/one.json", "must be an ID or a repository briefs"),
            ("briefs/../one.json", "must be an ID or a repository briefs"),
            ("one\\two", "invalid brief token"),
            ("", "no brief IDs supplied"),
            (" ".join(["one"] * 11), "daily cap is 10"),
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, message):
                    plan_dispatch(value, production_receipt="reels-studio/research/production/receipts/daily.json",
                                  repo_root=self.root)

    def test_quality_crf_and_tag_are_validated_before_attempt_reservation(self):
        invalid = (
            {"quality": "ultra"},
            {"crf": "52"},
            {"crf": "23.5"},
            {"tag": "../releases"},
        )
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    plan_dispatch("one", production_receipt="reels-studio/research/production/receipts/daily.json",
                                  repo_root=self.root, **kwargs)

    def test_full_render_requires_receipt_and_exact_receipt_validation(self):
        with self.assertRaisesRegex(ValueError, "six-stage production receipt"):
            plan_dispatch("one", repo_root=self.root)
        one_summary = {"briefs": {"one": self.receipt_summary["briefs"]["one"]}}
        with patch("tools.validate_dispatch.production_gate.validate_receipt", return_value=one_summary) as receipt:
            with patch("tools.validate_dispatch.render_attempts.make_attempts", return_value=self._make_attempts()):
                plan_dispatch("one", production_receipt="reels-studio/research/production/receipts/daily.json",
                              repo_root=self.root)
        receipt.assert_called_once()

    def test_scene_rebuild_requires_one_known_scene_and_reason(self):
        with patch("tools.validate_dispatch.production_gate.validate_receipt") as receipt:
            with patch("tools.validate_dispatch.render_attempts.make_attempts", return_value=self._make_attempts()):
                plan = plan_dispatch("one", rebuild_scenes="hook,demo_1", rebuild_reason="Fix transition timing",
                                     from_tag="renders-2026-10-13", repo_root=self.root)
        receipt.assert_not_called()
        self.assertEqual(plan["rebuild_scenes"], ["hook", "demo_1"])
        self.assertEqual(plan["production_receipt"], "")
        for kwargs, message in (
            ({"rebuild_scenes": "hook", "rebuild_reason": "no"}, "4-240 printable"),
            ({"rebuild_scenes": "unknown", "rebuild_reason": "Fix transition timing"}, "unknown scene"),
            ({"rebuild_scenes": "hook", "rebuild_reason": "Fix transition timing", "from_tag": "unsafe/tag"}, "invalid from_tag"),
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, message):
                    plan_dispatch("one", repo_root=self.root, **kwargs)

    def test_brief_paths_must_be_repo_relative_and_canonical(self):
        self.assertEqual(_brief_id("one"), "one")
        self.assertEqual(_brief_id("briefs/one.json"), "one")
        self.assertEqual(_brief_id("reels-studio/briefs/one.json"), "one")
        for value in ("/briefs/one.json", "C:/briefs/one.json", "briefs//one.json", "reels-studio/one.json"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    _brief_id(value)

    def test_github_workflow_rejects_non_dispatch_events_and_non_main_refs(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main"}):
            self.assertEqual(main(), 2)
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/feature"}):
            self.assertEqual(main(), 2)


if __name__ == "__main__":
    unittest.main()
