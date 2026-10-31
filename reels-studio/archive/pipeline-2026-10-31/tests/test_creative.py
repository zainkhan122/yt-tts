"""Creative-treatment tests (PLAYBOOK §8A): the viewer-first layer above the gates."""
import unittest

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(__file__))  # sibling import when run as tests.test_creative
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

    def test_structure_must_follow_the_archetype_grammar(self):
        b = brief()
        b["treatment"]["structure"] = [{"scene": "hook", "beat": "demo"},
                                       {"scene": "how", "beat": "proof"},
                                       {"scene": "catch", "beat": "catch"},
                                       {"scene": "cta", "beat": "close"}]
        self.lint(b)
        self.assertNotIn("BL130", self.ids())
        b["treatment"]["structure"] = [{"scene": "hook", "beat": "demo"},
                                       {"scene": "how", "beat": "proof"},
                                       {"scene": "catch", "beat": "catch"}]
        self.lint(b)
        self.assertIn("BL129", self.ids(), "a scene without a beat must fail (it would fall back to the template)")

    def test_structure_cannot_reuse_the_same_skeleton_for_every_archetype(self):
        b = brief()
        b["treatment"]["structure"] = [{"scene": "hook", "beat": "claim"},
                                       {"scene": "how", "beat": "evidence"},
                                       {"scene": "catch", "beat": "catch"},
                                       {"scene": "cta", "beat": "close"}]
        self.lint(b)  # demo-first grammar wants demo/proof/how/catch/close
        self.assertIn("BL130", self.ids())

    def test_structure_must_open_and_close_correctly(self):
        b = brief()
        b["treatment"]["structure"] = [{"scene": "hook", "beat": "proof"},
                                       {"scene": "how", "beat": "demo"},
                                       {"scene": "catch", "beat": "catch"},
                                       {"scene": "cta", "beat": "close"}]
        self.lint(b)
        self.assertIn("BL130", self.ids(), "must open on the archetype's first beat")
        b["treatment"]["structure"] = [{"scene": "hook", "beat": "demo"},
                                       {"scene": "how", "beat": "proof"},
                                       {"scene": "catch", "beat": "catch"},
                                       {"scene": "cta", "beat": "how"}]
        self.lint(b)
        self.assertIn("BL130", self.ids(), "must end on close")

    def test_proof_moment_cannot_be_a_card(self):
        b = brief()
        b["treatment"]["proof_moment"] = "catch"  # a verdict card, not product evidence
        self.lint(b)
        self.assertIn("BL128", self.ids())

    def test_selected_cover_range(self):
        b = brief()
        b["treatment"]["selected_cover"] = 5
        self.lint(b)
        self.assertIn("BL127", self.ids())


if __name__ == "__main__":
    unittest.main()
