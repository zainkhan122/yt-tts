"""Fail-closed contracts for final render QA and voice intelligibility."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.pipeline import (
    require_flow_match,
    require_lint_gate,
    require_qa_checks,
    require_whisper_match,
    verify_chatterbox_snapshot,
)


class PipelineQualityGateTests(unittest.TestCase):
    def test_pinned_chatterbox_snapshot_verifies_file_size_and_sha256(self):
        data = b"fixture model bytes"
        expected = {"fixture.safetensors": {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}}
        with tempfile.TemporaryDirectory() as temp:
            model_dir = Path(temp)
            model_file = model_dir / "fixture.safetensors"
            model_file.write_bytes(data)
            with patch("lib.pipeline.CHATTERBOX_MODEL_FILE_HASHES", expected):
                self.assertEqual(verify_chatterbox_snapshot(model_dir), {"fixture.safetensors": expected["fixture.safetensors"]["sha256"]})
                model_file.write_bytes(b"altered")
                with self.assertRaisesRegex(SystemExit, "size mismatch"):
                    verify_chatterbox_snapshot(model_dir)
                model_file.write_bytes(b"altered bytes!!!!")
                expected["fixture.safetensors"]["size"] = model_file.stat().st_size
                with self.assertRaisesRegex(SystemExit, "checksum mismatch"):
                    verify_chatterbox_snapshot(model_dir)

    def test_lint_requires_zero_errors_and_a_successful_measurable_report(self):
        self.assertTrue(require_lint_gate(0, 0))
        with self.assertRaisesRegex(SystemExit, "exit=1, errors=0"):
            require_lint_gate(1, 0)
        with self.assertRaisesRegex(SystemExit, "exit=0, errors=2"):
            require_lint_gate(0, 2)
        with self.assertRaisesRegex(SystemExit, "missing or invalid"):
            require_lint_gate(0, None)

    def test_every_render_check_must_pass(self):
        self.assertTrue(require_qa_checks({"1080x1920": True, "approved_voice": True}))
        with self.assertRaisesRegex(SystemExit, "loudness_-14"):
            require_qa_checks({"1080x1920": True, "loudness_-14": False})
        with self.assertRaisesRegex(SystemExit, "no render checks"):
            require_qa_checks({})

    def test_each_tts_chunk_keeps_the_92_percent_floor_and_fails_after_distinct_seeds(self):
        self.assertTrue(require_flow_match(0.92, 0.92, 0, 1))
        # A brief cannot lower the actual floor by setting min_match below 0.92.
        with self.assertRaisesRegex(SystemExit, "chunk 2 matched 91.0%.*after 3 distinct-seed attempt.*minimum is 92%"):
            require_flow_match(0.91, 0.80, 1, 3, expected="Qwen model", heard="queen model")
        # A stricter configured floor is respected.
        with self.assertRaisesRegex(SystemExit, "minimum is 95%"):
            require_flow_match(0.94, 0.95, 0, 2)

    def test_english_final_voiceover_must_meet_the_95_percent_whisper_floor(self):
        self.assertAlmostEqual(require_whisper_match(95, 100), 0.95)
        with self.assertRaisesRegex(SystemExit, "94.9%.*95%.*not matched: Qwen"):
            require_whisper_match(949, 1000, diagnostics="script words not matched: Qwen, fourteenth")
        with self.assertRaisesRegex(SystemExit, "0.0%"):
            require_whisper_match(0, 0)

    def test_nonfinite_or_invalid_qa_values_fail_closed(self):
        with self.assertRaisesRegex(SystemExit, "finite ratios"):
            require_flow_match(float("nan"), 0.92, 0, 1)
        with self.assertRaisesRegex(SystemExit, "invalid match counts"):
            require_whisper_match(101, 100)


if __name__ == "__main__":
    unittest.main()
