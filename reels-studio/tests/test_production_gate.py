import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reels import preflight_local_render  # noqa: E402
from tools.production_gate import (  # noqa: E402
    ProductionGateError,
    script_sha256,
    script_word_count,
    sha256_bytes,
    validate_receipt,
    verify_capture_assets,
)


class ProductionGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.now = "2026-10-14T12:00:00Z"
        self.brief = {
            "id": "one",
            "lang": "en-us",
            "capture": "captures/cap-one",
            "sources": [{"url": "https://example.com/official", "title": "Official docs"}],
            "scenes": [{"id": "hook", "type": "page", "image": "screen.jpg",
                        "say": "{Model 2|Model two} is a real feature."},
                       {"id": "demo", "type": "image", "image": "screen.jpg"}],
        }
        self.brief_raw = (json.dumps(self.brief, ensure_ascii=False, indent=2) + "\n").encode()
        self.brief_path = self.root / "reels-studio/briefs/one.json"
        self.brief_path.parent.mkdir(parents=True)
        self.brief_path.write_bytes(self.brief_raw)
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
        script_sha = script_sha256(self.brief)
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
            "discover": {"status": "complete", "checked_at": self.now,
                         "evidence": ["reels-studio/research/ideas/feed.md", "reels-studio/research/radar/radar.md"]},
            "select": {"status": "complete", "selection_status": "selected", "topic": "Test topic",
                       "score": 75, "score_breakdown": score_breakdown,
                       "metrics_snapshot_sha256": sha256_bytes(self.snapshot_raw), "basis_post_ids": ["post-one"],
                       "hard_gates": {"risk_flags_clear": True, "claim_verifiable": True, "license_clear": True}},
            "research": {"status": "complete", "evidence": ["reels-studio/briefs/one.json"],
                         "dynamic_facts_checked_at": self.now,
                         "primary_sources": [{"url": "https://example.com/official", "checked_at": self.now, "claim": "The official model capability."}]},
            "script": {"status": "complete", "script_sha256": script_sha, "word_count": 6},
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
                                now=__import__("datetime").datetime.fromisoformat("2026-10-14T12:00:00+00:00"))

    def test_complete_receipt_passes_and_hashes_script(self):
        result = self.validate()
        self.assertEqual(result["briefs"]["one"]["topic_score"], 75)
        self.assertEqual(result["briefs"]["one"]["script_sha256"], script_sha256(self.brief))
        self.assertEqual(script_word_count(self.brief), 6)

    def test_discovery_must_have_a_fresh_timezone_aware_timestamp(self):
        discover = self.receipt["briefs"]["one"]["stages"]["discover"]
        del discover["checked_at"]
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "DISCOVER evidence timestamp is missing"):
            self.validate()
        discover["checked_at"] = "2026-10-12T23:59:59Z"  # just over the 36-hour limit
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "DISCOVER evidence is stale"):
            self.validate()
        discover["checked_at"] = "not-a-timezone"
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "timestamp is invalid"):
            self.validate()

    def test_script_word_count_must_match_spoken_form_not_display_markup(self):
        brief = {"scenes": [{"id": "hook", "say": "A {8,000|eight thousand} token window. 🚀"}]}
        self.assertEqual(script_word_count(brief), 5)
        self.receipt["briefs"]["one"]["stages"]["script"]["word_count"] = 9
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "word_count must equal the 6 spoken words"):
            self.validate()
        self.receipt["briefs"]["one"]["stages"]["script"]["word_count"] = True
        self.receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        with self.assertRaisesRegex(ProductionGateError, "word_count must equal the 6 spoken words"):
            self.validate()

    def test_local_full_render_requires_receipt_while_preview_does_not(self):
        with self.assertRaisesRegex(SystemExit, "require --receipt"):
            preflight_local_render(["briefs/one.json"], "", repo_root=self.root)
        self.assertIsNone(preflight_local_render(["briefs/one.json"], "", no_render=True, repo_root=self.root))
        with patch("tools.production_gate.validate_receipt", return_value={"ok": True}) as validate:
            preflight_local_render(["briefs/one.json"], "reels-studio/research/production/receipts/daily.json",
                                   repo_root=self.root)
        validate.assert_called_once_with(self.root, "reels-studio/research/production/receipts/daily.json",
                                         ["one"], verify_assets=True)

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

    def test_receipt_path_traversal_is_rejected(self):
        with self.assertRaisesRegex(ProductionGateError, "must be under"):
            validate_receipt(self.root, "../daily.json", ["one"])


if __name__ == "__main__":
    unittest.main()
