"""Tests for the v2 shorts system: hard rules, brief checks, copy checks, draw, CLI, planner gate."""
import copy
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from studio import check as check_cli
from studio import draw
from studio.rules import (CREDIT_PATTERN, DISCLOSURE_TEXT, GENERIC_TAGS, LIMITS, PROMO_PATTERN,
                          assemble, check_brief, check_copy, errors)

ROOT = Path(__file__).resolve().parent.parent
TODAY = dt.date(2026, 10, 21)


def codes(findings, level="error"):
    return sorted(f.code for f in findings if f.level == level)


def good_copy():
    return {
        "youtube": {"title": "Scrawl: Stop Describing the Bug", "description": "Show the bug. Free and open source.",
                    "hashtags": ["#Shorts", "#ClaudeCode"]},
        "tiktok": {"caption": "Show the bug, not the paragraphs.", "hashtags": ["#DevTools", "#MacApps"]},
        "instagram": {"caption": "Record the bug once and send it.", "hashtags": ["#ClaudeCode", "#macOS"]},
        "facebook": {"caption": "Describing a bug takes forever. Record it instead.", "hashtags": ["#macOS"]},
        "x": {"text": "Record the bug, send the frames.", "hashtags": ["#macOS"]},
    }


def good_brief():
    return {
        "id": "t-01", "title": "Test", "niche": "dev tools", "lang": "en-us",
        "viewer": {"who": "developers", "problem": "they describe bugs in text and the agent guesses"},
        "idea": "Show the bug instead of describing it.",
        "claims": [{"id": "c1", "text": "Free and open source.", "source": "https://github.com/x/y"}],
        "proof_plan": [{"claim": "c1", "evidence": "source:https://github.com/x/y", "how_shown": "spoken"}],
        "scenes": [{"type": "page", "say": "Describing a bug takes four paragraphs."},
                   {"type": "proof", "say": "Record the screen and talk while you point."}],
        "duration_s": 12,
        "sources": ["https://github.com/x/y"],
        "review": {"reviewed_at": "2026-10-21T09:00:00Z", "expires_at": "2026-10-28", "reviewer": "agent"},
        "seo": good_copy(),
    }


class CreditAndPromoPatterns(unittest.TestCase):
    def test_credit_text_is_caught(self):
        for bad in ["Credits: own captures", "Own browser captures of the site", "captured on 2026-10-20",
                    "(checked 2026-10-20)", "Attribution: the repo", "© 2026 someone", "capture date 10/20"]:
            self.assertTrue(CREDIT_PATTERN.search(bad), bad)

    def test_plain_copy_is_not_flagged_as_credit(self):
        for ok in ["Scrawl records your screen while you talk.", "Free and open source under MIT.",
                   "Five free prompts, then sign in.", "The copy it writes is placeholder text."]:
            self.assertFalse(CREDIT_PATTERN.search(ok), ok)

    def test_promo_words_are_caught(self):
        for bad in ["a game-changer for devs", "truly revolutionary", "This is a must-have", "in this video we"]:
            self.assertTrue(PROMO_PATTERN.search(bad), bad)
        self.assertFalse(PROMO_PATTERN.search("Record the screen and send the frames."))

    def test_generic_tags_set(self):
        for tag in ["#ai", "#coding", "#video", "#fyp", "#viral"]:
            self.assertIn(tag, GENERIC_TAGS)
        for tag in ["#shorts", "#devtools", "#claudecode", "#webdev"]:
            self.assertNotIn(tag, GENERIC_TAGS, "platform and niche tags must not be generic")


class Assembly(unittest.TestCase):
    def test_facebook_gets_disclosure_and_hashtags_once(self):
        text = assemble(good_copy(), "facebook")
        self.assertEqual(text.count(DISCLOSURE_TEXT), 1)
        self.assertTrue(text.endswith("#macOS"))

    def test_other_platforms_have_no_disclosure(self):
        for p in ("youtube", "tiktok", "instagram", "x"):
            self.assertNotIn(DISCLOSURE_TEXT, assemble(good_copy(), p))

    def test_hashtags_are_not_written_into_copy(self):
        c = good_copy()
        self.assertNotIn("#", c["tiktok"]["caption"])


