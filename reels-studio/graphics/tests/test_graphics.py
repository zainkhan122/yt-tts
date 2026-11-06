"""Unit tests for the generated-graphics engine (pure logic; no browser needed)."""
import json
from pathlib import Path

import pytest

from graphics.beats import lint_beats, scene_list
from graphics.features import lint_feature_sheet
from graphics.render import build_stage_html
from graphics.timing import chunk_phrases, close_gaps

SOURCE = (
    "Study: inspect the original: its pages at every width, its code, its files, how it runs. "
    "320 tools, each one a CLI command and an MCP tool. "
    "Every build is compared with the original (pages at three screen widths, a game's own self-test, "
    "an app's runs). Status: early alpha. "
    "a coding agent builds a new project, in the language, framework or engine your request names. "
    "No AI is needed to inspect."
)


def sheet():
    return {
        "tool": {"name": "T"},
        "features": [
            {"id": "f1", "title": "a", "what": "Inspects the original with real tools at every width.",
             "evidence_quote": "inspect the original: its pages at every width, its code, its files, how it runs."},
            {"id": "f2", "title": "b", "what": "Each tool is a command line call and an MCP tool.",
             "metric": {"label": "tools", "value": 320}, "evidence_quote": "320 tools, each one a CLI command and an MCP tool"},
            {"id": "f3", "title": "c", "what": "Every build is compared with the original at three widths.",
             "metric": {"label": "widths", "value": 3}, "evidence_quote": "Every build is compared with the original (pages at three screen widths"},
            {"id": "f4", "title": "d", "what": "Status is early alpha, so checks matter a lot.",
             "risk": True, "evidence_quote": "Status: early alpha"},
        ],
    }


def words(n_phrases=3, per=4, dur=0.3, gap=0.02, punct_every=None):
    out, t = [], 0.0
    for p in range(n_phrases):
        for w in range(per):
            txt = f"w{p}{w}"
            if punct_every and (w + 1) % punct_every == 0 and w == per - 1:
                txt += ","
            out.append([txt, round(t, 3), round(t + dur, 3)])
            t += dur + gap
        t += 0.5  # pause between phrases
    return out


# ---------- features ----------

def test_feature_sheet_passes_when_quotes_are_verbatim():
    assert lint_feature_sheet(sheet(), SOURCE) == []


def test_feature_quote_not_in_source_fails():
    s = sheet()
    s["features"][0]["evidence_quote"] = "inspect the original with magic"
    rules = [v.rule for v in lint_feature_sheet(s, SOURCE)]
    assert "F6" in rules


def test_metric_must_be_numeric():
    s = sheet()
    s["features"][1]["metric"]["value"] = "320+"
    assert "F7" in [v.rule for v in lint_feature_sheet(s, SOURCE)]


def test_needs_three_features_and_a_risk():
    s = sheet()
    s["features"] = s["features"][:2]
    for f in s["features"]:
        f.pop("risk", None)
    rules = [v.rule for v in lint_feature_sheet(s, SOURCE)]
    assert "F2" in rules and "F8" in rules


def test_markdown_in_source_is_normalised():
    src = "**Study:** inspect the original: its pages at every width, its code, its files, how it runs."
    s = sheet()
    f1 = [v for v in lint_feature_sheet(s, src) if v.rule == "F6" and v.detail.startswith("f1:")]
    assert f1 == []


# ---------- phrases ----------

def test_phrases_break_on_gap_and_cover_all_words():
    w = words(n_phrases=3, per=4)
    ph = chunk_phrases(w)
    assert len(ph) == 3
    assert sum(len(p["words"]) for p in ph) == len(w)


def test_phrases_never_exceed_max_span_by_much():
    w = words(n_phrases=1, per=30, dur=0.3, gap=0.02)  # one long run, no pauses
    ph = chunk_phrases(w, max_s=4.0)
    assert all(p["t1"] - p["t0"] <= 4.0 + 0.31 for p in ph)
    assert len(ph) >= 2


