"""Topic selection v4: random daily pick count, judgment record checks, owner-approved claims."""
import datetime as dt
import random
import unittest

from studio import select as S

TODAY = dt.date(2026, 10, 31)
CFG = S.load_config()


def pick(**kw):
    base = {
        "id": "p1", "subject": "Free DeepSeek proxy", "source_url": "https://github.com/x/y",
        "found_at": TODAY.isoformat(), "classification": "a free-model proxy: a free offer and a tool",
        "viewer_gain": "run a strong model with no key in five minutes",
        "demand": {"autocomplete_queries": ["free deepseek"]},
        "competition": "three videos, all over 60 days old",
        "media_plan": "terminal graphic for the install command",
        "reason": "fresh, provable, not covered this month",
        "claims": [{"text": "runs with no key", "source_line": "README: 'no API key needed'"}],
    }
    base.update(kw)
    return base


class PickCount(unittest.TestCase):
    def test_draw_is_within_range_and_recorded(self):
        seen = set()
        for seed in range(200):
            n = S.draw_pick_count(CFG, random.Random(seed))
            self.assertTrue(2 <= n <= 7)
            seen.add(n)
        self.assertEqual(seen, {2, 3, 4, 5, 6, 7})  # the draw really is spread across the range
        rec = S.new_day_record(TODAY, CFG, random.Random(1))
        self.assertEqual(rec["pick_count"], S.draw_pick_count(CFG, random.Random(1)))
        self.assertEqual(rec["picks"], [])

    def test_bad_range_is_refused(self):
        with self.assertRaises(ValueError):
            S.draw_pick_count({"picks_per_day": {"min": 5, "max": 2}})


class PickRecord(unittest.TestCase):
    def test_complete_record_passes(self):
        self.assertEqual(S.validate_pick(pick(), today=TODAY, cfg=CFG), [])

    def test_missing_judgment_fields_block(self):
        bad = pick()
        bad["viewer_gain"] = "  "
        problems = S.validate_pick(bad, today=TODAY, cfg=CFG)
        self.assertTrue(any("viewer_gain" in p for p in problems))

    def test_source_must_be_https(self):
        problems = S.validate_pick(pick(source_url="http://example.com/x"), today=TODAY, cfg=CFG)
        self.assertTrue(any("https" in p for p in problems))

    def test_freshness_is_one_day_unless_reason_given(self):
        old = (TODAY - dt.timedelta(days=5)).isoformat()
        problems = S.validate_pick(pick(found_at=old), today=TODAY, cfg=CFG)
        self.assertTrue(any("older_reason" in p for p in problems))
        ok = S.validate_pick(pick(found_at=old, older_reason="still climbing on the trending list"), today=TODAY, cfg=CFG)
        self.assertEqual(ok, [])

    def test_claim_needs_source_or_owner_approval(self):
        p = pick(claims=[{"text": "no usage cap"}])
        self.assertTrue(any("no usage cap" in x for x in S.validate_pick(p, today=TODAY, cfg=CFG)))
        approved = pick(claims=[{"text": "no usage cap", "owner_approved": True}])
        self.assertEqual(S.validate_pick(approved, today=TODAY, cfg=CFG), [])

    def test_autocomplete_evidence_is_required(self):
        p = pick(demand={})
        self.assertTrue(any("autocomplete" in x for x in S.validate_pick(p, today=TODAY, cfg=CFG)))


class DayRecord(unittest.TestCase):
    def test_pick_count_must_match_draw(self):
        day = {"date": TODAY.isoformat(), "pick_count": 3, "picks": [pick(id="a", subject="A"), pick(id="b", subject="B")]}
        self.assertTrue(any("draw was 3" in p for p in S.validate_day(day, today=TODAY, cfg=CFG)))

    def test_same_subject_twice_in_a_day_blocks(self):
        day = {"date": TODAY.isoformat(), "pick_count": 2,
               "picks": [pick(id="a", subject="Same Thing"), pick(id="b", subject="same thing!")]}
        self.assertTrue(any("repeated" in p for p in S.validate_day(day, today=TODAY, cfg=CFG)))

    def test_recent_subject_is_blocked_inside_novelty_window(self):
        day = {"date": TODAY.isoformat(), "pick_count": 2,
               "picks": [pick(id="a", subject="A"), pick(id="b", subject="B")]}
        recent = [("A", TODAY - dt.timedelta(days=10))]
        self.assertTrue(any("already covered" in p for p in S.validate_day(day, today=TODAY, cfg=CFG, recent_subjects=recent)))

    def test_valid_day_passes(self):
        day = {"date": TODAY.isoformat(), "pick_count": 2,
               "picks": [pick(id="a", subject="A"), pick(id="b", subject="B")]}
        self.assertEqual(S.validate_day(day, today=TODAY, cfg=CFG), [])


if __name__ == "__main__":
    unittest.main()
