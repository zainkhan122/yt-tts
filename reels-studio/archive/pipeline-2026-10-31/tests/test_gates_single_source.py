"""One source for QA thresholds: config/gates.json. Code and channel config must agree with it."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

GATES = json.loads((ROOT / "config" / "gates.json").read_text(encoding="utf-8"))


class SingleSourceTests(unittest.TestCase):
    def test_production_gate_reads_config(self):
        import production_gate as pg
        self.assertEqual(pg.MIN_TOPIC_SCORE, GATES["topic_score_min"])
        self.assertEqual(pg.MIN_CHUNK_MATCH, GATES["tts_chunk_match_min"])
        self.assertEqual(pg.MIN_ENGLISH_OVERALL_MATCH, GATES["tts_english_overall_match_min"])

    def test_pipeline_reads_config(self):
        from lib import pipeline as pl
        self.assertEqual(pl.MIN_FLOW_MATCH, GATES["tts_chunk_match_min"])
        self.assertEqual(pl.MIN_ENGLISH_WHISPER_MATCH, GATES["tts_english_whisper_match_min"])

    def test_channel_min_match_not_below_floor(self):
        channel = json.loads((ROOT / "config" / "channel.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(channel["tts"]["min_match"], GATES["tts_chunk_match_min"])


class PreflightTests(unittest.TestCase):
    def test_unknown_brief_blocks(self):
        import preflight
        self.assertEqual(preflight.preflight("no-such-brief-xyz")["verdict"], "BLOCK")

    def test_outclass_briefs_pass_lint_and_rules(self):
        import preflight
        for bid in ("repo-edge0-01", "repo-deeptutor-01", "repo-impeccable-01", "repo-cleanyourtv-01"):
            r = preflight.preflight(bid)
            blocks = [x for x in r["results"] if x["status"] == "BLOCK"]
            self.assertEqual(blocks, [], bid)


if __name__ == "__main__":
    unittest.main()
