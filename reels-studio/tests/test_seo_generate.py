"""The SEO generator: copy for every platform, judged by the same rulebook the shipping gate uses."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import seo_generate as G  # noqa: E402
import seo_pack  # noqa: E402


BRIEF = {
    "id": "tool-demo-01",
    "title": "Demo Tool 2.0: the chart tool that beats the old one",
    "niche": "AI chart tools",
    "keywords": ["demo tool 2.0", "demo chart alternative", "free chart generator"],
    "claims": [
        {"id": "c1", "text": "Demo Tool 2.0 renders a 40-point chart in under a second, "
                             "which is twice as fast as the previous release.", "source": "https://example.com/a"},
        {"id": "c2", "text": "It exports straight to SVG.", "source": "https://example.com/b"},
    ],
    "scenes": [
        {"id": "hook", "heading": "TWICE AS FAST", "say": "This chart tool just got twice as fast."},
        {"id": "point1", "say": "It renders a 40-point chart in under a second."},
        {"id": "catch", "heading": "THE CATCH", "say": "It still needs a desktop browser."},
        {"id": "cta", "say": "Want the benchmark? Comment CHART and I will pin it."},
    ],
    "viewer": {"job": "decide whether to switch the chart tool this week"},
    "sources": ["https://example.com/demo-tool"],
}


def _brief(**over):
    b = json.loads(json.dumps(BRIEF))
    b.update(over)
    return b


def test_generated_copy_passes_the_seo_rulebook():
    seo, notes = G.generate(_brief())
    probe = _brief()
    probe["seo"] = seo
    bid, errors, warns, findings, b, seo2, blocks, spoken5, onscreen = seo_pack.check(json.dumps(probe))
    assert errors == [], errors


def test_every_platform_block_exists():
    seo, _ = G.generate(_brief())
    for plat in ("youtube", "tiktok", "instagram", "facebook", "x"):
        assert plat in seo


def test_keyword_is_in_the_first_words_of_every_caption():
    seo, _ = G.generate(_brief())
    for plat in ("tiktok", "instagram", "facebook"):
        text = seo[plat]["caption"]
        assert "demo tool" in text.lower().split(":", 1)[0].lower()


def test_hashtag_count_is_the_owner_count_and_has_no_generic_tags():
    seo, _ = G.generate(_brief())
    for plat in ("youtube", "tiktok", "instagram", "facebook"):
        tags = seo[plat]["hashtags"]
        assert len(tags) == 5
        assert not any(t.lower() in G.GENERIC_TAGS for t in tags)


def test_youtube_backend_tags_carry_the_keyword_and_aliases():
    seo, _ = G.generate(_brief())
    tags = seo["youtube"]["tags"]
    assert 4 <= len(tags) <= 10
    assert any("demo tool 2.0" == t.lower() for t in tags)


def test_only_the_youtube_description_may_carry_a_link():
    seo, _ = G.generate(_brief())
    assert "http" in seo["youtube"]["description"]
    for plat in ("tiktok", "instagram", "facebook", "x"):
        body = seo[plat].get("caption") or seo[plat].get("text")
        assert "http" not in body


def test_copy_cuts_at_a_sentence_or_clause_boundary():
    text = G.shorten("One claim here. Another claim that goes on and on and should be cut somewhere sensible.", 40)
    assert text.endswith(".") or text.endswith(",") is False
    assert len(text) <= 40


def test_dangling_function_words_are_dropped_at_a_cut():
    assert G.trim_dangling("the video model above Veo 3 that you can") == "the video model above Veo 3"
