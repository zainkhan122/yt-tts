"""Beat cues: when each visual element fires, taken from the spoken word timings.

Every list item (chip, step, node, terminal line, CTA pill) is bound to the first spoken word in its
phrase that matches its own wording. A number is bound to the spoken number word. Anything unmatched
falls back to an even spread across the phrase, and the fallback is recorded so the QA report shows it.
"""
from __future__ import annotations

import re

_STOP = set("a an the and or of to in on for with is it its be by as at from that this so any every each "
            "you your we our they them then first before with can or not no do does one two".split())
_NUMBER_WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                 "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "twenty": 20, "hundred": 100,
                 "thousand": 1000}

# keyword -> icon name (drawn by the engine, see templates/engine.js ICONS)
ICON_RULES = [
    (("code", "source", "function", "logic"), "code"),
    (("file", "files", "folder", "folders"), "files"),
    (("page", "pages", "width", "widths", "screen", "screens", "website", "browser", "visual"), "page"),
    (("run", "runs", "runtime", "how", "play"), "play"),
    (("tool", "tools", "toolset"), "wrench"),
    (("cli", "command", "terminal", "shell"), "terminal"),
    (("mcp", "plug", "connect", "api"), "plug"),
    (("agent", "agents", "ai", "robot"), "agent"),
    (("build", "builds", "project", "projects", "new", "layers"), "layers"),
    (("check", "checked", "checks", "compare", "compared", "match", "mismatch", "mismatches", "verify"), "check"),
    (("study", "inspect", "inspection", "look", "watch", "eye"), "eye"),
    (("alpha", "early", "risk", "risks", "warning", "careful"), "bolt"),
    (("game", "games", "star", "best"), "star"),
    (("clean", "room", "safe", "shield", "private"), "shield"),
    (("save", "bookmark"), "bookmark"),
    (("comment", "chat", "reply"), "chat"),
    (("follow", "more", "plus"), "plus"),
]


def norm(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def tokens(text: str) -> list[str]:
    return [t for t in (norm(w) for w in text.split()) if len(t) > 2 and t not in _STOP]


def icon_for(text: str) -> str:
    toks = set(tokens(text))
    for keys, icon in ICON_RULES:
        if toks & set(keys):
            return icon
    return "dot"


def _first_match(text: str, words: list[list], lo: float, hi: float):
    want = set(tokens(text))
    if not want:
        return None
    for w in words:
        if lo <= w[1] < hi and norm(w[0]) in want:
            return float(w[1])
    return None


def number_word_time(words: list[list], lo: float, hi: float, value=None):
    """Time of the spoken number (digit or number word) in the phrase, or None."""
    for w in words:
        if not (lo <= w[1] < hi):
            continue
        n = norm(w[0])
        if n.isdigit() and (value is None or int(n) == int(value)):
            return float(w[1])
        if n in _NUMBER_WORDS and (value is None or _NUMBER_WORDS[n] == int(value)):
            return float(w[1])
    return None


def compute(scene: dict, words: list[list], t0: float, t1: float, cue_word: str | None = None) -> dict:
    """Returns the scene's cue times and icons. `words` are the phrase's own [text, start, end] items."""
    arch = scene["archetype"]
    payload = scene.get("payload", {})
    d = max(0.5, t1 - t0)
    fallback = []
    cue = None
    cues: list[float] = []
    icons: list[str] = []

    if arch in ("chip_grid", "toggle_steps", "flow_link", "cta_stack"):
        items = (payload.get("chips") or payload.get("steps") or payload.get("nodes") or payload.get("lines") or [])
        for i, text in enumerate(items):
            c = _first_match(text, words, t0, t1)
            if c is None:
                fallback.append(f"item{i}")
                c = t0 + 0.18 + i * (d * 0.55 / max(1, len(items)))
            cues.append(round(c, 3))
            icons.append(icon_for(text))
        cue = cues[0] if cues else t0 + 0.15
    elif arch == "terminal_type":
        lines = payload.get("lines", [])
        for i, text in enumerate(lines):
            c = _first_match(text, words, t0, t1)
            if c is None:
                fallback.append(f"line{i}")
                c = t0 + 0.15 + i * (d * 0.5 / max(1, len(lines)))
            cues.append(round(c, 3))
        cue = cues[0] if cues else t0 + 0.15
    elif arch == "stat_pop":
        c = None
        if cue_word:
            c = _first_match(cue_word, words, t0, t1)
        if c is None:
            c = number_word_time(words, t0, t1, payload.get("value"))
        if c is None:
            fallback.append("stat")
            c = t0 + 0.2
        cue = c
    else:  # concept_card, endcard
        c = _first_match(cue_word or payload.get("big", ""), words, t0, t1) if (cue_word or payload.get("big")) else None
        if c is None:
            fallback.append("concept")
            c = t0 + 0.12
        cue = c

    return {"cue": round(float(cue), 3), "cues": cues, "icons": icons, "fallback": fallback}
