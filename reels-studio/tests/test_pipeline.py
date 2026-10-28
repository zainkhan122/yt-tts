"""Tests for the unified pipeline orchestrator."""
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent


class PipelineWiringTests(unittest.TestCase):
    def test_all_stages_defined(self):
        """All 9 pipeline stages must be defined with contracts."""
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import pipeline as pl
        for name in pl.STAGE_ORDER:
            self.assertIn(name, pl.STAGES)
            stage = pl.STAGES[name]
            for key in ("module", "produces", "consumes", "gate"):
                self.assertIn(key, stage)
                self.assertGreater(len(stage[key]), 0)

    def test_stage_order_is_correct(self):
        """Pipeline stages must flow in logical order."""
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import pipeline as pl
        self.assertEqual(pl.STAGE_ORDER, (
            "discover", "select", "research", "script",
            "voice", "assets", "gate", "render", "publish"
        ))

    def test_wiring_check_passes(self):
        """All stage modules must be resolvable."""
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import pipeline as pl
        issues = pl.check_wiring()
        self.assertEqual(len(issues), 0, f"Wiring issues: {issues}")

    def test_stage_status_returns_dict(self):
        """Stage status must return a dict for each stage."""
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import pipeline as pl
        status = pl.stage_status()
        for name in pl.STAGE_ORDER:
            self.assertIn(name, status)
            self.assertIsInstance(status[name], dict)
            self.assertIn("ready", status[name])


class PipelineIntegrationTests(unittest.TestCase):
    def test_reference_study_reports_exist(self):
        """Reference analyzer must have produced reports."""
        study_dir = ROOT / "research" / "reference-study"
        self.assertTrue(study_dir.exists(), "reference-study directory not found")
        reports = list(study_dir.glob("*.md"))
        self.assertGreater(len(reports), 0, "No reference study reports found")
        # Check at least one report has real data
        content = reports[0].read_text()
        self.assertIn("# Reference analysis:", content)

    def test_sources_csv_cleaned(self):
        """Instagram entry for gittrend.io must be removed."""
        import csv
        sources = ROOT / "research" / "sources.csv"
        rows = list(csv.DictReader(open(sources)))
        ig_rows = [r for r in rows if r["type"] == "instagram" and r["handle"] == "gittrend.io"]
        self.assertEqual(len(ig_rows), 0, "Instagram gittrend.io entry still present")

    def test_audio_analyzer_syntax(self):
        """audio_analyze.py must parse cleanly."""
        import ast
        src = (ROOT / "tools" / "audio_analyze.py").read_text()
        ast.parse(src)

    def test_reference_analyzer_syntax(self):
        """reference_analyzer.py must parse cleanly."""
        import ast
        src = (ROOT / "tools" / "reference_analyzer.py").read_text()
        ast.parse(src)


if __name__ == "__main__":
    unittest.main()
