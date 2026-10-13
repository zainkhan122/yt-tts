"""Post-kit voice metadata must name the renderer, not Chatterbox's reference voice."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.pipeline import voice_disclosure  # noqa: E402


class VoiceDisclosureTests(unittest.TestCase):
    def test_chatterbox_final_is_not_mislabeled_as_kokoro(self):
        line = voice_disclosure("am_michael", "chatterbox")
        self.assertIn("Chatterbox", line)
        self.assertIn("Option-3", line)
        self.assertIn("reference only", line)
        self.assertNotIn("Kokoro TTS `am_michael`", line)

    def test_kokoro_preview_is_marked_preview_only(self):
        line = voice_disclosure("am_michael", "kokoro-preview")
        self.assertIn("Kokoro TTS `am_michael`", line)
        self.assertIn("preview only", line)
        self.assertIn("not approved for final media", line)

    def test_legacy_kokoro_engine_remains_described_as_kokoro(self):
        line = voice_disclosure("am_michael", "kokoro")
        self.assertIn("Kokoro TTS `am_michael`", line)
        self.assertNotIn("Chatterbox", line)

    def test_own_recording_is_not_called_synthetic(self):
        self.assertEqual(voice_disclosure("files", "own recordings"), "- Voice: your own recording.")


if __name__ == "__main__":
    unittest.main()
