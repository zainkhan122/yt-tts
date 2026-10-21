"""Topic selection v3: ranking by value, proof, freshness, deadlines and category balance. Never by template."""
import datetime as dt
import unittest
from pathlib import Path

from studio import topics as T

TODAY = dt.date(2026, 10, 21)
CFG = T.load_config()
STUDY = TODAY


def cand(id, cat="tool", value=3.0, found=TODAY, **kw):
    base = dict(id=id, subject=f"subject {id}", category=cat, source_url=f"https://example.com/{id}",
                found_at=found, value=value)
    base.update(kw)
    return T.Candidate(**base)


class Discovery(unittest.TestCase):
    def test_category_comes_from_source(self):
        self.assertEqual(T.category_from_url("https://github.com/a/b"), "repo")
        self.assertEqual(T.category_from_url("https://www.github.com/a/b"), "repo")
        self.assertEqual(T.category_from_url("https://huggingface.co/x/y"), "tool")
        self.assertEqual(T.category_from_url("https://www.youtube.com/shorts/abc"), "unclassified")


class Study(unittest.TestCase):
    def test_refuses_without_study(self):
        with self.assertRaises(T.StudyMissing):
            T.rank([cand("a")], [], None, TODAY)

    def test_refuses_stale_study(self):
        with self.assertRaises(T.StudyMissing):
            T.rank([cand("a")], [], TODAY - dt.timedelta(days=8), TODAY)

    def test_accepts_fresh_study(self):
        picks, _ = T.rank([cand("a")], [], TODAY - dt.timedelta(days=7), TODAY)
        self.assertEqual([p.id for p in picks], ["a"])


class Eligibility(unittest.TestCase):
    def skipped_reason(self, c, recent=()):
        _, skipped = T.rank([c], list(recent), STUDY, TODAY)
        return dict(skipped).get(c.id)

    def test_unclassified_is_not_ranked(self):
        self.assertIn("unclassified", self.skipped_reason(cand("a", cat="unclassified")))

    def test_unjudged_is_not_ranked(self):
        self.assertIn("not judged", self.skipped_reason(cand("a", value=None)))

    def test_needs_https_source(self):
        self.assertIn("https", self.skipped_reason(cand("a", source_url="http://x.io")))

    def test_blocking_risk_flags_exclude(self):
        self.assertIn("blocked", self.skipped_reason(cand("a", risk_flags=("unverified-claim",))))

    def test_non_blocking_flag_still_ranks(self):
        self.assertIsNone(self.skipped_reason(cand("a", risk_flags=("paid-only",))))

    def test_expired_deadline_excluded(self):
        self.assertIn("expired", self.skipped_reason(cand("a", deadline=TODAY - dt.timedelta(days=1))))

    def test_novelty_block(self):
        recent = [("tool", TODAY - dt.timedelta(days=5), "subject a")]
        self.assertIn("covered within", self.skipped_reason(cand("a"), recent))
        recent = [("tool", TODAY - dt.timedelta(days=40), "subject a")]
        self.assertIsNone(self.skipped_reason(cand("a"), recent))


