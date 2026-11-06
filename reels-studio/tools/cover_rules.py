#!/usr/bin/env python3
"""The cover rules, in code. COVER-RULES.md is the human copy; this module is what runs.

Every tool that touches a cover imports from here: video_plan (authoring), brief_from_plan (brief),
cover_lab (render + audit) and preflight (cloud gate). If a rule changes, it changes here and in
COVER-RULES.md together; tests/test_cover_rules.py keeps the two in step.

What code can prove:
  * headline: 4-5 words, all caps, only letters and the punctuation ? ! ' , -
  * three concepts, each with a different layout (bleed / window / split)
  * each concept's media: either a real tool asset (a file in captures/<id>/ at least 1080 px on its
    longest side) or a designed graphic that names the tool's own world (a written design note)
  * text contrast on the real plate (>= 4.5:1), measured by cover_lab
What code cannot prove, and the viewer panel judges cold: whether the headline is click-baited,
intent-seeking and true to the video.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HEADLINE_WORDS = (4, 5)
CONCEPTS = 3
LAYOUTS = ("bleed", "window", "split")
MIN_MEDIA_SIDE = 1080
CONTRAST_MIN = 4.5
CANVAS = (1080, 1920)
SAFE_TOP, SAFE_BOTTOM = 330, 1590
MEDIA_KINDS = ("tool_media", "designed")
HEADLINE_CHARS = re.compile(r"^[A-Z0-9 ?!',\-]+$")
DESIGN_NOTE_MIN = 20


def headline_problems(text):
    """Rule 1: 4-5 words, all caps, plain characters only."""
    if not isinstance(text, str) or not text.strip():
        return ["headline is empty"]
    out = []
    words = text.split()
    lo, hi = HEADLINE_WORDS
    if not lo <= len(words) <= hi:
        out.append(f"headline {text!r} has {len(words)} words (must be {lo}-{hi})")
    if text != text.upper():
        out.append(f"headline {text!r} is not all caps")
    if not HEADLINE_CHARS.match(text):
        out.append(f"headline {text!r} has characters outside A-Z, digits and ? ! ' , -")
    return out


def media_problems(media, tool_dir=None, cover_dir=None):
    """Rule 2: a usable real tool asset (file in captures/<id>/), or a designed graphic (file in
    covers/<id>/ plus a note saying which part of the tool's world it shows). Both files must exist
    and be at least MIN_MEDIA_SIDE on the longest side. With no directories given, only the shape
    is checked (authoring time, before the media is pulled)."""
    if not isinstance(media, dict):
        return ["media missing"]
    kind = media.get("kind")
    if kind not in MEDIA_KINDS:
        return [f"media kind {kind!r} must be one of {MEDIA_KINDS}"]
    if kind == "designed":
        note = media.get("design", "")
        if not isinstance(note, str) or len(note.strip()) < DESIGN_NOTE_MIN:
            return ["designed media needs a design note (what the graphic shows of the tool, >= 20 characters)"]
        base = cover_dir
    else:
        base = tool_dir
    f = media.get("file")
    if not isinstance(f, str) or not f:
        return [f"{kind} media needs a file name"]
    if base is None:
        return []  # shape only
    path = Path(base) / f
    if not path.exists():
        return [f"{kind} media file missing: {path}"]
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
    except Exception as exc:  # an unreadable image is a rule failure, not a crash
        return [f"{kind} media unreadable: {path.name} ({exc})"]
    if max(w, h) < MIN_MEDIA_SIDE:
        return [f"{kind} media {path.name} is {w}x{h}; longest side must be >= {MIN_MEDIA_SIDE}px"]
    return []


def concepts_problems(concepts, tool_dir=None, cover_dir=None):
    """Rule 3: exactly three concepts, distinct layouts, each headline and media valid."""
    if not isinstance(concepts, list):
        return ["cover.concepts must be a list of three concepts"]
    out = []
    if len(concepts) != CONCEPTS:
        out.append(f"cover needs {CONCEPTS} concepts, found {len(concepts)}")
    layouts = [c.get("layout") for c in concepts if isinstance(c, dict)]
    if len(layouts) != len(LAYOUTS) or any(not isinstance(x, str) for x in layouts) or sorted(layouts) != sorted(LAYOUTS):
        out.append(f"concept layouts must be exactly {LAYOUTS}, found {layouts}")
    for i, c in enumerate(concepts):
        if not isinstance(c, dict):
            out.append(f"concept {i} is not an object")
            continue
        out += [f"concept {i}: {p}" for p in headline_problems(c.get("text"))]
        out += [f"concept {i}: {p}" for p in media_problems(c.get("media"), tool_dir, cover_dir)]
    texts = [c.get("text") for c in concepts if isinstance(c, dict)]
    if all(isinstance(text, str) for text in texts) and len(set(texts)) != len(texts):
        out.append("concept headlines must differ from each other")
    return out


def plan_cover_problems(plan, tool_dir=None, cover_dir=None):
    """Used by video_plan.py. The plan's cover.text must be one of its three concepts."""
    cov = plan.get("cover") or {}
    out = concepts_problems(cov.get("concepts"), tool_dir, cover_dir)
    texts = [c.get("text") for c in cov.get("concepts") or [] if isinstance(c, dict)]
    if cov.get("text") not in texts:
        out.append("cover.text must be the headline of one of the three concepts")
    return out
