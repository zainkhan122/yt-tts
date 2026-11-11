import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools import short_qa as q

TH = q.load_thresholds()

GOOD = {
    "id": "repo-demo-tool-01",
    "title": "demo-tool: reads the screen",
    "keywords": ["demo tool"],
    "seo": {"keyword": "demo tool"},
    "capture": "captures/repo-demo-tool-01",
    "scenes": [
        {"id": "hook", "type": "image", "image": "plan-1.jpg", "heading": "DEMO TOOL READS 3 APPS",
         "sub": "open source", "say": "Demo tool reads your apps without guessing from pixels.",
         "focus": [{"box": [0, 0.2, 1, 0.4], "at": 0.0}]},
        {"id": "p1", "type": "page", "say": "It reads the accessibility tree, the same structure screen readers use, so every button, field and menu item has a name the agent can act on.",
         "image": "p1.jpg"},
        {"id": "p2", "type": "image", "image": "p2.jpg", "say": "Every element gets a ref, so it clicks a target instead of a guessed spot on the screen, and it checks the result before it moves on to the next step.",
         "focus": [{"box": [0, 0.3, 1, 0.3], "at": 0.0}]},
        {"id": "p3", "type": "scroll", "say": "It runs on macOS, Windows and Linux with one install, and the same loop works across all three of those systems without any extra setup.",
         "image": "p3.jpg"},
        {"id": "cta", "type": "endcard", "say": "Follow for more, and comment DEMO to get the link."},
    ],
}


def _ffmpeg_ok():
    try:
        q.ffmpeg_exe()
        return True
    except q.MeasureError:
        return False


def ids(results, status="BLOCK"):
    return [r["gate"] for r in results if r["status"] == status]


class PlanGateTests(unittest.TestCase):
    def test_thresholds_file_holds_the_approved_numbers(self):
        self.assertEqual(TH["duration_s"], [29, 55])
        self.assertEqual(TH["speech_wpm"], [167, 211])
        self.assertEqual(TH["longest_pause_s"], 1.2)
        self.assertEqual(TH["graphic_only_share_max"], 0.25)
        self.assertEqual(TH["visual_change_speech_share_min"], 0.75)
        self.assertEqual(TH["hashtags_per_platform"], 5)

    def test_good_brief_passes_every_plan_gate(self):
        self.assertEqual(ids(q.plan_results(GOOD, TH)), [])

    def test_missing_call_to_action_in_last_15_percent_blocks(self):
        b = copy.deepcopy(GOOD)
        b["scenes"][-1]["say"] = "Here is the last thought about the tool and its design."
        self.assertIn("cta_last_15pct", ids(q.plan_results(b, TH)))

    def test_text_card_as_frame_zero_blocks(self):
        b = copy.deepcopy(GOOD)
        b["scenes"][0] = {"id": "hook", "type": "verdict", "say": "Demo tool reads 3 apps for you today."}
        self.assertIn("frame0_media", ids(q.plan_results(b, TH)))

    def test_hook_without_number_or_tool_name_blocks(self):
        b = copy.deepcopy(GOOD)
        b["scenes"][0]["heading"] = "WHAT A DAY"
        b["scenes"][0]["sub"] = "wow"
        b["title"] = "other: thing"
        b["keywords"] = ["ai"]
        b["id"] = "repo-other-01"
        self.assertIn("hook_anchor", ids(q.plan_results(b, TH)))

    def test_long_static_card_blocks(self):
        b = copy.deepcopy(GOOD)
        b["scenes"][2] = {"id": "p2", "type": "image", "image": "p2.jpg",
                          "say": " ".join(["word"] * 40)}  # no focus: a still card for ~13 s
        res = q.plan_results(b, TH)
        self.assertIn("static_scene_len", ids(res))
        self.assertIn("motion_gap", ids(res))

    def test_image_without_focus_is_static_when_rule_says_so(self):
        scene = {"type": "image", "image": "x.jpg", "say": "hi"}
        self.assertFalse(q.is_motion_scene(scene, TH))
        self.assertTrue(q.is_motion_scene({**scene, "focus": [{"box": [0, 0, 1, 1]}]}, TH))

    def test_out_of_range_script_length_blocks(self):
        b = copy.deepcopy(GOOD)
        b["scenes"][1]["say"] = "word " * 300
        self.assertIn("duration_est", ids(q.plan_results(b, TH)))

    def test_empty_brief_blocks(self):
        self.assertEqual(ids(q.plan_results({"scenes": []}, TH)), ["scenes"])


