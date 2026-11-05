"""The shipped plan for repo-craft-anything-01: fingerprint, scene binding, and lint against synthetic timings."""
import json
from pathlib import Path

from graphics.beats import lint_beats, script_fingerprint, script_tokens
from graphics.features import lint_feature_sheet
from graphics.stage import GraphicsError, plan_scenes, segments_from_timing

def _fixture_dir():
    """The batch plan lives in briefs/graphics/ inside the repo, and in fixtures/ in the standalone package."""
    root = Path(__file__).resolve().parents[2]  # reels-studio/ (repo) or graphics/ parent (standalone)
    for cand in (root / "briefs" / "graphics" / "repo-craft-anything-01",
                 Path(__file__).resolve().parents[1] / "fixtures" / "craft-anything"):
        if (cand / "beats.json").exists():
            return cand
    raise FileNotFoundError("craft-anything plan not found")

FIX = _fixture_dir()


def _say_scenes():
    # The brief's scenes (id, say) as the voice stage will see them.
    return [("hook", "Can Craft Anything rebuild an app?"),
            ("point1", "It studies the original first, with real inspection tools, before any AI writes a line."),
            ("point2", "Then a coding agent builds a new project, in the language or framework you ask for."),
            ("point3", "Every build is checked against the original, at three screen widths, and mismatches are listed."),
            ("point4", "Every tool is a command line call and an MCP tool, so an agent can drive the same engine the app uses."),
            ("catch", "It is early alpha, so every build still needs checking against the original."),
            ("cta", "Would you let an AI rebuild an app it studied? Comment CRAFT and I'll pin the repo link.")]


def _timing(punct_noise=False):
    timing, order, t = {}, [], 0.2
    for sid, say in _say_scenes():
        words = []
        for w in say.split():
            w2 = w.rstrip("?.,") if punct_noise else w
            words.append([w2, round(t, 3), round(t + 0.3, 3)])
            t += 0.36
        timing[sid] = {"words": words}
        order.append(sid)
        t += 0.4
    return timing, order, t + 0.5


def test_fingerprint_ignores_case_and_punctuation():
    a, _, _ = _timing(False)
    b, _, _ = _timing(True)
    wa = [w for sid in a for w in a[sid]["words"]]
    wb = [w for sid in b for w in b[sid]["words"]]
    assert script_fingerprint(wa) == script_fingerprint(wb)


def test_fingerprint_matches_the_brief_script():
    brief = json.loads((FIX / "beats.json").read_text(encoding="utf-8"))
    tokens = [t for _, say in _say_scenes() for t in script_tokens(say)]
    assert brief["script_sha256"] == "sha256:" + __import__("hashlib").sha256(" ".join(tokens).encode()).hexdigest()


def test_plan_lints_clean_against_its_own_voice():
    sheet = json.loads((FIX / "features.json").read_text(encoding="utf-8"))
    source = (FIX / "source.md").read_text(encoding="utf-8")
    beats = json.loads((FIX / "beats.json").read_text(encoding="utf-8"))
    timing, order, dur = _timing(True)
    words = [w for sid in order for w in timing[sid]["words"]]
    phrases = segments_from_timing(timing, order)
    doc, _ = plan_scenes(sheet, source, beats, phrases, dur, words)
    assert len(doc["scenes"]) == 7
    assert [s["archetype"] for s in doc["scenes"]] == ["concept_card", "chip_grid", "flow_link", "stat_pop",
                                                      "terminal_type", "toggle_steps", "cta_stack"]


def test_wrong_script_fails_closed():
    sheet = json.loads((FIX / "features.json").read_text(encoding="utf-8"))
    source = (FIX / "source.md").read_text(encoding="utf-8")
    beats = json.loads((FIX / "beats.json").read_text(encoding="utf-8"))
    timing, order, dur = _timing(False)
    timing["hook"]["words"][0][0] = "Could"  # the voice said something else
    words = [w for sid in order for w in timing[sid]["words"]]
    try:
        plan_scenes(sheet, source, beats, segments_from_timing(timing, order), dur, words)
    except GraphicsError as e:
        assert any(v["rule"] == "B0" for v in e.violations)
    else:
        raise AssertionError("expected B0")


def test_scene_binding_is_checked():
    sheet = json.loads((FIX / "features.json").read_text(encoding="utf-8"))
    source = (FIX / "source.md").read_text(encoding="utf-8")
    beats = json.loads((FIX / "beats.json").read_text(encoding="utf-8"))
    beats["scenes"][1]["scene_id"] = "cta"
    timing, order, dur = _timing(False)
    words = [w for sid in order for w in timing[sid]["words"]]
    try:
        plan_scenes(sheet, source, beats, segments_from_timing(timing, order), dur, words)
    except GraphicsError as e:
        assert any(v["rule"] == "B9" for v in e.violations)
    else:
        raise AssertionError("expected B9")
