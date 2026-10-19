"""Gate receipts: stable rule IDs persisted into the render manifest (feature c)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib import gates  # noqa: E402

BRIEF = {
    "id": "gate-demo-01", "template": "tool-spotlight", "capture": "captures/none",
    "research_basis": ["research/social/decode-2026-10-18.md"],
    "treatment": {"audience": "developers", "viewer_job": "learn hello world",
                  "intent": "search", "archetype": "demo-first",
                  "hook_mechanic": "result first",
                  "open_loop": {"plant": "does it help?", "payoff_scene": "s2"},
                  "proof_moment": "s1",
                  "cover_concepts": [
                      {"text": "HELLO WORLD", "visual": "shot.png", "gap": "what does it do?"},
                      {"text": "ONE MINUTE", "visual": "shot.png", "gap": "learn what?"},
                      {"text": "TRY THIS", "visual": "shot.png", "gap": "try what?"}],
                  "selected_cover": 0},
    "scenes": [{"id": "s1", "type": "page", "say": "hello world this tool helps", "heading": "hello world"},
               {"id": "s2", "type": "image", "image": "shot.png", "hold": True}],
    "seo": {"keyword": "hello world", "onscreen_first3s": "hello world",
            "youtube": {"title": "hello world in one minute", "description": "hello world is a demo tool for testing.",
                        "hashtags": ["#Shorts", "#demo", "#tools"], "tags": ["hello world", "demo"]},
            "tiktok": {"caption": "hello world tool in 20 seconds", "hashtags": ["#shorts", "#demo", "#tools"]},
            "instagram": {"caption": "hello world tool in 20 seconds", "hashtags": ["#shorts", "#demo"]},
            "facebook": {"caption": "hello world tool in 20 seconds", "hashtags": ["#shorts", "#demo"]},
            "x": {"text": "hello world tool in 20 seconds", "hashtags": ["#shorts"]}},
}  # error-free apart from the missing capture pack (BL020, warning)


def write_brief(root, brief):
    p = Path(root) / f"{brief['id']}.json"
    p.write_text(json.dumps(brief))
    return p


class GateReportTests(unittest.TestCase):
    def test_clean_brief_reports_no_errors_and_names_the_one_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = gates.run(write_brief(tmp, BRIEF))
        self.assertEqual(report["brief"], "gate-demo-01")
        self.assertEqual(report["rollup"]["errors"], 0)
        self.assertEqual([f["id"] for f in report["lint"]], ["BL020"])
        self.assertEqual(report["rollup"]["by_id"], {"BL020": 1})  # missing capture pack locally
        self.assertIn("0 error(s), 1 warning(s)", gates.summary_lines(report)[0])

    def test_findings_carry_rule_ids_and_roll_up_by_id(self):
        brief = json.loads(json.dumps(BRIEF))
        brief["scenes"][0]["heading"] = "BROKEN *HIGHLIGHT"
        brief["seo"]["youtube"]["hashtags"] = ["#notshorts"]
        with tempfile.TemporaryDirectory() as tmp:
            report = gates.run(write_brief(tmp, brief))
        ids = [f["id"] for f in report["lint"]] + [f["id"] for f in report["seo"]]
        self.assertIn("BL040", ids)
        self.assertIn("SP070", ids)
        self.assertGreaterEqual(report["rollup"]["errors"], 2)
        self.assertEqual(report["rollup"]["by_id"]["BL040"], 1)
        self.assertTrue(all("[" in line for line in gates.summary_lines(report)[1:]))

    def test_unreadable_brief_is_recorded_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "broken.json"
            p.write_text("{not json")
            report = gates.run(p)
        ids = [f["id"] for f in report["lint"]]
        self.assertEqual(ids, ["BL900"])
        self.assertTrue(report["rollup"]["errors"] >= 1)


class ManifestRecordTests(unittest.TestCase):
    def manifest(self, tmp):
        p = Path(tmp) / "manifest.json"
        p.write_text(json.dumps({"id": "gate-demo-01", "qa": {"checks": {}}}))
        return p

    def test_record_writes_current_and_history_and_flags_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = self.manifest(tmp)
            clean = gates.run(write_brief(tmp, BRIEF))
            clean["at"] = "2026-10-12T10:00:00Z"
            gates.record(manifest, clean)
            dirty_brief = json.loads(json.dumps(BRIEF))
            dirty_brief["scenes"][0]["heading"] = "BROKEN *HIGHLIGHT"
            dirty = gates.run(write_brief(tmp, dirty_brief))
            dirty["at"] = "2026-10-12T11:00:00Z"
            gates.record(manifest, dirty)
            stored = json.loads(manifest.read_text())["gates"]
        self.assertEqual(stored["current"]["at"], "2026-10-12T11:00:00Z")
        self.assertEqual([h["at"] for h in stored["history"]], ["2026-10-12T10:00:00Z", "2026-10-12T11:00:00Z"])
        change = stored["changed_since_last_run"]
        self.assertEqual(change["after"]["BL040"], 1)
        self.assertIsNone(change["before"].get("BL040"))
        self.assertEqual(change["before"], {"BL020": 1})  # clean run: only the missing-pack warning

    def test_unchanged_run_adds_no_change_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = self.manifest(tmp)
            report = gates.run(write_brief(tmp, BRIEF))
            report["at"] = "2026-10-12T10:00:00Z"
            first = gates.record(manifest, report)
            second = gates.record(manifest, {**report, "at": "2026-10-12T12:00:00Z"})
        self.assertNotIn("changed_since_last_run", first)
        self.assertNotIn("changed_since_last_run", second)
        self.assertEqual(len(second["history"]), 2)

    def test_history_is_capped(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = self.manifest(tmp)
            report = gates.run(write_brief(tmp, BRIEF))
            for i in range(12):
                stored = gates.record(manifest, {**report, "at": f"run-{i}"})
        self.assertEqual(len(stored["history"]), 10)
        self.assertEqual(stored["current"]["at"], "run-11")


if __name__ == "__main__":
    unittest.main()
