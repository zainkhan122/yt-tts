"""Scene manifest + rebuild decision logic (lib/scenes.py).

The boundary these tests pin down: a visual-only edit is rebuildable; any narration
change is not (the audio timeline is reused bit-for-bit from the published MP4).
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from lib import scenes


def manifest():
    return {"scenes": [
        scenes.scene_record(0, "hook", "image", (0.25, 6.4), "one model video and audio",
                            {"id": "hook", "type": "image", "heading": "ONE MODEL"}, [], []),
        scenes.scene_record(1, "changed", "steps", (6.4, 18.2), "what changed in this release",
                            {"id": "changed", "type": "steps", "steps": ["a", "b", "c"]}, [], []),
        scenes.scene_record(2, "cta", "endcard", (18.2, 30.0), "grab it free",
                            {"id": "cta", "type": "endcard"}, [], []),
    ]}


def specs(**overrides):
    base = {
        "hook": {"id": "hook", "type": "image", "heading": "ONE MODEL"},
        "changed": {"id": "changed", "type": "steps", "steps": ["a", "b", "c"]},
        "cta": {"id": "cta", "type": "endcard"},
    }
    base.update(overrides)
    return base


NARRATION = {"hook": "one model video and audio", "changed": "what changed in this release", "cta": "grab it free"}


class DigestTests(unittest.TestCase):
    def test_visual_edit_keeps_narration_digest_and_moves_spec_digest(self):
        before = manifest()["scenes"][1]
        after = specs(changed={"id": "changed", "type": "steps", "steps": ["a", "b"]})["changed"]
        self.assertEqual(scenes.narration_digest(NARRATION["changed"]), before["narration_sha256"])
        self.assertNotEqual(scenes.spec_digest(after), before["spec_sha256"])

    def test_say_markup_does_not_leak_into_the_scene_record(self):
        record = scenes.scene_record(0, "hook", "image", (0, 3), "spoken form",
                                     {"id": "hook", "type": "image", "say": "{LTX 2.5|LTX two point five} is live"}, [], [])
        self.assertEqual(record["narration_sha256"], scenes.narration_digest("spoken form"))
        self.assertIn("say", record)


class PlanRebuildTests(unittest.TestCase):
    def test_visual_only_edit_is_rebuildable_and_auto_included(self):
        plan = scenes.plan_rebuild(manifest(), specs(changed={"id": "changed", "type": "steps", "steps": ["a", "b"]}),
                                   NARRATION, requested=[])
        self.assertTrue(plan["ok"])
        self.assertEqual(plan["effective"], ["changed"])
        self.assertEqual(plan["visual_changes"], ["changed"])

    def test_narration_change_refuses_and_names_the_scenes(self):
        narration = dict(NARRATION, changed="what is new in this release")
        plan = scenes.plan_rebuild(manifest(), specs(), narration, requested=["changed"])
        self.assertFalse(plan["ok"])
        self.assertEqual(plan["reason"], scenes.NARRATION_CHANGED)
        self.assertEqual(plan["scenes"], ["changed"])

    def test_new_scene_in_the_brief_is_a_full_render(self):
        new_specs = specs(extra={"id": "extra", "type": "stat"})
        plan = scenes.plan_rebuild(manifest(), new_specs, {**NARRATION, "extra": "one more number"}, requested=[])
        self.assertFalse(plan["ok"])
        self.assertEqual(plan["reason"], scenes.NARRATION_CHANGED)
        self.assertIn("extra", plan["scenes"])

    def test_unknown_requested_scene_is_refused(self):
        plan = scenes.plan_rebuild(manifest(), specs(), NARRATION, requested=["nope"])
        self.assertFalse(plan["ok"])
        self.assertEqual(plan["reason"], scenes.UNKNOWN_SCENE)
        self.assertEqual(plan["scenes"], ["nope"])

    def test_missing_manifest_refuses_with_its_own_reason(self):
        plan = scenes.plan_rebuild({}, specs(), NARRATION, requested=["hook"])
        self.assertFalse(plan["ok"])
        self.assertEqual(plan["reason"], scenes.PREV_MANIFEST_MISSING)

    def test_no_change_with_an_explicit_request_still_rebuilds_that_scene(self):
        plan = scenes.plan_rebuild(manifest(), specs(), NARRATION, requested=["hook"])
        self.assertTrue(plan["ok"])
        self.assertEqual(plan["effective"], ["hook"])
        self.assertEqual(plan["visual_changes"], [])


class FrameDriftTests(unittest.TestCase):
    def write(self, tmp, name, color, noise=0):
        """Solid patch, optionally with deterministic +-noise (pure PIL: no numpy in the light suites)."""
        w, h = 27, 48
        pixels = bytearray()
        state = 12345
        for _ in range(w * h * 3):
            state = (1103515245 * state + 12345) & 0x7FFFFFFF
            value = color + ((state % (2 * noise + 1)) - noise if noise else 0)
            pixels.append(max(0, min(255, value)))
        Image.frombytes("RGB", (w, h), bytes(pixels)).save(Path(tmp) / name)
        return Path(tmp) / name

    def test_identical_frames_pass_and_shifted_frames_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.write(tmp, "a.png", 120)
            b = self.write(tmp, "b.png", 120)
            c = self.write(tmp, "c.png", 180)
            same = scenes.frame_drift(a, b)
            self.assertTrue(same["match"])
            self.assertEqual(same["mean_abs"], 0.0)
            self.assertTrue(scenes.frames_verdict([same])["ok"])
            moved = scenes.frame_drift(a, c)
            self.assertGreater(moved["mean_abs"], scenes.FRAME_MAD_LIMIT)
            self.assertFalse(scenes.frames_verdict([moved])["ok"])

    def test_encoder_noise_stays_within_the_limit(self):
        # worst case for the metric: a flat patch with uniform +-2 noise (real encoder
        # noise sits on textured frames, where the mean difference is smaller)
        with tempfile.TemporaryDirectory() as tmp:
            a = self.write(tmp, "a.png", 120)
            b = self.write(tmp, "b.png", 120, noise=2)
            drift = scenes.frame_drift(a, b)
            self.assertTrue(scenes.frames_verdict([drift])["ok"])

    def test_size_change_is_reported_not_crashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            big, small = self.write(tmp, "big.png", 10), self.write(tmp, "small.png", 10)
            Image.open(small).resize((14, 24)).save(small)
            drift = scenes.frame_drift(big, small)
            self.assertFalse(drift["match"])
            self.assertFalse(scenes.frames_verdict([drift])["ok"])


class WindowTests(unittest.TestCase):
    def test_samples_skip_rebuilt_scenes(self):
        times = scenes.sample_times(manifest()["scenes"], rebuilt_ids=["changed"])
        self.assertTrue(times)
        self.assertTrue(all(6.4 <= t <= 18.2 for t in times) is False)
        self.assertTrue(all(t < 6.4 or t > 18.2 for t in times))

    def test_duration_verdict_tolerance(self):
        self.assertTrue(scenes.duration_verdict(30.0, 30.02)["ok"])
        self.assertFalse(scenes.duration_verdict(30.0, 30.4)["ok"])


if __name__ == "__main__":
    unittest.main()
