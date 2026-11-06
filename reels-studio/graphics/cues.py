"""Beat cues: when each visual element fires, taken from the spoken word timings.

Every list item (chip, step, node, terminal line, CTA pill) is bound to the first spoken word in its
phrase that matches its own wording. A number is bound to the spoken number word. Anything unmatched
falls back to an even spread across the phrase, and the fallback is recorded so the QA report shows it.

Two rules keep the picture on the voice instead of behind it (owner, 6 Nov 2026):
  * the FIRST item of a scene lands at the scene's first word, not on a late cue phrase, so no scene
    opens on an empty stage;
  * the end-card's follow press uses the pipeline's own `press` time, the same number the click SFX
    uses, so the click and the cursor press are one event.
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


_NSTOP = {re.sub(r"[^a-z0-9]", "", w) for w in _STOP}


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


def _seq_match(text: str, words: list[list], lo: float, hi: float, not_before: float | None = None):
    """Time of the spoken phrase that matches `text`, in order and after `not_before`.

    A multi-word item binds to a run of consecutive spoken words (two or more matching in a row), so
    "npm install" binds to the spoken "npm install", never to a stray "install". A single-word item
    binds to its first distinctive spoken word. Returns None when the phrase is not spoken."""
    target = [norm(w) for w in text.split()]
    target = [t for t in target if t]
    if not target:
        return None
    spoken = [(norm(w[0]), float(w[1])) for w in words
              if lo <= float(w[1]) < hi and (not_before is None or float(w[1]) >= not_before)]
    # Best run wins; a run that starts on the item's own first word gets a bonus, so "Add the Poki MCP
    # server" fires on "Add" (10.29) and not on the "MCP server" that happens to match two words later.
    best_key, best_run, best_t = None, 0, None
    for i in range(len(spoken)):
        for j in range(len(target)):
            k = 0
            while i + k < len(spoken) and j + k < len(target) and spoken[i + k][0] == target[j + k]:
                k += 1
            if not k:
                continue
            key = (k + (1 if j == 0 else 0), -spoken[i][1])
            if best_key is None or key > best_key:
                # fire on the run's FIRST spoken word: the picture must land with the phrase, not after it
                best_key, best_run, best_t = key, k, spoken[i][1]
    # A run that begins the item's own wording counts even at one word ("Add …" -> the spoken "add");
    # a lone match in the middle of the item does not (it would hop onto an unrelated word).
    if best_key is not None and best_key[0] >= min(2, len(target)) and best_t is not None:
        return best_t
    if len(target) >= 2:  # a multi-word item may still bind to one distinctive word it shares
        for tok in target:
            if len(tok) >= 4 and tok not in _STOP:
                for w, t in spoken:
                    if w == tok:
                        return t
    return None


def _bind_items(items: list[str], words: list[list], t0: float, t1: float, d: float, fallback: list[str],
                prefix: str) -> list[float]:
    """Bind each item to its own spoken phrase, in order; unmatched items get an even spread (recorded)."""
    cues: list[float] = []
    last = None
    for i, text in enumerate(items):
        c = _seq_match(text, words, t0, t1, not_before=last)
        if c is None:
            fallback.append(f"{prefix}{i}")
            c = t0 + 0.18 + i * (d * 0.55 / max(1, len(items)))
        c = round(c, 3)
        if last is not None and c <= last:  # two items never fire on the same frame
            c = round(last + 0.35, 3)
        cues.append(c)
        last = c
    return cues


def _lead(cues: list[float], t0: float, lead: float = 0.10) -> list[float]:
    """The first item is on screen when the scene opens; the rest stay bound to their own words."""
    if cues and cues[0] > t0 + lead:
        cues = [round(t0 + lead, 3)] + list(cues[1:])
    return cues


def compute(scene: dict, words: list[list], t0: float, t1: float, cue_word: str | None = None) -> dict:
    """Returns the scene's cue times and icons. `words` are the phrase's own [text, start, end] items."""
    arch = scene["archetype"]
    payload = scene.get("payload", {})
    d = max(0.5, t1 - t0)
    fallback = []
    cue = None
    cues: list[float] = []
    icons: list[str] = []

    if arch == "endcard":
        # Keyword chip on the spoken keyword, follow press on the CTA word. stage.plan_scenes overrides
        # both with the pipeline's own event times when it has them (events from the template).
        c = _first_match(payload.get("keyword") or "", words, t0, t1)
        if c is None:
            c = _first_match("comment", words, t0, t1)
        if c is None:
            fallback.append("keyword")
            c = t0 + 0.3
        cue = c
        press = _first_match("follow", words, t0, t1) or _first_match("comment", words, t0, t1)
        press = max(press or 0.0, c + 1.2)  # the card is up, the keyword has landed, then the press
        press = min(t1 - 0.9, press)
        cues = [round(float(press), 3)]
        return {"cue": round(float(cue), 3), "cues": cues, "icons": [], "fallback": fallback}

    if arch in ("chip_grid", "toggle_steps", "flow_link", "cta_stack"):
        items = (payload.get("chips") or payload.get("steps") or payload.get("nodes") or payload.get("lines") or [])
        phrases = payload.get("cue_phrases") if isinstance(payload.get("cue_phrases"), list) else None
        if not phrases:  # the item's own wording unless the brief names the spoken phrase
            phrases = items
        elif len(phrases) < len(items):  # a short list names the first items only; the rest bind by wording
            phrases = list(phrases) + items[len(phrases):]
        elif len(phrases) > len(items):
            phrases = list(phrases[:len(items)])
        cues = _lead(_bind_items(phrases, words, t0, t1, d, fallback, "item"), t0)
        icons = [icon_for(text) for text in items]
        cue = cues[0] if cues else t0 + 0.15
    elif arch == "terminal_type":
        lines = payload.get("lines", [])
        phrases = payload.get("cue_phrases") if isinstance(payload.get("cue_phrases"), list) else None
        if not phrases:
            phrases = lines
        elif len(phrases) < len(lines):
            phrases = list(phrases) + lines[len(phrases):]
        elif len(phrases) > len(lines):
            phrases = list(phrases[:len(lines)])
        cues = _bind_items(phrases, words, t0, t1, d, fallback, "line")
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
