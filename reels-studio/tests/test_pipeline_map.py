import re
import unittest
from pathlib import Path

from tools import pipeline_map, make_shorts

ROOT = Path(__file__).resolve().parents[1]


class PipelineMapTests(unittest.TestCase):
    def test_map_is_up_to_date_with_the_code(self):
        self.assertEqual((ROOT / "docs" / "pipeline-stages.html").read_text(encoding="utf-8"), pipeline_map.build_html(),
                         "run: python3 tools/pipeline_map.py")

    def test_stage_order_matches_make_shorts(self):
        self.assertEqual(pipeline_map.stage_order(), make_shorts.STAGES)

    def test_new_qa_and_fallback_tools_are_shown_in_their_stages(self):
        fns = pipeline_map.stage_functions()
        self.assertIn("tools/feature_card.py", pipeline_map.tools_called(fns["build"]))
        self.assertIn("tools/short_qa.py", pipeline_map.tools_called(fns["fetch"]))

    def test_gate_rows_cover_plan_and_video(self):
        where = {g["stage"] for g in pipeline_map.gate_rows()}
        self.assertEqual(where, {"plan (preflight)", "video (fetch)"})


if __name__ == "__main__":
    unittest.main()
