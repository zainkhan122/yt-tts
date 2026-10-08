"""Spotlight scene engine, shared by templates/repo-spotlight (F1) and templates/tool-spotlight (F2).

A spotlight brief is a list of scenes. Each scene = one voice line ("say") + a visual type:
  clip          official demo clip: blurred full-bleed fill + framed video; optional headline/sub (the hook)
  clip-montage  2-4 cuts from a clip, each a framed card with a big label chip, whip transitions
  page          browser frame on a capture image: camera moves to regions, cursor click, optional stat count-up
  scroll        README scroll in a browser frame: camera visits regions, highlight boxes + label chips (F1 core)
  steps         numbered steps lit in sync with the voice over a dimmed scrolling page (+ optional figure)
  terminal      install commands typed live with key-tap SFX + check-mark outputs
  verdict       catches + pros, each revealed as it is said
  stat          huge count-up number + label
  image         official image / logo / og card with a Ken Burns punch-in, optional heading + chips
  endcard       question + keyword CTA chip + follow card with a cursor press

Every visual event is anchored to the real voice-over words (T[scene_id]["words"]); regions + facts come from
the capture pack (tools/capture.py -> captures/<id>/manifest.json). Display vs spoken text: "{GTA V|GTA Five}".
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STOP = set("a an the and or of to in on at for with it its is are was be this that you your our we they them from by "
           "as into over under all any most more some just real own".split())


# ------------------------------------------------------------------ inputs
def capture(b):
    d = (ROOT / b["capture"]) if b.get("capture") else None
    m = json.loads((d / "manifest.json").read_text()) if d and (d / "manifest.json").exists() else {}
    return d, m


def scenes(b):
    return [s for s in b.get("scenes", []) if not s.get("skip")]


def _norm(w):
    return re.sub(r"[^a-z0-9]", "", str(w).lower())


def _display(text):
    """Display form of a markup string ('{GTA V|GTA Five}' -> 'GTA V')."""
    return re.sub(r"\{([^{}|]+)\|[^{}]+\}", r"\1", text or "")


def image_dims(b, name):
    """CSS size of a capture image: manifest css_width/scale for page captures, else pixel size."""
    d, m = capture(b)
    for f in (m.get("files") or {}).values():
        if f.get("file") == name and f.get("px") and f.get("css_width"):
            sc = f.get("scale") or (f["px"][0] / f["css_width"])
            return {"file": name, "w": f["css_width"], "h": round(f["px"][1] / sc), "kind": f.get("kind", "")}
    try:
        from PIL import Image
        with Image.open(d / name) as im:
            return {"file": name, "w": im.size[0], "h": im.size[1], "kind": "image"}
    except Exception:
        return {"file": name, "w": 1280, "h": 800, "kind": "image"}


def video_len(b, name):
    import subprocess
    d, _ = capture(b)
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(d / name)],
                             capture_output=True, text=True, timeout=30).stdout
        return float(out.strip())
    except Exception:
        return 9999.0


# ------------------------------------------------------------------ anchors
def anchor(seg, pats, frac=0.5, after=None):
    """Time of the first spoken word (at/after `after`) whose normalised form fully matches a regex in pats."""
    if pats:
        for w in seg.get("words", []):
            if after is not None and w[1] < after - 1e-6:
                continue
            n = _norm(w[0])
            if n and any(re.fullmatch(p, n) for p in pats):
                return w[1]
    return seg["start"] + frac * max(0.01, seg["end"] - seg["start"])


def _item_pats(text):
    pats = []
    for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", _display(text)):
        n = _norm(w)
        if len(n) >= 3 and n not in STOP:
            stem = re.sub(r"(ing|ed|es|s)$", "", n) if len(n) > 4 else n
            pats.append(re.escape(stem) + r"[a-z]*")
    return pats


def seq_anchors(seg, items, t0, t1, explicit=None):
    """One time per item, in order: explicit word patterns > fuzzy keyword match > even spacing between found anchors."""
    times, after = [], t0
    for i, it in enumerate(items):
        pats = (explicit or {}).get(i) or _item_pats(it)
        t = None
        for w in seg.get("words", []):
            if w[1] < after - 1e-6:
                continue
            n = _norm(w[0])
            if n and any(re.fullmatch(p, n) for p in pats):
                t = w[1]
                break
        times.append(t)
        if t is not None:
            after = t + 0.05
    known = [(i, t) for i, t in enumerate(times) if t is not None]
    pts = [(-1, t0)] + known + [(len(items), t1)]
    for (ia, ta), (ib, tb) in zip(pts, pts[1:]):
        for k in range(ia + 1, ib):
            times[k] = ta + (tb - ta) * (k - ia) / (ib - ia)
    return [round(max(t0, min(t1, t)), 3) for t in times]


# ------------------------------------------------------------------ template API
POST = {"terminal": 0.85, "endcard": 0.9, "verdict": 0.3, "clip": 0.1, "clip-montage": 0.12, "page": 0.2, "stat": 0.25}


def segments(b, cfg):
    sc = scenes(b)
    b.setdefault("captions", {}).setdefault("keywords", keywords(b))
    out = []
    for i, s in enumerate(sc):
        cap = s.get("caption", not ((s["type"] == "clip" and s.get("headline")) or s["type"] == "endcard"))
        seg = {"id": s["id"], "text": s.get("say", ""), "caption": cap,
               "pre": s.get("pre", 0.0 if i == 0 else cfg["gap"]), "post": s.get("post", POST.get(s["type"], cfg["post"]))}
        if not s.get("say"):
            seg["hold"] = float(s.get("hold", 2.0))
        out.append(seg)
    return out


def keywords(b):
    """Caption words shown in yellow: brief keywords + product name + CTA keyword + 'free'."""
    kw = list(b.get("keywords", []))
    _, m = capture(b)
    repo = (m.get("facts") or {}).get("repo", "")
    kw += re.split(r"[-_/ ]+", repo.split("/")[-1]) if repo else []
    for s in scenes(b):
        if s.get("keyword"):
            kw.append(s["keyword"])
    kw += ["free"]
    return sorted({_norm(k) for k in kw if len(_norm(k)) >= 2})


def _footage(s):
    """Seconds of usable footage for a clip / montage scene (None = unlimited)."""
    if s["type"] == "clip" and s.get("out") is not None:
        return float(s["out"]) - float(s.get("in", 0.0))
    if s["type"] == "clip-montage" and s.get("cuts") and all(c.get("out") is not None for c in s["cuts"]):
        return sum(float(c["out"]) - float(c.get("in", 0.0)) for c in s["cuts"])
    return None


def windows(b, T, D, lead):
    sc, out = scenes(b), {}
    starts = [0.0 if i == 0 else max(0.0, T[s["id"]]["start"] - lead) for i, s in enumerate(sc)]
    for i, s in enumerate(sc[:-1]):  # a clip scene ends when its footage does; the next scene's visuals lead its voice
        f = _footage(s)
        if f is not None and starts[i + 1] - starts[i] > f + 0.15:
            starts[i + 1] = round(starts[i] + f, 3)
    for i, s in enumerate(sc):
        out[s["id"]] = (round(starts[i], 3), round(starts[i + 1] if i + 1 < len(sc) else D, 3))
    return out


def events(b, T, D, cfg):
    sc = scenes(b)
    W = windows(b, T, D, cfg["lead"])
    ev = {"cover": round(min(0.6, D / 4), 3)}
    media_end = {}  # src -> source time where the previous clip scene stopped (continuity editing)
    for s in sc:
        sid, (t0, t1) = s["id"], W[s["id"]]
        seg = T[sid]
        ev[f"{sid}_in"], ev[f"{sid}_out"] = t0, t1
        typ = s["type"]
        if typ == "clip":
            media_end[s.get("src")] = float(s.get("in", 0.0)) + (t1 - t0)
        if typ == "clip-montage":  # cut k switches on its own word ("at"), else even spacing; >= 0.45 s per cut
            cuts = [dict(c) for c in s.get("cuts", [])]
            if cuts:  # first cut continues where the previous clip of the same source stopped (no repeat, no jump)
                me = media_end.get(s.get("src"))
                c0 = cuts[0]
                if me is not None and float(c0.get("in", 0.0)) <= me < float(c0.get("out", 1e9)) - 0.3:
                    c0["in"] = round(me, 3)
                ev[f"{sid}_cut0_in"] = float(c0.get("in", 0.0))
            n = max(1, len(cuts))
            ts = []
            for k, c in enumerate(cuts or [{}]):
                even = t0 + (t1 - t0) * k / n
                t = (anchor(seg, [c["at"]], 0) - 0.08) if (k and c.get("at")) else even
                if k:
                    prev = cuts[k - 1]
                    if prev.get("out") is not None:  # cut before the previous shot ends (visual may lead the voice)
                        t = min(t, ts[-1] + float(prev["out"]) - float(prev.get("in", 0.0)))
                ts.append(t0 if k == 0 else max(ts[-1] + 0.45, min(t, t1 - 0.45 * (n - k))))
            for k, t in enumerate(ts):
                ev[f"{sid}_cut{k}"] = round(t, 3)
        elif typ == "page":
            cams = s.get("camera", [])
            pats = [c.get("at") for c in cams]
            ts = []
            for k, c in enumerate(cams):
                default = seg["start"] + (seg["end"] - seg["start"]) * (0.08 + 0.55 * k / max(1, len(cams)))
                t = anchor(seg, [c["at"]] if c.get("at") else None, 0) if c.get("at") else default
                ts.append(round(max(t0 + 0.15, t - 0.35), 3))
            for k, t in enumerate(ts):
                ev[f"{sid}_cam{k}"] = t
            for k, c in enumerate(s.get("cursor", [])):
                t = anchor(seg, [c["at"]] if c.get("at") else None, 0.78)
                ev[f"{sid}_click{k}"] = round(min(t1 - 0.5, t), 3)
            if s.get("stat"):
                st = s["stat"]
                t = anchor(seg, [st["at"]] if st.get("at") else [r"\d[\d,]*", r"stars?"], 0.6)
                ev[f"{sid}_stat"] = round(min(t1 - 1.2, t - 0.1), 3)
        elif typ == "scroll":
            stops = s.get("stops", [])
            ts = seq_anchors(seg, [st.get("label", "") for st in stops], seg["start"], seg["end"] - 0.4,
                             {k: [st["at"]] for k, st in enumerate(stops) if st.get("at")})
            for k, t in enumerate(ts):
                ev[f"{sid}_stop{k}"] = round(max(t0 + 0.2, t - 0.45), 3)
        elif typ == "steps":
            steps = s.get("steps", [])
            ts = seq_anchors(seg, steps, seg["start"], seg["end"] - 0.3,
                             {k: [p] for k, p in enumerate(s.get("step_at", [])) if p})
            for k, t in enumerate(ts):
                ev[f"{sid}_step{k}"] = round(max(t0 + 0.15, t - 0.12), 3)
            if s.get("figure"):
                fk = s.get("figure_step", max(0, len(steps) - 2))
                ev[f"{sid}_figure"] = ev.get(f"{sid}_step{min(fk, len(steps) - 1)}", t0 + 1.0)
        elif typ == "terminal":
            lines = s.get("lines", [])
            avail = max(1.2, (t1 - t0) - 0.9 - 0.35 * len(lines))
            total = sum(len(l) for l in lines) or 1
            cps = min(70.0, max(24.0, total / avail))
            t = t0 + 0.4
            for k, line in enumerate(lines):
                dur = len(line) / cps
                ev[f"{sid}_type{k}"], ev[f"{sid}_type{k}_end"] = round(t, 3), round(t + dur, 3)
                t += dur + 0.35
            ev[f"{sid}_cps"] = round(cps, 2)
        elif typ == "verdict":
            order = s.get("order", ["cons", "pros"])
            items = [(grp, k, txt) for grp in order for k, txt in enumerate(s.get(grp, []))]
            ts = seq_anchors(seg, [txt for _, _, txt in items], seg["start"] + 0.35, seg["end"] - 0.2,
                             {i: [p] for i, p in enumerate(s.get("item_at", [])) if p})
            for (grp, k, _), t in zip(items, ts):
                ev[f"{sid}_{grp}{k}"] = round(t - 0.1, 3)
            for grp in order:
                if s.get(grp):
                    ev[f"{sid}_{grp}_card"] = round(ev[f"{sid}_{grp}0"] - 0.25, 3)
        elif typ == "stat":
            ev[f"{sid}_stat"] = round(anchor(seg, [s["at"]] if s.get("at") else [r"\d[\d,]*"], 0.3) - 0.1, 3)
        elif typ == "endcard":
            kw = _norm(s.get("keyword", "")) or "comment"
            tk = anchor(seg, [r"comment", re.escape(kw)], 0.45)
            ev[f"{sid}_keyword"] = round(tk - 0.08, 3)
            ev["cta_in"] = t0
            ev["follow_in"] = round(min(t1 - 2.0, tk + 0.9), 3)
            ev["press"] = round(min(t1 - 0.75, max(ev["follow_in"] + 1.1, seg["end"] - 0.2)), 3)
    return ev


def qa_montage(b, T, D, ev):
    """Each montage cut with an 'at' word must have that word spoken while the cut is on screen (0.3 s lead allowed)."""
    issues = []
    for s in scenes(b):
        if s["type"] != "clip-montage":
            continue
        cuts, t1 = s.get("cuts", []), ev[f"{s['id']}_out"]
        for k, c in enumerate(cuts):
            if not c.get("at"):
                continue
            a = ev[f"{s['id']}_cut{k}"]
            z = ev[f"{s['id']}_cut{k + 1}"] if k + 1 < len(cuts) else t1
            w = anchor(T[s["id"]], [c["at"]], -1)
            if w < a - 0.3 or w > z:
                issues.append(f"{s['id']} cut {k} '{c.get('label', '')}' on screen {a:.2f}-{z:.2f}s but '{c['at']}' is said at {w:.2f}s")
    return issues


def html(b, T, D, ev, cfg):
    """Static <video> clips (the renderer extracts frames from DOM-declared media). JS animates the wrappers."""
    for issue in qa_montage(b, T, D, ev):
        print(f"[spotlight] WARNING label/voice mismatch: {issue}  (reword the line or adjust the cut)", flush=True)
    out = []
    track = 4
    for s in scenes(b):
        sid = s["id"]
        t0, t1 = ev[f"{sid}_in"], ev[f"{sid}_out"]
        if s["type"] == "clip":
            src = s["src"]
            dur = t1 - t0
            vlen = video_len(b, src)
            mstart = float(s.get("in", 0.0))
            if s.get("out") is not None and mstart + dur > float(s["out"]):
                mstart = max(0.0, mstart - 0.2, float(s["out"]) - dur)
            mstart = max(0.0, min(mstart, vlen - dur)) if vlen < 9000 else mstart
            out.append(_vset(f"{sid}", src, t0, dur, mstart, track, fill=s.get("fit", "fill-blur") == "fill-blur"))
            track += 2
        elif s["type"] == "clip-montage":
            cuts = s.get("cuts", [])
            vlen = video_len(b, s["src"])
            for k, c in enumerate(cuts):
                a = ev[f"{sid}_cut{k}"]
                z = ev[f"{sid}_cut{k + 1}"] if k + 1 < len(cuts) else t1
                dur = z - a
                mstart = float(ev.get(f"{sid}_cut0_in", c.get("in", 0.0))) if k == 0 else float(c.get("in", 0.0))
                if c.get("out") is not None and mstart + dur > float(c["out"]):  # avoid the next shot, but never back
                    mstart = max(0.0, mstart - 0.2, float(c["out"]) - dur)        # more than 0.2 s into the previous one
                mstart = max(0.0, min(mstart, vlen - dur)) if vlen < 9000 else mstart
                out.append(_vset(f"{sid}-{k}", s["src"], a, dur, mstart, track, fill=True))
                track += 2
    return "\n".join(out)


def blur_name(src):
    return Path(src).stem + "-blurfill.mp4"


def _vset(key, src, start, dur, mstart, track, fill=True):
    v = (lambda vid, file, tr: f'<video id="{vid}" class="sp-v" src="assets/{file}" data-start="{start:.3f}" data-duration="{dur:.3f}" '
                               f'data-media-start="{mstart:.3f}" data-track-index="{tr}" muted playsinline></video>')
    fill_html = f'<div class="sp-vfill">{v(f"vf-{key}", blur_name(src), track)}</div>' if fill else ""
    return (f'<div class="sp-vset" id="vs-{key}" data-layout-allow-overflow>{fill_html}'
            f'<div class="sp-vcard"><div class="sp-vclip">{v(f"vc-{key}", src, track + 1)}</div></div></div>')


def _blurred(src_path):
    """Low-res pre-blurred, darkened copy for the full-bleed fill (cached). Cheaper than a live CSS blur, distinct source."""
    import subprocess
    cache = Path("/var/tmp/spot-cache")
    cache.mkdir(parents=True, exist_ok=True)
    out = cache / f"{src_path.parent.name}-{blur_name(src_path.name)}"
    if not out.exists() or out.stat().st_mtime < src_path.stat().st_mtime:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src_path), "-an", "-vf",
                        "scale=320:-2,boxblur=12:3,eq=brightness=-0.22:saturation=1.3", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)
    return out


def assets(b):
    d, _ = capture(b)
    names = []
    for s in scenes(b):
        for k in ("src", "image", "figure", "logo"):
            if isinstance(s.get(k), str):
                names.append(s[k])
        bg = s.get("background")
        if isinstance(bg, dict) and bg.get("image"):
            names.append(bg["image"])
    seen, out = set(), []
    for n in names:
        if n not in seen and d and (d / n).exists():
            seen.add(n)
            out.append((d / n, n))
    for s in scenes(b):  # blurred fill derivatives for clip scenes
        if s["type"] in ("clip", "clip-montage") and d and (d / s["src"]).exists() and blur_name(s["src"]) not in seen:
            seen.add(blur_name(s["src"]))
            out.append((_blurred(d / s["src"]), blur_name(s["src"])))
    return out


def sfx(b, T, D, ev, cfg):
    out = [("impact", 0.03, 0.75)]
    sc = scenes(b)
    for i, s in enumerate(sc):
        sid, typ = s["id"], s["type"]
        if i > 0:
            out.append(("whoosh", max(0, ev[f"{sid}_in"] - 0.12), 0.5 if cfg["cut"] == "whip" else 0.3))
        if typ == "clip-montage":
            for k in range(1, len(s.get("cuts", []))):
                out.append(("whoosh", ev[f"{sid}_cut{k}"] - 0.1, 0.45))
            for k in range(len(s.get("cuts", []))):
                out.append(("pop", ev[f"{sid}_cut{k}"] + 0.12, 0.5))
        elif typ == "page":
            for k, _ in enumerate(s.get("cursor", [])):
                out.append(("click", ev[f"{sid}_click{k}"], 1.0))
            if s.get("stat"):
                out += [("pop", ev[f"{sid}_stat"], 0.6), ("ding", ev[f"{sid}_stat"] + 1.25, 0.45)]
        elif typ == "scroll":
            for k, _ in enumerate(s.get("stops", [])):
                out.append(("pop", ev[f"{sid}_stop{k}"] + 0.35, 0.5))
        elif typ == "steps":
            for k, _ in enumerate(s.get("steps", [])):
                out.append(("pop", ev[f"{sid}_step{k}"], 0.55))
        elif typ == "terminal":
            for k, line in enumerate(s.get("lines", [])):
                a, z = ev[f"{sid}_type{k}"], ev[f"{sid}_type{k}_end"]
                t = a
                while t < z - 0.1:
                    out.append(("typing", t, 0.55))
                    t += 0.85
                out.append(("correct", z + 0.18, 0.45))
        elif typ == "verdict":
            for grp in s.get("order", ["cons", "pros"]):
                for k, _ in enumerate(s.get(grp, [])):
                    out.append(("pop" if grp == "cons" else "correct", ev[f"{sid}_{grp}{k}"], 0.5))
        elif typ == "stat":
            out += [("pop", ev[f"{sid}_stat"], 0.6), ("ding", ev[f"{sid}_stat"] + 1.25, 0.45)]
        elif typ == "endcard":
            out += [("sparkle", ev[f"{sid}_keyword"] + 0.05, 0.6), ("whoosh", ev["follow_in"] - 0.1, 0.4),
                    ("click", ev["press"], 1.0), ("sparkle", ev["press"] + 0.05, 0.5)]
    return out


def data(b, T, D, ev, cfg):
    d, m = capture(b)
    sc = []
    for s in scenes(b):
        x = json.loads(json.dumps(s))
        for k in ("image",):
            if x.get(k):
                x["img"] = image_dims(b, x[k])
        bg = x.get("background")
        if isinstance(bg, dict) and bg.get("image"):
            bg["img"] = image_dims(b, bg["image"])
        if x.get("figure"):
            x["fig"] = image_dims(b, x["figure"])
        if x["type"] in ("verdict",) and x.get("region") and not x.get("image"):
            x["img"] = image_dims(b, "desktop-full.jpg")
        for k in ("headline", "sub", "heading", "label"):
            if isinstance(x.get(k), str):
                x[k] = _display(x[k])
        sc.append(x)
    facts = dict(m.get("facts") or {})
    facts.update(b.get("facts") or {})
    return {"scenes": sc, "facts": facts, "regions": m.get("regions_css", {}), "url": m.get("url", ""),
            "credits": b.get("credits_on_screen", ""), "cut": cfg["cut"], "flavor": cfg["flavor"]}


def music(b, T, D, ev, cfg):
    return dict(cfg["music"])
