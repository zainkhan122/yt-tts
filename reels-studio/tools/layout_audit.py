#!/usr/bin/env python3
"""Layout audit: measure the REAL spotlight DOM in Chromium and fail on collisions.

Why this exists: the renderer can claim "captions never touch the media" in a comment
while a 608px cover stage ends at y=1308 and the caption zone starts at y=1160. This
tool builds the actual composition HTML for a brief (same template functions, same CSS,
same GSAP timeline), seeks the timeline to sampled moments, and reads element boxes.

  python3 tools/layout_audit.py briefs/repo-huashu-motion-01.json [--shots out/]
  -> prints a table per scene; exit 1 on any overlap / out-of-safe-area element.

It measures geometry, not taste: a human still reviews the frames it writes.
"""
import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "templates" / "_base"
SHARED = ROOT / "templates" / "_spotlight"

# Elements that are design overlays on purpose (stamps, highlight boxes, cursors,
# dimmers). They may sit on top of media but still must stay out of the caption zone.
OVERLAYS = ".arch-stamp, .arch-kicker, .sp-chip, .sp-hlbox, .sp-cursor, .sp-dim, .sp-ripple"
# Surfaces: anything a caption must never touch.
SURFACES = (".sp-imgcard, .sp-vcard, .sp-browser, .sp-term, .sp-steps, .sp-vcardx, .sp-stat, "
            ".sp-question, #endcard, .sp-vset")


