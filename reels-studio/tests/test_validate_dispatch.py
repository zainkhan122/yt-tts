import csv
import datetime
import hashlib
import json
import os
import sys
import io
import tempfile
import unittest
from pathlib import Path

SPARSE_CHECKOUT_SKIP = not Path(__file__).resolve().parent.parent.parent.joinpath('.github/workflows').exists()
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.production_gate import script_sha256, sha256_bytes  # noqa: E402
from tools import validate_dispatch  # noqa: E402
from tools.validate_dispatch import plan_dispatch  # noqa: E402


RENDER_FILES = (
    ".github/workflows/render.yml",
    "reels-studio/reels.py",
    "reels-studio/lib/pipeline.py",
    "reels-studio/lib/scenes.py",
    "reels-studio/lib/framecheck.py",
    "reels-studio/lib/synth.py",
    "reels-studio/lib/gates.py",
    "reels-studio/config/channel.json",
    "reels-studio/cloud/setup-render.sh",
    "reels-studio/setup/setup-whisper.sh",
    "reels-studio/setup/setup-sandbox.sh",
    "reels-studio/tools/capture_store.py",
    "reels-studio/tools/seo_pack.py",
    "reels-studio/tools/production_gate.py",
    "reels-studio/tools/publish_verified_batch.py",
    "reels-studio/brand/voice/michael-ref.wav",
)


class DispatchPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.briefs = self.repo / "reels-studio/briefs"
        self.briefs.mkdir(parents=True)
        self.now = datetime.datetime(2026, 10, 14, 12, 0, tzinfo=datetime.timezone.utc)
        for rel in RENDER_FILES:
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(rel.encode())
        (self.repo / "reels-studio/templates/_base").mkdir(parents=True)
        (self.repo / "reels-studio/templates/_base/base.js").write_text("template", encoding="utf-8")
        (self.repo / "reels-studio/research/ideas").mkdir(parents=True)
        (self.repo / "reels-studio/research/ideas/feed.md").write_text("discovery evidence", encoding="utf-8")
        (self.repo / "reels-studio/research/radar").mkdir(parents=True)
        (self.repo / "reels-studio/research/radar/radar.md").write_text("radar evidence", encoding="utf-8")
        (self.repo / "reels-studio/topics").mkdir(parents=True)
        with (self.repo / "reels-studio/topics/backlog.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["video_id", "topic", "score", "status"])
            w.writeheader()
            w.writerow({"video_id": "one", "topic": "Test topic", "score": "75", "status": "selected"})
        (self.repo / "reels-studio/tracker").mkdir(parents=True)
        self.brief = {"id": "one", "lang": "en-us", "capture": "captures/cap-one",
                      "sources": [{"url": "https://example.com/official"}],
                      "scenes": [{"id": "hook", "say": "A real feature has a measurable result."}]}
        self.brief_path = self.briefs / "one.json"
        self._write_brief()
        self._write_receipt()

    def _write_brief(self):
        self.brief_raw = (json.dumps(self.brief, ensure_ascii=False, indent=2) + "\n").encode()
        self.brief_path.write_bytes(self.brief_raw)

    def _write_receipt(self, *, score=75, stage_status="complete"):
        snapshot = {"schema_version": 1, "fetched_at": "2026-10-14T11:00:00Z", "complete": True,
                    "metrics_coverage_ok": True, "video_post_count": 1, "missing_expected_post_ids": [],
                    "coverage_by_platform": {"youtube": {"total_video_posts": 1, "metrics_available_posts": 1, "fresh_metric_posts": 1}},
                    "posts": {"post-1": {"post_id": "post-1", "metrics": [{"type": "views", "value": 10}]}}}
        snapshot_raw = (json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
        (self.repo / "reels-studio/tracker/buffer-insights.json").write_bytes(snapshot_raw)
        breakdown = {"trend_velocity": 20, "demo_ability": 15, "audience_breadth": 12,
                     "social_proof_gap": 10, "free_value": 8, "freshness_angle": 10}
        breakdown["freshness_angle"] += score - sum(breakdown.values())
        decisions = {"topic": "Use stronger topic clusters from the per-channel median.",
                     "script": "Use a direct problem-led opening in the first line.",
                     "voice": "Retain approved voice; metrics do not isolate voice effects.",
                     "visual": "Keep proof visible in the first frame and cover."}
        stages = {
            "discover": {"status": stage_status, "checked_at": self.now.isoformat(),
                         "evidence": ["reels-studio/research/ideas/feed.md", "reels-studio/research/radar/radar.md"]},
            "select": {"status": stage_status, "selection_status": "selected", "topic": "Test topic",
                       "score": score, "score_breakdown": breakdown,
                       "metrics_snapshot_sha256": sha256_bytes(snapshot_raw), "basis_post_ids": ["post-1"],
                       "hard_gates": {"risk_flags_clear": True, "claim_verifiable": True, "license_clear": True}},
            "research": {"status": stage_status, "evidence": ["reels-studio/briefs/one.json"],
                         "dynamic_facts_checked_at": self.now.isoformat(),
                         "primary_sources": [{"url": "https://example.com/official", "checked_at": self.now.isoformat(), "claim": "Official feature claim."}]},
            "script": {"status": stage_status, "script_sha256": script_sha256(self.brief), "word_count": 7},
            "voice": {"status": stage_status, "engine": "chatterbox", "profile": "option-3", "qa_thresholds": {"per_chunk": 0.92, "overall": 0.95}},
            "assets": {"status": stage_status, "capture_id": "cap-one", "manifest_sha256": "a" * 64,
                       "files": [{"path": "screen.jpg", "sha256": "b" * 64}],
                       "rights_checked": True, "approval_constraints_checked": True},
        }
        receipt = {"schema_version": 1, "batch_id": "daily", "created_at": self.now.isoformat(),
                   "buffer_insights": {"path": "reels-studio/tracker/buffer-insights.json", "sha256": sha256_bytes(snapshot_raw)},
                   "metrics_review": {"snapshot_sha256": sha256_bytes(snapshot_raw), "reviewed_video_count": 1,
                                      "sample_post_ids": ["post-1"], "findings": ["Product demos exceed channel median for views."],
                                      "decisions": decisions},
                   "briefs": {"one": {"brief_sha256": hashlib.sha256(self.brief_raw).hexdigest(),
                                       "stages": stages, "metrics_decisions": decisions}}}
        path = self.repo / "reels-studio/research/production/receipts/daily.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, raw="one", **kwargs):
        return plan_dispatch(raw, briefs_root=self.briefs, repo_root=self.repo, now=self.now,
                             today=datetime.date(2026, 10, 14), production_receipt="reels-studio/research/production/receipts/daily.json", **kwargs)

    def test_valid_inputs_are_normalized_and_date_tag_is_deterministic(self):
        result = self.plan("briefs/one.json", quality="looks", crf="23")
        self.assertEqual(result["briefs"], ["one"])
        self.assertEqual(result["tag"], "renders-2026-10-14")
        self.assertEqual(result["crf"], 23)
        self.assertEqual(len(result["attempts"]), 1)

    def test_implicit_daily_tag_uses_asia_karachi_calendar_date(self):
        result = plan_dispatch("one", briefs_root=self.briefs, repo_root=self.repo, now=self.now,
                               production_receipt="reels-studio/research/production/receipts/daily.json",
                               today=datetime.date(2026, 10, 14))
        self.assertEqual(result["tag"], "renders-2026-10-14")

    def test_unknown_or_mismatched_brief_fails_before_dispatch(self):
        with self.assertRaisesRegex(ValueError, "unknown brief"):
            self.plan("missing")
        (self.briefs / "wrong.json").write_text(json.dumps({"id": "not-wrong"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ID mismatch"):
            self.plan("wrong")

    def test_duplicate_unsafe_or_oversized_batch_fails(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.plan("one one")
        with self.assertRaisesRegex(ValueError, "brief input"):
            self.plan("../one")
        with self.assertRaisesRegex(ValueError, "daily cap"):
            self.plan(" ".join(f"short-{i}" for i in range(11)))

    def test_invalid_quality_crf_and_tag_fail(self):
        with self.assertRaisesRegex(ValueError, "quality"):
            self.plan(quality="ultra")
        with self.assertRaisesRegex(ValueError, "CRF"):
            self.plan(crf="not-a-number")
        with self.assertRaisesRegex(ValueError, "CRF"):
            self.plan(crf=52)
        with self.assertRaisesRegex(ValueError, "invalid tag"):
            self.plan(tag="refs/heads/main")

    def test_new_render_requires_receipt_and_scene_rebuild_remains_available(self):
        with self.assertRaisesRegex(ValueError, "require a production receipt"):
            plan_dispatch("one", briefs_root=self.briefs, repo_root=self.repo)
        result = plan_dispatch("one", briefs_root=self.briefs, repo_root=self.repo,
                               rebuild_scenes="hook", rebuild_reason="fix scene label", from_tag="renders-2026-10-10")
        self.assertEqual(result["rebuild_scenes"], ["hook"])

    def test_scene_rebuild_requires_valid_unique_scene_ids_and_reason(self):
        with self.assertRaisesRegex(ValueError, "non-empty rebuild reason"):
            self.plan(rebuild_scenes="hook")
        with self.assertRaisesRegex(ValueError, "unknown scene"):
            self.plan(rebuild_scenes="not-a-scene", rebuild_reason="typo fix")
        with self.assertRaisesRegex(ValueError, "safe and unique"):
            self.plan(rebuild_scenes="hook hook", rebuild_reason="typo fix")
        result = self.plan(rebuild_scenes="hook", rebuild_reason="fix labels", from_tag="renders-2026-10-10")
        self.assertEqual(result["rebuild_scenes"], ["hook"])

    def test_receipt_with_unfinished_stage_is_rejected(self):
        self._write_receipt(stage_status="pending")
        with self.assertRaisesRegex(ValueError, "is not complete"):
            self.plan()

    def test_selection_must_be_explicit_not_scored(self):
        # Topic score and backlog rules were retired 31 Oct 2026 (pipeline plan, decision 6):
        # a low number on the receipt no longer blocks a pick. An explicit selection still does.
        self._write_receipt(score=59)
        self.plan()

    def test_workflow_entry_rejects_non_main_branch_before_remote_access(self):
        env = {"GITHUB_ACTIONS": "true", "GITHUB_REF": "refs/heads/feature", "BRIEFS": "one"}
        stderr = io.StringIO()
        with patch.dict(os.environ, env, clear=False), patch.object(validate_dispatch.render_attempts, "check_remote") as check:
            with redirect_stderr(stderr):
                code = validate_dispatch.main()
        self.assertEqual(code, 2)
        self.assertIn("protected main branch", stderr.getvalue())
        check.assert_not_called()

    @unittest.skipIf(SPARSE_CHECKOUT_SKIP, 'workflow files not in sparse checkout')
    def test_render_plan_sparse_checkout_includes_validator_and_its_imports(self):
        workflow = (ROOT.parent / ".github/workflows/render.yml").read_text(encoding="utf-8")
        plan_checkout = workflow.split("name: Six-stage / score / Insights / duplicate-render plan", 1)[0]
        for path in ("/reels-studio/tools/validate_dispatch.py",
                     "/reels-studio/tools/production_gate.py",
                     "/reels-studio/tools/render_attempts.py",
                     "/reels-studio/tools/gh_actions.py",
                     "/reels-studio/lib/"):
            with self.subTest(path=path):
                self.assertIn(path, plan_checkout)

    @unittest.skipIf(SPARSE_CHECKOUT_SKIP, 'workflow files not in sparse checkout')
    def test_workflow_entry_checks_and_reserves_only_when_requested(self):
        fake_plan = {"briefs": ["one"], "tag": "renders-2026-10-14", "attempts": [{"fingerprint": "a" * 64}]}
        env = {"GITHUB_ACTIONS": "true", "GITHUB_REF": "refs/heads/main", "BRIEFS": "one",
               "QUALITY": "looks", "CRF": "23", "RECORD_ATTEMPT": "true", "GITHUB_RUN_ID": "123"}
        stdout = io.StringIO()
        with patch.dict(os.environ, env, clear=False), \
             patch.object(validate_dispatch, "plan_dispatch", return_value=fake_plan), \
             patch.object(validate_dispatch.render_attempts, "check_remote") as check, \
             patch.object(validate_dispatch.render_attempts, "reserve_remote") as reserve, \
             redirect_stdout(stdout):
            code = validate_dispatch.main()
        self.assertEqual(code, 0)
        check.assert_called_once_with(fake_plan["attempts"])
        reserve.assert_called_once_with(fake_plan["attempts"], "123")
        self.assertIn('briefs=["one"]', stdout.getvalue())
        self.assertIn("attempt_fingerprints=", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
