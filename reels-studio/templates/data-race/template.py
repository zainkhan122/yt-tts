"""Data race: real time-series (e.g. World Bank) drawn as a racing line chart synced to narration beats -> final ranking -> CTA.

Viral mechanics: a "guess who wins" hook, lead changes as mini-payoffs, a screenshot-worthy
final ranking (drives shares/sends), and comment bait that is factual, not inflammatory.
content: title, subtitle, hook, [hook_display], [hook_sub], series[{name, flag, color, values{year: v}}],
         beats[{year, text}], takeaway, [rank_title], cta, [unit_prefix="$"], [unit_suffix=""], [source_note]
Narration numbers must come from the data (use tools/fetch_worldbank.py fact sheet).
"""

DEFAULTS = {"voice": "am_michael", "speed": 1.0, "style": "neon", "captions": {"y": 1535, "maxWords": 3}}


def segments(b):
    c = b["content"]
    segs = [{"id": "hook", "text": c["hook"], "caption": False, "post": 0.5}]
    for k, bt in enumerate(c["beats"]):
        segs.append({"id": f"beat{k}", "text": bt["text"], "caption": True, "pre": 0.25 if k == 0 else 0.0, "post": 0.55})
    segs.append({"id": "takeaway", "text": c["takeaway"], "caption": True, "pre": 0.2, "post": 0.4})
    segs.append({"id": "cta", "text": c["cta"], "caption": True, "pre": 0.1, "post": 0.2})
    return segs


def _years(c):
    return sorted(int(y) for y in c["series"][0]["values"])


def anchors(c, T):
    """(time, year) pairs: the chart arrives at a beat's year ~30% into its sentence, holds to ~80%, then races on."""
    beats = c["beats"]
    out = []
    for k, bt in enumerate(beats):
        s, e = T[f"beat{k}"]["start"], T[f"beat{k}"]["end"]
        d = e - s
        arrive = s if k == 0 else s + 0.3 * d  # reach the year while the sentence is spoken...
        out.append((round(arrive, 3), bt["year"]))
        out.append((round(s + 0.8 * d, 3), bt["year"]))  # ...hold, then race to the next beat in the gap
    ys = _years(c)
    if out[-1][1] < ys[-1]:  # make sure the race reaches the last data year
        out.append((round(T[f"beat{len(beats) - 1}"]["end"] - 0.2, 3), ys[-1]))
    return out


def year_time(A, year):
    if year <= A[0][1]:
        return A[0][0]
    for (t0, y0), (t1, y1) in zip(A, A[1:]):
        if y0 <= year <= y1 and y1 > y0:
            return t0 + (t1 - t0) * (year - y0) / (y1 - y0)
    return A[-1][0]


def leaders(c):
    out = {}
    for y in _years(c):
        vals = [s["values"][str(y)] for s in c["series"]]
        out[y] = vals.index(max(vals))
    return out


def events(b, T, D):
    c = b["content"]
    A = anchors(c, T)
    L = leaders(c)
    ys = _years(c)
    changes = [y for p, y in zip(ys, ys[1:]) if L[y] != L[p]]
    return {
        "cover": 1.1,
        "chart_in": round(T["beat0"]["start"] - 0.55, 3),
        "anchors": A,
        "lead_changes": [[y, round(year_time(A, y), 3)] for y in changes],
        "rank_in": round(T["takeaway"]["start"] - 0.15, 3),
        "cta_in": round(T["cta"]["start"] - 0.12, 3),
        "press": round(T["cta"]["start"] + max(1.3, (T["cta"]["end"] - T["cta"]["start"]) * 0.6), 3),
    }


def sfx(b, T, D, ev):
    out = [("impact", 0.04, 0.8), ("whoosh", ev["chart_in"], 0.7)]
    out += [("pop", t, 0.75) for _, t in ev["lead_changes"]]
    out += [("whoosh", ev["rank_in"], 0.7), ("sparkle", ev["rank_in"] + 0.5, 0.6)]
    out += [("whoosh", ev["cta_in"], 0.5), ("click", ev["press"], 1.0), ("sparkle", ev["press"] + 0.05, 0.5)]
    return out


def music(b, T, D, ev):
    return {"style": "cinematic", "progression": "uplift", "bpm": 92, "hits": [ev["rank_in"]]}


def data(b, T, D, ev):
    c = b["content"]
    ys = _years(c)
    return {"years": ys, "first": ys[0], "last": ys[-1]}
