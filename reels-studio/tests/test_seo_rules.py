import json
import tempfile
import unittest
from pathlib import Path

from tools import seo_pack

GOOD = {
    "id": "repo-x-01",
    "scenes": [{"id": "hook", "say": "AI voice cloning runs on your own computer, no cloud upload needed.",
                "headline": "AI VOICE CLONING", "sub": "open source"}],
    "seo": {
        "keyword": "AI voice cloning",
        "aliases": ["ElevenLabs alternative", "AI video dubbing", "clone voice on PC"],
        "onscreen_first3s": "AI VOICE CLONING",
        "youtube": {
            "title": "AI Voice Cloning on Your Own PC (Open Source)",
            "description": "Open-source, fully local AI voice cloning and video dubbing. An ElevenLabs alternative that runs on your own computer.\n\nTool page: https://github.com/o/r\n\n#shorts #aivoicecloning #aidubbing #localai",
            "tags": ["AI voice cloning", "voice cloning", "ElevenLabs alternative", "AI video dubbing", "clone voice on PC", "open source voice AI"],
            "hashtags": ["#shorts", "#aivoicecloning", "#aidubbing", "#localai"],
        },
        "instagram": {"caption": "AI voice cloning and video dubbing, open source and fully local.", "hashtags": ["#aivoicecloning", "#aidubbing", "#localai"]},
        "facebook": {"caption": "AI voice cloning and video dubbing that runs on your own computer.", "hashtags": ["#aivoicecloning", "#aidubbing"]},
        "tiktok": {"caption": "AI voice cloning, open source.", "hashtags": ["#aivoicecloning", "#aidubbing", "#localai"]},
        "x": {"text": "AI voice cloning, open source and fully local.", "hashtags": ["#aivoicecloning"]},
    },
}


def run(brief):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "b.json"
        p.write_text(json.dumps(brief, ensure_ascii=False), encoding="utf-8")
        return seo_pack.check(str(p))


class SeoRuleTests(unittest.TestCase):
    def test_search_tuned_copy_passes(self):
        _, errors, _, _, *_ = run(GOOD)
        self.assertEqual(errors, [])

    def test_keyword_missing_from_title_and_tags_fails(self):
        bad = json.loads(json.dumps(GOOD))
        bad["seo"]["youtube"]["title"] = "Clone and dub voices on your own machine (open source)"
        bad["seo"]["youtube"]["tags"] = ["voice cloning", "AI dubbing"]
        _, errors, *_ = run(bad)
        joined = " ".join(errors)
        self.assertIn("SP100", joined)
        self.assertIn("SP101", joined)

    def test_link_outside_youtube_description_fails(self):
        bad = json.loads(json.dumps(GOOD))
        bad["seo"]["instagram"]["caption"] = "AI voice cloning at https://github.com/o/r"
        _, errors, *_ = run(bad)
        self.assertIn("SP103", " ".join(errors))

    def test_description_must_open_with_keyword_sentence(self):
        bad = json.loads(json.dumps(GOOD))
        bad["seo"]["youtube"]["description"] = "Tool.\n\n#shorts #aivoicecloning #aidubbing #localai"
        _, errors, *_ = run(bad)
        self.assertIn("SP102", " ".join(errors))

    def test_no_keyword_hashtag_fails(self):
        bad = json.loads(json.dumps(GOOD))
        bad["seo"]["instagram"]["hashtags"] = ["#coding", "#tools"]
        _, errors, *_ = run(bad)
        self.assertIn("SP104", " ".join(errors))


if __name__ == "__main__":
    unittest.main()
