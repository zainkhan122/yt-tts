"""Non-render checks for the single visual skin constant (lib/pipeline.py DEFAULT_SKIN).

The full visual test (render, frames, loudness, captions) runs in CI via render-validation.yml.
These tests make sure the skin the pipeline names is the skin that exists and exposes the hooks
the pipeline calls, so a rename cannot silently break rendering.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


from lib import pipeline as P  # noqa: E402


class SkinConstant(unittest.TestCase):
    def test_default_skin_is_tool_spotlight(self):
        self.assertEqual(P.DEFAULT_SKIN, "tool-spotlight")

    def test_default_skin_is_listed(self):
        self.assertIn(P.DEFAULT_SKIN, P.list_templates())

    def test_skin_module_loads_and_exposes_hooks(self):
        tpl = P.load_template(P.DEFAULT_SKIN)
        for fn in ("segments", "events", "html", "assets", "sfx", "music", "data"):
            self.assertTrue(callable(getattr(tpl, fn, None)), f"skin is missing {fn}()")
        self.assertIn("speed", tpl.DEFAULTS)
        self.assertIn("captions", tpl.DEFAULTS)
        self.assertEqual(tpl.DIR.name, "tool-spotlight")

    def test_skin_example_brief_is_v2(self):
        import json
        ex = json.loads((ROOT / "templates" / P.DEFAULT_SKIN / "example.json").read_text(encoding="utf-8"))
        self.assertNotIn("template", ex)


if __name__ == "__main__":
    unittest.main()
