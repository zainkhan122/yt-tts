"""Post-kit voice metadata must name the renderer, without importing the heavy render stack."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_PATH = ROOT / "lib/pipeline.py"
PIPELINE_TREE = ast.parse(PIPELINE_PATH.read_text())


def _load_pure_voice_disclosure():
    """Execute only the pure helper AST; posting CI intentionally does not install NumPy/TTS."""
    fn = next(node for node in PIPELINE_TREE.body
              if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "voice_disclosure")
    namespace = {}
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    exec(compile(module, str(PIPELINE_PATH), "exec"), namespace)
    return namespace["voice_disclosure"]


voice_disclosure = _load_pure_voice_disclosure()


class VoiceDisclosureTests(unittest.TestCase):
    def test_chatterbox_final_is_not_mislabeled_as_kokoro(self):
        line = voice_disclosure("am_michael", "chatterbox")
        self.assertIn("Chatterbox", line)
        self.assertIn("Option-3", line)
        self.assertIn("reference only", line)
        self.assertNotIn("Kokoro TTS `am_michael`", line)

    def test_kokoro_preview_is_marked_preview_only(self):
        line = voice_disclosure("am_michael", "kokoro-preview")
        self.assertIn("Kokoro TTS `am_michael`", line)
        self.assertIn("preview only", line)
        self.assertIn("not approved for final media", line)

    def test_legacy_kokoro_engine_remains_described_as_kokoro(self):
        line = voice_disclosure("am_michael", "kokoro")
        self.assertIn("Kokoro TTS `am_michael`", line)
        self.assertNotIn("Chatterbox", line)

    def test_own_recording_is_not_called_synthetic(self):
        self.assertEqual(voice_disclosure("files", "own recordings"), "- Voice: your own recording.")

    def test_write_post_passes_the_selected_engine_to_the_disclosure(self):
        cls = next(node for node in PIPELINE_TREE.body if isinstance(node, ast.ClassDef) and node.name == "Job")
        method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "write_post")
        calls = [node for node in ast.walk(method)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "voice_disclosure"]
        self.assertEqual(len(calls), 1)
        call = calls[0]
        self.assertEqual(len(call.args), 2)
        self.assertIsInstance(call.args[0], ast.Name)
        self.assertEqual(call.args[0].id, "voice")
        engine = call.args[1]
        self.assertIsInstance(engine, ast.Call)
        self.assertIsInstance(engine.func, ast.Name)
        self.assertEqual(engine.func.id, "getattr")
        self.assertEqual(ast.unparse(engine), "getattr(self, 'voice_engine', 'kokoro')")


if __name__ == "__main__":
    unittest.main()
