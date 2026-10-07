"""Say-this-not-that (bilingual): wrong phrase (struck) -> right phrase -> spoken English explanation + Urdu/Hindi on-screen -> save/follow CTA.

Viral mechanics: "stop saying X" pattern-interrupt hook, instant usefulness (saves + sends),
series potential (daily tips), and bilingual reach (English audio + Urdu text) for South Asia.
content: hook, [hook_display], [hook_ur], [kicker], pairs[{wrong, right, explain, ur, [say_wrong], [say_right]}], cta, [cta_ur]
Urdu text is rendered in Noto Nastaliq Urdu (RTL). TTS stays English: Kokoro has no Urdu voice;
for Urdu narration record your own voice ("voice": "files").
"""

DEFAULTS = {"voice": "bf_emma", "speed": 0.95, "style": "editorial", "urdu": True, "captions": {"y": 1440, "maxWords": 3}}


def _sw(p):
    return p.get("say_wrong", f"Don't say: {p['wrong']}")


def _sr(p):
    return p.get("say_right", f"Say: {p['right']}")


def segments(b):
    c = b["content"]
    segs = [{"id": "hook", "text": c["hook"], "caption": False, "post": 0.4}]
    for i, p in enumerate(c["pairs"]):
        segs.append({"id": f"w{i}", "text": _sw(p), "caption": False, "pre": 0.3, "post": 0.35})
        segs.append({"id": f"r{i}", "text": _sr(p), "caption": False, "post": 0.3})
        uv = b.get("urdu_voice")
        if uv and p.get("say_ur"):  # explanation spoken in Urdu (experimental TTS) - the Urdu card is the visual
            segs.append({"id": f"e{i}", "text": p["say_ur"], "caption": False, "post": 0.9,
                         "lang": "ur", "voice": uv.get("voice", "hf_alpha"), "speed": uv.get("speed", 0.95)})
        else:
            segs.append({"id": f"e{i}", "text": p["explain"], "caption": True, "post": 0.9})
    segs.append({"id": "cta", "text": c["cta"], "caption": True, "pre": 0.1, "post": 0.2})
    return segs


def events(b, T, D):
    c = b["content"]
    n = len(c["pairs"])
    ev = {"cover": 1.0}
    for i in range(n):
        ev[f"p{i}_in"] = round(T[f"w{i}"]["start"] - 0.32, 3)
        ev[f"w{i}_strike"] = round(T[f"w{i}"]["end"] + 0.05, 3)
        ev[f"r{i}_in"] = round(T[f"r{i}"]["start"] - 0.12, 3)
        ev[f"e{i}_in"] = round(T[f"e{i}"]["start"] - 0.1, 3)
        nxt = T[f"w{i + 1}"]["start"] - 0.32 if i + 1 < n else T["cta"]["start"] - 0.12
        ev[f"p{i}_out"] = round(nxt - 0.04, 3)
    ev["cta_in"] = round(T["cta"]["start"] - 0.12, 3)
    ev["press"] = round(T["cta"]["start"] + max(1.3, (T["cta"]["end"] - T["cta"]["start"]) * 0.6), 3)
    return ev


def sfx(b, T, D, ev):
    n = len(b["content"]["pairs"])
    out = [("impact", 0.04, 0.7)]
    for i in range(n):
        out += [("whoosh", ev[f"p{i}_in"], 0.6), ("wrong", ev[f"w{i}_strike"], 0.8),
                ("correct", ev[f"r{i}_in"], 0.75), ("pop", ev[f"e{i}_in"], 0.5)]
    out += [("whoosh", ev["cta_in"], 0.5), ("click", ev["press"], 1.0), ("sparkle", ev["press"] + 0.05, 0.5)]
    return out


def music(b, T, D, ev):
    return {"style": "chill", "progression": "chill", "bpm": 84}


def data(b, T, D, ev):
    c = b["content"]
    return {"urdu_voice": bool(b.get("urdu_voice")),
            "wrong_from": [len(_sw(p).split()) - len(p["wrong"].split()) for p in c["pairs"]],
            "right_from": [len(_sr(p).split()) - len(p["right"].split()) for p in c["pairs"]]}
