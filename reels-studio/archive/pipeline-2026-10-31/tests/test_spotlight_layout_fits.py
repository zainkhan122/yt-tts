"""Layout-fit regressions: spotlight text must never overlap or escape its card.

Born from repo-indra-01 (2026-10-15): a non-cover image scene's `sub` sat at
436px while the image card kept its fixed 470px top, so the card covered the
sub; and a big-stat with suffix " pages/s" + a two-line label overflowed its
540px card because the number was never measured against the box.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "templates/_spotlight/scene.js"


class SpotlightLayoutFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = JS.read_text()

    def test_image_scene_noncover_card_starts_below_sub(self):
        # The non-cover branch must derive cardTop from the sub's rendered height.
        self.assertIn('cardTop = Math.max(470, Math.ceil(436 + sub.scrollHeight + 26));', self.js)
        self.assertIn('if (cover || s.sub) card.style.top = cardTop + "px";', self.js)

    def test_stat_badge_autofits_final_string_inside_card(self):
        # statBadge must measure the final formatted string and shrink to fit.
        self.assertIn("num.textContent = fmt(v);", self.js)
        self.assertIn("card.scrollHeight > card.clientHeight", self.js)
        self.assertIn("n.style.fontSize = statFs + \"px\";", self.js)
        # The shrink loop must be bounded so it always terminates.
        self.assertRegex(self.js, r"while \(statFs > 56 &&")

    def test_stat_label_stays_inside_bigstat_card(self):
        # CSS contract: bigstat card is a fixed-height flex column; the label is
        # part of the measured content (scrollHeight check above covers it).
        css = (ROOT / "templates/_spotlight/scene.css").read_text()
        m = re.search(r"\.sp-bigstat\s*\{([^}]*)\}", css)
        self.assertIsNotNone(m)
        self.assertIn("height: 540px", m.group(1))


if __name__ == "__main__":
    unittest.main()
