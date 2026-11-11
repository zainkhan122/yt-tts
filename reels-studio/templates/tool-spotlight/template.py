"""Tool Spotlight (F2, 35-42 s): demo-clip hook, montage, page reveal + stars, steps, terminal, catch, keyword CTA.
Tool Spotlight (format F2, 35-42 s). Beat sheet:
  hook (official demo clip + headline) -> proof montage -> reveal + stars (browser page, camera, cursor click, count-up)
  -> how (3-5 steps) -> install (terminal) -> the catch (verdict) -> value close + keyword CTA (endcard).
Energy: hard cuts every 1.5-3 s with whip transitions, brighter music. Brief: scenes[] (types in
templates/_spotlight/spotcore.py) + a capture pack (tools/capture.py). Display vs spoken text: "{GTA V|GTA Five}".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_spotlight"))
import spotcore as core  # noqa: E402

SHARED = "_spotlight"
DEFAULTS = {"voice": "af_heart", "speed": 1.33, "style": "midnight", "captions": {"y": 1330, "maxWords": 3}}
CFG = {"flavor": "tool", "cut": "whip", "lead": 0.12, "gap": 0.06, "post": 0.16,
       "music": {"style": "pulse", "progression": "uplift", "bpm": 122}}


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