class CopyRules(unittest.TestCase):
    def brief(self, **over):
        b = good_brief()
        b["seo"] = copy.deepcopy(good_copy())
        for k, v in over.items():
            b["seo"][k] = v
        return b

    def test_good_copy_passes(self):
        self.assertEqual(errors(check_copy(good_brief())), [])

    def test_missing_platform_is_an_error(self):
        b = good_brief()
        del b["seo"]["x"]
        self.assertIn("C001", codes(check_copy(b)))

    def test_title_length(self):
        b = good_brief()
        b["seo"]["youtube"]["title"] = "x" * 101
        self.assertIn("C002", codes(check_copy(b)))
        b["seo"]["youtube"]["title"] = ""
        self.assertIn("C002", codes(check_copy(b)))

    def test_credit_in_visible_copy_is_error(self):
        b = good_brief()
        b["seo"]["tiktok"]["caption"] = "Show the bug. Own captures of the app."
        self.assertIn("C010", codes(check_copy(b)))

    def test_promo_in_copy_is_error(self):
        b = good_brief()
        b["seo"]["instagram"]["caption"] = "A game-changer for every dev."
        self.assertIn("C011", codes(check_copy(b)))

    def test_placeholder_in_copy_is_error(self):
        b = good_brief()
        b["seo"]["x"]["text"] = "TODO write the line [link]"
        self.assertIn("C012", codes(check_copy(b)))

    def test_character_limits_use_final_text(self):
        b = good_brief()
        b["seo"]["x"]["text"] = "word " * 60  # over 280 once hashtags are added
        self.assertIn("C013", codes(check_copy(b)))
        self.assertLessEqual(LIMITS["x"], 280)

    def test_non_https_link_is_error(self):
        b = good_brief()
        b["seo"]["youtube"]["description"] = "see http://example.com for more"
        self.assertIn("C014", codes(check_copy(b)))

    def test_generic_tag_is_error(self):
        b = good_brief()
        b["seo"]["tiktok"]["hashtags"] = ["#AI", "#DevTools"]
        self.assertIn("C022", codes(check_copy(b)))

    def test_malformed_tag_is_error(self):
        b = good_brief()
        b["seo"]["tiktok"]["hashtags"] = ["#Dev Tools", "#MacApps"]
        self.assertIn("C021", codes(check_copy(b)))

    def test_hashtag_count_range(self):
        b = good_brief()
        b["seo"]["facebook"]["hashtags"] = []
        self.assertIn("C023", codes(check_copy(b)))
        b["seo"]["facebook"]["hashtags"] = ["#a1", "#b1", "#c1", "#d1"]
        self.assertIn("C023", codes(check_copy(b)))

    def test_youtube_requires_shorts_tag(self):
        b = good_brief()
        b["seo"]["youtube"]["hashtags"] = ["#ClaudeCode", "#MacApps"]
        self.assertIn("C024", codes(check_copy(b)))

    def test_identical_copy_across_platforms_is_error(self):
        b = good_brief()
        same = "Record the bug once and send it to the agent."
        b["seo"]["tiktok"]["caption"] = same
        b["seo"]["instagram"]["caption"] = same
        b["seo"]["tiktok"]["hashtags"] = ["#DevTools", "#MacApps"]
        b["seo"]["instagram"]["hashtags"] = ["#DevTools", "#MacApps"]
        self.assertIn("C040", codes(check_copy(b)))

    def test_facebook_disclosure_required_when_synthetic(self):
        b = good_brief()
        self.assertEqual(errors(check_copy(b)), [])
        # Forcing an empty disclosure must not silently pass a synthetic voice.
        self.assertIn("C031", codes(check_copy(b, disclosure="")))

    def test_real_voice_needs_no_disclosure(self):
        b = good_brief()
        b["voice"] = {"synthetic": False}
        self.assertEqual(errors(check_copy(b, disclosure="")), [])


