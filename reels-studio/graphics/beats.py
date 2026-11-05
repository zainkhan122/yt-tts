"""Beat plan: one generated scene per spoken phrase, lint-checked against the feature sheet.

The beat plan is the only place a visual is decided. It is authored (by the agent or an LLM) and then
checked here, deterministically. Lint rules (B*) are hard: a failing plan does not render.
"""
from __future__ import annotations

import re

from .features import Violation, feature_index

# archetype -> required payload keys and their types
ARCHETYPES: dict[str, dict] = {
    "concept_card": {"req": ["big"], "opt": ["sub"], "script_ok": True, "facts": False},
    "stat_pop":     {"req": ["value", "sub"], "opt": ["suffix", "unit"], "script_ok": False, "facts": True},
    "chip_grid":    {"req": ["chips"], "opt": ["highlight"], "script_ok": False, "facts": True},
    "flow_link":    {"req": ["nodes"], "opt": ["edge_label"], "script_ok": False, "facts": True},
    "terminal_type": {"req": ["lines"], "opt": [], "script_ok": False, "facts": True},
    "toggle_steps": {"req": ["steps"], "opt": ["done"], "script_ok": False, "facts": True},
    "cta_stack":    {"req": ["lines"], "opt": [], "script_ok": True, "facts": False},
}
SCRIPT_ARCHETYPES = {a for a, d in ARCHETYPES.items() if d["script_ok"]}
MAX_TEXT = 42
MAX_LIST = 6
_STOP = set("a an the and or of to in on for with is it its be by as at from that this so any "
            "every each you your we our they them then first before".split())
_URL = re.compile(r"https?://|www\.", re.I)
_MD = re.compile(r"[*_`#\[\]]|!\[")
_EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")


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
    for k, s in enumerate(scenes):
        arch = s.get("archetype")
        tag = f"scene {k}"
        spec = ARCHETYPES.get(arch)
        if spec is None:
            v.append(Violation("B8", f"{tag}: unknown archetype {arch!r}"))
            continue
        # B2 no two identical archetypes in a row (visual variety; owner rejected sameness).
        if arch == prev_arch:
            v.append(Violation("B2", f"{tag}: same archetype '{arch}' as the previous scene"))
        prev_arch = arch

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
        for key in payload:
            if key not in spec["req"] + spec["opt"]:
                v.append(Violation("B6", f"{tag}: payload key '{key}' not allowed for {arch}"))
        for text in _texts(payload):
            if isinstance(text, str):
                if _URL.search(text) or _MD.search(text) or _EMOJI.search(text):
                    v.append(Violation("B5", f"{tag}: URL, markdown or emoji in payload: {text!r}"))
                if len(text) > MAX_TEXT:
                    v.append(Violation("B5", f"{tag}: text longer than {MAX_TEXT} chars"))
        for lkey in ("chips", "nodes", "steps", "lines"):
            if isinstance(payload.get(lkey), list) and len(payload[lkey]) > MAX_LIST:
                v.append(Violation("B5", f"{tag}: '{lkey}' has more than {MAX_LIST} items"))

        # B7 numbers are grounded: a stat must be the feature's own metric value.
        if arch == "stat_pop" and fid in feats:
            metric = feats[fid].get("metric") or {}
            if metric.get("value") != payload.get("value"):
                v.append(Violation("B7", f"{tag}: stat value {payload.get('value')!r} is not the "
                                         f"feature metric {metric.get('value')!r}"))
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
            "payload": s.get("payload", {}),
            "words": p["words"],
            "text": p["text"],
        }
        scene.update(compute(scene, p["words"], p["t0"], p["t1"], s.get("cue_word")))
        out.append(scene)
    return out
