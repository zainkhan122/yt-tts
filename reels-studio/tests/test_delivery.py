import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib import delivery  # noqa: E402


class DeliveryVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.brief_id = "sample-short"
        self.render = self.root / "stage" / self.brief_id
        self.render.mkdir(parents=True)
        for name in (f"{self.brief_id}.mp4", *delivery.REQUIRED_FILES[:-1]):
            path = self.render / name
            path.write_bytes(b"x" * (1_000_000 if name.endswith(".mp4") else 32))
        checks = {name: True for name in delivery.CORE_CHECKS}
        checks["approved_voice"] = True
        (self.render / "manifest.json").write_text(json.dumps({
            "id": self.brief_id,
            "qa": {"duration": 30.0, "size_mb": 1.0, "checks": checks},
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_passing_artifact_returns_video_hash_and_metrics(self):
        receipt = delivery.validate_render_dir(self.render, self.brief_id, require_approved_voice=True)
        self.assertEqual(receipt["id"], self.brief_id)
        self.assertEqual(receipt["duration_s"], 30.0)
        self.assertEqual(receipt["qa_passed"], receipt["qa_total"])
        self.assertEqual(len(receipt["mp4_sha256"]), 64)

    def test_failed_or_non_boolean_gate_is_rejected(self):
        manifest_path = self.render / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["qa"]["checks"]["frame0_visible"] = False
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(delivery.DeliveryError, "frame0_visible"):
            delivery.validate_render_dir(self.render, self.brief_id)

    def test_missing_required_sidecar_is_rejected(self):
        (self.render / "seo.md").unlink()
        with self.assertRaisesRegex(delivery.DeliveryError, "seo.md"):
            delivery.validate_render_dir(self.render, self.brief_id)

    def test_wrong_manifest_id_is_rejected(self):
        manifest_path = self.render / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["id"] = "another-short"
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(delivery.DeliveryError, "identity mismatch"):
            delivery.validate_render_dir(self.render, self.brief_id)

    def test_missing_approved_voice_gate_is_rejected_when_required(self):
        manifest_path = self.render / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        del manifest["qa"]["checks"]["approved_voice"]
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(delivery.DeliveryError, "approved-voice"):
            delivery.validate_render_dir(self.render, self.brief_id, require_approved_voice=True)

    def test_duplicate_and_unsafe_ids_are_rejected(self):
        with self.assertRaisesRegex(delivery.DeliveryError, "duplicate"):
            delivery.validate_ids([self.brief_id, self.brief_id])
        with self.assertRaisesRegex(delivery.DeliveryError, "unsafe"):
            delivery.validate_ids(["../outside"])
        with self.assertRaisesRegex(delivery.DeliveryError, "daily cap"):
            delivery.validate_ids([f"short-{i}" for i in range(11)])

    def test_failed_or_timed_out_workflow_is_never_a_successful_delivery(self):
        delivery.require_success("success")
        for result in ("failure", "cancelled", None):
            with self.subTest(result=result):
                with self.assertRaisesRegex(delivery.DeliveryError, "no render delivery"):
                    delivery.require_success(result)

    def test_workspace_budget_counts_snapshot_files_and_reserves_margin(self):
        root = self.root / "workspace"
        root.mkdir()
        (root / "source.bin").write_bytes(b"x" * 100)
        (root / ".git").mkdir()
        (root / ".git" / "history.pack").write_bytes(b"x" * 50)
        (root / ".cache").mkdir()
        (root / ".cache" / "ignored.bin").write_bytes(b"x" * 500)
        self.assertEqual(delivery.workspace_size_bytes(root), 150)
        report = delivery.require_workspace_capacity(root, 700, limit_bytes=1000, reserve_bytes=100)
        self.assertEqual(report["projected_bytes"], 850)
        with self.assertRaisesRegex(delivery.DeliveryError, "safe budget"):
            delivery.require_workspace_capacity(root, 751, limit_bytes=1000, reserve_bytes=100)

    def test_existing_destination_is_never_overwritten(self):
        final_root = self.root / "renders"
        (final_root / self.brief_id).mkdir(parents=True)
        with self.assertRaisesRegex(delivery.DeliveryError, "refusing to merge/overwrite"):
            delivery.ensure_destinations_unused(final_root, [self.brief_id])

    def test_batch_promotion_moves_all_verified_paths(self):
        final_root = self.root / "renders"
        receipts = delivery.promote_verified_batch(
            self.root / "stage", final_root, [self.brief_id],
            require_approved_voice_ids={self.brief_id},
        )
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["id"], self.brief_id)
        self.assertTrue((final_root / self.brief_id / f"{self.brief_id}.mp4").is_file())
        self.assertFalse((self.root / "stage" / self.brief_id).exists())

    def test_batch_promotion_rejects_one_bad_artifact_before_installing_any(self):
        second = self.root / "stage" / "second-short"
        second.mkdir()
        (second / "second-short.mp4").write_bytes(b"x" * 1_000_000)
        checks = {name: True for name in delivery.CORE_CHECKS}
        (second / "manifest.json").write_text(json.dumps({
            "id": "second-short",
            "qa": {"duration": 30.0, "size_mb": 1.0, "checks": checks},
        }), encoding="utf-8")
        for name in delivery.REQUIRED_FILES[:-1]:
            (second / name).write_bytes(b"x" * 32)
        final_root = self.root / "renders"
        with self.assertRaisesRegex(delivery.DeliveryError, "approved-voice"):
            delivery.promote_verified_batch(
                self.root / "stage", final_root, [self.brief_id, "second-short"],
                require_approved_voice_ids={self.brief_id, "second-short"},
            )
        self.assertFalse(final_root.exists())


if __name__ == "__main__":
    unittest.main()