class BriefRules(unittest.TestCase):
    def test_good_brief_passes(self):
        self.assertEqual(errors(check_brief(good_brief(), today=TODAY)), [])

    def test_template_field_is_refused(self):
        b = good_brief()
        b["template"] = "tool-spotlight"
        self.assertIn("B001", codes(check_brief(b, today=TODAY)))

    def test_credits_field_is_refused(self):
        b = good_brief()
        b["credits_on_screen"] = "Own captures"
        self.assertIn("B002", codes(check_brief(b, today=TODAY)))

    def test_missing_required_fields_stop_early(self):
        findings = check_brief({"id": "x"}, today=TODAY)
        self.assertTrue(all(f.code in ("B003", "B001", "B002") for f in findings))
        self.assertIn("B003", codes(findings))

    def test_viewer_needs_problem(self):
        b = good_brief()
        b["viewer"] = {"who": "devs"}
        self.assertIn("B010", codes(check_brief(b, today=TODAY)))

    def test_scene_rules(self):
        b = good_brief()
        b["scenes"][0] = {"type": "page", "say": ""}
        self.assertIn("B022", codes(check_brief(b, today=TODAY)))
        b["scenes"][0] = {"type": "page", "say": "", "hold": 2.0}
        self.assertNotIn("B022", codes(check_brief(b, today=TODAY)))
        b["scenes"][0] = {"say": "no type"}
        self.assertIn("B021", codes(check_brief(b, today=TODAY)))
        b["scenes"] = []  # an empty list is a missing required field
        self.assertIn("B003", codes(check_brief(b, today=TODAY)))
        b["scenes"] = "not a list"
        self.assertIn("B020", codes(check_brief(b, today=TODAY)))

    def test_no_fixed_scene_order_is_required(self):
        b = good_brief()
        b["scenes"] = [{"type": "cta", "say": "Follow for more."}, {"type": "page", "say": "Describing a bug takes four paragraphs."}]
        self.assertEqual(errors(check_brief(b, today=TODAY)), [])

    def test_credit_or_placeholder_in_scene_text(self):
        b = good_brief()
        b["scenes"][1]["say"] = "Recorded with own captures from the site."
        self.assertIn("B030", codes(check_brief(b, today=TODAY)))
        b = good_brief()
        b["scenes"][1]["say"] = "TBD line here"
        self.assertIn("B032", codes(check_brief(b, today=TODAY)))

    def test_promo_in_scene_is_warning_only(self):
        b = good_brief()
        b["scenes"][1]["say"] = "A game-changer for every developer."
        findings = check_brief(b, today=TODAY)
        self.assertEqual(errors(findings), [])
        self.assertIn("B031", codes(findings, level="warning"))

    def test_licence_in_opening_scene_is_error(self):
        b = good_brief()
        b["scenes"][0]["say"] = "This MIT licensed tool records your screen."
        self.assertIn("B040", codes(check_brief(b, today=TODAY)))

    def test_spoken_length_must_fit_duration(self):
        b = good_brief()
        b["duration_s"] = 2
        self.assertIn("B023", codes(check_brief(b, today=TODAY)))

    def test_claim_needs_https_source(self):
        b = good_brief()
        b["claims"][0]["source"] = "github.com/x/y"
        self.assertIn("B051", codes(check_brief(b, today=TODAY)))

    def test_every_claim_needs_proof(self):
        b = good_brief()
        b["claims"].append({"id": "c2", "text": "Works offline.", "source": "https://example.com/a"})
        self.assertIn("B054", codes(check_brief(b, today=TODAY)))

    def test_proof_entry_must_point_at_a_claim(self):
        b = good_brief()
        b["proof_plan"][0]["claim"] = "nope"
        self.assertIn("B052", codes(check_brief(b, today=TODAY)))

    def test_evidence_format(self):
        b = good_brief()
        b["proof_plan"][0]["evidence"] = "trust me"
        self.assertIn("B053", codes(check_brief(b, today=TODAY)))

    def test_capture_evidence_must_exist(self):
        with tempfile.TemporaryDirectory() as d:
            b = good_brief()
            b["proof_plan"][0]["evidence"] = "capture:missing.jpg"
            self.assertIn("B053", codes(check_brief(b, today=TODAY, captures_dir=Path(d))))
            (Path(d) / "missing.jpg").write_bytes(b"x")
            self.assertEqual(errors(check_brief(b, today=TODAY, captures_dir=Path(d))), [])

    def test_owner_test_evidence_is_accepted(self):
        b = good_brief()
        b["proof_plan"][0]["evidence"] = "owner_test"
        self.assertEqual(errors(check_brief(b, today=TODAY)), [])

    def test_review_expiry_is_not_a_gate(self):
        # Owner 31 Oct 2026: fact-age rules are not needed; an old review date must not block a brief.
        b = good_brief()
        b["review"]["expires_at"] = "2026-10-20"
        self.assertNotIn("B060", codes(check_brief(b, today=TODAY)))


