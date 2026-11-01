import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "motion"))
import focus_check as fc  # noqa: E402

KEEP = [[0.068, 0.277], [0.396, 0.604], [0.723, 0.932]]


class FocusCheckTests(unittest.TestCase):
    def scene(self, boxes, say="short line"):
        return {"id": "t", "type": "image", "say": say, "keep_visible": KEEP,
                "focus": [{"box": b, "at": t} for b, t in boxes]}

    def test_cut_label_is_caught(self):
        # the 2026-10-31 failure: a 0.6-wide box that clipped the COMPRESS and RECALL labels
        probs = fc.check_scene(self.scene([([0.25, 0.2, 0.6, 0.7], 0.0), ([0.0, 0.2, 0.6, 0.7], 2.0)]))
        self.assertTrue(any("cuts label" in p for p in probs))

    def test_whole_label_pan_passes(self):
        probs = fc.check_scene(self.scene([([0.0, 0.1, 0.72, 0.8], 0.0), ([0.28, 0.1, 0.72, 0.8], 2.0)]))
        self.assertEqual(probs, [])

    def test_static_scene_is_caught(self):
        long_line = " ".join(["word"] * 20)  # about 8 s at the estimate
        probs = fc.check_scene(self.scene([([0, 0, 1, 1], 0.0)], say=long_line))
        self.assertTrue(any("static" in p for p in probs))


if __name__ == "__main__":
    unittest.main()
