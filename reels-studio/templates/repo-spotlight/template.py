"""Repo Spotlight (F1 Repo Drop, 22-35 s): hook, name + stars, README scroll with feature highlights, install, CTA.
Repo Spotlight (format F1 "Repo Drop", 22-35 s). Beat sheet:
  hook (README top + headline or demo clip) -> name + what it does (page: camera to title, star count-up)
  -> 2-3 features (scroll: continuous README camera with highlight boxes) -> install line (terminal) -> value close + CTA.
Energy: continuous camera moves and soft glide transitions, steadier music. Brief: scenes[] (types in
templates/_spotlight/spotcore.py) + a capture pack (tools/capture.py). Display vs spoken text: "{GTA V|GTA Five}".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_spotlight"))
import spotcore as core  # noqa: E402

SHARED = "_spotlight"
DEFAULTS = {"voice": "af_heart", "speed": 1.33, "style": "midnight", "captions": {"y": 1330, "maxWords": 3}}
CFG = {"flavor": "repo", "cut": "glide", "lead": 0.15, "gap": 0.08, "post": 0.18,
       "music": {"style": "pulse", "progression": "minor_pop", "bpm": 112}}


def segments(b):
    return core.segments(b, CFG)


def events(b, T, D):
    return core.events(b, T, D, CFG)


def html(b, T, D, ev):
    return core.html(b, T, D, ev, CFG)


def assets(b):
    return core.assets(b)


def sfx(b, T, D, ev):
    return core.sfx(b, T, D, ev, CFG)


def music(b, T, D, ev):
    return core.music(b, T, D, ev, CFG)


def data(b, T, D, ev):
    return core.data(b, T, D, ev, CFG)