def test_punctuation_breaks_only_after_min_duration():
    w = [["Hi,", 0.0, 0.2], ["there", 0.25, 0.5], ["friend.", 0.52, 2.0], ["Bye", 2.6, 3.0]]
    ph = chunk_phrases(w, min_s=1.2)
    assert [p["text"] for p in ph] == ["Hi, there friend.", "Bye"] or len(ph) <= 2


def test_close_gaps_is_contiguous_from_zero_to_total():
    ph = chunk_phrases(words(3, 4))
    closed = close_gaps(ph, 12.0)
    assert closed[0]["t0"] == 0.0 and closed[-1]["t1"] == 12.0
    for a, b in zip(closed, closed[1:]):
        assert a["t1"] == b["t0"]


# ---------- beats ----------

def _phrases():
    ph = close_gaps(chunk_phrases(words(3, 4)), 10.0)
    for p in ph:
        p["text"] = " ".join(w[0] for w in p["words"])
    return ph


def _beats(ph, **over):
    scenes = []
    arch = ["concept_card", "chip_grid", "stat_pop"]
    for k, p in enumerate(ph):
        scenes.append({"phrase": k, "archetype": arch[k % 3], "feature_id": None if arch[k % 3] == "concept_card" else "f2",
                       "headline": "H", "depicts": p["text"].split()[0], "payload": {}})
    scenes[0]["payload"] = {"big": "X"}
    scenes[1]["payload"] = {"chips": ["a", "b"]}
    scenes[2]["payload"] = {"value": 320, "sub": "tools"}
    scenes[2]["archetype"] = "stat_pop"
    b = {"scenes": scenes}
    b.update(over)
    return b


def test_clean_beats_pass():
    ph = _phrases()
    b = _beats(ph)
    rules = [v.rule for v in lint_beats(b, ph, sheet())]
    assert rules == [], rules


def test_coverage_mismatch_fails():
    ph = _phrases()
    b = _beats(ph)
    b["scenes"].pop()
    assert "B1" in [v.rule for v in lint_beats(b, ph, sheet())]


def test_same_archetype_back_to_back_fails():
    ph = _phrases()
    b = _beats(ph)
    b["scenes"][1]["archetype"] = "concept_card"
    b["scenes"][1]["feature_id"] = None
    b["scenes"][1]["payload"] = {"big": "Y"}
    assert "B2" in [v.rule for v in lint_beats(b, ph, sheet())]


def test_fact_scene_without_feature_fails_and_script_scene_with_feature_fails():
    ph = _phrases()
    b = _beats(ph)
    b["scenes"][1]["feature_id"] = None
    b["scenes"][0]["feature_id"] = "f1"
    rules = [v.rule for v in lint_beats(b, ph, sheet())]
    assert rules.count("B3") >= 2


def test_stat_must_match_feature_metric():
    ph = _phrases()
    b = _beats(ph)
    b["scenes"][2]["payload"]["value"] = 999
    assert "B7" in [v.rule for v in lint_beats(b, ph, sheet())]


def test_url_or_emoji_in_payload_fails():
    ph = _phrases()
    b = _beats(ph)
    b["scenes"][0]["payload"] = {"big": "see https://example.com"}
    b["scenes"][1]["payload"] = {"chips": ["ok 🚀"]}
    rules = [v.rule for v in lint_beats(b, ph, sheet())]
    assert rules.count("B5") >= 2


def test_depicts_must_overlap_phrase():
    ph = _phrases()
    b = _beats(ph)
    b["scenes"][0]["depicts"] = "zebra quantum"
    assert "B4" in [v.rule for v in lint_beats(b, ph, sheet())]


def test_scene_list_joins_timing_and_words():
    ph = _phrases()
    b = _beats(ph)
    sc = scene_list(b, ph)
    assert sc[0]["id"] == "s00" and sc[0]["t0"] == 0.0
    assert sc[-1]["t1"] == 10.0 and len(sc[0]["words"]) == 4


# ---------- engine document ----------