class RealBriefs(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "briefs" / f"{name}.json").read_text(encoding="utf-8"))

    def test_rewritten_shorts_pass(self):
        captures = ROOT / "captures" / "tool-scrawl-01"
        for name in ("tool-scrawl-01", "tool-fx0-01"):
            b = self.load(name)
            findings = check_brief(b, today=TODAY, captures_dir=captures if name == "tool-scrawl-01" else None)
            self.assertEqual(errors(findings), [], name)
            self.assertNotIn("template", b)
            self.assertNotIn("credits_on_screen", b)
            self.assertNotIn("post", b)

    def test_rewritten_copy_has_no_unsupported_claims(self):
        # Lines the owner's facts do not support were removed from the shorts' copy.
        blob = json.dumps(self.load("tool-fx0-01")["seo"]).lower()
        for phrase in ("publishes it", "keeps each version", "roll back", "ten seconds"):
            self.assertNotIn(phrase, blob)

    def test_no_brief_in_repo_still_has_template(self):
        for f in (ROOT / "briefs").glob("*.json"):
            self.assertNotIn('"template"', f.read_text(encoding="utf-8"), f.name)


class DrawRules(unittest.TestCase):
    def test_draw_is_within_bounds(self):
        class Fake:
            def __init__(self, v):
                self.v = v

            def randint(self, a, b):
                return self.v
        self.assertEqual(draw.draw_count(Fake(1)), 1)
        self.assertEqual(draw.draw_count(Fake(5)), 5)
        for _ in range(200):
            self.assertTrue(1 <= draw.draw_count() <= 5)

    def test_record_refuses_overwrite_and_bad_counts(self):
        rec = draw.record_draw({}, "2026-10-22", 3, "2026-10-21T08:00:00+00:00")
        with self.assertRaises(ValueError):
            draw.record_draw(rec, "2026-10-22", 4, "2026-10-21T09:00:00+00:00")
        with self.assertRaises(ValueError):
            draw.record_draw({}, "2026-10-23", 6, "2026-10-21T08:00:00+00:00")
        with self.assertRaises(ValueError):
            draw.record_draw({}, "2026-10-23", 0, "2026-10-21T08:00:00+00:00")

    def test_reconcile_matches(self):
        rec = draw.record_draw({}, "2026-10-21", 2, "2026-10-21T08:00:00+00:00")
        slots = [draw.Slot("a", "2026-10-21T13:00:00-04:00"), draw.Slot("b", "2026-10-21T15:00:00-04:00")]
        self.assertEqual(draw.reconcile(rec, "2026-10-21", slots), [])

    def test_same_video_twice_counts_once(self):
        rec = draw.record_draw({}, "2026-10-21", 1, "2026-10-21T08:00:00+00:00")
        slots = [draw.Slot("a", "2026-10-21T13:00:00-04:00"), draw.Slot("a", "2026-10-21T15:00:00-04:00")]
        self.assertEqual(draw.reconcile(rec, "2026-10-21", slots), [])

    def test_over_schedule_is_error(self):
        rec = draw.record_draw({}, "2026-10-21", 1, "2026-10-21T08:00:00+00:00")
        slots = [draw.Slot("a", "2026-10-21T13:00:00-04:00"), draw.Slot("b", "2026-10-21T15:00:00-04:00")]
        self.assertEqual(codes(draw.reconcile(rec, "2026-10-21", slots)), ["D003"])

    def test_under_schedule_needs_a_reason(self):
        rec = draw.record_draw({}, "2026-10-21", 3, "2026-10-21T08:00:00+00:00")
        slots = [draw.Slot("a", "2026-10-21T13:00:00-04:00")]
        self.assertEqual(codes(draw.reconcile(rec, "2026-10-21", slots), "warning"), ["D004"])
        self.assertEqual(draw.reconcile(rec, "2026-10-21", slots, reason="one video held for approval"), [])

    def test_late_draw_is_error(self):
        rec = draw.record_draw({}, "2026-10-21", 2, "2026-10-21T18:00:00+00:00")  # after the 17:00Z slot
        slots = [draw.Slot("a", "2026-10-21T13:00:00-04:00"), draw.Slot("b", "2026-10-21T15:00:00-04:00")]
        self.assertIn("D002", codes(draw.reconcile(rec, "2026-10-21", slots)))

    def test_schedule_without_draw_is_error(self):
        slots = [draw.Slot("a", "2026-10-21T13:00:00-04:00")]
        self.assertEqual(codes(draw.reconcile({}, "2026-10-21", slots)), ["D001"])

    def test_reconcile_uses_current_record(self):
        # The recorded 21 Oct draw in the tracker is 1, but two videos are scheduled that day.
        rec = {"days": {"2026-10-21": {"count": 1, "drawn_at": "2026-10-21T07:26:03+00:00", "method": "x"}}}
        slots = [draw.Slot("tool-scrawl-01", "2026-10-21T13:00:00-04:00"),
                 draw.Slot("tool-fx0-01", "2026-10-21T18:00:00-04:00")]
        self.assertIn("D003", codes(draw.reconcile(rec, "2026-10-21", slots)))


