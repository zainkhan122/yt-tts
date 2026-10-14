import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import capture_store  # noqa: E402


class CaptureStoreTests(unittest.TestCase):
    def _tar(self, cid="cap-one", entries=None):
        entries = entries or {
            f"{cid}/manifest.json": json.dumps({"id": cid, "files": {"screen": {"file": "screen.jpg"}}}).encode(),
            f"{cid}/screen.jpg": b"image bytes",
        }
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as tf:
            for name, value in entries.items():
                info = tarfile.TarInfo(name)
                if isinstance(value, tuple) and value[0] == "symlink":
                    info.type = tarfile.SYMTYPE
                    info.linkname = value[1]
                    tf.addfile(info)
                else:
                    payload = value if isinstance(value, bytes) else bytes(value)
                    info.size = len(payload)
                    tf.addfile(info, io.BytesIO(payload))
        return stream.getvalue()

    def test_missing_capture_store_is_read_only_for_pull_and_list(self):
        with patch.object(capture_store, "call", return_value=(404, {"message": "not found"})) as call:
            with self.assertRaisesRegex(SystemExit, "will not create a public Release"):
                capture_store.release()
        call.assert_called_once()
        self.assertEqual(call.call_args.args[:2], ("GET", f"{capture_store.API}/releases/tags/{capture_store.TAG}"))

    def test_only_explicit_push_path_can_create_capture_store_release(self):
        created = {"tag_name": capture_store.TAG, "assets": []}
        with patch.object(capture_store, "call", side_effect=[(404, {}), (201, created)]) as call:
            self.assertEqual(capture_store.release(create=True), created)
        self.assertEqual(call.call_count, 2)
        self.assertEqual(call.call_args_list[1].args[0], "POST")

    def test_github_api_urls_are_pinned_to_expected_repo_hosts(self):
        capture_store._validate_api_url(f"https://api.github.com/repos/{capture_store.REPO}/releases/tags/{capture_store.TAG}")
        capture_store._validate_api_url(f"https://uploads.github.com/repos/{capture_store.REPO}/releases/1/assets?name=cap-one.tar")
        for url in (
            "https://attacker.invalid/repos/zainkhan122/yt-tts/releases/assets/1",
            "https://api.github.com/repos/other/repo/releases/tags/capture-packs",
            "http://api.github.com/repos/zainkhan122/yt-tts/releases/tags/capture-packs",
            "https://api.github.com.evil.invalid/repos/zainkhan122/yt-tts/releases/tags/capture-packs",
        ):
            with self.subTest(url=url), self.assertRaises(SystemExit):
                capture_store._validate_api_url(url)

    def test_asset_redirect_must_be_trusted_and_tokenless(self):
        with self.assertRaisesRegex(SystemExit, "trusted signed GitHub"):
            capture_store._download_signed_asset("https://attacker.invalid/payload?token=x", 1000)

        class Response:
            status = 200
            headers = {"Content-Length": "4"}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, _limit=-1): return b"data"

        class Opener:
            def open(self, req, timeout):
                self.request = req
                if any(k.lower() == "authorization" for k in req.headers):
                    raise AssertionError("signed object-store request must not receive the GitHub token")
                return Response()

        opener = Opener()
        with patch.object(capture_store.urllib.request, "build_opener", return_value=opener):
            data = capture_store._download_signed_asset(
                "https://release-assets.githubusercontent.com/signed/file?token=secret", 1000
            )
        self.assertEqual(data, b"data")

    def test_pull_extracts_only_safe_members_into_staging_and_never_creates_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "reels-studio"
            repo.mkdir()
            blob = self._tar()
            with patch.object(capture_store, "ROOT", repo), \
                 patch.object(capture_store, "release", return_value={"assets": [{
                     "name": "cap-one.tar", "url": f"https://api.github.com/repos/{capture_store.REPO}/releases/assets/1"
                 }]}) as release, \
                 patch.object(capture_store, "call", return_value=(200, blob)):
                capture_store.pull("cap-one")
            release.assert_called_once_with()
            self.assertEqual((repo / "captures/cap-one/screen.jpg").read_bytes(), b"image bytes")
            self.assertTrue((repo / "captures/cap-one/manifest.json").is_file())
            self.assertEqual(list((repo / "captures").glob(".cap-one.pull-*")), [])

    def test_pull_refuses_path_traversal_and_symlink_members_without_writing_outside(self):
        malicious = (
            self._tar(entries={
                "cap-one/manifest.json": b"{}",
                "cap-one/../escape.txt": b"no",
            }),
            self._tar(entries={
                "cap-one/manifest.json": b"{}",
                "cap-one/link": ("symlink", "../../escape.txt"),
            }),
        )
        for blob in malicious:
            with self.subTest(size=len(blob)), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "reels-studio"
                repo.mkdir()
                with patch.object(capture_store, "ROOT", repo), \
                     patch.object(capture_store, "release", return_value={"assets": [{
                         "name": "cap-one.tar", "url": f"https://api.github.com/repos/{capture_store.REPO}/releases/assets/1"
                     }]}), \
                     patch.object(capture_store, "call", return_value=(200, blob)):
                    with self.assertRaises(SystemExit):
                        capture_store.pull("cap-one")
                self.assertFalse((repo / "captures/cap-one").exists())
                self.assertFalse((Path(tmp) / "escape.txt").exists())
                self.assertEqual(list((repo / "captures").glob(".cap-one.pull-*")), [])

    def test_existing_capture_pack_is_never_overwritten_by_pull(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "reels-studio"
            existing = repo / "captures/cap-one"
            existing.mkdir(parents=True)
            (existing / "manifest.json").write_text("{}", encoding="utf-8")
            with patch.object(capture_store, "ROOT", repo), patch.object(capture_store, "release") as release:
                capture_store.pull("cap-one")
            release.assert_not_called()
            self.assertEqual((existing / "manifest.json").read_text(encoding="utf-8"), "{}")

    def test_pull_for_rejects_briefs_outside_canonical_directory_and_unsafe_capture_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "reels-studio"
            briefs = repo / "briefs"
            briefs.mkdir(parents=True)
            bad = briefs / "bad.json"
            bad.write_text(json.dumps({"id": "bad", "capture": "captures/../outside"}), encoding="utf-8")
            with patch.object(capture_store, "ROOT", repo), patch.object(capture_store, "pull") as pull:
                with self.assertRaises(SystemExit):
                    capture_store.pull_for(str(Path(tmp) / "outside.json"))
                with self.assertRaises(SystemExit):
                    capture_store.pull_for("reels-studio/briefs/bad.json")
            pull.assert_not_called()


if __name__ == "__main__":
    unittest.main()