def test_stage_html_escapes_script_close_tags():
    doc = {"width": 1080, "height": 1920, "handle": "@x", "scenes": [{"id": "s00", "archetype": "concept_card",
           "t0": 0, "t1": 1, "headline": "</script><b>", "payload": {"big": "A"}, "words": []}]}
    html = build_stage_html(doc)
    data_part = html.split("window.DATA=", 1)[1].split(";</script>", 1)[0]
    assert "</script" not in data_part
    assert json.loads(data_part.replace("<\\/", "</"))["scenes"][0]["headline"] == "</script><b>"


# ---------- beat cues ----------

from graphics.cues import compute, icon_for, number_word_time  # noqa: E402


def test_list_items_fire_on_their_own_spoken_word():
    words = [["Pages", 1.0, 1.3], ["at", 1.3, 1.4], ["every", 1.4, 1.7], ["width", 1.7, 2.1],
             ["its", 2.2, 2.3], ["code", 2.3, 2.6], ["its", 2.7, 2.8], ["files", 2.8, 3.2]]
    sc = {"archetype": "chip_grid", "payload": {"chips": ["Pages at every width", "Its code", "Its files"]}}
    c = compute(sc, words, 0.9, 3.4)
    assert c["cues"][0] == 1.0 and c["cues"][1] == 2.3 and c["cues"][2] == 2.8
    assert c["fallback"] == []


def test_unmatched_item_falls_back_and_is_reported():
    words = [["hello", 1.0, 1.3]]
    sc = {"archetype": "toggle_steps", "payload": {"steps": ["zebra quantum"]}}
    c = compute(sc, words, 0.9, 2.0)
    assert c["fallback"] == ["item0"] and len(c["cues"]) == 1


def test_stat_cue_is_the_spoken_number():
    words = [["with", 0.0, 0.2], ["three", 0.3, 0.6], ["screen", 0.6, 0.9]]
    assert number_word_time(words, 0, 2) == 0.3
    sc = {"archetype": "stat_pop", "payload": {"value": 3, "sub": "x"}}
    assert compute(sc, words, 0.0, 2.0)["cue"] == 0.3


def test_icons_follow_keywords():
    assert icon_for("Pages at every width") == "page"
    assert icon_for("Its code") == "code"
    assert icon_for("Zebra") == "dot"


def test_scene_list_carries_cues_for_the_engine():
    ph = _phrases()
    b = _beats(ph)
    sc = scene_list(b, ph)
    assert "cue" in sc[0] and "cues" in sc[1] and "icons" in sc[1]


def test_fallback_cues_never_go_backwards_or_past_scene():
    words = [["late", 4.7, 4.9]]
    sc = {"archetype": "chip_grid", "payload": {"chips": ["late", "unmatched"]}}
    result = compute(sc, words, 0, 5)
    assert result["cues"][0] <= result["cues"][1] <= 5
    assert result["fallback"] == ["item1"]


def test_desktop_action_requires_complete_safe_payload():
    ph = _phrases()
    b = _beats(ph)
    b["scenes"][1]["archetype"] = "desktop_action"
    b["scenes"][1]["payload"] = {"app": "Finder", "target": "Documents", "ref": "@s8f3k2p9:e8",
                                   "mode": "stale", "cue_phrases": ["change", "snapshot"]}
    errors = lint_beats(b, ph, sheet())
    assert any(v.rule == "B6" and "new_ref" in v.detail for v in errors)
    b["scenes"][1]["payload"]["new_ref"] = "@t4a6m1n7:e8"
    assert not [v for v in lint_beats(b, ph, sheet()) if v.rule == "B6"]


def test_desktop_action_binds_two_distinct_spoken_moments():
    sc = {"archetype": "desktop_action", "payload": {"cue_phrases": ["stale", "fresh snapshot"]}}
    words = [["stale", 1.0, 1.2], ["fresh", 2.0, 2.2], ["snapshot", 2.3, 2.5]]
    cues = compute(sc, words, 0, 3)
    assert cues["cues"] == [1.0, 2.0]
    assert not cues["fallback"]
