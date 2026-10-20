"""Creative application: the treatment, archetypes and cover lab must LAND in the shipped film.

These tests exist because the first "creative" pilot shipped two films with the same
seven-scene spotlight structure and frame-grab covers while the briefs, the CSS
archetype colours and the cover concepts all looked distinct on paper.
"""
import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "templates" / "_spotlight"
ARCHETYPES = {"demo-first", "duel", "myth-bust", "quest", "warning", "workflow", "spotlight"}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cover_lab = load("cover_lab", ROOT / "tools" / "cover_lab.py")
creative_check = load("creative_check", ROOT / "tools" / "creative_check.py")


def spotcore():
    import sys
    sys.path.insert(0, str(SHARED))
    import spotcore as core  # noqa: WPS433
    return core


def treatment(archetype="quest", selected=0):
    return {"audience": "indie makers", "viewer_job": "ship a launch film", "intent": "browse",
            "archetype": archetype, "hook_mechanic": "one-person film crew",
            "open_loop": {"plant": "what will the cut look like?", "payoff_scene": "how"},
            "proof_moment": "how",
            "cover_concepts": [{"text": "AGENT SHOOTS ADS", "visual": "repo page", "gap": "what can it shoot?"},
                               {"text": "NO CREW NEEDED", "visual": "demo clip", "gap": "really, no crew?"},
                               {"text": "POINT. RE-EDIT.", "visual": "readme", "gap": "edit by pointing?"}],
            "selected_cover": selected}


# ---------------------------------------------------------------- archetype layer
class ArchetypeLayerTests(unittest.TestCase):
    def rules_for(self, css, arch):
        import re
        rows = []
        for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            sels = [x.strip() for x in selectors.split(",") if x.strip()]
            if any(sel.startswith(f'#root[data-archetype="{arch}"]') for sel in sels):
                rows.append(([sel for sel in sels if sel.startswith(f'#root[data-archetype="{arch}"]')], body))
        return rows

    def test_every_archetype_has_its_own_css_voice_not_only_a_colour(self):
        import re
        css = (SHARED / "archetype.css").read_text()
        for arch in ARCHETYPES:
            rules = self.rules_for(css, arch)
            self.assertTrue(rules, f"{arch} has no archetype rule (a treatment that changes "
                                   f"nothing is the template in disguise)")
            if arch == "spotlight":
                continue
            layout_rules = [(sels, body) for sels, body in rules
                            if re.search(r"(position|text-align|justify-content|border|padding|background|"
                                         r"letter-spacing|display|font-family|width|height|top|bottom|left)", body)]
            self.assertGreaterEqual(len(layout_rules), 2,
                                    f"{arch} only recolours; give it at least two layout/type rules, not a hue")
            self.assertTrue(any(".cg" in " ".join(sels) for sels, _ in rules),
                            f"{arch} never restyles the caption plate")

    def test_archetype_chrome_builds_devices_for_quest_and_myth_bust(self):
        js = (SHARED / "archetype.js").read_text()
        self.assertIn('"quest"', js)
        self.assertIn('"myth-bust"', js)
        for device in ("arch-rail", "arch-stamp", "arch-kicker", "arch-hud"):
            self.assertIn(device, js)
            self.assertIn("." + device, (SHARED / "archetype.css").read_text())

    def test_layout_contract_travels_with_the_data(self):
        core = spotcore()
        b = {"id": "t", "capture": "", "scenes": [{"id": "hook", "type": "image", "say": "hi", "image": "x.png"}],
             "treatment": {"archetype": "quest", "proof_moment": "hook",
                           "open_loop": {"payoff_scene": "hook"}}}
        data = core.data(b, {}, 10.0, {}, {"cut": "whip", "flavor": "tool"})
        self.assertEqual(data["archetype"], "quest")
        self.assertGreaterEqual(data["layout"]["stage_bottom"], 1100)
        self.assertLess(data["layout"]["stage_bottom"], data["layout"]["cap_top"])
        self.assertEqual(data["beats"]["proof_scene"], "hook")

    def test_stage_geometry_leaves_a_real_gap_above_captions(self):
        core = spotcore()
        self.assertLessEqual(core.LAYOUT["cover_top"], core.LAYOUT["stage_bottom"] - 300)
        self.assertGreater(core.LAYOUT["cap_top"] - core.LAYOUT["stage_bottom"], 24,
                           "media stage and caption zone must not touch: that collision shipped once")


