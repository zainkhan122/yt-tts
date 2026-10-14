import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.render_attempts import (  # noqa: E402
    RENDER_CODE_FIXED,
    DuplicateRenderError,
    check_registry,
    finish_in_registry,
    make_attempts,
    reserve_in_registry,
    reserve_remote,
    renderer_fingerprint,
)


FIXED = (
    ".github/workflows/render.yml",
    "reels-studio/reels.py",
    "reels-studio/lib/pipeline.py",
    "reels-studio/lib/scenes.py",
    "reels-studio/lib/framecheck.py",
    "reels-studio/lib/synth.py",
    "reels-studio/lib/gates.py",
    "reels-studio/lib/secrets.py",
    "reels-studio/config/channel.json",
    "reels-studio/cloud/setup-render.sh",
    "reels-studio/setup/setup-whisper.sh",
    "reels-studio/setup/setup-sandbox.sh",
    "reels-studio/tools/capture_store.py",
    "reels-studio/tools/seo_pack.py",
    "reels-studio/tools/brief_lint.py",
    "reels-studio/tools/gh_actions.py",
    "reels-studio/tools/production_gate.py",
    "reels-studio/tools/validate_dispatch.py",
    "reels-studio/tools/render_attempts.py",
    "reels-studio/brand/voice/michael-ref.wav",
)


class RenderAttemptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in FIXED:
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(rel.encode())
        (self.root / "reels-studio/templates/_base").mkdir(parents=True)
        (self.root / "reels-studio/templates/_base/base.js").write_text("base", encoding="utf-8")
        self.plan = {"briefs": ["one"], "quality": "looks", "crf": 23, "rebuild_scenes": [], "from_tag": ""}
        self.briefs = {"one": {"id": "one", "voice_seed": 0}}
        self.hashes = {"one": "a" * 64}
        self.asset_hashes = {"one": "b" * 64}
        self.attempts = make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)
        self.empty = {"schema_version": 1, "attempts": {}, "legacy_completed_briefs": [], "legacy_completed_ids": []}

    def tearDown(self):
        self.tmp.cleanup()

    def test_fingerprint_is_stable_and_changes_with_renderer_or_voice_seed(self):
        first = self.attempts[0]["fingerprint"]
        again = make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)[0]["fingerprint"]
        self.assertEqual(first, again)
        sandbox_setup = self.root / "reels-studio/setup/setup-sandbox.sh"
        original_setup = sandbox_setup.read_bytes()
        sandbox_setup.write_text("sandbox adjustment", encoding="utf-8")
        changed_setup = make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)[0]["fingerprint"]
        self.assertNotEqual(first, changed_setup)
        sandbox_setup.write_bytes(original_setup)
        (self.root / "reels-studio/lib/pipeline.py").write_text("bug fix", encoding="utf-8")
        changed_renderer = make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)[0]["fingerprint"]
        self.assertNotEqual(first, changed_renderer)
        self.briefs["one"]["voice_seed"] = 1
        changed_seed = make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)[0]["fingerprint"]
        self.assertNotEqual(changed_renderer, changed_seed)
        self.briefs["one"]["voice_seed"] = 0
        self.asset_hashes = {"one": {"manifest_sha256": "b" * 64, "files_sha256": "c" * 64, "capture_id": "cap-one"}}
        first_asset = make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)[0]["fingerprint"]
        self.asset_hashes["one"]["files_sha256"] = "d" * 64
        changed_asset = make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)[0]["fingerprint"]
        self.assertNotEqual(first_asset, changed_asset)

    def test_generated_template_bytecode_does_not_change_fingerprint(self):
        before = renderer_fingerprint(self.root)
        cache_dir = self.root / "reels-studio/templates/_base/__pycache__"
        cache_dir.mkdir()
        (cache_dir / "base.cpython-312.pyc").write_bytes(b"runtime-only bytecode")
        self.assertEqual(before, renderer_fingerprint(self.root))
        source = self.root / "reels-studio/templates/_base/base.js"
        source.write_text("edited source", encoding="utf-8")
        self.assertNotEqual(before, renderer_fingerprint(self.root))

    def test_template_symlinks_are_rejected_from_renderer_fingerprint(self):
        alias = self.root / "reels-studio/templates/_base/alias.js"
        alias.symlink_to(self.root / "reels-studio/templates/_base/base.js")
        with self.assertRaisesRegex(ValueError, "unsafe symlink"):
            make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)

    def test_voice_seed_must_be_bounded_non_negative_integer(self):
        self.briefs["one"]["voice_seed"] = -1
        with self.assertRaisesRegex(ValueError, "between 0 and 1000000"):
            make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)
        self.briefs["one"]["voice_seed"] = True
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)

    def test_completed_or_failed_identical_inputs_are_blocked(self):
        registry = reserve_in_registry(self.empty, self.attempts, "123")
        with self.assertRaisesRegex(DuplicateRenderError, "identical render inputs"):
            check_registry(registry, self.attempts)
        registry = finish_in_registry(registry, "123", "failed", conclusion="failure")
        with self.assertRaises(DuplicateRenderError):
            check_registry(registry, self.attempts)
        self.assertEqual(next(iter(registry["attempts"].values()))["status"], "failed")

    def test_legacy_completed_id_cannot_be_reused_even_with_a_new_voice_seed(self):
        self.empty["legacy_completed_ids"] = ["one"]
        with self.assertRaisesRegex(DuplicateRenderError, "belongs to an existing rendered video"):
            check_registry(self.empty, self.attempts)
        self.briefs["one"]["voice_seed"] = 1
        changed = make_attempts(self.root, self.plan, self.briefs, self.hashes, self.asset_hashes)
        with self.assertRaises(DuplicateRenderError):
            check_registry(self.empty, changed)

    def test_repository_registry_seeds_the_four_existing_video_ids(self):
        registry_path = ROOT / "tracker/render-attempts.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        expected = {
            "model-embeddinggemma2-01",
            "news-gpt6-intelligent-ui-01",
            "repo-manimgx-01",
            "tool-qwen-image-21-turbo-01",
        }
        self.assertEqual(set(registry["legacy_completed_ids"]), expected)
        self.assertEqual(len(registry["legacy_completed_briefs"]), 4)
        candidate = {"brief_id": "news-gpt6-intelligent-ui-01", "fingerprint": "f" * 64, "rebuild_scenes": []}
        with self.assertRaisesRegex(DuplicateRenderError, "existing rendered video"):
            check_registry(registry, [candidate])

    def test_scene_rebuild_is_not_treated_as_a_duplicate_full_video(self):
        legacy = {"schema_version": 1, "attempts": {}, "legacy_completed_briefs": [
            {"brief_sha256": "a" * 64, "voice_seed": 0, "run_id": "10", "release_tag": "renders-old"}]}
        plan = {**self.plan, "rebuild_scenes": ["hook"], "from_tag": "renders-old"}
        attempt = make_attempts(self.root, plan, self.briefs, self.hashes)[0]
        check_registry(legacy, [attempt])

    def test_identical_scene_rebuild_inputs_are_blocked_after_an_attempt(self):
        plan = {**self.plan, "rebuild_scenes": ["hook"], "from_tag": "renders-old"}
        attempt = make_attempts(self.root, plan, self.briefs, self.hashes)[0]
        registry = reserve_in_registry(self.empty, [attempt], "124")
        with self.assertRaisesRegex(DuplicateRenderError, "identical scene rebuild inputs"):
            check_registry(registry, [attempt])

    def test_finalizer_requires_and_updates_a_started_attempt(self):
        registry = reserve_in_registry(self.empty, self.attempts, "123")
        registry = finish_in_registry(registry, "123", "success", conclusion="success")
        row = next(iter(registry["attempts"].values()))
        self.assertEqual(row["status"], "success")
        self.assertIsNotNone(row["finished_at"])
        with self.assertRaisesRegex(ValueError, "no started"):
            finish_in_registry(registry, "456", "failed")

    def test_render_only_success_is_a_valid_finalized_status(self):
        registry = reserve_in_registry(self.empty, self.attempts, "125")
        registry = finish_in_registry(registry, "125", "render_only_success")
        self.assertEqual(next(iter(registry["attempts"].values()))["status"], "render_only_success")

    def test_finalizer_script_bootstraps_package_imports_when_run_by_path(self):
        script = ROOT / "tools/render_attempts.py"
        code = r"""
import importlib.util
import pathlib
import sys
script = pathlib.Path(sys.argv[1]).resolve()
sys.path[:] = [str(script.parent)] + [entry for entry in sys.path[1:] if entry != str(script.parent)]
spec = importlib.util.spec_from_file_location("render_attempts_finalizer", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from tools import gh_actions
assert gh_actions.REPO == "zainkhan122/yt-tts"
"""
        subprocess.run([sys.executable, "-c", code, str(script)], check=True, capture_output=True, text=True)

    def test_workflow_is_artifact_only_and_has_no_release_publisher(self):
        workflow = (ROOT.parent / ".github/workflows/render.yml").read_text(encoding="utf-8")
        self.assertNotIn("publish_release", workflow)
        self.assertNotIn("actions/create-release", workflow)
        self.assertIn("retention-days: 1", workflow)
        self.assertIn("Record terminal status (never publish a Release)", workflow)
        self.assertIn("--run-id \"$RUN_ID\" --status \"$STATUS\" --conclusion \"$RENDER_RESULT\"", workflow)

    def test_plan_sparse_checkout_contains_every_fingerprinted_file(self):
        workflow = (ROOT.parent / ".github/workflows/render.yml").read_text(encoding="utf-8")
        plan_checkout = workflow.split("- name: Checkout the exact dispatch commit", 1)[1]
        sparse = plan_checkout.split("sparse-checkout: |", 1)[1].split("sparse-checkout-cone-mode", 1)[0]
        patterns = [line.strip() for line in sparse.splitlines() if line.strip().startswith("/")]
        missing = []
        for rel in RENDER_CODE_FIXED:
            if not any(rel == pattern.lstrip("/") or rel.startswith(pattern.lstrip("/").rstrip("/") + "/")
                       for pattern in patterns):
                missing.append(rel)
        self.assertEqual(missing, [], f"plan sparse checkout omits fingerprint inputs: {missing}")

    def test_remote_reservation_uses_contents_compare_and_swap(self):
        raw = (json.dumps(self.empty) + "\n").encode()
        responses = [(200, {"content": base64.b64encode(raw).decode(), "sha": "contents-sha"}), (200, {})]
        with patch("tools.gh_actions.api", side_effect=responses) as api:
            reserve_remote(self.attempts, "123")
        self.assertEqual(api.call_args_list[0].args, ("GET", "/contents/reels-studio/tracker/render-attempts.json?ref=main"))
        method, path, payload = api.call_args_list[1].args
        self.assertEqual(method, "PUT")
        self.assertEqual(path, "/contents/reels-studio/tracker/render-attempts.json")
        self.assertEqual(payload["sha"], "contents-sha")
        saved = json.loads(base64.b64decode(payload["content"]))
        self.assertEqual(next(iter(saved["attempts"].values()))["run_id"], "123")

    def test_remote_contents_conflict_fails_before_render(self):
        raw = (json.dumps(self.empty) + "\n").encode()
        responses = [(200, {"content": base64.b64encode(raw).decode(), "sha": "contents-sha"}), (409, {"message": "conflict"})]
        with patch("tools.gh_actions.api", side_effect=responses):
            with self.assertRaisesRegex(RuntimeError, "failed/conflicted"):
                reserve_remote(self.attempts, "123")


if __name__ == "__main__":
    unittest.main()
