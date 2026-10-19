"""Creative-treatment tests (PLAYBOOK §8A): the viewer-first layer above the gates."""
import unittest

from test_brief_lint import BriefLintTests, brief


class TreatmentLintTests(BriefLintTests):
    def ids(self):
        return {f["id"] for f in self.last_findings}

    def test_missing_treatment_warns_not_errors(self):
        b = brief()
        del b["treatment"]
        _, errors, _ = self.lint(b)
        self.assertIn("BL120", self.ids())
        self.assertEqual([e for e in errors if "[BL12" in e], [])

    def test_valid_treatment_is_clean(self):
        _, errors, warns = self.lint(brief())
        self.assertEqual(errors, [])
        self.assertEqual(warns, [])

    def test_bad_archetype_errors(self):
        b = brief()
        b["treatment"]["archetype"] = "slideshow"
        self.lint(b)
        self.assertIn("BL122", self.ids())

    def test_cover_text_over_four_words_errors(self):
        b = brief()
        b["treatment"]["cover_concepts"][0]["text"] = "THIS COVER HAS FIVE WORDS"
        self.lint(b)
        self.assertIn("BL126", self.ids())

    def test_payoff_scene_must_exist(self):
        b = brief()
        b["treatment"]["open_loop"]["payoff_scene"] = "nope"
        self.lint(b)
        self.assertIn("BL123", self.ids())

    def test_selected_cover_range(self):
        b = brief()
        b["treatment"]["selected_cover"] = 5
        self.lint(b)
        self.assertIn("BL127", self.ids())


if __name__ == "__main__":
    unittest.main()
