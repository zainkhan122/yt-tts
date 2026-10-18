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
        "research_basis": ["research/social/decode-test.md"],
        "production_category": "tool",
        "scenes": [
            {"id": "hook", "type": "clip", "src": "demo.mp4", "in": 0, "out": 3,
             "headline": "A *HOOK*", "say": "A hook."},
            {"id": "how", "type": "steps", "heading": "HOW *IT* WORKS", "steps": ["one"],
             "background": {"img": "demo.mp4"}, "say": "One step."},
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
        basis = self.root / "research" / "social"
        basis.mkdir(parents=True)
        (basis / "decode-test.md").write_text("decode fixture", encoding="utf-8")
        (pack / "demo.mp4").write_bytes(b"x")
        (pack / "manifest.json").write_text(json.dumps({
            "files": {"demo": {"file": "demo.mp4", "kind": "own capture"}},
            "regions_css": {"repo_title": {"x": 1, "y": 2, "w": 3, "h": 4}},
            "url": "https://example.com"}))

    def lint(self, b):
        p = self.root / f"{b['id']}.json"
        p.write_text(json.dumps(b))
        with patch.object(brief_lint, "ROOT", self.root):
            bid, errors, warns, findings = check(p)
        self.last_findings = findings
        return bid, errors, warns

    def test_findings_carry_stable_rule_ids(self):
        b = brief()
        b["scenes"][0]["headline"] = "A *BROKEN HOOK"
        b["scenes"][0]["camera"] = [{"region": "below_the_viewport"}]
        _, errors, _ = self.lint(b)
        ids = {f["id"] for f in self.last_findings}
        self.assertEqual(ids, {"BL040", "BL070"})
        self.assertTrue(all(e.startswith("[") for e in errors))
        self.assertTrue(all(f["severity"] == "error" for f in self.last_findings))

    def test_warning_rule_ids_and_clean_brief_has_no_findings(self):
        b = brief()
        b["scenes"][0].pop("at", None)
        self.lint(b)
        self.assertEqual(self.last_findings, [])
        b2 = brief()
        b2["scenes"] = [{"id": "s1", "type": "verdict", "say": "one two", "cons": ["a", "b"]}]
        _, errors, warns = self.lint(b2)
        self.assertEqual(errors, [])
        # BL110 (media standard, 2026-10-18): this minimal brief stages no media at all.
        self.assertEqual([f["id"] for f in self.last_findings], ["BL051", "BL110"])
        self.assertTrue(all(f["severity"] == "warning" for f in self.last_findings))

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

    def test_montage_cut_anchor_must_match_an_exact_spoken_word(self):
        b = brief()
        hook = b["scenes"][0]
        hook["type"] = "clip-montage"
        hook["say"] = "The Pi case closes ports—real quick."
        hook["cuts"] = [{"in": 1, "out": 2, "label": "CUT SIDE PORTS", "at": "ports"}]
        _, errors, _ = self.lint(b)
        self.assertTrue(any(e.startswith("[BL081]") and "exact spoken word" in e for e in errors))

        hook["say"] = "The Pi case closes the side ports."
        _, errors, _ = self.lint(b)
        self.assertFalse(any(e.startswith("[BL081]") for e in errors))

    def test_licence_in_hook_is_an_error(self):
        b = brief()
        b["scenes"][0]["say"] = "This MIT tool is free!"
        _, errors, _ = self.lint(b)
        self.assertTrue(any(e.startswith("[BL101]") for e in errors), errors)

    def test_repeated_spoken_licence_mentions_warn(self):
        b = brief()
        b["scenes"][1]["say"] = "It is MIT licensed, honestly the licence is great."
        _, errors, warns = self.lint(b)
        self.assertTrue(any(w.startswith("[BL100]") for w in warns), warns)
        self.assertFalse(any(e.startswith("[BL101]") for e in errors), errors)

    def test_missing_pack_skips_asset_checks_with_a_warning(self):
        b = brief(capture="captures/never-captured")
        _, errors, warns = self.lint(b)
        self.assertEqual(errors, [])
        self.assertTrue(any("not present locally" in w for w in warns))

    # Briefs rendered and published before the 2026-10-18 viewer-benefit rule (PLAYBOOK §4).
    # Their brief text is pinned by queue/receipt hashes and cannot be rewritten; BL101
    # applies as an error to every brief created after that date.
    GRANDFATHERED_BL101 = {"repo-blender-mcp-01.json", "repo-earshot-01.json"}

    def test_every_repo_brief_lints_without_errors(self):
        for p in sorted((ROOT / "briefs").glob("*.json")):
            with self.subTest(brief=p.name):
                _, errors, _, _ = check(p)
                if p.name in self.GRANDFATHERED_BL101:
                    errors = [e for e in errors if not e.startswith("[BL101]")]
                self.assertEqual(errors, [], f"{p.name}: {errors}")


if __name__ == "__main__":
    unittest.main()
