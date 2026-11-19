import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import cover_lab
import cover_rules

class CoverCropSafety(unittest.TestCase):
    def test_headline_safe_box(self):
        self.assertEqual((cover_rules.SAFE_LEFT, cover_rules.SAFE_TOP, cover_rules.SAFE_RIGHT, cover_rules.SAFE_BOTTOM), (54, 315, 1026, 1605))
        report = [{'concept': i, 'text': t, 'layout': layout, 'source': str(i),
                   'text_box': [54, 315, 1026, 1605], 'contrast_white': 8, 'contrast_accent': 8}
                  for i, (t, layout) in enumerate(zip(['ONE TWO THREE FOUR','FIVE SIX SEVEN EIGHT','NINE TEN ELEVEN TWELVE'], cover_rules.LAYOUTS))]
        self.assertEqual(cover_lab.audit(report), [])
        report[0]['text_box'] = [53, 314, 1026, 1605]
        problems = cover_lab.audit(report)
        self.assertTrue(any('vertical' in p for p in problems))
        self.assertTrue(any('horizontal' in p for p in problems))
