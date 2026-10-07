"""Quiz / trivia: hook -> N questions (read-along question, options, countdown, reveal + fact) -> score CTA + follow card.

Viral mechanics: a curiosity hook, a "can you beat the timer" game the viewer plays along with,
a comment prompt ("comment your score"), and a rewatch reason (wrong answers -> replay).
content: hook, [hook_display], [kicker], [sub], questions[{q, options[2-4], answer(index), fact, [say_answer]}],
         [think_seconds=3], cta, [cta_title]
"""
import re

DEFAULTS = {"voice": "af_bella", "speed": 1.05, "style": "midnight", "captions": {"y": 1440, "maxWords": 3}}


def _clean(t):
    return re.sub(r"\s+", " ", re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", t)).strip()


def _answer_line(q):
    return f"{q.get('say_answer', q['options'][q['answer']])}!"


def segments(b):
    c = b["content"]
    think = float(c.get("think_seconds", 3))
    segs = [{"id": "hook", "text": c["hook"], "caption": False, "post": 0.35}]
    for i, q in enumerate(c["questions"]):
        segs.append({"id": f"q{i}", "text": q["q"], "caption": False, "pre": 0.3, "post": 0.2})
        segs.append({"id": f"think{i}", "text": "", "hold": think, "post": 0.0})
        segs.append({"id": f"a{i}", "text": f"{_answer_line(q)} {q['fact']}", "caption": False, "post": 0.3})
    segs.append({"id": "cta", "text": c["cta"], "caption": True, "pre": 0.15, "post": 0.2})
    return segs


def events(b, T, D):
    c = b["content"]
    qs = c["questions"]
    think = int(round(float(c.get("think_seconds", 3))))
    ev = {"cover": 1.2}
    for i, q in enumerate(qs):
        qs_t, q_end = T[f"q{i}"]["start"], T[f"q{i}"]["end"]
        ev[f"q{i}_in"] = round(qs_t - 0.32, 3)
        o0 = max(qs_t + 0.35, q_end - 0.7)
        for k in range(len(q["options"])):
            ev[f"q{i}_opt{k}"] = round(o0 + 0.2 * k, 3)
        ts = T[f"think{i}"]["start"]
        ev[f"t{i}_start"] = ts
        for s in range(think):
            ev[f"t{i}_tick{s}"] = round(ts + s, 3)
        ev[f"r{i}"] = round(T[f"a{i}"]["start"] - 0.06, 3)
        nxt = T[f"q{i + 1}"]["start"] - 0.32 if i + 1 < len(qs) else T["cta"]["start"] - 0.12
        ev[f"q{i}_out"] = round(nxt - 0.04, 3)
    ev["cta_in"] = round(T["cta"]["start"] - 0.12, 3)
    ev["press"] = round(T["cta"]["start"] + max(1.3, (T["cta"]["end"] - T["cta"]["start"]) * 0.6), 3)
    return ev


def sfx(b, T, D, ev):
    c = b["content"]
    think = int(round(float(c.get("think_seconds", 3))))
    out = [("impact", 0.04, 0.9), ("riser", max(0.0, ev["q0_in"] - 1.2), 0.35)]
    for i, q in enumerate(c["questions"]):
        out.append(("whoosh", ev[f"q{i}_in"], 0.7))
        out += [("pop", ev[f"q{i}_opt{k}"], 0.8) for k in range(len(q["options"]))]
        out += [("tick" if s % 2 == 0 else "tock", ev[f"t{i}_tick{s}"], 1.0) for s in range(think)]
        out.append(("correct", ev[f"r{i}"], 0.9))
    out += [("whoosh", ev["cta_in"], 0.6), ("click", ev["press"], 1.0), ("sparkle", ev["press"] + 0.05, 0.6)]
    return out


def music(b, T, D, ev):
    n = len(b["content"]["questions"])
    return {"style": "tension", "progression": "dark", "bpm": 100,
            "breaks": [(T[f"think{i}"]["start"], T[f"think{i}"]["end"]) for i in range(n)],
            "hits": [ev[f"r{i}"] for i in range(n)]}


def data(b, T, D, ev):
    c = b["content"]
    return {"think": int(round(float(c.get("think_seconds", 3)))),
            "ans_words": [len(_clean(_answer_line(q)).split()) for q in c["questions"]]}
