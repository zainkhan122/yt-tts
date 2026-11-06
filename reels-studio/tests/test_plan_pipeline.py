"""Plan -> brief pipeline: packaging is checked at authoring time, the brief builder is generic, and
the preflight phases run in the order the stages need (regression for the 2 Nov ordering faults)."""
import importlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "motion"))

import video_plan  # noqa: E402

PLANS = sorted(ROOT.glob("videos/*/plan.json"))


VID = "repo-craft-anything-01"   # a plan that still has a brief; the removed shorts must not be pinned here


def _plan_path():
    return ROOT / "videos" / VID / "plan.json"


def _plan():
    return json.loads(_plan_path().read_text(encoding="utf-8"))


class PackagingRules(unittest.TestCase):
    def test_every_authored_plan_passes(self):
        for path in PLANS:
            res = video_plan.check(json.loads(path.read_text(encoding="utf-8")))
            blocks = [m for s, m in res if s == "BLOCK"]
            self.assertEqual(blocks, [], f"{path.parent.name}: {blocks}")

    def test_missing_packaging_is_blocked(self):
        p = _plan()
        del p["seo"]
        res = video_plan.check_packaging(p)
        self.assertTrue(any(s == "BLOCK" and "seo" in m for s, m in res))

    def test_copy_rules_run_on_plan_copy(self):
        p = _plan()
        p["seo"]["instagram"]["hashtags"] = ["#ai", "#coding", "#tech", "#viral", "#fyp", "#foryou"]
        res = video_plan.check_packaging(p)
        self.assertTrue(any(s == "BLOCK" and "copy rules" in m for s, m in res))

    def test_cta_keyword_must_be_one_capital_word(self):
        p = _plan()
        p["cta_keyword"] = "two words"
        res = video_plan.check_packaging(p)
        self.assertTrue(any(s == "BLOCK" and "cta_keyword" in m for s, m in res))


class BriefBuilder(unittest.TestCase):
    def test_brief_comes_from_plan_only(self):
        import brief_from_plan as bfp
        vid = _plan_path().parent.name
        cap = ROOT / "captures" / vid
        self.assertTrue((cap / "plan-keep.json").exists(), "run build_plan_kit first")
        # Build into the real location and keep it: the brief is a production artifact, not scratch.
        out = bfp.build(ROOT / "videos" / vid / "plan.json")
        brief = json.loads(out.read_text(encoding="utf-8"))
        text = json.dumps(brief, ensure_ascii=False)
        self.assertNotIn("iFixAi", text, "no iFixAi copy may leak into another video's brief")
        self.assertNotIn("owner approval of plan given", text)
        self.assertIsNone(brief["review"]["expires_at"])
        self.assertIn("Topic approved by owner", brief["review"]["notes"])
        kinds = [s["type"] for s in brief["scenes"]]
        self.assertEqual(kinds[0], "image")
        self.assertEqual(kinds[-1], "endcard")
        self.assertEqual(brief["scenes"][-2]["id"], "catch")

    def test_missing_kit_names_the_fix(self):
        import brief_from_plan as bfp
        keep = {"plan-1": [0.1, 0.5]}
        with self.assertRaises(SystemExit) as cm:
            bfp._keep_for(keep, "plan-9", "x-01")
        self.assertIn("build_plan_kit", str(cm.exception))


class PreflightPhases(unittest.TestCase):
    def setUp(self):
        import brief_from_plan as bfp
        import preflight as pf
        self.pf = importlib.reload(pf)
        if not (ROOT / "briefs/repo-craft-anything-01.json").exists():
            bfp.build(ROOT / "videos/repo-craft-anything-01/plan.json")

    def test_pre_phase_does_not_need_tracking_release_or_cover(self):
        calls = []
        with mock.patch.object(self.pf, "check_tracked", side_effect=lambda v: calls.append("tracked") or []), \
             mock.patch.object(self.pf, "check_capture_pack_release", side_effect=lambda *a: calls.append("release") or []), \
             mock.patch.object(self.pf, "check_cover", side_effect=lambda v: calls.append("cover") or []), \
             mock.patch.object(self.pf, "check_dispatch_head", side_effect=lambda *a: calls.append("head") or []):
            self.pf.preflight("repo-craft-anything-01", phase="pre")
        self.assertEqual(calls, [])

    def test_dispatch_phase_runs_head_and_release_but_not_cover(self):
        calls = []
        with mock.patch.object(self.pf, "check_tracked", side_effect=lambda v: calls.append("tracked") or []), \
             mock.patch.object(self.pf, "check_capture_pack_release", side_effect=lambda *a: calls.append("release") or []), \
             mock.patch.object(self.pf, "check_cover", side_effect=lambda v: calls.append("cover") or []), \
             mock.patch.object(self.pf, "check_dispatch_head", side_effect=lambda *a: calls.append("head") or []):
            self.pf.preflight("repo-craft-anything-01", phase="dispatch", receipt_rel="research/production/receipts/x.json")
        self.assertEqual(calls, ["tracked", "release", "head"])

    def test_dispatch_without_receipt_is_blocked(self):
        res = self.pf.preflight("repo-craft-anything-01", phase="dispatch")
        self.assertEqual(res["verdict"], "BLOCK")
        self.assertTrue(any("receipt" in r["detail"] for r in res["results"] if r["check"] == "dispatch_head"))

    def test_full_phase_includes_cover(self):
        calls = []
        with mock.patch.object(self.pf, "check_cover", side_effect=lambda v: calls.append("cover") or []):
            self.pf.preflight("repo-craft-anything-01", phase="full", receipt_rel="r.json")
        self.assertEqual(calls, ["cover"])

    def test_unknown_phase_rejected(self):
        with self.assertRaises(ValueError):
            self.pf.preflight("repo-craft-anything-01", phase="later")


class DriverOrder(unittest.TestCase):
    def test_render_gate_runs_dispatch_phase_and_queue_gate_runs_full(self):
        import inspect
        import make_shorts
        render_src = inspect.getsource(make_shorts.stage_render)
        queue_src = inspect.getsource(make_shorts.stage_queue)
        gate_src = inspect.getsource(make_shorts.stage_gate)
        self.assertIn('"dispatch"', render_src)
        self.assertIn('"full"', queue_src)
        self.assertIn('"pre"', gate_src)
        self.assertLess(make_shorts.STAGES.index("source"), make_shorts.STAGES.index("render"))
        self.assertLess(make_shorts.STAGES.index("cover"), make_shorts.STAGES.index("queue"))


if __name__ == "__main__":
    unittest.main()
