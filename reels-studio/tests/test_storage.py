"""Storage safeguards: no blind deletion/replacement of immutable media."""
import hashlib
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.maintenance.storage import verify_capture_tar
from tools.publish_release import upload, release


class StorageTests(unittest.TestCase):
    def archive(self,tmp):
        folder=Path(tmp)/"pack";folder.mkdir();(folder/"media.bin").write_bytes(b"archived-source")
        archive=Path(tmp)/"pack.tar"
        with tarfile.open(archive,"w") as tf:tf.add(folder,arcname="pack")
        return folder,archive

    def test_pruning_requires_byte_for_byte_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder,archive=self.archive(tmp)
            self.assertEqual(verify_capture_tar(folder,archive,"pack"),(1,len(b"archived-source")))
            (folder/"media.bin").write_bytes(b"changed--source")
            with self.assertRaises(ValueError):verify_capture_tar(folder,archive,"pack")
            self.assertTrue(folder.exists())

    def test_unarchived_file_prevents_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder,archive=self.archive(tmp);(folder/"new.bin").write_bytes(b"not-backed-up")
            with self.assertRaises(ValueError):verify_capture_tar(folder,archive,"pack")
            self.assertTrue((folder/"new.bin").exists())

    def test_capture_symlink_prevents_automatic_pruning(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder,archive=self.archive(tmp);(folder/"link").symlink_to(folder/"media.bin")
            with self.assertRaises(ValueError):verify_capture_tar(folder,archive,"pack")

    def test_parallel_release_creation_adopts_existing_tag(self):
        existing={"tag_name":"renders-test","id":42}
        with patch("tools.publish_release.call",side_effect=[(404,{}),(422,{"message":"already exists"}),(200,existing)]) as http:
            self.assertEqual(release("renders-test"),existing)
            self.assertEqual(http.call_count,3)

    def test_changed_finished_render_cannot_be_replaced(self):
        rel={"tag_name":"renders-2026-10-10","assets":[{"name":"test.mp4","url":"https://api.github.com/asset","browser_download_url":"https://example.invalid/test.mp4","digest":"sha256:"+"0"*64}]}
        with patch("tools.publish_release.call") as http:
            with self.assertRaises(SystemExit):upload(rel,"test.mp4",b"new media",True)
            http.assert_not_called()

    def test_identical_immutable_asset_does_not_reupload(self):
        data=b"same-media";url="https://example.invalid/test.mp4"
        rel={"tag_name":"long-renders-2026-10-10","assets":[{"name":"test.mp4","url":"https://api.github.com/asset","browser_download_url":url,"digest":"sha256:"+hashlib.sha256(data).hexdigest()}]}
        with patch("tools.publish_release.call") as http:
            self.assertEqual(upload(rel,"test.mp4",data,True),url)
            http.assert_not_called()


class PruneAllTests(unittest.TestCase):
    """prune-all: verified pruning in one command; one bad pack must never stop or endanger others."""

    def test_skips_packs_without_a_verified_archive_and_keeps_going(self):
        from tools.maintenance import storage as st
        with patch.object(st, "local_packs", return_value=["a-01", "b-01", "c-01"]), \
             patch.object(st, "archived_packs", return_value={"a-01": {"id": 1, "digest": "sha256:x"},
                                                              "b-01": {"id": 2, "digest": "sha256:y"}}), \
             patch.object(st, "prune_capture",
                          side_effect=[{"pack": "a-01", "files_verified": 3, "bytes_verified": 100, "deleted": True},
                                       ValueError("Capture archive content differs: b-01/media.bin")]):
            out = st.prune_all(apply=True)
        self.assertEqual(out["deleted"], 1)          # a-01 pruned
        self.assertEqual(out["freed_bytes"], 100)
        reasons = {s["pack"]: s["reason"] for s in out["skipped"]}
        self.assertIn("c-01", reasons)               # no archive -> untouched
        self.assertIn("differs", reasons["b-01"])    # verification failure -> untouched, run continued

    def test_prune_all_defaults_to_read_only(self):
        from tools.maintenance import storage as st
        with patch.object(st, "local_packs", return_value=["a-01"]), \
             patch.object(st, "archived_packs", return_value={"a-01": {}}), \
             patch.object(st, "prune_capture", return_value={"pack": "a-01", "files_verified": 1,
                                                             "bytes_verified": 10, "deleted": False}) as prune:
            out = st.prune_all()
        prune.assert_called_once_with("a-01", False)
        self.assertEqual(out["deleted"], 0)


if __name__=="__main__":unittest.main()
