"""The house visual system: the archetype contract, the visual language, and chart grounding.

These are the rules that keep a short from drifting back to flat cards on a black background:
an archetype must be drawable by the engine, a scene must belong to the tool's visual language,
and every number a chart shows must be spoken or listed on the feature it cites.
"""
import json
from pathlib import Path

from graphics.beats import (ARCHETYPES, HOUSE_ARCHETYPES, archetypes, implemented_archetypes,
                             lint_beats, template_archetypes)
from graphics.features import lint_feature_sheet
from graphics.visual_language import (LANGUAGES, detect_category, language_for,
                                      palette_for)

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


def _sheet(tool=None, values=None):
    s = {
        "tool": tool or {"name": "T"},
        "features": [
            {"id": "f1", "title": "a", "what": "It reads every changed file before it comments.",
             "evidence_quote": "It reads every changed file"},
            {"id": "f2", "title": "b", "what": "Static analysis runs on the diff itself.",
             "metric": {"label": "rules", "value": 412},
             "evidence_quote": "Static analysis runs on the diff itself"},
            {"id": "f3", "title": "c", "what": "It runs on your own runner and needs a licence.",
             "risk": True, "evidence_quote": "It runs on your own runner"},
        ],
    }
    if values:
        s["features"][1]["values"] = values
    return s


def _phrases(texts):
    return [{"sid": f"s{k}", "text": t, "words": [], "t0": float(k), "t1": float(k + 1)}
            for k, t in enumerate(texts)]


# ---------- the engine is the contract ----------

def test_every_house_archetype_is_declared_and_implemented():
    impl = implemented_archetypes()
    assert HOUSE_ARCHETYPES <= impl, sorted(HOUSE_ARCHETYPES - impl)
    for name in HOUSE_ARCHETYPES:
        assert name in ARCHETYPES, name


def test_the_default_template_can_draw_every_house_archetype():
    merged = archetypes()
    assert HOUSE_ARCHETYPES <= set(merged)
    # ...and the eight originals too.
    for name in ("concept_card", "stat_pop", "chip_grid", "flow_link", "terminal_type",
                 "toggle_steps", "cta_stack", "endcard"):
        assert name in merged


def test_a_per_tool_template_does_not_claim_archetypes_it_cannot_draw():
    """The old linter merged the eight defaults into every template, so a plan could lint clean
    and then crash on the first frame. The engine is now the contract — and a per-tool engine draws
    its own scenes, so it never inherits the house library either."""
    merged = archetypes("musike")
    assert "player_hook" in merged
    assert "concept_card" not in merged, "musike's engine cannot draw concept_card"
    assert "chart_bars" not in merged, "musike's engine cannot draw the house charts"


def test_an_archetype_the_engine_cannot_draw_is_a_lint_error_not_a_crash():
    ph = _phrases(["reads every changed file"])
    beats = {"scenes": [{"phrase": 0, "archetype": "concept_card", "feature_id": None,
                         "headline": "H", "depicts": "reads", "payload": {"big": "X"}}]}
    # force a template whose engine has no concept_card
    beats["template"] = "musike"
    rules = [v.rule for v in lint_beats(beats, ph, _sheet())]
    assert "B11" in rules


def test_the_four_shipped_templates_keep_their_own_vocabulary():
    for name in ("musike", "design-review", "photo-to-3d", "velocity-black"):
        own = template_archetypes(name)
        assert own, name
        merged = archetypes(name)
        assert own <= set(merged), f"{name}: a declared archetype is not lintable"
        # A per-tool engine draws its own scenes, so it must NOT claim the house archetypes:
        # a beat plan using one would lint clean and then fall through to nothing on screen.
        assert not (HOUSE_ARCHETYPES & set(merged)), f"{name}: claims house archetypes it cannot draw"


# ---------- the visual language ----------

def test_a_tool_category_picks_its_own_language():
    assert detect_category({"name": "x", "category": "audio"}) == "audio"
    assert detect_category({"name": "x", "category": "coding"}) == "coding"
    # a tool that does not name a category is detected from its own words
    assert detect_category({"name": "Whisper TTS server"}) == "audio"
    assert detect_category({"name": "a terminal linter for go"}) == "coding"
    assert detect_category({"name": "something"}) == "general"


def test_each_language_has_a_plate_a_palette_and_a_vocabulary():
    for key, lang in LANGUAGES.items():
        assert lang["plates"], key
        assert lang["palette"]["accent"], key
        assert lang["allowed"], key
        assert lang["props"], key


