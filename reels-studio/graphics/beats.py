"""Beat plan: one generated scene per spoken phrase, lint-checked against the feature sheet.

The beat plan is the only place a visual is decided. It is authored (by the agent or an LLM) and then
checked here, deterministically. Lint rules (B*) are hard: a failing plan does not render.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .features import Violation, feature_index

# archetype -> required payload keys and their types
ARCHETYPES: dict[str, dict] = {
    "concept_card": {"req": ["big"], "opt": ["sub"], "script_ok": True, "facts": False, "max_text": 64},
    "stat_pop":     {"req": ["value", "sub"], "opt": ["suffix", "unit"], "script_ok": False, "facts": True,
                     "max_text": 48},
    "chip_grid":    {"req": ["chips"], "opt": ["highlight", "cue_phrases"], "script_ok": False, "facts": True,
                     "max_text": 48},
    "flow_link":    {"req": ["nodes"], "opt": ["edge_label", "cue_phrases"], "script_ok": False, "facts": True,
                     "max_text": 48},
    "terminal_type": {"req": ["lines"], "opt": ["title", "cue_phrases"], "script_ok": False, "facts": True,
                      "max_text": 72},
    "toggle_steps": {"req": ["steps"], "opt": ["done", "cue_phrases"], "script_ok": False, "facts": True,
                     "max_text": 56},
    "cta_stack":    {"req": ["lines"], "opt": [], "script_ok": True, "facts": False, "max_text": 64},
    # The brand end-card: real logo, follow button, cursor press (same press time as the audio click).
    "endcard":      {"req": ["keyword"], "opt": ["follow", "lines", "cue_phrases", "prompt"],
                     "script_ok": True, "facts": False, "max_text": 48},
    # --- the house library (graphics/templates/house.js) ------------------------------
    # The illustration stage: the agent lays out drawn props in normalised coordinates. This is
    # the scene type that makes a short look drawn rather than templated.
    "stage_board":  {"req": ["props"], "opt": ["notes", "stamp", "cable", "cue_phrases"],
                     "script_ok": False, "facts": True, "list_cap": 12, "max_text": 48},
    "chart_bars":   {"req": ["labels", "values"], "opt": ["unit", "max", "min", "highlight", "caption",
                     "source", "cue_phrases"], "script_ok": False, "facts": True, "list_cap": 8, "max_text": 72},
    "chart_line":   {"req": ["labels", "values"], "opt": ["unit", "max", "min", "highlight", "caption",
                     "source", "cue_phrases"], "script_ok": False, "facts": True, "list_cap": 12, "max_text": 72},
    "chart_donut":  {"req": ["segments"], "opt": ["center_value", "center_label", "unit", "cue_phrases"],
                     "script_ok": False, "facts": True, "list_cap": 6, "max_text": 48},
    "compare_split": {"req": ["left", "right"], "opt": ["caption", "cue_phrases"],
                     "script_ok": False, "facts": True, "max_text": 56},
    "verdict_pair": {"req": ["pros", "cons"], "opt": ["pros_title", "cons_title", "cue_phrases"],
                     "script_ok": False, "facts": True, "max_text": 64},
    "app_mock":     {"req": ["title"], "opt": ["tabs", "active_tab", "sidebar", "cards", "rows", "input",
                     "comment", "badge", "cue_phrases"], "script_ok": False, "facts": True, "max_text": 56},
    "steps_path":   {"req": ["steps"], "opt": ["caption", "cue_phrases"], "script_ok": False, "facts": True,
                     "max_text": 56},
    "stamp_card":   {"req": ["stamp"], "opt": ["sub", "note", "tone"], "script_ok": True, "facts": False,
                     "max_text": 48},
    "spec_strip":   {"req": ["items"], "opt": ["caption", "cue_phrases"], "script_ok": False, "facts": True,
                     "max_text": 40},
    "quote_block":  {"req": ["quote"], "opt": ["attrib"], "script_ok": True, "facts": False, "max_text": 220},
}
# The house archetypes live in the shared library, so EVERY template can draw them.
HOUSE_ARCHETYPES = {
    "stage_board", "chart_bars", "chart_line", "chart_donut", "compare_split", "verdict_pair",
    "app_mock", "steps_path", "stamp_card", "spec_strip", "quote_block",
}
# Every archetype may carry the frame furniture: the plate (the scene's mood) and the HUD chrome.
GLOBAL_OPT = {"plate", "hud"}
# Charts must say where the numbers came from (a short on-screen attribution, never a URL).
CHART_ARCHETYPES = {"chart_bars", "chart_line", "chart_donut"}
SCRIPT_ARCHETYPES = {a for a, d in ARCHETYPES.items() if d["script_ok"]}
TEMPLATES = Path(__file__).resolve().parent / "templates"
# Three ways an engine names an archetype it can draw:
#   ARCH.name = {...}      the registry form (musike, design-review, pulse, redline, ...)
#   archetype === 'name'   the dispatch form (design-agent, modern-web-guidance, pika-flex, ...)
#   name: { build: ... }   the object-map form (negative)
# An engine that dispatches by name AND has a catch-all branch can draw names it never mentions,
# so a template's own template.json is also part of the contract (see archetypes()).
_ARCH_RE = re.compile(r"\bARCH\.([A-Za-z_][A-Za-z0-9_]*)\s*=")
_CMP_RE = re.compile(r"archetype\s*===?\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]")
_KEY_RE = re.compile(r"^[ \t]{2,}([a-z][a-z0-9_]*)[ \t]*:[ \t]*\{", re.M)


def _engine_archetypes(path: Path) -> set[str]:
    if not path.exists():
        return set()
    src = path.read_text(encoding="utf-8")
    return set(_ARCH_RE.findall(src)) | set(_CMP_RE.findall(src)) | set(_KEY_RE.findall(src))


def implemented_archetypes(template: str | None = None) -> set[str]:
    """The archetypes a template's engine can actually draw.

    The engine.js is the real contract: `ARCH[name].build()` is called by name at render time, so an
    archetype the engine does not define is a runtime crash, not a style choice. Previously the linter
    merged the eight default archetypes into every template, which meant a beat plan could lint clean
    and then explode on the first frame. The linter now asks the engine.

    The house library is only part of the DEFAULT template's vocabulary: a per-tool engine draws its
    own scenes and never reads window.HOUSE, so a house archetype in a per-tool brief is still a
    crash — B11 must keep saying so.
    """
    if template and template != "default":
        engine = TEMPLATES / template / "engine.js"
        if not engine.exists():
            engine = TEMPLATES / "engine.js"
        return _engine_archetypes(engine)
    names = _engine_archetypes(TEMPLATES / "engine.js")
    house = TEMPLATES / "house.js"
    if house.exists():
        names |= _engine_archetypes(house)
    return names


def template_archetypes(template: str | None) -> set[str]:
    """The archetype names a per-tool template declares for itself (its own visual vocabulary)."""
    if not template or template == "default":
        return set()
    cfg_path = TEMPLATES / template / "template.json"
    if not cfg_path.exists():
        return set()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    return set((cfg.get("archetypes") or {}).keys())


def archetypes(template: str | None = None) -> dict[str, dict]:
    """The archetype vocabulary for a beat plan.

    A template's vocabulary is everything its engine can draw PLUS everything it declares in its own
    template.json. The declaration matters because several per-tool engines dispatch with a catch-all
    branch: they draw an archetype they never name (modern-web-guidance's atlas_review is the review
    card; design-agent's proof_counter and friends all land on its final layout). Those are declared,
    so they are lintable — and the linter still refuses an archetype neither the engine nor the
    template declares (B11), which is what would crash on the first frame.
    """
    impl = implemented_archetypes(template)
    declared: dict[str, dict] = {}
    max_text = MAX_TEXT
    if template and template != "default":
        cfg_path = TEMPLATES / template / "template.json"
        if not cfg_path.exists():
            raise FileNotFoundError(f"unknown graphics template {template!r}: {cfg_path}")
        cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
        max_text = int(cfg.get("max_text") or MAX_TEXT)
        for name, spec in (cfg.get("archetypes") or {}).items():
            declared[name] = {"req": list(spec.get("req") or []), "opt": list(spec.get("opt") or []),
                              "script_ok": bool(spec.get("script_ok", False)),
                              "facts": bool(spec.get("facts", False)),
                              "max_text": int(spec.get("max_text") or max_text)}
    merged: dict[str, dict] = {}
    # 'endcard' is the house outro: every template draws it through the shared house layer.
    for name in set(impl) | set(declared) | {"endcard"}:
        spec = declared.get(name) or ARCHETYPES.get(name)
        if spec is None:
            continue
        merged[name] = dict(spec)
        merged[name].setdefault("max_text", max_text)
    return merged
MAX_TEXT = 42
MAX_LIST = 6
_STOP = set("a an the and or of to in on for with is it its be by as at from that this so any "
            "every each you your we our they them then first before".split())
_URL = re.compile(r"https?://|www\.", re.I)
# Markdown that would show up raw on screen. The house typography uses *word* for the italic-serif
# emphasis, so a balanced *pair* is allowed; bold, code, links and headings are not.
_MD = re.compile(r"`|\[|\]|!\[|~~|\*\*|__|(^|\n)\s*#{1,6}\s", re.M)
_EMOJI = re.compile("[\U0001F300-\U0001FAFF]")
# The house draws these as icons, not as pasted emoji (the reference reels use tick and warning
# glyphs as design elements). The set is the typography a short may use on screen: ticks, warning
# signs, arrows, dashes and the comparison signs a chart label needs ("≈ 2 S", "≤ 5 ms").
_SYMBOL_OK = set("✓✔✕✖⚠★☆✦●○▲▼■□◆→←↑↓•…−–—+±≈≤≥×÷°′″‹›«»∙")
_EMOJI_BLOCK = re.compile("[\u2190-\u27BF\u2B00-\u2BFF]")


def _bad_text(text: str) -> str | None:
    """Why a payload string cannot go on screen, or None when it can."""
    if _URL.search(text):
        return "URL"
    if _MD.search(text):
        return "markdown"
    if _EMOJI.search(text):
        return "emoji"
    for ch in _EMOJI_BLOCK.findall(text):
        if ch in _SYMBOL_OK:
            continue
        if "▀" <= ch <= "◿":   # the geometric-shapes block: the house's icon alphabet
            continue
        return "emoji"
    return None


def _says_number(phrase: str, value) -> bool:
    """Does this spoken phrase actually say that number?

    Digits are matched literally. A spoken-out number ("four hundred and twelve") is not a digit
    match: a chart value that was never said out loud has to be listed on the feature instead.
    """
    if value is None:
        return False
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(phrase)
    if isinstance(value, int):
        return str(value) in text or str(abs(value)) in text
    return str(value) in text


def _tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in _STOP and len(t) > 1}


def _texts(payload) -> list[str]:
    out: list[str] = []
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        for v in payload.values():
            out += _texts(v)
    elif isinstance(payload, list):
        for v in payload:
            out += _texts(v)
    return out


def script_tokens(text_or_words) -> list[str]:
    """Normalized spoken tokens: lowercase a-z and 0-9 runs. Punctuation and casing never change the fingerprint."""
    if isinstance(text_or_words, str):
        return re.findall(r"[a-z0-9]+", text_or_words.lower())
    out: list[str] = []
    for w in text_or_words:
        out += re.findall(r"[a-z0-9]+", str(w[0]).lower())
    return out


def script_fingerprint(words: list[list]) -> str:
    """sha256 of the normalized spoken tokens. A beat plan is valid only for the script it was written for."""
    import hashlib
    return "sha256:" + hashlib.sha256(" ".join(script_tokens(words)).encode("utf-8")).hexdigest()


def lint_beats(beats: dict, phrases: list[dict], sheet: dict, script_fp: str | None = None) -> list[Violation]:
    v: list[Violation] = []
    scenes = beats.get("scenes", [])
    feats = feature_index(sheet)
    ARCH = archetypes(beats.get("template"))

    # B0 the beat plan belongs to this exact script (fingerprint of the spoken words).
    if script_fp is not None and beats.get("script_sha256") != script_fp:
        v.append(Violation("B0", f"beat plan is for script {beats.get('script_sha256')!r}, "
                                 f"the voice is {script_fp!r}; re-plan the beats"))

    # B1 coverage: exactly one scene per phrase, in order (phrases are the brief's scenes, in voice order).
    if len(scenes) != len(phrases):
        v.append(Violation("B1", f"{len(scenes)} scenes for {len(phrases)} phrases"))
    for k, s in enumerate(scenes):
        if s.get("phrase") != k:
            v.append(Violation("B1", f"scene {k} points at phrase {s.get('phrase')}"))
            break

    prev_arch = None
    # B12 the scene must belong to the tool's visual language: the category of the tool decides which
    # archetypes are on the table, so a benchmark video is built from charts and a CLI video from
    # interfaces. A template's own archetypes are always allowed.
    from .visual_language import allowed_archetypes, language_for
    _lang = language_for(sheet.get("tool"))
    _allowed = (allowed_archetypes(sheet.get("tool")) or set()) | template_archetypes(beats.get("template"))
    for k, s in enumerate(scenes):
        arch = s.get("archetype")
        tag = f"scene {k}"
        spec = ARCH.get(arch)
        if spec is None:
            # B11 the archetype exists on paper but this template's engine cannot draw it. The engine
            # dispatches by name at render time, so this used to crash the first frame.
            if arch in ARCHETYPES:
                v.append(Violation("B11", f"{tag}: archetype '{arch}' is not implemented by template "
                                          f"{beats.get('template') or 'default'!r}"))
            else:
                v.append(Violation("B8", f"{tag}: unknown archetype {arch!r}"))
            continue
        # B2 no two identical archetypes in a row (visual variety; owner rejected sameness).
        if arch == prev_arch:
            v.append(Violation("B2", f"{tag}: same archetype '{arch}' as the previous scene"))
        prev_arch = arch

        # B12 the archetype belongs to this tool's visual language.
        if _allowed and arch not in _allowed:
            v.append(Violation("B12", f"{tag}: archetype '{arch}' is not part of the "
                                      f"{_lang.get('label')!r} visual language"))

        # B3 grounding: fact-bearing scenes cite a feature; script scenes may not.
        fid = s.get("feature_id")
        if spec["facts"]:
            if fid not in feats:
                v.append(Violation("B3", f"{tag}: {arch} needs a feature_id from the sheet"))
        elif fid is not None:
            v.append(Violation("B3", f"{tag}: {arch} is script-only; feature_id must be null"))
        if not spec["script_ok"] and not spec["facts"]:
            v.append(Violation("B3", f"{tag}: archetype has no grounding class"))

        # B4 depicts overlap: the visual must name something the phrase says.
        if phrases[k:k + 1]:
            phrase_tok = _tokens(phrases[k]["text"])
            dep_tok = _tokens(s.get("depicts", ""))
            if not (phrase_tok & dep_tok):
                v.append(Violation("B4", f"{tag}: 'depicts' shares no word with the phrase"))

        # B5 payload safety and caps.
        payload = s.get("payload") or {}
        for req in spec["req"]:
            if req not in payload:
                v.append(Violation("B6", f"{tag}: payload missing '{req}'"))
        allowed = set(spec["req"]) | set(spec["opt"]) | GLOBAL_OPT
        for key in payload:
            if key not in allowed:
                v.append(Violation("B6", f"{tag}: payload key '{key}' not allowed for {arch}"))
        for text in _texts(payload):
            if isinstance(text, str):
                why = _bad_text(text)
                if why:
                    v.append(Violation("B5", f"{tag}: {why} in payload: {text!r}"))
                limit = spec.get("max_text", MAX_TEXT)
                if len(text) > limit:
                    v.append(Violation("B5", f"{tag}: text longer than {limit} chars"))
        cap = spec.get("list_cap", MAX_LIST)
        for lkey in ("chips", "nodes", "steps", "lines", "labels", "values", "props", "notes",
                     "items", "segments", "pros", "cons", "tabs", "cards", "rows"):
            if isinstance(payload.get(lkey), list) and len(payload[lkey]) > cap:
                v.append(Violation("B5", f"{tag}: '{lkey}' has more than {cap} items"))

        # B7 numbers are grounded: a stat must be the feature's own metric value.
        if arch == "stat_pop" and fid in feats:
            metric = feats[fid].get("metric") or {}
            if metric.get("value") != payload.get("value"):
                v.append(Violation("B7", f"{tag}: stat value {payload.get('value')!r} is not the "
                                         f"feature metric {metric.get('value')!r}"))

        # B10 a chart must carry its numbers and say where they came from. A chart with no source is
        # a decoration; a chart with no values is a lie.
        if arch in CHART_ARCHETYPES:
            if not payload.get("source"):
                v.append(Violation("B10", f"{tag}: {arch} needs a 'source' attribution"))
            if arch in ("chart_bars", "chart_line"):
                vals = payload.get("values")
                if not isinstance(vals, list) or len(vals) < 3:
                    v.append(Violation("B10", f"{tag}: {arch} needs at least 3 numeric values"))
                elif not all(isinstance(x, (int, float)) for x in vals):
                    v.append(Violation("B10", f"{tag}: {arch} values must all be numeric"))
                labs = payload.get("labels")
                if not isinstance(labs, list) or len(labs) != len(vals):
                    v.append(Violation("B10", f"{tag}: {arch} needs one label per value"))
            else:  # chart_donut
                segs = payload.get("segments")
                if not isinstance(segs, list) or not segs:
                    v.append(Violation("B10", f"{tag}: chart_donut needs segments"))
                else:
                    for sg in segs:
                        if not isinstance(sg, dict) or not isinstance(sg.get("value"), (int, float)):
                            v.append(Violation("B10", f"{tag}: chart_donut segments need numeric values"))
                            break

        # B13 every number a chart shows is either spoken in this phrase or listed on the feature.
        # A chart that invents a number is worse than no chart.
        if arch in ("chart_bars", "chart_line"):
            vals = payload.get("values") or []
            phrases = payload.get("cue_phrases") or []
            known = set()
            if fid in feats:
                for x in (feats[fid].get("values") or []):
                    if isinstance(x, (int, float)):
                        known.add(x)
                m = feats[fid].get("metric") or {}
                if isinstance(m.get("value"), (int, float)):
                    known.add(m["value"])
            for i, num in enumerate(vals):
                if not isinstance(num, (int, float)) or num in known:
                    continue
                # A cue phrase only excuses a value if the phrase actually SAYS that number.
                if i < len(phrases) and _says_number(str(phrases[i]), num):
                    continue
                v.append(Violation("B13", f"{tag}: chart value {num!r} is neither spoken in this phrase "
                                          f"nor listed on feature {fid!r}"))
    return v


def scene_list(beats: dict, phrases: list[dict]) -> list[dict]:
    """Joins beats with phrase timing and computes the beat cues. Called only after lint passes."""
    from .cues import compute
    out = []
    for k, (s, p) in enumerate(zip(beats["scenes"], phrases)):
        scene = {
            "id": f"s{k:02d}",
            "archetype": s["archetype"],
            "t0": p["t0"],
            "t1": p["t1"],
            "headline": s.get("headline", ""),
            "sub": s.get("sub", ""),
            "payload": s.get("payload", {}),
            # Upstream feature (kept): a scene may show a locally captured still as evidence.
            "evidence_image": s.get("evidence_image"),
            "evidence_focus": s.get("evidence_focus"),
            "words": p["words"],
            "text": p["text"],
        }
        scene.update(compute(scene, p["words"], p["t0"], p["t1"], s.get("cue_word")))
        out.append(scene)
    return out