class VideoGateTests(unittest.TestCase):
    def words_for(self, text, start, wpm=186.0):
        out, t = [], start
        step = 60.0 / wpm
        for w in text.split():
            out.append([w, round(t, 3), round(t + step * 0.8, 3)])
            t += step
        return out

    def test_timing_gates_pass_on_a_clean_read(self):
        words = self.words_for("one two three four five six seven eight nine ten. " * 12, 0.05)
        res = q.timing_results([tuple(w) for w in words], duration=40.0, th=TH)
        self.assertEqual(ids(res), [])

    def test_long_pause_and_late_start_block(self):
        words = [("Hook.", 0.9, 1.2), ("next", 3.0, 3.3)]  # starts late, pause 1.8 s
        res = q.timing_results(words, duration=40.0, th=TH)
        self.assertIn("hook_speech_start", ids(res))
        self.assertIn("longest_pause", ids(res))

    def test_no_word_timings_blocks(self):
        self.assertEqual(ids(q.timing_results([], 40.0, TH)), ["speech_timing"])

    def test_picture_gates_on_synthetic_bins(self):
        n = 160  # 40 s at 0.25 s bins
        changed = [True] * n
        speech = [True] * n
        self.assertEqual(ids(q.picture_results(changed, speech, 0.25, TH)), [])
        # visual share on speech is 60%; the floor is 75%, so it must block
        mostly_still = [i < 48 or i >= 112 for i in range(n)]  # 96 of 160 bins = 60%
        self.assertIn("visual_change_speech", ids(q.picture_results(mostly_still, speech, 0.25, TH)))
        # a 5 s still stretch (20 bins) is longer than the 3 s gap
        longest = q.picture_results([True] * 20 + [False] * 20 + [True] * 120, speech, 0.25, TH)
        self.assertIn("motion_gap", ids(longest))

    def test_change_bins_flag_only_real_changes(self):
        frames = np.zeros((9, 4, 4), dtype=np.float32)
        frames[4:] = 200.0  # one hard cut between sample 3 and 4
        flags = q.change_bins(frames, fps=4, bin_s=0.25, threshold=2.0)
        self.assertTrue(flags[4])
        self.assertEqual(sum(flags), 1)

    def test_kit_manifest_loads_from_zip(self):
        import zipfile
        with tempfile.TemporaryDirectory() as d:
            z = Path(d) / "x-kit.zip"
            with zipfile.ZipFile(z, "w") as zf:
                zf.writestr("manifest.json", json.dumps({"scenes": [], "duration": 40}))
                zf.writestr("post.md", "x")
            self.assertEqual(q.load_kit_manifest(z)["duration"], 40)

    @unittest.skipUnless(_ffmpeg_ok(), "ffmpeg not available")
    def test_real_mp4_is_measured_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            mp4 = Path(d) / "t.mp4"
            exe = q.ffmpeg_exe()
            # 6 s: moving test pattern for 3 s, then a frozen colour for 3 s
            cmd = [exe, "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x568:rate=12:duration=3",
                   "-f", "lavfi", "-i", "color=c=gray:size=320x568:rate=12:duration=3",
                   "-filter_complex", "[0][1]concat=n=2:v=1:a=0", "-pix_fmt", "yuv420p", str(mp4)]
            subprocess.run(cmd, check=True)
            frames = q.sample_gray_frames(mp4, fps=4)
            self.assertGreater(len(frames), 20)
            flags = q.change_bins(frames, fps=4, bin_s=0.25, threshold=2.0)
            moving = sum(flags[:10])
            still = sum(flags[14:])
            self.assertGreater(moving, 6)
            self.assertLess(still, 3)

    def test_missing_ffmpeg_is_a_block_not_a_pass(self):
        real = q.shutil.which
        q.shutil.which = lambda name: None
        orig = q.ffmpeg_exe
        def boom():
            raise q.MeasureError("ffmpeg not found")
        q.ffmpeg_exe = boom
        try:
            res, measured = q.video_results(Path("/nope.mp4"), {"scenes": []}, TH)
        finally:
            q.ffmpeg_exe = orig
            q.shutil.which = real
        self.assertEqual(ids(res), ["measure"])
        self.assertEqual(measured, {})


if __name__ == "__main__":
    unittest.main()


class FindingsAdditions4Nov(unittest.TestCase):
    """HOOKS-TTS-METADATA section 5 and FINDINGS 3B: card cap (blocks), familiar-name hook (warns), measures (info)."""

    def _res(self, brief):
        return {r["gate"]: r for r in q.plan_results(brief, TH)}

    def test_good_plan_has_card_rule_passing_and_no_blocks_from_new_rules(self):
        r = self._res(GOOD)
        self.assertEqual(r["card_max_2s"]["status"], "PASS")
        self.assertIn(r["hook_familiar_anchor"]["status"], ("PASS", "WARN"))

    def test_verdict_card_longer_than_two_seconds_blocks(self):
        b = copy.deepcopy(GOOD)
        b["scenes"].insert(1, {"id": "card", "type": "verdict", "say": "Ten words of verdict text here for the card scene now"})
        b["scenes"][1]["say"] = " ".join(["word"] * 40)  # long enough that the card is measured in seconds
        r = self._res(b)
        self.assertEqual(r["card_max_2s"]["status"], "BLOCK")
        self.assertIn("card", r["card_max_2s"]["value"])

    def test_familiar_name_missing_from_hook_only_warns(self):
        b = copy.deepcopy(GOOD)
        b["scenes"][0]["say"] = "A small local helper reads your screen without guessing."
        r = self._res(b)
        self.assertEqual(r["hook_familiar_anchor"]["status"], "WARN")
        # a warning must never block the plan
        self.assertEqual(q.plan_verdict(list(r.values())), "PASS" if all(v["status"] != "BLOCK" for v in r.values()) else "BLOCK")

    def test_familiar_name_in_hook_passes(self):
        b = copy.deepcopy(GOOD)
        b["scenes"][0]["say"] = "Windows users can now have it read their screen without guessing."
        self.assertEqual(self._res(b)["hook_familiar_anchor"]["status"], "PASS")

    def test_timing_measures_are_info_and_never_block(self):
        words = [(f"w{i}", i * 0.4, i * 0.4 + 0.3) for i in range(60)]
        words[10] = ("gap", words[9][2] + 0.5, words[9][2] + 0.8)  # one pause >= 0.35 s
        res = q.timing_results(words, 24.0, TH)
        info = [r for r in res if r["gate"].startswith("measure_")]
        self.assertEqual({r["gate"] for r in info}, {"measure_first3s_wpm", "measure_phrases"})
        self.assertTrue(all(r["status"] == "INFO" for r in info))
        self.assertNotIn("BLOCK", [r["status"] for r in info])
