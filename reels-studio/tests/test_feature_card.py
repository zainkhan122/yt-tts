import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools import feature_card as fc
from tools import seo_pack


def make_root(tmp, scenes, plan=None, pushed=None):
    root = Path(tmp)
    (root / "briefs").mkdir()
    cap = root / "captures" / "demo-01"
    cap.mkdir(parents=True)
    Image.new("RGB", (1080, 1440), (9, 9, 9)).save(cap / "ok.png")
    if pushed is not None:
        (root / "tracker").mkdir()
        (root / "tracker" / "capture-pushes.json").write_text(json.dumps({"demo-01": {"files": {p: "x" for p in pushed}}}))
    brief = {"id": "demo-01", "capture": "captures/demo-01", "title": "demo: does a thing",
             "keywords": ["demo tool"], "scenes": scenes}
    (root / "briefs" / "demo-01.json").write_text(json.dumps(brief))
    if plan is not None:
        (root / "videos" / "demo-01").mkdir(parents=True)
        (root / "videos" / "demo-01" / "plan.json").write_text(json.dumps(plan))
    return root


SCENES = [
    {"id": "hook", "type": "image", "image": "missing.png", "heading": "DEMO 3 STEPS", "sub": "demo",
     "say": "Demo does three things for your laptop in one command today friends."},
    {"id": "p1", "type": "clip", "src": "gone.mp4", "in": 0, "out": 3, "heading": "ONE",
     "say": "It reads the screen with its accessibility tree, the same structure screen readers use."},
    {"id": "p2", "type": "image", "image": "ok.png", "heading": "REF PER ELEMENT",
     "say": "Each element gets a ref so it clicks a target."},
]


class FeatureCardTests(unittest.TestCase):
    def test_missing_media_gets_a_generated_card_and_present_media_is_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp, [dict(s) for s in SCENES])
            out = fc.ensure_media("demo-01", root=root)
            self.assertTrue(out["changed"])
            self.assertEqual([g["scene"] for g in out["generated"]], ["hook", "p1"])
            brief = json.loads((root / "briefs" / "demo-01.json").read_text())
            hook, p1, p2 = brief["scenes"]
            self.assertEqual(hook["image"], "generated/hook.png")
            self.assertEqual(hook["generated"], "feature-card")
            self.assertEqual(p1["type"], "image")          # clip became a card that keeps its say line
            self.assertNotIn("src", p1)
            self.assertEqual(p1["say"], SCENES[1]["say"])
            self.assertEqual(p2["image"], "ok.png")        # real media untouched
            self.assertNotIn("generated", p2)
            self.assertTrue((root / "captures/demo-01/generated/hook.png").exists())
            img = Image.open(root / "captures/demo-01/generated/hook.png")
            self.assertEqual(img.size, fc.PORTRAIT)

    def test_focus_steps_follow_the_spoken_words_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp, [dict(s) for s in SCENES])
            fc.ensure_media("demo-01", root=root)
            hook = json.loads((root / "briefs/demo-01.json").read_text())["scenes"][0]
            times = [f["at"] for f in hook["focus"]]
            self.assertEqual(times, sorted(times))
            self.assertEqual(times[0], 0.0)
            self.assertGreater(times[-1], 0.0)
            for f in hook["focus"]:
                x, y, w, h = f["box"]
                self.assertTrue(0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1)

    def test_second_run_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp, [dict(s) for s in SCENES])
            fc.ensure_media("demo-01", root=root)
            again = fc.ensure_media("demo-01", root=root)
            self.assertFalse(again["changed"])
            self.assertEqual(again["generated"], [])

    def test_scene_without_media_and_fewer_than_two_features_blocks(self):
        scenes = [{"id": "hook", "type": "image", "image": "missing.png", "say": "Demo does a thing today."}]
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp, scenes)
            with self.assertRaises(fc.FallbackError):
                fc.ensure_media("demo-01", root=root)

    def test_plan_points_are_the_feature_source(self):
        plan = {"points": [{"title": "Read the UI"}, {"title": "Ref every element"}, {"title": "Check each step"}]}
        self.assertEqual(fc.features_for({"scenes": []}, plan),
                         ["Read the UI", "Ref every element", "Check each step"])

    def test_pushed_release_file_counts_as_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp, [dict(s) for s in SCENES], pushed=["missing.png", "gone.mp4"])
            out = fc.ensure_media("demo-01", root=root)
            self.assertEqual(out["generated"], [])


class HashtagRuleTests(unittest.TestCase):
    def test_hashtag_count_must_be_five_on_short_form_platforms(self):
        brief = {"id": "repo-x-01", "qa_gates": True, "scenes": [{"id": "hook", "say": "x", "headline": "X"}],
                 "seo": {"keyword": "demo tool", "youtube": {"title": "Demo tool", "description": "Demo tool. #Shorts",
                                                             "hashtags": ["#shorts", "#demotool", "#a", "#b"],
                                                             "tags": ["demo tool"]},
                         "tiktok": {"caption": "demo tool", "hashtags": ["#demotool", "#a", "#b"]}}}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "b.json"
            p.write_text(json.dumps(brief))
            _, errors, *_ = seo_pack.check(str(p))
        self.assertTrue(any(e.startswith("[SP042]") and "tiktok" in e for e in errors))
        self.assertTrue(any(e.startswith("[SP042]") and "youtube" in e for e in errors))

    def test_legacy_brief_without_flag_keeps_its_three_hashtags(self):
        brief = {"id": "repo-x-01", "scenes": [{"id": "hook", "say": "x", "headline": "X"}],
                 "seo": {"keyword": "demo tool", "tiktok": {"caption": "demo tool", "hashtags": ["#demotool", "#a", "#b"]}}}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "b.json"
            p.write_text(json.dumps(brief))
            _, errors, *_ = seo_pack.check(str(p))
        self.assertFalse(any("SP042" in e for e in errors))


class CutoverTests(unittest.TestCase):
    def test_gates_apply_only_to_flagged_briefs(self):
        from tools import short_qa
        self.assertTrue(short_qa.gates_apply({"qa_gates": True}))
        self.assertFalse(short_qa.gates_apply({}))
        self.assertFalse(short_qa.gates_apply({"qa_gates": "yes"}))

    def test_legacy_brief_is_not_gated_in_preflight(self):
        from tools import preflight
        legacy = {"id": "repo-old-01", "scenes": [{"id": "hook", "type": "verdict", "say": "x"}]}
        res = preflight.check_short_qa_plan("repo-old-01", legacy)
        self.assertEqual([r["status"] for r in res], ["PASS"])
        self.assertIn("legacy", res[0]["detail"])
        res = preflight.check_media_fallback("repo-old-01", legacy)
        self.assertEqual(res[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
