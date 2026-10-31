"""Fail-closed contracts for final render QA and voice intelligibility."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.pipeline import (cover_contract_check, hyperframes_failure_message, hyperframes_lint_summary,
                          normalized_match_text, normalize_match_words, parse_markup, require_flow_match,
                          require_hyperframes_lint, require_qa_checks, require_whisper_match,
                          should_run_whisper_qa, verify_chatterbox_snapshot, voice_reuse_proof)


class PipelineQualityGateTests(unittest.TestCase):
    def _voice_fixture(self, temp, *, approve=True, hash_matches=True):
        track = Path(temp) / "voiceover.mp3"
        track.write_bytes(b"published voice track bytes")
        good = "sha256:" + hashlib.sha256(track.read_bytes()).hexdigest()
        manifest = {"audio_sha256": good if hash_matches else "sha256:" + "0" * 64,
                    "qa": {"checks": {"approved_voice": approve}}}
        return manifest, track

    def test_rebuild_voice_is_proven_by_the_reused_published_track(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest, track = self._voice_fixture(temp)
            ok, evidence = voice_reuse_proof(manifest, track)
        self.assertTrue(ok, evidence)
        self.assertTrue(evidence["matches_source"])
        self.assertTrue(evidence["source_qa_approved_voice"])

    def test_rebuild_voice_fails_closed_when_the_track_differs_from_the_published_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest, track = self._voice_fixture(temp, hash_matches=False)
            ok, _ = voice_reuse_proof(manifest, track)
        self.assertFalse(ok)

    def test_rebuild_voice_fails_closed_when_the_source_render_did_not_pass_the_voice_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest, track = self._voice_fixture(temp, approve=False)
            ok, _ = voice_reuse_proof(manifest, track)
        self.assertFalse(ok)

    def test_cover_contract_requires_cover_lab_only_when_the_brief_promised_concepts(self):
        promised = {"treatment": {"archetype": "quest", "cover_concepts": [{"text": "A"}]}}
        legacy = {"id": "x"}
        self.assertEqual(cover_contract_check(promised, {"source": "frame-grab"}), (False, "cover-lab"))
        self.assertEqual(cover_contract_check(promised, {"source": "cover-lab"}), (True, "cover-lab"))
        self.assertEqual(cover_contract_check(legacy, {"source": "frame"}), (True, "legacy-frame-grab"))
        self.assertEqual(cover_contract_check(legacy, {"source": "frame-grab"}), (True, "legacy-frame-grab"))
        self.assertEqual(cover_contract_check(legacy, {"source": "stale"}),(False, "legacy-frame-grab"))

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

    def test_hyperframes_lint_fails_closed_and_exposes_the_diagnostic(self):
        self.assertEqual(hyperframes_lint_summary("0 error(s), 4 warning(s)"), (0, 4))
        self.assertEqual(require_hyperframes_lint(0, "0 error(s), 4 warning(s)", "/tmp/build.log"), (0, 4))
        with self.assertRaises(SystemExit) as caught:
            require_hyperframes_lint(0, "1 error(s), 0 warning(s)" + chr(10) + "layout overflow", "/tmp/build.log")
        self.assertIn("1 error(s), 0 warning(s)", str(caught.exception))
        self.assertIn("layout overflow", str(caught.exception))
        with self.assertRaisesRegex(SystemExit, "exit status 1"):
            require_hyperframes_lint(1, "0 error(s), 0 warning(s)", "/tmp/build.log")
        with self.assertRaisesRegex(SystemExit, "could not parse error/warning summary"):
            require_hyperframes_lint(0, "Unexpected HyperFrames output", "/tmp/build.log")

    def test_browser_check_failure_includes_a_bounded_log_tail(self):
        output = chr(10).join(f"diagnostic {i}" for i in range(100))
        message = hyperframes_failure_message("check", output, "/tmp/build.log", reason="exit status 1", max_lines=3)
        self.assertIn("diagnostic 99", message)
        self.assertIn("diagnostic 98", message)
        self.assertNotIn("diagnostic 0", message)
        self.assertIn("full log: /tmp/build.log", message)

    def test_numeric_pronunciation_alternates_keep_display_and_speech_forms(self):
        display, spoken, _ = parse_markup("{8,000-token|eight-thousand-token}")
        self.assertEqual(display, "8,000-token")
        self.assertEqual(spoken, "eight-thousand-token")

    def test_every_render_check_must_pass(self):
        self.assertTrue(require_qa_checks({"1080x1920": True, "approved_voice": True}))
        with self.assertRaisesRegex(SystemExit, "loudness_-14"):
            require_qa_checks({"1080x1920": True, "loudness_-14": False})

    def test_flow_chunk_below_minimum_blocks_final_alignment(self):
        self.assertTrue(require_flow_match(0.92, 0.92, 0, 1))
        with self.assertRaisesRegex(SystemExit, "chunk 2 matched 91.0%"):
            require_flow_match(0.91, 0.92, 1, 3)
        with self.assertRaisesRegex(SystemExit, "Whisper heard='embedding gemini'"):
            require_flow_match(0.91, 0.92, 1, 3,
                               expected="EmbeddingGemma two", heard="embedding gemini")

    def test_english_final_voiceover_must_meet_whisper_character_match(self):
        self.assertAlmostEqual(require_whisper_match(95, 100), 0.95)
        with self.assertRaisesRegex(SystemExit, "88.9%.*90%.*script words not matched: Qwen, fourteenth"):
            require_whisper_match(889, 1000, diagnostics="script words not matched: Qwen, fourteenth")
        with self.assertRaisesRegex(SystemExit, "0.0%"):
            require_whisper_match(0, 0)


    def test_tts_threshold_cannot_be_weakened_and_retries_are_bounded(self):
        from lib.pipeline import tts_retry_policy
        self.assertEqual(tts_retry_policy({"min_match": 0.90, "max_retries": 2}), (3, 0.90))
        with self.assertRaisesRegex(SystemExit, "cannot be lowered below 85%"):
            tts_retry_policy({"min_match": 0.84, "max_retries": 2})
        with self.assertRaisesRegex(SystemExit, "at most two alternate-seed retries"):
            tts_retry_policy({"min_match": 0.90, "max_retries": 3})
        with self.assertRaisesRegex(SystemExit, "cannot be lowered below 85%"):
            tts_retry_policy({"min_match": float("nan"), "max_retries": 2})
        with self.assertRaisesRegex(SystemExit, "max_retries must be an integer"):
            tts_retry_policy({"min_match": 0.90, "max_retries": 2.5})
        with self.assertRaisesRegex(SystemExit, "cannot be lowered below 85%"):
            require_flow_match(0.99, 0.80, 0, 1)
        with self.assertRaisesRegex(SystemExit, "cannot be lowered below 90%"):
            require_whisper_match(100, 100, threshold=0.89)

    def test_english_whisper_qa_cannot_be_disabled_by_brief(self):
        self.assertTrue(should_run_whisper_qa("en-us", True))
        self.assertFalse(should_run_whisper_qa("es-es", False))
        with self.assertRaisesRegex(SystemExit, "cannot be disabled"):
            should_run_whisper_qa("en-us", False)

    def test_whisper_aligns_spoken_cardinals_ordinals_and_display_numbers_equivalently(self):
        self.assertEqual(normalize_match_words(["October", "fourteenth"]),
                         normalize_match_words(["October", "14th"]))
        self.assertEqual(normalized_match_text(["eight-thousand-token"]),
                         normalized_match_text(["8,000-token"]))
        self.assertEqual(normalized_match_text(["two", "point", "one"]),
                         normalized_match_text(["2.1"]))
        self.assertEqual(normalize_match_words(["twenty-first"]), ["21"])


if __name__ == "__main__":
    unittest.main()