def test_the_palette_follows_the_category():
    assert palette_for({"category": "audio"})["accent"] == LANGUAGES["audio"]["palette"]["accent"]
    assert palette_for({"category": "coding"})["accent"] == LANGUAGES["coding"]["palette"]["accent"]


def test_a_scene_outside_the_tools_language_is_a_lint_error():
    ph = _phrases(["reads every changed file"])
    beats = {"scenes": [{"phrase": 0, "archetype": "chart_donut", "feature_id": "f1",
                         "headline": "H", "depicts": "reads",
                         "payload": {"segments": [{"label": "a", "value": 1}],
                                     "source": "s"}}]}
    # a coding tool may not lead with a donut chart
    rules = [v.rule for v in lint_beats(beats, ph, _sheet({"name": "x", "category": "coding"}))]
    assert "B12" in rules


def test_a_scene_inside_the_tools_language_passes():
    ph = _phrases(["reads every changed file"])
    beats = {"scenes": [{"phrase": 0, "archetype": "chart_bars", "feature_id": "f2",
                         "headline": "H", "depicts": "reads",
                         "payload": {"labels": ["a", "b", "c"], "values": [412, 2, 3],
                                     "source": "s", "cue_phrases": ["rules", "b", "c"]}}]}
    rules = [v.rule for v in lint_beats(beats, ph, _sheet({"name": "x", "category": "coding"}))]
    assert "B12" not in rules


# ---------- chart grounding ----------

def test_a_chart_value_must_be_spoken_or_listed_on_the_feature():
    ph = _phrases(["static analysis runs on the diff"])
    beats = {"scenes": [{"phrase": 0, "archetype": "chart_bars", "feature_id": "f2",
                         "headline": "H", "depicts": "static",
                         "payload": {"labels": ["a", "b", "c"], "values": [412, 999, 7],
                                     "source": "s", "cue_phrases": ["rules", "b", "c"]}}]}
    rules = [v.rule for v in lint_beats(beats, ph, _sheet())]
    assert "B13" in rules, "999 was neither spoken nor on the feature"


def test_a_chart_value_listed_on_the_feature_is_allowed():
    ph = _phrases(["static analysis runs on the diff"])
    beats = {"scenes": [{"phrase": 0, "archetype": "chart_bars", "feature_id": "f2",
                         "headline": "H", "depicts": "static",
                         "payload": {"labels": ["a", "b", "c"], "values": [412, 999, 7],
                                     "source": "s"}}]}
    sheet = _sheet(values=[412, 999, 7])
    rules = [v.rule for v in lint_beats(beats, ph, sheet)]
    assert "B13" not in rules


def test_a_chart_needs_a_source_and_three_numbers():
    ph = _phrases(["static analysis runs on the diff"])
    beats = {"scenes": [{"phrase": 0, "archetype": "chart_bars", "feature_id": "f2",
                         "headline": "H", "depicts": "static",
                         "payload": {"labels": ["a", "b"], "values": [1, 2]}}]}
    rules = [v.rule for v in lint_beats(beats, ph, _sheet())]
    assert "B10" in rules


# ---------- the text rules ----------

def test_an_issue_number_and_a_tick_are_allowed_but_a_url_and_an_emoji_are_not():
    ph = _phrases(["reads every changed file"])
    beats = {"scenes": [{"phrase": 0, "archetype": "concept_card", "feature_id": None,
                         "headline": "H", "depicts": "reads",
                         "payload": {"big": "fix #418 ✓ today"}}]}
    assert [v.rule for v in lint_beats(beats, ph, _sheet())] == []

    beats["scenes"][0]["payload"] = {"big": "see https://example.com"}
    assert "B5" in [v.rule for v in lint_beats(beats, ph, _sheet())]

    beats["scenes"][0]["payload"] = {"big": "ship it 🚀"}
    assert "B5" in [v.rule for v in lint_beats(beats, ph, _sheet())]


def test_the_italic_emphasis_marker_is_allowed():
    ph = _phrases(["reads every changed file"])
    beats = {"scenes": [{"phrase": 0, "archetype": "concept_card", "feature_id": None,
                         "headline": "H", "depicts": "reads",
                         "payload": {"big": "your reviewer *never read* the issue"}}]}
    assert [v.rule for v in lint_beats(beats, ph, _sheet())] == []


# ---------- the feature sheet ----------

def test_a_feature_may_publish_the_series_a_chart_may_draw():
    s = _sheet(values=[1, 2, 3])
    assert "values" in s["features"][1]
    src = ("It reads every changed file Static analysis runs on the diff itself "
           "It runs on your own runner")
    assert lint_feature_sheet(s, src) == []
