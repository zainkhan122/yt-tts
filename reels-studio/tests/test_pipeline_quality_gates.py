"""Fail-closed contracts for final render QA and voice intelligibility."""
import unittest

from lib.pipeline import require_flow_match, require_qa_checks, require_whisper_match


class PipelineQualityGateTests(unittest.TestCase):
    def test_every_render_check_must_pass(self):
        self.assertTrue(require_qa_checks({"1080x1920": True, "approved_voice": True}))
        with self.assertRaisesRegex(SystemExit, "loudness_-14"):
            require_qa_checks({"1080x1920": True, "loudness_-14": False})

    def test_flow_chunk_below_minimum_blocks_final_alignment(self):
        self.assertTrue(require_flow_match(0.92, 0.92, 0, 1))
        with self.assertRaisesRegex(SystemExit, "chunk 2 matched 91.0%"):
            require_flow_match(0.91, 0.92, 1, 3)

    def test_english_final_voiceover_must_meet_whisper_character_match(self):
        self.assertAlmostEqual(require_whisper_match(95, 100), 0.95)
        with self.assertRaisesRegex(SystemExit, "94.9%.*95%"):
            require_whisper_match(949, 1000)
        with self.assertRaisesRegex(SystemExit, "0.0%"):
            require_whisper_match(0, 0)


if __name__ == "__main__":
    unittest.main()
