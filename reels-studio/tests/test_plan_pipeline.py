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


def _plan():
    return json.loads((ROOT / "videos/repo-agent-desktop-01/plan.json").read_text(encoding="utf-8"))


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
        import tempfile
        import brief_from_plan as bfp
        plan = _plan()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "briefs").mkdir()
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            existing = {"id": plan["id"], "renderer": "graphics", "graphics": {"dir": "briefs/graphics/example"},
                        "status": "draft", "scenes": [{"id": "old", "say": "old"}]}
            (root / "briefs" / (plan["id"] + ".json")).write_text(json.dumps(existing), encoding="utf-8")
            with mock.patch.object(bfp, "ROOT", root):
                out = bfp.build(plan_path)
            brief = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(brief["scenes"][0]["say"], plan["question"])
            self.assertEqual([s["say"] for s in brief["scenes"][1:-2]], [p["spoken"] for p in plan["points"]])
            self.assertEqual(brief["scenes"][-2]["say"], plan["catch"])
            self.assertEqual(brief["scenes"][-1]["say"], plan["cta"])
            self.assertIsNone(brief["review"]["reviewer"])
            self.assertEqual(brief["renderer"], "graphics")

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
        if not (ROOT / "briefs/repo-agent-desktop-01.json").exists():
            bfp.build(ROOT / "videos/repo-agent-desktop-01/plan.json")

    def test_pre_phase_does_not_need_tracking_release_or_cover(self):
        calls = []
        with mock.patch.object(self.pf, "check_tracked", side_effect=lambda v: calls.append("tracked") or []), \
             mock.patch.object(self.pf, "check_capture_pack_release", side_effect=lambda *a: calls.append("release") or []), \
             mock.patch.object(self.pf, "check_cover", side_effect=lambda v: calls.append("cover") or []), \
             mock.patch.object(self.pf, "check_dispatch_head", side_effect=lambda *a: calls.append("head") or []):
            self.pf.preflight("repo-agent-desktop-01", phase="pre")
        self.assertEqual(calls, [])

    def test_dispatch_phase_runs_head_and_release_but_not_cover(self):
        calls = []
        with mock.patch.object(self.pf, "check_tracked", side_effect=lambda v: calls.append("tracked") or []), \
             mock.patch.object(self.pf, "check_capture_pack_release", side_effect=lambda *a: calls.append("release") or []), \
             mock.patch.object(self.pf, "check_cover", side_effect=lambda v: calls.append("cover") or []), \
             mock.patch.object(self.pf, "check_dispatch_head", side_effect=lambda *a: calls.append("head") or []):
            self.pf.preflight("repo-agent-desktop-01", phase="dispatch", receipt_rel="research/production/receipts/x.json")
        self.assertEqual(calls, ["tracked", "release", "head"])

    def test_dispatch_without_receipt_is_blocked(self):
        res = self.pf.preflight("repo-agent-desktop-01", phase="dispatch")
        self.assertEqual(res["verdict"], "BLOCK")
        self.assertTrue(any("receipt" in r["detail"] for r in res["results"] if r["check"] == "dispatch_head"))

    def test_full_phase_includes_cover(self):
        calls = []
        with mock.patch.object(self.pf, "check_cover", side_effect=lambda v: calls.append("cover") or []):
            self.pf.preflight("repo-agent-desktop-01", phase="full", receipt_rel="r.json")
        self.assertEqual(calls, ["cover"])

    def test_unknown_phase_rejected(self):
        with self.assertRaises(ValueError):
            self.pf.preflight("repo-agent-desktop-01", phase="later")


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
