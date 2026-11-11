"""Montage label pills must be as prominent as the spoken captions, without crowding the video card."""
import re
import unittest
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "templates/_spotlight/scene.css"
JS = ROOT / "templates/_spotlight/scene.js"


def rule(css, selector):
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    if not match:
        raise AssertionError(f"missing CSS rule {selector}")
    return match.group(1)


class SpotlightMontageTypographyTests(unittest.TestCase):
    def test_montage_pill_and_bottom_caption_share_one_size_token(self):
        css = CSS.read_text()
        captions = rule(css, ".cg")
        chip = rule(css, ".sp-chip")
        root = rule(css, "#root")
        token = re.search(r"--sp-caption-size:\s*([0-9.]+px)", root)
        self.assertIsNotNone(token, "missing shared caption-size token")
        self.assertEqual(token.group(1), "74px")
        for name, block in (("bottom caption", captions), ("montage pill", chip)):
            self.assertRegex(block, r'font:\s*900\s+var\(--sp-caption-size\)/1\.06\s+"Inter"', name)

    def test_longest_pilot_label_fits_the_pill_max_width(self):
        css = CSS.read_text()
        chip = rule(css, ".sp-chip")
        max_width = float(re.search(r"max-width:\s*([0-9.]+)px", chip).group(1))
        padding = re.search(r"padding:\s*([0-9.]+)px\s+([0-9.]+)px", chip)
        self.assertRegex(chip, r"white-space:\s*nowrap")
        self.assertIsNotNone(padding)
        root = rule(css, "#root")
        font_size = int(float(re.search(r"--sp-caption-size:\s*([0-9.]+)px", root).group(1)))
        font = ImageFont.truetype(str(ROOT / "templates/_base/fonts/Inter.ttf"), font_size)
        longest_label_width = font.getlength("PATTERN FEATURES")
        self.assertLessEqual(longest_label_width + 2 * float(padding.group(2)), max_width)

    def test_large_chip_stays_clear_of_the_montage_video_card(self):
        css = CSS.read_text()
        chip = rule(css, ".sp-chip")
        card = rule(css, ".sp-vcard")
        root = rule(css, "#root")
        chip_font_size = float(re.search(r"--sp-caption-size:\s*([0-9.]+)px", root).group(1))
        line_height = float(re.search(r"font:\s*900\s+var\(--sp-caption-size\)/([0-9.]+)", chip).group(1))
        pad_y = float(re.search(r"padding:\s*([0-9.]+)px", chip).group(1))
        card_top = float(re.search(r"top:\s*([0-9.]+)px", card).group(1))
        js = JS.read_text()
        chip_top = float(re.search(r'chip\.style\.top\s*=\s*"([0-9.]+)px"', js).group(1))
        rendered_chip_height = chip_font_size * line_height + 2 * pad_y
        self.assertGreaterEqual(card_top - (chip_top + rendered_chip_height), 24)


if __name__ == "__main__":
    unittest.main()