def load_template(template):
    path = ROOT / "templates" / template / "template.py"
    spec = importlib.util.spec_from_file_location("tpl_" + template.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def synth_timing(b, tpl):
    """Word-level timing with the same shape the TTS stage produces (geometry only)."""
    T, order, t = {}, [], 0.6
    for seg in tpl.segments(b):
        words, start = [], t
        for w in (seg.get("text") or "hold").split():
            dur = max(0.22, min(0.62, 0.16 + 0.05 * len(w)))
            words.append([w, round(t, 3), round(t + dur, 3)])
            t += dur + 0.04
        end = round(t + float(seg.get("post", 0.2)), 3)
        T[seg["id"]] = {"start": round(start, 3), "end": end, "text": seg.get("text", ""),
                        "spoken": seg.get("text", ""), "caption": seg.get("caption", True),
                        "words": words, "lang": b.get("lang", "en-us")}
        order.append(seg["id"])
        t = end + float(seg.get("pre", 0.12))
    return T, order, round(t + 0.4, 3)


def scene_part(name):
    return "\n".join(p.read_text() for p in (SHARED / name, SHARED / name.replace(".", "_arch."))
                     if p.exists())


def build_page(b, work, tpl):
    T, order, D = synth_timing(b, tpl)
    ev = tpl.events(b, T, D)
    caps = {**tpl.DEFAULTS.get("captions", {}), **b.get("captions", {})}
    data = {"id": b["id"], "duration": D, "fps": 30, "seed": 7, "lang": b.get("lang", "en-us"),
            "urdu": False, "brand": {"handle": "@hypeless.ai", "name": "Hypeless AI", "tagline": ""},
            "segs": T, "order": order, "events": ev, "captions": caps,
            "content": b.get("content", {}), "extra": tpl.data(b, T, D, ev)}
    fonts = []
    (work / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    for fam, (fn, wght) in {"Anton": ("Anton.ttf", 400), "Inter": ("Inter.ttf", 900),
                            "JetBrains Mono": ("JetBrainsMono.ttf", 500)}.items():
        src = BASE / "fonts" / fn
        if src.exists():
            shutil.copy2(src, work / "assets" / "fonts" / fn)
            fonts.append(f'@font-face {{ font-family: "{fam}"; src: url("assets/fonts/{fn}") format("truetype"); '
                         f'font-weight: {wght}; font-style: normal; }}')
    for src, name in (tpl.assets(b) if hasattr(tpl, "assets") else []):
        dst = work / "assets" / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    scene_css = (SHARED / "scene.css").read_text() + "\n" + (SHARED / "archetype.css").read_text()
    scene_js = (SHARED / "scene.js").read_text() + "\n" + (SHARED / "archetype.js").read_text()
    rep = {"{{FONTS_CSS}}": "\n".join(fonts), "{{BASE_CSS}}": (BASE / "base.css").read_text(),
           "{{SCENE_CSS}}": scene_css, "{{MEDIA_HTML}}": tpl.html(b, T, D, ev),
           "{{SCENE_HTML}}": (SHARED / "scene.html").read_text() if (SHARED / "scene.html").exists() else "",
           "{{BASE_JS}}": (BASE / "base.js").read_text(), "{{SCENE_JS}}": scene_js,
           "{{DATA_JSON}}": json.dumps(data, ensure_ascii=False).replace("</", "<\\/"),
           "{{LANG}}": "en", "{{TITLE}}": b["id"], "{{PRESET}}": b.get("style", "midnight"),
           "{{ARCHETYPE}}": (b.get("treatment") or {}).get("archetype", "spotlight"), "{{D}}": f"{D:g}"}
    html = (BASE / "base.html").read_text()
    for k, v in rep.items():
        html = html.replace(k, v)
    (work / "index.html").write_text(html, encoding="utf-8")
    return T, ev, D


MEASURE_JS = r"""
() => {
  const vis = (el) => {
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const s = getComputedStyle(n);
      if (s.visibility === "hidden" || parseFloat(s.opacity) < 0.4 || s.display === "none") return false;
    }
    return true;
  };
  const box = (el) => { const r = el.getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; };
  const pick = (sel) => [...document.querySelectorAll(sel)].filter(vis).map((el) => ({
    sel: el.className || el.id, box: box(el)}));
  const caps = [...document.querySelectorAll("#cap-zone .cg")].filter(vis)
      .filter((el) => el.textContent.trim().length > 0).map(box);
  const cap = caps.length ? {
      x: Math.min(...caps.map((c) => c.x)), y: Math.min(...caps.map((c) => c.y)),
      w: Math.max(...caps.map((c) => c.x + c.w)) - Math.min(...caps.map((c) => c.x)),
      h: Math.max(...caps.map((c) => c.y + c.h)) - Math.min(...caps.map((c) => c.y))} : null;
  return {cap, surfaces: pick(".sp-imgcard, .sp-vcard, .sp-browser, .sp-term, .sp-steps, .sp-vcardx, .sp-stat, .sp-question, #endcard"),
          overlays: pick(".arch-stamp, .arch-kicker, .sp-chip, #arch-hud, .arch-rail"),
          arch: document.querySelector("#root").dataset.archetype,
          captionPlates: [...document.querySelectorAll("#cap-zone .cg")].filter(vis).length};
}
"""


def intersects(a, b, pad=8):
    if not a or not b:
        return False
    return not (a["x"] + a["w"] <= b["x"] + pad or b["x"] + b["w"] <= a["x"] + pad
                or a["y"] + a["h"] <= b["y"] + pad or b["y"] + b["h"] <= a["y"] + pad)


def audit(brief_path, out_dir=None, keep=False):
    b = json.loads(Path(brief_path).read_text())
    tpl = load_template(b.get("template", "tool-spotlight"))
    work = Path(tempfile.mkdtemp(prefix="layout-audit-"))
    T, ev, D = build_page(b, work, tpl)
    L = (tpl.data(b, T, D, ev)).get("layout") or {}
    cap_top, cap_bottom, stage_bottom = L.get("cap_top", 1160), L.get("cap_bottom", 1500), L.get("stage_bottom", 1128)

    from playwright.sync_api import sync_playwright
    shots = Path(out_dir) if out_dir else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
    problems, rows = [], []
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--no-sandbox"])
        page = br.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        # The render page loads GSAP from the same CDN the production renderer uses.
        page.goto((work / "index.html").as_uri())
        for _ in range(120):  # boot: GSAP + fonts + scene build
            if page.evaluate("() => !!(window.__timelines && window.__timelines.main)"):
                break
            page.wait_for_timeout(150)
        else:
            br.close()
            raise SystemExit("composition never finished booting (timeline missing)")
        page.evaluate("() => document.fonts.ready")
        for sid in T:
            t0, t1 = T[sid]["start"], T[sid]["end"]
            for frac in (0.25, 0.6, 0.9):
                t = round(t0 + (t1 - t0) * frac, 2)
                page.evaluate("(t) => { const tl = window.__timelines.main; tl.pause(); tl.seek(t); }", t)
                page.wait_for_timeout(120)
                m = page.evaluate(MEASURE_JS)
                for s in m["surfaces"]:
                    bx = s["box"]
                    label = f"{sid} @{t}s {str(s['sel']).split()[0]}"
                    floor = stage_bottom if m["cap"] else 1540  # no captions: only the platform UI edge applies
                    if bx["y"] + bx["h"] > floor + 1:
                        problems.append(f"{label}: bottom {bx['y'] + bx['h']:.0f} > {floor}")
                    if m["cap"] and intersects(bx, m["cap"]):
                        problems.append(f"{label}: overlaps caption box {m['cap']}")
                    rows.append({"scene": sid, "t": t, "el": str(s["sel"]), "bottom": round(bx["y"] + bx["h"]),
                                 "cap": bool(m["cap"]) and intersects(bx, m["cap"])})
                if m["cap"]:
                    if m["cap"]["y"] < cap_top - 2:
                        problems.append(f"{sid} @{t}s: caption box top {m['cap']['y']:.0f} < {cap_top}")
                    if m["cap"]["y"] + m["cap"]["h"] > cap_bottom + 2:
                        problems.append(f"{sid} @{t}s: caption box bottom {m['cap']['y'] + m['cap']['h']:.0f} > {cap_bottom}")
                if shots and frac == 0.6:
                    page.screenshot(path=str(shots / f"{sid}-{t}s.jpg"), quality=82, type="jpeg")
        br.close()
    result = {"brief": b["id"], "archetype": (b.get("treatment") or {}).get("archetype"), "duration": D,
              "samples": len(rows), "problems": problems, "rows": rows, "work": str(work)}
    if not keep:
        shutil.rmtree(work, ignore_errors=True)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("briefs", nargs="+")
    ap.add_argument("--shots")
    ap.add_argument("--json")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()
    results = [audit(p, args.shots, args.keep) for p in args.briefs]
    for r in results:
        print(f"\n== {r['brief']} [{r['archetype']}] {r['duration']}s, {r['samples']} samples")
        if r["problems"]:
            for p in sorted(set(r["problems"])):
                print("  FAIL", p)
        else:
            print("  OK: no surface touches the caption zone; nothing crosses stage_bottom")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2))
    return 1 if any(r["problems"] for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