class CliAndPlanner(unittest.TestCase):
    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            ok = Path(d) / "ok.json"
            bad = Path(d) / "bad.json"
            ok.write_text(json.dumps(good_brief()), encoding="utf-8")
            b = good_brief()
            b["template"] = "x"
            bad.write_text(json.dumps(b), encoding="utf-8")
            self.assertEqual(check_cli.main([str(ok), "--today", "2026-10-21"]), 0)
            self.assertEqual(check_cli.main([str(bad), "--today", "2026-10-21"]), 1)
            self.assertEqual(check_cli.main([str(Path(d) / "missing.json")]), 1)

    def test_planner_refuses_legacy_brief(self):
        from tools.post import planner
        cfg = {"disclosure": {"facebook_caption": DISCLOSURE_TEXT}}
        with self.assertRaises(ValueError) as ctx:
            planner.copy_for({"video_id": "tool-muse-01"}, "tiktok", cfg)
        self.assertIn("studio checks failed", str(ctx.exception))

    def test_planner_uses_final_text_for_shorts(self):
        from tools.post import planner
        cfg = {"disclosure": {"facebook_caption": DISCLOSURE_TEXT}}
        text, brief = planner.copy_for({"video_id": "tool-scrawl-01"}, "facebook", cfg)
        self.assertIn(DISCLOSURE_TEXT, text)
        self.assertEqual(text, assemble(brief["seo"], "facebook", DISCLOSURE_TEXT))


if __name__ == "__main__":
    unittest.main()
