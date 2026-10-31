import io
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import gh_actions  # noqa: E402


class ArtifactExtractionTests(unittest.TestCase):
    def zip_bytes(self, entries):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in entries:
                info = zipfile.ZipInfo(name)
                info.compress_type = zipfile.ZIP_DEFLATED
                if isinstance(data, tuple):
                    info.create_system = 3
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    payload = data[0]
                else:
                    payload = data
                z.writestr(info, payload)
        return buf.getvalue()

    def test_extracts_a_valid_small_artifact_and_reports_size(self):
        with tempfile.TemporaryDirectory() as d:
            count, size = gh_actions.safe_extract_artifact(self.zip_bytes([("render/manifest.json", b"{}")]), Path(d) / "stage")
            self.assertEqual(count, 1)
            self.assertEqual(size, 2)
            self.assertEqual((Path(d) / "stage/render/manifest.json").read_bytes(), b"{}")

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(SystemExit, "unsafe artifact path"):
                gh_actions.safe_extract_artifact(self.zip_bytes([("../escape.txt", b"no")]), Path(d) / "stage")
            self.assertFalse((Path(d) / "escape.txt").exists())

    def test_rejects_symlink_entries(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(SystemExit, "symlink"):
                gh_actions.safe_extract_artifact(self.zip_bytes([("link", (b"target",))]), Path(d) / "stage")

    def test_rejects_nonempty_destination_instead_of_merging(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "stage"
            dest.mkdir()
            (dest / "stale.txt").write_text("stale")
            with self.assertRaisesRegex(SystemExit, "refusing to merge"):
                gh_actions.safe_extract_artifact(self.zip_bytes([("fresh.txt", b"new")]), dest)
            self.assertTrue((dest / "stale.txt").is_file())
            self.assertFalse((dest / "fresh.txt").exists())

    def test_rejects_artifact_over_configured_expansion_limit(self):
        blob = self.zip_bytes([("file.txt", b"0" * 100_000)])
        previous = gh_actions.MAX_ARTIFACT_BYTES
        try:
            gh_actions.MAX_ARTIFACT_BYTES = len(blob) + 1
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaisesRegex(SystemExit, "expands beyond size limit"):
                    gh_actions.safe_extract_artifact(blob, Path(d) / "stage")
        finally:
            gh_actions.MAX_ARTIFACT_BYTES = previous


if __name__ == "__main__":
    unittest.main()
