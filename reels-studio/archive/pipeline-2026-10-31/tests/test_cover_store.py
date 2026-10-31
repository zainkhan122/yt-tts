"""The reviewed cover must reach the cloud render, byte-identical.

`covers/` is gitignored, so before cover_store.py a locally reviewed cover made every
cloud render of that brief fail closed at creative_proof() - correct contract, missing
transport. These tests pin the transport: verify refuses stale bytes, and a pushed pack
pulls back to the same two files the renderer checks.
"""
import hashlib
import importlib.util
import io
import json
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cover_store = load("cover_store", ROOT / "tools" / "cover_store.py")


class CoverStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.orig = cover_store.ROOT
        cover_store.ROOT = self.tmp
        self.addCleanup(setattr, cover_store, "ROOT", self.orig)

    def make(self, cid="demo-01", payload=b"designed-cover-bytes"):
        d = self.tmp / "covers" / cid
        d.mkdir(parents=True)
        (d / "cover-selected.jpg").write_bytes(payload)
        sel = {"brief": cid, "selected": 1, "text": "NO CREW NEEDED", "archetype": "demo-first",
               "sha256": hashlib.sha256(payload).hexdigest()}
        (d / "selection.json").write_text(json.dumps(sel))
        return d

    def test_verify_accepts_a_matching_selection(self):
        self.make()
        self.assertEqual(cover_store.verify_dir("demo-01")["selected"], 1)

    def test_verify_refuses_a_cover_edited_after_selection(self):
        d = self.make()
        (d / "cover-selected.jpg").write_bytes(b"edited")
        with self.assertRaisesRegex(SystemExit, "changed after selection"):
            cover_store.verify_dir("demo-01")

    def test_verify_refuses_a_missing_selection(self):
        d = self.make()
        (d / "selection.json").unlink()
        with self.assertRaisesRegex(SystemExit, "selection.json"):
            cover_store.verify_dir("demo-01")

    def test_verify_refuses_someone_elses_selection(self):
        d = self.make()
        sel = json.loads((d / "selection.json").read_text())
        sel["brief"] = "other-01"
        (d / "selection.json").write_text(json.dumps(sel))
        with self.assertRaisesRegex(SystemExit, "belongs to"):
            cover_store.verify_dir("demo-01")

    def test_tar_roundtrip_restores_the_same_bytes(self):
        d = self.make()
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tf:
            tf.add(d, arcname="covers/demo-01")
        shutil.rmtree(self.tmp / "covers")
        (self.tmp / "covers").mkdir()
        with tarfile.open(fileobj=io.BytesIO(buf.getvalue()), mode="r") as tf:
            for member in tf.getmembers():  # same renaming rule as pull()
                if member.name.split("/")[0] == "covers":
                    member.name = "/".join(member.name.split("/")[1:])
                tf.extract(member, self.tmp / "covers", filter="data")
        self.assertEqual(cover_store.verify_dir("demo-01")["selected"], 1)
        self.assertEqual((self.tmp / "covers" / "demo-01" / "cover-selected.jpg").read_bytes(),
                         b"designed-cover-bytes")

    def test_legacy_brief_without_a_treatment_needs_no_cover_pack(self):
        legacy = self.tmp / "legacy.json"
        legacy.write_text(json.dumps({"id": "legacy-01"}))
        import subprocess, sys
        out = subprocess.run([sys.executable, str(ROOT / "tools" / "cover_store.py"), "pull-for", str(legacy)],
                             capture_output=True, text=True,
                             env={**__import__("os").environ, "PYTHONPATH": str(ROOT)})
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("no cover pack needed", out.stdout)


if __name__ == "__main__":
    unittest.main()