class Ranking(unittest.TestCase):
    def test_value_beats_equal_candidates_on_freshness(self):
        a = cand("a", value=5)
        b = cand("b", value=2)
        picks, _ = T.rank([a, b], [], STUDY, TODAY)
        self.assertEqual(picks[0].id, "a")

    def test_fresher_wins_when_value_equal(self):
        old = cand("old", value=4, found=TODAY - dt.timedelta(days=20))
        new = cand("new", value=4, found=TODAY)
        picks, _ = T.rank([old, new], [], STUDY, TODAY)
        self.assertEqual(picks[0].id, "new")

    def test_proof_counts(self):
        plain = cand("plain", value=4, proof_assets=0)
        proven = cand("proven", value=4, proof_assets=3, official_source=True)
        picks, _ = T.rank([plain, proven], [], STUDY, TODAY)
        self.assertEqual(picks[0].id, "proven")

    def test_deadline_gives_urgency(self):
        normal = cand("normal", value=4)
        urgent = cand("urgent", value=4, deadline=TODAY + dt.timedelta(days=2))
        picks, _ = T.rank([normal, urgent], [], STUDY, TODAY)
        self.assertEqual(picks[0].id, "urgent")

    def test_category_balance_pulls_under_represented_category(self):
        # Recent output is all repos. A tool and a news item of equal value should beat a repo.
        recent = [("repo", TODAY - dt.timedelta(days=i), f"r{i}") for i in range(1, 8)]
        repo = cand("repo-x", cat="repo", value=4)
        tool = cand("tool-x", cat="tool", value=4)
        news = cand("news-x", cat="news", value=4)
        picks, _ = T.rank([repo, tool, news], recent, STUDY, TODAY, n=2)
        self.assertNotIn("repo-x", [p.id for p in picks][:1])

    def test_no_run_longer_than_limit(self):
        limit = CFG["max_consecutive_same_category"]
        cands = [cand(f"r{i}", cat="repo", value=5 - i * 0.1) for i in range(5)]
        cands += [cand("t1", cat="tool", value=2.0), cand("n1", cat="news", value=2.0)]
        picks, _ = T.rank(cands, [], STUDY, TODAY, n=6)
        cats = [p.category for p in picks]
        for i in range(len(cats) - limit):
            window = cats[i:i + limit + 1]
            self.assertFalse(len(set(window)) == 1 and len(window) == limit + 1, cats)

    def test_template_field_is_never_used(self):
        # A candidate's old template-like label must not change its rank.
        a = cand("a", value=3)
        b = cand("b", value=3)
        setattr(a, "type", "repo-spotlight")
        setattr(b, "type", "tool-spotlight")
        p1, _ = T.rank([a, b], [], STUDY, TODAY)
        b2 = cand("b", value=3)
        setattr(b2, "type", "repo-spotlight")
        p2, _ = T.rank([a, b2], [], STUDY, TODAY)
        self.assertEqual([p.score for p in p1], [p.score for p in p2])

    def test_reasons_explain_the_pick(self):
        picks, _ = T.rank([cand("a", value=4, deadline=TODAY + dt.timedelta(days=2))], [], STUDY, TODAY)
        text = " ".join(picks[0].reasons)
        for part in ("value", "fresh", "proof", "mix", "deadline"):
            self.assertIn(part, text)


class RealCandidates(unittest.TestCase):
    def test_meta_offer_is_ranked_with_its_deadline(self):
        cands = T.load_candidates(Path(T.ROOT) / "topics" / "candidates.csv")
        picks, skipped = T.rank(cands, [], STUDY, TODAY)
        self.assertEqual(picks[0].id, "offer-meta-hackathon-2026")
        self.assertIn("deadline", " ".join(picks[0].reasons))

    def test_every_candidate_is_either_picked_or_explained(self):
        cands = T.load_candidates(Path(T.ROOT) / "topics" / "candidates.csv")
        picks, skipped = T.rank(cands, [], STUDY, TODAY, n=50)
        ids = {p.id for p in picks} | {s[0] for s in skipped}
        self.assertEqual(ids, {c.id for c in cands})

    def test_candidate_ids_are_safe_slugs(self):
        import re
        for c in T.load_candidates(Path(T.ROOT) / "topics" / "candidates.csv"):
            self.assertRegex(c.id, r"^[a-z0-9][a-z0-9-]*$")


class Cli(unittest.TestCase):
    def test_cli_refuses_without_current_study(self):
        self.assertEqual(T.main(["--study-date", "2026-09-01", "--today", "2026-10-21"]), 1)

    def test_cli_ranks_with_current_study(self):
        self.assertEqual(T.main(["--study-date", "2026-10-21", "--today", "2026-10-21", "-n", "3"]), 0)


if __name__ == "__main__":
    unittest.main()
