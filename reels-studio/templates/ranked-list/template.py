"""Ranked countdown (#N -> #1): rank slam, name, one-liner, counted stat bar, mini-leaderboard that fills up, suspense before #1.

Viral mechanics: open loop ("wait for #1"), escalating reveals, a growing leaderboard viewers
screenshot/share, and an opinion CTA ("which would you pick?") that drives comments.
content: hook, [hook_display], [kicker], [sub], metric_label, [metric_icon], items[{rank, name, [say], line, value, [tag], [mono], [color]}], cta
"""
import re

DEFAULTS = {"voice": "af_heart", "speed": 1.05, "style": "sunset", "captions": {"y": 1430, "maxWords": 3}}
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def _items(c):
    return sorted(c["items"], key=lambda it: -it["rank"])  # countdown order


def _intro(it, last):
    return f"{'And number' if last else 'Number'} {WORDS.get(it['rank'], it['rank'])}:"


def segments(b):
    c = b["content"]
    items = _items(c)
    segs = [{"id": "hook", "text": c["hook"], "caption": False, "post": 0.4}]
    for i, it in enumerate(items):
        last = i == len(items) - 1
        segs.append({"id": f"item{i}", "text": f"{_intro(it, last)} {it.get('say', it['name'])}. {it['line']}",
                     "caption": False, "pre": 1.1 if last else 0.2, "post": 0.45})
    segs.append({"id": "cta", "text": c["cta"], "caption": True, "pre": 0.2, "post": 0.2})
    return segs


def events(b, T, D):
    c = b["content"]
    items = _items(c)
    ev = {"cover": 1.0}
    for i, it in enumerate(items):
        s = T[f"item{i}"]
        n_intro = len(_intro(it, i == len(items) - 1).split())
        n_name = len(re.sub(r"\s+", " ", it.get("say", it["name"])).split())
        ws = s["words"]
        name_t = ws[n_intro][1] if len(ws) > n_intro else s["start"] + 0.6
        line_from = n_intro + n_name
        ev[f"i{i}_in"] = round(s["start"] - 0.28, 3)
        ev[f"i{i}_name"] = round(name_t, 3)
        ev[f"i{i}_stat"] = round(name_t + 0.45, 3)
        ev[f"i{i}_line_from"] = line_from
        nxt = T[f"item{i + 1}"]["start"] - 0.28 if i + 1 < len(items) else T["cta"]["start"] - 0.15
        if i + 1 < len(items) and i + 1 == len(items) - 1:
            nxt = T[f"item{i + 1}"]["start"] - 1.15  # leave the stage empty during the #1 suspense beat
        ev[f"i{i}_out"] = round(nxt, 3)
        ev[f"i{i}_board"] = round(nxt - 0.05, 3)
    last = len(items) - 1
    ev["one_riser"] = round(T[f"item{last}"]["start"] - 1.05, 3)
    ev["one_hit"] = round(T[f"item{last}"]["start"] - 0.05, 3)
    ev["cta_in"] = round(T["cta"]["start"] - 0.15, 3)
    ev["press"] = round(T["cta"]["start"] + max(1.3, (T["cta"]["end"] - T["cta"]["start"]) * 0.6), 3)
    return ev


def sfx(b, T, D, ev):
    n = len(b["content"]["items"])
    out = [("impact", 0.04, 0.8)]
    for i in range(n):
        out += [("whoosh", ev[f"i{i}_in"], 0.6), ("impact", ev[f"i{i}_in"] + 0.28, 0.45 if i < n - 1 else 1.0),
                ("pop", ev[f"i{i}_stat"], 0.6), ("ding", ev[f"i{i}_stat"] + 0.8, 0.35)]
        if i < n - 1:
            out.append(("pop", ev[f"i{i}_board"], 0.7))
    out += [("riser", ev["one_riser"], 0.7), ("sparkle", ev["one_hit"] + 0.1, 0.8)]
    out += [("whoosh", ev["cta_in"], 0.5), ("click", ev["press"], 1.0), ("sparkle", ev["press"] + 0.05, 0.5)]
    return out


def music(b, T, D, ev):
    return {"style": "pulse", "progression": "minor_pop", "bpm": 118,
            "breaks": [(ev["one_riser"], ev["one_hit"])], "hits": [ev["one_hit"]]}


def data(b, T, D, ev):
    return {"items": _items(b["content"])}
