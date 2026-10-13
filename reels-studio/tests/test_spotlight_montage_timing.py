"""Montage timing mismatches must block the render rather than pass as a warning."""
import unittest

from templates._spotlight import spotcore


def fixture(cut_at="ports", anchor_time=3.0):
    brief = {"scenes": [{"id": "demo", "type": "clip-montage",
                         "cuts": [{"label": "CUT SIDE PORTS", "at": cut_at}]}]}
    timing = {"demo": {"start": 2.0, "end": 4.0,
                        "words": [["ports", anchor_time, anchor_time + 0.2]]}}
    events = {"demo_cut0": 2.5, "demo_out": 4.0}
    return brief, timing, events


class MontageTimingTests(unittest.TestCase):
    def test_anchor_spoken_during_label_window_passes(self):
        brief, timing, events = fixture()
        self.assertEqual(spotcore.qa_montage(brief, timing, 4.0, events), [])

    def test_anchor_outside_label_window_is_a_hard_render_error(self):
        brief, timing, events = fixture(anchor_time=2.0)
        self.assertTrue(spotcore.qa_montage(brief, timing, 4.0, events))
        with self.assertRaisesRegex(SystemExit, "montage timing QA failed"):
            spotcore.html(brief, timing, 4.0, events, {})


if __name__ == "__main__":
    unittest.main()
