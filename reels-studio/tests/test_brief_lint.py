"""Brief-lint regression tests.

These encode the mistake classes caught by hand during the 2026-10-12 batch: assets that
were not in the capture pack, camera regions below the captured viewport, sync words that
were never spoken, and unbalanced * markers that abort the renderer. Every one of them
should now fail (or warn) in `tools/brief_lint.py` before a cloud runner is spent.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import brief_lint
from tools.brief_lint import check

ROOT = Path(__file__).resolve().parent.parent


def brief(**over):
    b = {
        "id": "lint-fixture",
        "template": "tool-spotlight",
        "capture": "captures/lint-fixture",
        "title": "Fixture",
        "keywords": ["fixture"],
        "facts": {"checked": "2026-10-12"},
        "credits_on_screen": "Own motion graphic.",
        "sources": ["https://example.com"],
        "verify_before_render": ["checked"],
        "production_category": "tool",
        "scenes": [
            {"id": "hook", "type": "clip", "src": "demo.mp4", "in": 0, "out": 3,
             "headline": "A *HOOK*", "say": "A hook."},
            {"id": "how", "type": "steps", "heading": "HOW *IT* WORKS", "steps": ["one"],
             "say": "One step."},
            {"id": "catch", "type": "verdict", "heading": "THE *CATCH*", "cons": ["one con"],
             "pros": ["one pro"], "item_at": ["con", "pro"], "say": "One con, one pro."},
            {"id": "cta", "type": "endcard", "keyword": "FIX", "say": "Comment fix."},
        ],
        "seo": {"keyword": "fixture", "aliases": [], "youtube": {"title": "Fixture",
                "description": "x", "hashtags": ["#Shorts"], "tags": ["fixture"]}},
    }
    b.update(over)
    return b


class BriefLintTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        pack = self.root / "captures" / "lint-fixture"
        pack.mkdir(parents=True)
        (pack / "demo.mp4").write_bytes(b"x")
        (pack / "manifest.json").write_text(json.dumps({
            "files": {"demo": {"file": "demo.mp4"}},
            "regions_css": {"repo_title": {"x": 1, "y": 2, "w": 3, "h": 4}},
            "url": "https://example.com"}))

    def lint(self, b):
        p = self.root / f"{b['id']}.json"
        p.write_text(json.dumps(b))
        with patch.object(brief_lint, "ROOT", self.root):
            return check(p)

    def test_valid_brief_is_clean(self):
        bid, errors, warns = self.lint(brief())
        self.assertEqual(errors, [])
        self.assertEqual(warns, [])

    def test_unbalanced_highlight_markers_are_an_error(self):
        b = brief()
        b["scenes"][0]["headline"] = "A *BROKEN HOOK"
        _, errors, _ = self.lint(b)
        self.assertTrue(any("unbalanced *" in e for e in errors))

    def test_asset_missing_from_pack_is_an_error(self):
        b = brief()
        b["scenes"][0]["src"] = "not-in-pack.mp4"
        _, errors, _ = self.lint(b)
        self.assertTrue(any("not in the capture pack" in e for e in errors))

    def test_camera_region_outside_pack_map_is_an_error(self):
        b = brief()
        b["scenes"][0]["camera"] = [{"region": "below_the_viewport", "zoom": 1.4}]
        _, errors, _ = self.lint(b)
        self.assertTrue(any("region 'below_the_viewport'" in e for e in errors))

    def test_background_image_missing_from_pack_is_an_error(self):
        b = brief()
        b["scenes"][1]["background"] = {"image": "no-such-bg.jpg"}
        _, errors, _ = self.lint(b)
        self.assertTrue(any("background 'no-such-bg.jpg'" in e for e in errors))

    def test_clip_without_in_out_is_an_error(self):
        b = brief()
        del b["scenes"][0]["out"]
        _, errors, _ = self.lint(b)
        self.assertTrue(any("clip without in/out" in e for e in errors))

    def test_verdict_without_item_at_is_a_warning_not_an_error(self):
        b = brief()
        b["scenes"][2].pop("item_at")
        _, errors, warns = self.lint(b)
        self.assertEqual(errors, [])
        self.assertTrue(any("item_at" in w for w in warns))

    def test_sync_word_not_spoken_is_a_warning(self):
        b = brief()
        b["scenes"][2]["item_at"] = ["nonsense", "pro"]
        _, errors, warns = self.lint(b)
        self.assertEqual(errors, [])
        self.assertTrue(any("not present in the spoken line" in w for w in warns))

    def test_missing_pack_skips_asset_checks_with_a_warning(self):
        b = brief(capture="captures/never-captured")
        _, errors, warns = self.lint(b)
        self.assertEqual(errors, [])
        self.assertTrue(any("not present locally" in w for w in warns))

    def test_every_repo_brief_lints_without_errors(self):
        for p in sorted((ROOT / "briefs").glob("*.json")):
            with self.subTest(brief=p.name):
                _, errors, _ = check(p)
                self.assertEqual(errors, [], f"{p.name}: {errors}")


if __name__ == "__main__":
    unittest.main()
