"""GitHub Release batching is fail-closed and never promotes MP4s into the workspace."""
import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib import delivery  # noqa: E402
from tools import publish_verified_batch as publisher  # noqa: E402


class VerifiedReleaseBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.artifacts = self.root / "release-artifacts"
        self.briefs = self.root / "briefs"
        self.artifacts.mkdir()
        self.briefs.mkdir()
        self.ids = ["first-short", "second-short"]
        for brief_id in self.ids:
            self._make_render(brief_id)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_render(self, brief_id, *, omit=None, failed_check=None):
        (self.briefs / f"{brief_id}.json").write_text(json.dumps({"id": brief_id}), encoding="utf-8")
        folder = self.artifacts / f"render-{brief_id}"
        folder.mkdir(exist_ok=True)
        mp4 = b"v" * 1_000_000
        (folder / f"{brief_id}.mp4").write_bytes(mp4)
        for name in delivery.REQUIRED_FILES[:-1]:
            if name != omit:
                (folder / name).write_text(f"{brief_id}: {name}\n", encoding="utf-8")
        (folder / "voiceover.mp3").write_bytes(b"voice")
        checks = {check: True for check in delivery.CORE_CHECKS}
        if failed_check:
            checks[failed_check] = False
        (folder / "manifest.json").write_text(json.dumps({
            "id": brief_id,
            "qa": {"duration": 30.0, "size_mb": 1.0, "checks": checks},
        }), encoding="utf-8")
        return folder

    def test_prepares_mp4_and_complete_kit_without_creating_workspace_copies(self):
        prepared = publisher.prepare_assets(self.ids, "renders-2026-10-14", self.artifacts, self.briefs)
        self.assertEqual([item["id"] for item in prepared], self.ids)
        self.assertEqual([asset["name"] for asset in prepared[0]["assets"]],
                         ["first-short.mp4", "first-short-kit.zip"])
        self.assertEqual(len(prepared[0]["assets"][0]["bytes"]), 1_000_000)
        with zipfile.ZipFile(io.BytesIO(prepared[0]["assets"][1]["bytes"])) as z:
            names = set(z.namelist())
        self.assertIn("first-short/manifest.json", names)
        self.assertIn("first-short/voiceover.mp3", names)
        self.assertIn("first-short/cover.jpg", names)
        self.assertTrue((self.artifacts / "render-first-short" / "first-short.mp4").exists())
        self.assertFalse((self.root / "renders").exists())

    def test_incomplete_or_failed_member_blocks_the_entire_batch_before_release_creation(self):
        (self.artifacts / "render-second-short" / "seo.md").unlink()
        with patch.object(publisher, "_publish") as create_release, \
             patch.object(publisher.gh_actions, "delete_artifact") as delete_artifact:
            with self.assertRaisesRegex(delivery.DeliveryError, "seo.md"):
                publisher.finalize_batch(self.ids, "renders-2026-10-14", self.artifacts,
                                         self.briefs, "123")
        create_release.assert_not_called()
        delete_artifact.assert_not_called()
        self.assertFalse((self.root / "renders").exists())

        self._make_render("second-short", failed_check="frame0_visible")
        with self.assertRaisesRegex(delivery.DeliveryError, "frame0_visible"):
            publisher.prepare_assets(self.ids, "renders-2026-10-14", self.artifacts, self.briefs)

    def test_symlinked_optional_voiceover_is_rejected(self):
        folder = self.artifacts / "render-first-short"
        voice = folder / "voiceover.mp3"
        voice.unlink()
        outside = self.root / "outside.mp3"
        outside.write_bytes(b"not part of artifact")
        voice.symlink_to(outside)
        with self.assertRaisesRegex(delivery.DeliveryError, "symlink in post kit"):
            publisher.prepare_assets(["first-short"], "renders-2026-10-14", self.artifacts, self.briefs)

    def test_new_release_is_staged_as_draft_then_published_as_one_batch(self):
        prepared = publisher.prepare_assets(self.ids, "renders-2026-10-14", self.artifacts, self.briefs)
        draft = {"id": 77, "tag_name": "renders-2026-10-14", "draft": True,
                 "html_url": "https://github.com/zainkhan122/yt-tts/releases/tag/renders-2026-10-14",
                 "upload_url": "https://uploads.github.com/", "assets": []}
        published = {**draft, "draft": False, "assets": [
            {"name": asset["name"], "digest": "sha256:" + hashlib.sha256(asset["bytes"]).hexdigest()}
            for item in prepared for asset in item["assets"]
        ]}
        calls = []

        def fake_call(method, url, data=None, **kwargs):
            calls.append((method, url, data))
            if method == "GET" and "/releases/tags/" in url:
                return 404, {"message": "Not Found"}
            if method == "POST" and url.endswith("/releases"):
                return 201, draft
            if method == "GET" and url.endswith("/releases/77"):
                return 200, published if any(call[0] == "PATCH" for call in calls) else draft
            if method == "PATCH" and url.endswith("/releases/77"):
                return 200, published
            raise AssertionError((method, url))

        with patch.object(publisher.publish_release, "call", side_effect=fake_call), \
             patch.object(publisher.publish_release, "upload", return_value="https://asset.invalid") as upload:
            url = publisher._publish(prepared, "renders-2026-10-14")
        self.assertEqual(url, published["html_url"])
        self.assertEqual(upload.call_count, 4)
        patch_call = next(call for call in calls if call[0] == "PATCH")
        self.assertEqual(patch_call[2], {"draft": False, "body": calls[1][2]["body"]})
        self.assertEqual(calls[-1][0], "GET")  # confirm the now-public asset list from GitHub
        self.assertEqual(calls[1][2]["tag_name"], "renders-2026-10-14")
        self.assertIn("no Buffer", calls[1][2]["body"])

    def test_same_tag_is_idempotent_only_when_every_published_asset_digest_matches(self):
        prepared = publisher.prepare_assets(self.ids, "renders-2026-10-14", self.artifacts, self.briefs)
        assets = []
        for item in prepared:
            for asset in item["assets"]:
                assets.append({"name": asset["name"],
                               "digest": "sha256:" + hashlib.sha256(asset["bytes"]).hexdigest()})
        release = {"tag_name": "renders-2026-10-14", "draft": False, "assets": assets,
                   "html_url": "https://github.com/zainkhan122/yt-tts/releases/tag/renders-2026-10-14"}
        with patch.object(publisher.publish_release, "call", return_value=(200, release)), \
             patch.object(publisher.publish_release, "upload") as upload:
            self.assertEqual(publisher._publish(prepared, "renders-2026-10-14"), release["html_url"])
        upload.assert_not_called()

        release["assets"][0]["digest"] = "sha256:" + "0" * 64
        with patch.object(publisher.publish_release, "call", return_value=(200, release)), \
             patch.object(publisher.publish_release, "upload") as upload:
            with self.assertRaisesRegex(SystemExit, "refusing to mutate a published daily release"):
                publisher._publish(prepared, "renders-2026-10-14")
        upload.assert_not_called()

    def test_finalizer_returns_release_url_and_leaves_mp4s_only_in_staging(self):
        with patch.object(publisher, "_publish", return_value="https://github.com/example/release"), \
             patch.object(publisher.gh_actions, "delete_artifact") as delete_artifact:
            url = publisher.finalize_batch(self.ids, "renders-2026-10-14", self.artifacts,
                                           self.briefs, "123")
        self.assertEqual(url, "https://github.com/example/release")
        self.assertEqual(delete_artifact.call_count, 2)
        for brief_id in self.ids:
            self.assertTrue((self.artifacts / f"render-{brief_id}" / f"{brief_id}.mp4").exists())
        self.assertFalse((self.root / "renders").exists())


if __name__ == "__main__":
    unittest.main()
