"""Fail-closed regression for spotlight montage labels and narration anchors."""
import unittest
from templates._spotlight import spotcore

BRIEF = {"scenes": [{"id": "demo", "type": "clip-montage", "cuts": [
    {"label": "PI CASE", "at": "case"},
    {"label": "PATTERN FEATURES", "at": "pattern"},
    {"label": "CUT SIDE PORTS", "at": "ports"},
]}]}
WORDS = [["Pi", .6, .8], ["case", 1.0, 1.2], ["pattern", 5.0, 5.3],
         ["features", 5.4, 5.8], ["cut", 8.0, 8.2], ["side", 8.2, 8.4], ["ports", 8.4, 8.8]]

def timings(words=None):
    return {"demo": {"start": 0.0, "end": 12.0, "words": WORDS if words is None else words}}

def events(cut1=4.92):
    return {"demo_in": 0.0, "demo_out": 12.0, "demo_cut0": 0.0, "demo_cut1": cut1, "demo_cut2": 7.92}

class MontageGuardTests(unittest.TestCase):
    def test_aligned_labels_pass(self):
        self.assertEqual(spotcore.qa_montage(BRIEF, timings(), 12.0, events()), [])

    def test_misaligned_label_blocks_html_render(self):
        with self.assertRaisesRegex(ValueError, r"(?s)render blocked.*PATTERN FEATURES"):
            spotcore.html(BRIEF, timings(), 12.0, events(cut1=5.8), {})

    def test_missing_spoken_anchor_blocks_html_render(self):
        words = [w for w in WORDS if w[0] != "pattern"]
        with self.assertRaisesRegex(ValueError, r"(?s)render blocked.*PATTERN FEATURES"):
            spotcore.html(BRIEF, timings(words), 12.0, events(), {})

if __name__ == "__main__":
    unittest.main()
