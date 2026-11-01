"""A capture pack is complete only when every file its manifest lists is on disk (1 Nov regression)."""
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import capture_store  # noqa: E402


class PackCompleteTests(unittest.TestCase):
    def _pack(self, files_on_disk, listed):
        d = Path(tempfile.mkdtemp()) / "cap"
        d.mkdir(parents=True)
        (d / "manifest.json").write_text(json.dumps({"files": {k: {"file": v} for k, v in listed.items()}}))
        for name in files_on_disk:
            (d / name).write_bytes(b"x")
        return d

    def test_manifest_alone_is_not_complete(self):
        d = self._pack([], {"clip": "anim.mp4"})
        self.assertFalse(capture_store.pack_complete(d))

    def test_all_listed_files_present_is_complete(self):
        d = self._pack(["anim.mp4"], {"clip": "anim.mp4"})
        self.assertTrue(capture_store.pack_complete(d))

    def test_no_manifest_is_not_complete(self):
        d = Path(tempfile.mkdtemp()) / "empty"
        d.mkdir()
        self.assertFalse(capture_store.pack_complete(d))


if __name__ == "__main__":
    unittest.main()
