"""Owner rule 2026-10-21: viewer-first copy, niche hashtags, no credits in visible text."""
import unittest

from tools import seo_pack


def _seo(**overrides):
    base = {
        "keyword": "Scrawl",
        "aliases": [],
        "youtube": {"title": "Scrawl: Show Your Agent the Bug", "description": "Scrawl: describe less, show more. Free and open source.",
                    "hashtags": ["#Shorts", "#DevTools", "#AICoding"], "tags": ["Scrawl"]},
        "tiktok": {"caption": "Scrawl: show the bug, not the paragraphs.", "hashtags": ["#DevTools", "#AICoding", "#MacApp"]},
        "instagram": {"caption": "Scrawl: record the bug once.", "hashtags": ["#DevTools", "#AICoding", "#MacApp"]},
        "facebook": {"caption": "Scrawl: record your screen while you talk.", "hashtags": ["#DevTools", "#AICoding"]},
        "x": {"text": "Scrawl: show the bug instead of describing it.", "hashtags": ["#DevTools"]},
    }
    base.update(overrides)
    return base


class CopyRuleTests(unittest.TestCase):
    def _codes(self, seo):
        brief = {"id": "t-01", "seo": seo, "scenes": [], "onscreen_first3s": "SCRAWL"}
        findings = seo_pack.check(brief) if hasattr(seo_pack, "check") else None
        return findings

    def test_regex_flags_credit_and_capture_text(self):
        for bad in ["Credits: Own captures of the repo", "Own browser captures of the site", "(checked 2026-10-19)"]:
            self.assertTrue(seo_pack.CREDIT_TEXT.search(bad), bad)

    def test_regex_allows_plain_copy(self):
        for good in ["Scrawl records your screen while you talk.", "Free and open source, Mac only for now."]:
            self.assertFalse(seo_pack.CREDIT_TEXT.search(good), good)

    def test_generic_tags_are_banned_list(self):
        for tag in ["#AI", "#Coding", "#Video", "#Tech", "#viral"]:
            self.assertIn(tag.lower(), seo_pack.GENERIC_TAGS)
        for tag in ["#DevTools", "#AICoding", "#WebDev"]:
            self.assertNotIn(tag.lower(), seo_pack.GENERIC_TAGS)

    def test_planner_never_appends_credits(self):
        import inspect
        from tools.post import planner
        source = inspect.getsource(planner.copy_for)
        self.assertNotIn('"\\n\\nCredits: "', source)
        self.assertNotIn("Credits: \" + credits", source)


if __name__ == "__main__":
    unittest.main()
