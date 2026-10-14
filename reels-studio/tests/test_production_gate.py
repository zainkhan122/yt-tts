import csv
import datetime as dt
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reels import preflight_local_render  # noqa: E402
from tools.production_gate import (  # noqa: E402
    ProductionGateError,
    main as production_gate_main,
    script_sha256,
    script_word_count,
    sha256_bytes,
    validate_receipt,
    verify_assets_for_brief,
    verify_capture_assets,
)


class ProductionGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.now_dt = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        self.now = self.now_dt.isoformat().replace("+00:00", "Z")
        self.brief = {
            "id": "one",
            "template": "production-gate-test",
            "lang": "en-us",
            "capture": "captures/cap-one",
            "sources": [{"url": "https://example.com/official", "title": "Official docs"}],
            "scenes": [{"id": "hook", "say": "{Model 2|Model two} is a real feature."}],
        }
        self.brief_raw = (json.dumps(self.brief, ensure_ascii=False, indent=2) + "\n").encode()
        self.brief_path = self.root / "reels-studio/briefs/one.json"
        self.brief_path.parent.mkdir(parents=True)
        self.brief_path.write_bytes(self.brief_raw)
        template_path = self.root / "reels-studio/templates/production-gate-test/template.py"
        template_path.parent.mkdir(parents=True)
        template_path.write_text(
            "def segments(brief):\n"
            "    return [{'id': scene['id'], 'text': scene.get('say', '')} for scene in brief['scenes']]\n",
            encoding="utf-8",
        )
        config_path = self.root / "reels-studio/config/channel.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(json.dumps({"lang": "en-us", "tts": {"engine": "chatterbox", "min_match": 0.92,
                                                                        "max_retries": 2}}), encoding="utf-8")
        (self.root / "reels-studio/research/ideas").mkdir(parents=True)
        (self.root / "reels-studio/research/ideas/feed.md").write_text("verified discovery", encoding="utf-8")
        (self.root / "reels-studio/research/radar").mkdir(parents=True)
        (self.root / "reels-studio/research/radar/radar.md").write_text("fresh radar", encoding="utf-8")
        (self.root / "reels-studio/topics").mkdir(parents=True)
        with (self.root / "reels-studio/topics/backlog.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["video_id", "topic", "score", "status"])
            w.writeheader()
            w.writerow({"video_id": "one", "topic": "Test topic", "score": "75", "status": "selected"})
        self.snapshot = {
            "schema_version": 1,
            "source": "Buffer GraphQL Post.metrics (read-only)",
            "fetched_at": self.now,
            "complete": True,
            "metrics_coverage_ok": True,
            "video_post_count": 1,
            "missing_expected_post_ids": [],
            "coverage_by_platform": {"youtube": {"total_video_posts": 1, "metrics_available_posts": 1, "fresh_metric_posts": 1}},
            "posts": {"post-one": {"post_id": "post-one", "metrics": [{"type": "views", "value": 100}] }},
        }
        self.snapshot_raw = (json.dumps(self.snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
        self.snapshot_path = self.root / "reels-studio/tracker/buffer-insights.json"
        self.snapshot_path.parent.mkdir(parents=True)
        self.snapshot_path.write_bytes(self.snapshot_raw)
        brief_sha = hashlib.sha256(self.brief_raw).hexdigest()
        script_sha = script_sha256(self.brief, self.root)
        script_words = script_word_count(self.brief, self.root)
        score_breakdown = {
            "trend_velocity": 20,
            "demo_ability": 15,
            "audience_breadth": 12,
            "social_proof_gap": 10,
            "free_value": 8,
            "freshness_angle": 10,
        }
        asset_hash = "a" * 64
        stage = {
            "discover": {"status": "complete", "evidence": ["reels-studio/research/ideas/feed.md", "reels-studio/research/radar/radar.md"]},
            "select": {"status": "complete", "selection_status": "selected", "topic": "Test topic",
                       "score": 75, "score_breakdown": score_breakdown,
                       "metrics_snapshot_sha256": sha256_bytes(self.snapshot_raw), "basis_post_ids": ["post-one"],
                       "hard_gates": {"risk_flags_clear": True, "claim_verifiable": True, "license_clear": True}},
            "research": {"status": "complete", "evidence": ["reels-studio/briefs/one.json"],
                         "dynamic_facts_checked_at": self.now,
                         "primary_sources": [{"url": "https://example.com/official", "checked_at": self.now, "claim": "The official model capability."}]},
            "script": {"status": "complete", "script_sha256": script_sha, "word_count": script_words},
            "voice": {"status": "complete", "engine": "chatterbox", "profile": "option-3", "qa_thresholds": {"per_chunk": 0.92, "overall": 0.95}},
            "assets": {"status": "complete", "capture_id": "cap-one", "manifest_sha256": asset_hash,
                       "files": [{"path": "screen.jpg", "sha256": "b" * 64}],
                       "rights_checked": True, "approval_constraints_checked": True},
        }
        decisions = {"topic": "Prioritize concepts that beat the platform median.",
                     "script": "Use the stronger first-three-second hook pattern.",
                     "voice": "Keep Option 3; no post metric isolates voice.",
                     "visual": "Use a clear first-frame proof, not a metric-only inference."}
        self.receipt = {
            "schema_version": 1,
            "batch_id": "daily",
            "created_at": self.now,
            "buffer_insights": {"path": "reels-studio/tracker/buffer-insights.json", "sha256": sha256_bytes(self.snapshot_raw)},
            "metrics_review": {"snapshot_sha256": sha256_bytes(self.snapshot_raw), "reviewed_video_count": 1,
                               "sample_post_ids": ["post-one"], "findings": ["YouTube views are strongest on the product-demo posts."],
                               "decisions": decisions},
            "briefs": {"one": {"brief_sha256": brief_sha, "stages": stage, "metrics_decisions": decisions}},
        }
        self.receipt_path = self.root / "reels-studio/research/production/receipts/daily.json"
        self.receipt_path.parent.mkdir(parents=True)
        self.receipt_path.write_text(json.dumps(self.receipt, indent=2), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def validate(self):
        return validate_receipt(self.root, "reels-studio/research/production/receipts/daily.json", ["one"],
                                now=self.now_dt)

    def test_complete_receipt_passes_and_hashes_script(self):
        result = self.validate()
        self.assertEqual(result["briefs"]["one"]["topic_score"], 75)
        self.assertEqual(result["briefs"]["one"]["script_sha256"], script_sha256(self.brief, self.root))

    def test_local_full_render_requires_receipt_while_preview_does_not(self):
        with self.assertRaisesRegex(SystemExit, "requires --production-receipt"):
            preflight_local_render(["briefs/one.json"], "", repo_root=self.root)
        self.assertIsNone(preflight_local_render(["briefs/one.json"], "", no_render=True, repo_root=self.root))
        self.assertIsNone(preflight_local_render(["briefs/one.json"], "", scene_rebuild=True, repo_root=self.root))
        receipt_path = "reels-studio/research/production/receipts/daily.json"
        stage = self.receipt["briefs"]["one"]["stages"]["assets"]
        validation = {
            "receipt_sha256": hashlib.sha256(self.receipt_path.read_bytes()).hexdigest(),
            "briefs": {"one": {"brief_sha256": hashlib.sha256(self.brief_raw).hexdigest()}},
        }
        with patch("tools.production_gate.validate_receipt", return_value=validation) as validate:
            with patch("tools.production_gate.verify_capture_assets", return_value={"ok": True}) as verify:
                preflight_local_render(["briefs/one.json"], receipt_path, repo_root=self.root)
        validate.assert_called_once_with(self.root, receipt_path, ["one"], verify_assets=False)
        verify.assert_called_once_with(self.root, "one", self.brief, stage)

    def test_missing_stage_fails_closed(self):
        del self.receipt["briefs"]["one"]["stages"]["assets"]
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "exactly the six"):
            self.validate()

    def test_score_below_60_or_mismatched_breakdown_fails(self):
        self.receipt["briefs"]["one"]["stages"]["select"]["score"] = 59
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "topic score must be an integer from 60"):
            self.validate()
        self.receipt["briefs"]["one"]["stages"]["select"]["score"] = 75
        self.receipt["briefs"]["one"]["stages"]["select"]["score_breakdown"]["freshness_angle"] = 9
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "does not equal"):
            self.validate()

    def test_stale_or_incomplete_buffer_snapshot_fails(self):
        self.snapshot["complete"] = False
        new_raw = (json.dumps(self.snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
        self.snapshot_path.write_bytes(new_raw)
        self.receipt["buffer_insights"]["sha256"] = sha256_bytes(new_raw)
        self.receipt["metrics_review"]["snapshot_sha256"] = sha256_bytes(new_raw)
        self.receipt["briefs"]["one"]["stages"]["select"]["metrics_snapshot_sha256"] = sha256_bytes(new_raw)
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "incomplete"):
            self.validate()

    def test_script_mutation_after_receipt_fails(self):
        self.brief["scenes"][0]["say"] += " Changed."
        self.brief_path.write_text(json.dumps(self.brief), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "brief changed"):
            self.validate()

    def test_current_spoken_word_count_must_match_receipt(self):
        self.brief["scenes"][0]["say"] += " Two extra words."
        new_raw = (json.dumps(self.brief, ensure_ascii=False, indent=2) + "\n").encode()
        self.brief_path.write_bytes(new_raw)
        self.receipt["briefs"]["one"]["brief_sha256"] = hashlib.sha256(new_raw).hexdigest()
        script = self.receipt["briefs"]["one"]["stages"]["script"]
        script["script_sha256"] = script_sha256(self.brief, self.root)
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "does not match current spoken text"):
            self.validate()

    def test_backlog_score_must_match(self):
        path = self.root / "reels-studio/topics/backlog.csv"
        path.write_text("video_id,topic,score,status\none,Test topic,59,selected\n", encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "does not match"):
            self.validate()

    def test_missing_metrics_decision_fails(self):
        del self.receipt["briefs"]["one"]["metrics_decisions"]["voice"]
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "voice"):
            self.validate()

    def test_english_whisper_qa_cannot_be_disabled_by_brief(self):
        self.brief["whisper_qa"] = False
        self.brief_raw = (json.dumps(self.brief, ensure_ascii=False, indent=2) + "\n").encode()
        self.brief_path.write_bytes(self.brief_raw)
        self.receipt["briefs"]["one"]["brief_sha256"] = hashlib.sha256(self.brief_raw).hexdigest()
        self.receipt_path.write_text(json.dumps(self.receipt, indent=2), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "Whisper TTS QA cannot be disabled"):
            self.validate()

    def test_runtime_tts_configuration_cannot_bypass_voice_floors_or_approved_engine(self):
        config_path = self.root / "reels-studio/config/channel.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["tts"]["min_match"] = 0.91
        config_path.write_text(json.dumps(config), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "runtime TTS min_match cannot be below 92%"):
            self.validate()
        config["tts"]["min_match"] = 0.92
        config["tts"]["max_retries"] = 5
        config_path.write_text(json.dumps(config), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "max_retries must be an integer"):
            self.validate()
        config["tts"]["max_retries"] = 2
        config["tts"]["engine"] = "kokoro"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "approved Chatterbox engine"):
            self.validate()

    def test_voice_thresholds_reject_nonfinite_and_above_one(self):
        thresholds = self.receipt["briefs"]["one"]["stages"]["voice"]["qa_thresholds"]
        thresholds["per_chunk"] = float("nan")
        self.receipt_path.write_text(json.dumps(self.receipt, indent=2), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "per-chunk threshold must be finite"):
            self.validate()
        thresholds["per_chunk"] = 0.92
        thresholds["overall"] = float("inf")
        self.receipt_path.write_text(json.dumps(self.receipt, indent=2), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "overall threshold must be finite"):
            self.validate()
        thresholds["overall"] = 1.01
        self.receipt_path.write_text(json.dumps(self.receipt, indent=2), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "overall threshold must be finite"):
            self.validate()

    def test_capture_pack_and_every_file_hash_are_verified(self):
        cap = self.root / "reels-studio/captures/cap-one"
        cap.mkdir(parents=True)
        img = cap / "screen.jpg"
        img.write_bytes(b"valid-image-bytes")
        manifest = {"id": "cap-one", "files": {"screenshot": {"file": "screen.jpg", "kind": "own capture"}}}
        raw = (json.dumps(manifest, indent=1) + "\n").encode()
        (cap / "manifest.json").write_bytes(raw)
        stage = self.receipt["briefs"]["one"]["stages"]["assets"]
        stage["manifest_sha256"] = sha256_bytes(raw)
        stage["files"][0]["sha256"] = hashlib.sha256(img.read_bytes()).hexdigest()
        result = verify_capture_assets(self.root, "one", self.brief, stage)
        self.assertEqual(result["verified_files"], 1)
        img.write_bytes(b"changed")
        with self.assertRaisesRegex(ProductionGateError, "digest mismatch"):
            verify_capture_assets(self.root, "one", self.brief, stage)

    def test_matrix_assets_preflight_checks_full_batch_and_local_pack(self):
        cap = self.root / "reels-studio/captures/cap-one"
        cap.mkdir(parents=True)
        img = cap / "screen.jpg"
        img.write_bytes(b"matrix capture bytes")
        manifest = {"id": "cap-one", "files": {"screenshot": {"file": "screen.jpg", "kind": "own capture"}}}
        raw = (json.dumps(manifest, indent=1) + "\n").encode()
        (cap / "manifest.json").write_bytes(raw)
        stage = self.receipt["briefs"]["one"]["stages"]["assets"]
        stage["manifest_sha256"] = sha256_bytes(raw)
        stage["files"] = [{"path": "screen.jpg", "sha256": hashlib.sha256(img.read_bytes()).hexdigest()}]
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        result = verify_assets_for_brief(
            self.root,
            "reels-studio/research/production/receipts/daily.json",
            ["one"],
            "one",
            now=self.now_dt,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["brief"]["verified_files"], 1)
        stdout = io.StringIO()
        with patch("tools.production_gate.REPO_ROOT", self.root), redirect_stdout(stdout):
            exit_code = production_gate_main([
                "assets-for",
                "reels-studio/research/production/receipts/daily.json",
                '["one"]',
                "one",
            ])
        self.assertEqual(exit_code, 0)
        self.assertTrue(json.loads(stdout.getvalue())["ok"])

    def test_receipt_path_traversal_is_rejected(self):
        with self.assertRaisesRegex(ProductionGateError, "must be under"):
            validate_receipt(self.root, "../daily.json", ["one"])


if __name__ == "__main__":
    unittest.main()
