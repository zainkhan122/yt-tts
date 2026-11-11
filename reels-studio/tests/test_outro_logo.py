"""Outro logo + queue watchability gate (owner, 2026-10-18).

The end-card used to render the channel initial ("H") as text. The owner requires
the real brand logo in every video outro. Also: queue approval must fail closed
without a PASSed viewer panel on file.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


class OutroLogoTests(unittest.TestCase):
    def test_channel_brand_names_the_logo_asset(self):
        chan = json.loads((ROOT / "config" / "channel.json").read_text())
        self.assertEqual(chan["brand"].get("logo"), "logo.png")
        self.assertTrue((ROOT / "brand" / "logo" / "avatar-1080.png").exists())

    def test_endcard_renders_logo_image_not_initial(self):
        base_js = (ROOT / "templates" / "_base" / "base.js").read_text()
        self.assertIn('if (b.logo)', base_js)
        self.assertIn('"assets/" + b.logo', base_js)
        base_css = (ROOT / "templates" / "_base" / "base.css").read_text()
        self.assertIn("#ec-avatar img", base_css)

    def test_spotlight_assets_stage_the_logo(self):
        spotcore = (ROOT / "templates" / "_spotlight" / "spotcore.py").read_text()
        self.assertIn('"brand" / "logo" / "avatar-1080.png"', spotcore)
        self.assertIn('"logo.png"', spotcore)


class PanelGateTests(unittest.TestCase):
    def test_approve_requires_a_passed_panel(self):
        from tools.post import queue_ctl
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prod = root / "research" / "production"
            prod.mkdir(parents=True)
            with patch.object(queue_ctl, "ROOT", root):
                self.assertFalse(queue_ctl.panel_passed("vid-01"))
                (prod / "viewer-panel-2026-10-18-vid-01.md").write_text(
                    "# panel\n## Panel result: FAIL\n", encoding="utf-8")
                self.assertFalse(queue_ctl.panel_passed("vid-01"))
                (prod / "viewer-panel-2026-10-18-vid-01-rebuild.md").write_text(
                    "# panel\n## Panel result: PASS\n", encoding="utf-8")
                self.assertTrue(queue_ctl.panel_passed("vid-01"))


if __name__ == "__main__":
    unittest.main()