# ---------------------------------------------------------------- cover lab application
class CoverLabTests(unittest.TestCase):
    def pack(self, tmp, colours=((20, 30, 60), (10, 12, 24), (40, 10, 50))):
        from PIL import Image
        cap = Path(tmp) / "captures" / "demo-01"
        cap.mkdir(parents=True)
        for name, colour in zip(("desktop-top.jpg", "desktop-full.jpg", "og.png"), colours):
            Image.new("RGB", (640, 400), colour).save(cap / name)
        b = {"id": "demo-01", "capture": "captures/demo-01", "scenes": [{"id": "hook", "image": "desktop-top.jpg"}],
             "treatment": treatment()}
        return b

    def test_three_concepts_are_three_designs_on_three_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = self.pack(tmp)
            made, report = cover_lab.make_concepts(b, Path(tmp) / "covers", root=Path(tmp))
            self.assertEqual(len(made), 3)
            self.assertEqual({c["layout"] for c in report}, {"bleed", "window", "split"})
            self.assertEqual(len({c["source"] for c in report}), 3,
                             "all concepts reused one capture image")
            self.assertEqual(cover_lab.audit(report), [])

    def test_audit_catches_reused_layout_low_contrast_and_long_text(self):
        rep = [{"concept": 0, "layout": "bleed", "source": "a.jpg", "contrast_white": 9, "contrast_accent": 9, "words": 3},
               {"concept": 1, "layout": "bleed", "source": "b.jpg", "contrast_white": 2.1, "contrast_accent": 3.0, "words": 6},
               {"concept": 2, "layout": "split", "source": "b.jpg", "contrast_white": 9, "contrast_accent": 9, "words": 3}]
        problems = cover_lab.audit(rep)
        # concepts 0/1 share a layout, 1 fails contrast AND word count, 1/2 share media
        self.assertTrue(any("reuse a layout" in p for p in problems))
        self.assertTrue(any("below 4.5" in p for p in problems))
        self.assertTrue(any("words" in p for p in problems))
        self.assertTrue(any("share capture images" in p for p in problems))

    def test_apply_freezes_the_selected_concept(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = self.pack(tmp)
            out = Path(tmp) / "covers"
            _, report = cover_lab.make_concepts(b, out, root=Path(tmp))
            sel = cover_lab.apply(b, out, report)
            self.assertEqual(sel["text"], b["treatment"]["cover_concepts"][0]["text"])
            self.assertEqual((out / "cover-selected.jpg").read_bytes(), (out / report[0]["file"]).read_bytes())
            self.assertEqual(sel["sha256"], hashlib.sha256((out / "cover-selected.jpg").read_bytes()).hexdigest())


# ---------------------------------------------------------------- renderer proof
class CreativeProofTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.brief = {"id": "demo-01", "treatment": treatment("quest", 1)}
        self.covers = self.tmp / "covers" / "demo-01"
        self.covers.mkdir(parents=True)
        (self.covers / "cover-selected.jpg").write_bytes(b"designed-cover-bytes")
        self.sel = {"brief": "demo-01", "selected": 1, "text": "NO CREW NEEDED", "layout": "window",
                    "archetype": "quest",
                    "sha256": hashlib.sha256(b"designed-cover-bytes").hexdigest()}
        self.write_sel()
        self.out = self.tmp / "renders" / "demo-01"
        self.out.mkdir(parents=True)

    def write_sel(self):
        (self.covers / "selection.json").write_text(json.dumps(self.sel))

    def proof(self):
        from lib.pipeline import creative_proof
        return creative_proof(self.brief, self.out, root=self.tmp)

    def test_legacy_brief_without_treatment_keeps_frame_cover(self):
        from lib.pipeline import creative_proof
        cover = creative_proof({"id": "legacy"}, self.out, root=self.tmp)
        self.assertEqual(cover["source"], "frame")

    def test_selected_concept_replaces_the_frame_grab(self):
        cover = self.proof()
        self.assertEqual(cover["source"], "cover-lab")
        self.assertEqual(cover["text"], "NO CREW NEEDED")
        self.assertTrue((self.out / "cover.jpg").read_bytes() == b"designed-cover-bytes")

    def test_missing_cover_lab_fails_the_render(self):
        shutil.rmtree(self.covers)
        with self.assertRaisesRegex(SystemExit, "cover lab not applied"):
            self.proof()

    def test_selection_for_another_archetype_fails_the_render(self):
        self.sel["archetype"] = "myth-bust"
        self.write_sel()
        with self.assertRaisesRegex(SystemExit, "archetype"):
            self.proof()

    def test_selection_text_must_match_the_brief_concept(self):
        self.sel["text"] = "SOME OTHER LINE"
        self.write_sel()
        with self.assertRaisesRegex(SystemExit, "not concept"):
            self.proof()

    def test_edited_cover_after_selection_fails_the_render(self):
        (self.covers / "cover-selected.jpg").write_bytes(b"edited-after-review")
        with self.assertRaisesRegex(SystemExit, "changed after selection"):
            self.proof()

    def test_brief_and_lab_must_agree_on_the_winner(self):
        self.brief["treatment"]["selected_cover"] = 2
        with self.assertRaisesRegex(SystemExit, "must agree"):
            self.proof()


class SkeletonTests(unittest.TestCase):
    def test_two_archetypes_cannot_share_a_beat_skeleton(self):
        quest = {"id": "a", "treatment": {**treatment("quest"), "structure": [
            {"scene": "s1", "beat": "briefing"}, {"scene": "s2", "beat": "objective"},
            {"scene": "s3", "beat": "proof"}, {"scene": "s4", "beat": "field-notes"},
            {"scene": "s5", "beat": "close"}]}}
        myth = {"id": "b", "treatment": {**treatment("myth-bust"), "structure": [
            {"scene": "s1", "beat": "briefing"}, {"scene": "s2", "beat": "objective"},
            {"scene": "s3", "beat": "proof"}, {"scene": "s4", "beat": "field-notes"},
            {"scene": "s5", "beat": "close"}]}}
        errs = creative_check.skeleton_errors([quest, myth])
        self.assertEqual(len(errs), 1)
        self.assertIn("repeats the beat skeleton", errs[0])

    def test_distinct_structures_and_legacy_briefs_pass(self):
        quest = {"id": "a", "treatment": {**treatment("quest"), "structure": [
            {"scene": "s1", "beat": "briefing"}, {"scene": "s2", "beat": "objective"},
            {"scene": "s3", "beat": "proof"}, {"scene": "s4", "beat": "field-notes"},
            {"scene": "s5", "beat": "close"}]}}
        myth = {"id": "b", "treatment": {**treatment("myth-bust"), "structure": [
            {"scene": "s1", "beat": "claim"}, {"scene": "s2", "beat": "evidence"},
            {"scene": "s3", "beat": "test"}, {"scene": "s4", "beat": "reality"},
            {"scene": "s5", "beat": "close"}]}}
        legacy = {"id": "c", "treatment": treatment("quest")}
        self.assertEqual(creative_check.skeleton_errors([quest, myth, legacy]), [])


class ApplicationCheckTests(unittest.TestCase):
    def brief(self):
        return {"id": "demo-01", "treatment": treatment("quest", 0)}

    def test_frame_cover_is_reported_as_not_applied(self):
        errs = creative_check.proof_errors(self.brief(), {"creative": {"archetype": "quest",
                                                                       "cover": {"source": "frame"}}})
        self.assertTrue(any("frame" in e for e in errs))

    def test_matching_render_is_clean(self):
        manifest = {"creative": {"archetype": "quest", "cover": {"source": "cover-lab",
                                                                  "text": "AGENT SHOOTS ADS"}}}
        self.assertEqual(creative_check.proof_errors(self.brief(), manifest), [])

    def test_wrong_archetype_and_wrong_cover_text_are_reported(self):
        manifest = {"creative": {"archetype": "spotlight", "cover": {"source": "cover-lab",
                                                                      "text": "WRONG LINE"}}}
        errs = creative_check.proof_errors(self.brief(), manifest)
        self.assertTrue(any("archetype" in e for e in errs))
        self.assertTrue(any("WRONG LINE" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
