"""reference_teardown: pure helpers + pipeline wiring (no network, no ffmpeg in tests)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import preflight  # noqa: E402
import reference_teardown as rt  # noqa: E402


class NgramDistanceTests(unittest.TestCase):
    def test_shared_five_grams_catches_borrowed_lines(self):
        ours = "This player strips YouTube Music down to just the music and runs anywhere"
        theirs = "It strips YouTube Music down to just the music, no ads, no account"
        self.assertIn("strips youtube music down to", rt.shared_ngrams(ours, theirs))

    def test_own_words_share_nothing(self):
        ours = "Your music app shows you ads. This one has none to hide."
        theirs = "It runs locally on your own hardware without email or signup"
        self.assertEqual(rt.shared_ngrams(ours, theirs), [])

    def test_reference_dir_naming(self):
        self.assertEqual(rt.reference_dir("tiktok", "github.signals", "123").name,
                         "tiktok-github.signals-123")


class PreflightWiringTests(unittest.TestCase):
    def test_no_inspiration_means_no_advisory(self):
        self.assertEqual(preflight.check_reference_advisories("x-01", {"id": "x-01"}), [])

    def test_missing_teardown_is_a_note(self):
        brief = {"id": "x-01", "inspiration": {"platform": "tiktok", "source": "nobody", "post_id": "0"}}
        res = preflight.check_reference_advisories("x-01", brief)
        self.assertEqual(res[0]["status"], "NOTE")
        self.assertIn("teardown not run", res[0]["detail"])

    def test_overlap_note_mentions_shared_phrase(self):
        with tempfile.TemporaryDirectory() as td:
            ref = Path(td)
            (ref / "manifest.json").write_text(json.dumps({
                "outlier_multiple": 3.5,
                "transcript": "no ads no account and no subscription at all"}))
            orig = rt.REFS
            try:
                rt.REFS = Path(td).parent
                brief = {"id": "x-01", "hook": "No ads no account and no subscription, ever.",
                         "inspiration": {"platform": "tiktok", "source": "s", "post_id": "1"}}
                (Path(td).parent / "tiktok-s-1").mkdir(exist_ok=True)
                (Path(td).parent / "tiktok-s-1" / "manifest.json").write_text(json.dumps({
                    "outlier_multiple": 3.5,
                    "transcript": "no ads no account and no subscription at all"}))
                res = preflight.check_reference_advisories("x-01", brief)
            finally:
                rt.REFS = orig
        self.assertEqual(res[0]["status"], "NOTE")
        self.assertIn("shared 5-gram", res[0]["detail"])


if __name__ == "__main__":
    unittest.main()
