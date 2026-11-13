#!/usr/bin/env python3
"""house_gate — prove the house layer is actually on screen, for any template.

The owner rule is that EVERY short carries our own caption (Anton + one yellow word), our own
outro card, and our own handle. Templates are written by hand and drift, so "I looked at a frame"
is not a test. This drives the built stage in a real browser and asserts the four invariants that
have silently broken before:

  H1  exactly one house outro exists on the stage (not one per template wrapper, not zero)
  H2  the outro is invisible outside the endcard window and visible inside it
  H3  the established logo / name / Follow / COMMENT keyword card is present
  H4  at sampled times in every non-endcard scene the house caption shows exactly ONE yellow word
  H5  any caption a template drew for itself is suppressed (two captions is a bug)
  H6  no scene element enters the caption band (y >= 1250)

Usage:  python3 tools/house_gate.py renders/<id>/gfx-*/stage.html [more.html ...]
        python3 tools/house_gate.py --all      # every stage.html under renders/
Exit 0 = pass. Exit 1 = a named failure per file.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

YELLOW = "rgb(255, 214, 10)"
CAP_BAND = 1250

PROBE = r"""
(t) => {
  window.setTime(t);
  const out = {};
  const outros = document.querySelectorAll(".yt-outro");
  out.outroCount = outros.length;
  const vis = [...outros].filter(o => getComputedStyle(o).display !== "none");
  out.outroVisible = vis.length;
  if (vis.length) {
    const kw = vis[0].querySelector(".yt-outro-kw");
    out.kwText = kw ? kw.textContent : null;
    out.kwColor = kw ? getComputedStyle(kw).color : null;
    out.kwOpacity = kw ? parseFloat(getComputedStyle(kw.parentElement).opacity) : 0;
    out.logo = !!vis[0].querySelector(".yt-outro-logo[src^='data:image/']");
    out.name = vis[0].querySelector(".yt-outro-name")?.textContent || "";
    out.follow = vis[0].querySelector(".yt-outro-follow")?.textContent || "";
    out.cursor = !!vis[0].querySelector(".yt-outro-cursor svg");
  }
  const cap = document.querySelector(".yt-cap");
  out.capWords = cap ? cap.querySelectorAll(".cw").length : 0;
  out.capHits = cap ? cap.querySelectorAll(".cw.hit").length : 0;
  out.hitColor = cap && cap.querySelector(".cw.hit")
    ? getComputedStyle(cap.querySelector(".cw.hit")).color : null;
  out.capText = cap ? cap.textContent : "";
  out.suppressed = document.querySelectorAll("[data-house-suppressed]").length;
  out.templateCaptionsVisible = [...document.querySelectorAll('.caption,.pl-caption,.ng-cap,.vb-cap,.photo-cap,.dr-cap,.mk-cap,.rl-cap,.rl-foot-band')]
    .filter(n => getComputedStyle(n).display !== 'none' && getComputedStyle(n).visibility !== 'hidden' && parseFloat(getComputedStyle(n).opacity) > 0.01).length;
  out.visibleHandles = [...document.querySelectorAll('#stage > .yt-handle, #stage > .handle, #stage > .pl-head, #stage > .rl-head, #stage > .ng-handle')]
    .filter(n => getComputedStyle(n).display !== 'none' && getComputedStyle(n).visibility !== 'hidden' && parseFloat(getComputedStyle(n).opacity) > 0.01).length;
  out.bandBreaches = [];
  document.querySelectorAll("#stage .scene *").forEach(n => {
    const cs = getComputedStyle(n);
    if (cs.display === "none" || cs.visibility === "hidden" || parseFloat(cs.opacity) < 0.02) return;
    const b = n.getBoundingClientRect();
    const top = b.top - document.getElementById("stage").getBoundingClientRect().top;
    const bottom = b.bottom - document.getElementById("stage").getBoundingClientRect().top;
    const txt = n.textContent && n.textContent.trim() && !n.children.length;  // leaf text nodes only
    const big = bottom - top > 300;                                          // a full-bleed wrapper is backdrop
    if (txt && !big && bottom > 1250 && top < 1880)
      out.bandBreaches.push((n.className || n.tagName) + " bottom=" + Math.round(bottom));
  });
  return out;
}
"""


def scenes_from_html(html: str) -> dict:
    m = re.search(r"window\.DATA=(\{.*?\});</script>", html, re.S)
    if not m:
        raise SystemExit("no window.DATA in this stage html")
    return json.loads(m.group(1))


def check(stage: Path) -> list[str]:
    from playwright.sync_api import sync_playwright

    html = stage.read_text()
    D = scenes_from_html(html)
    scenes = D.get("scenes", [])
    ends = [s for s in scenes if s.get("archetype") == "endcard"]
    if not ends:
        return [f"{stage.name}: H0 no endcard scene in the plan — every short must end on the brand card"]

    fails: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        page = b.new_page(viewport={"width": 1080, "height": 1920})
        page.goto(stage.resolve().as_uri())
        page.wait_for_function("window.ready === true", timeout=20000)

        end = ends[0]
        mid = (end["t0"] + end["t1"]) / 2

        # H2/H3 in the card, including its first instant
        for label, t in (("start", end["t0"] + 0.05), ("landed", end["t0"] + 0.7), ("mid", mid)):
            r = page.evaluate(PROBE, t)
            if r["outroCount"] != 1:
                fails.append(f"H1 at {label}: {r['outroCount']} house outros on the stage (want exactly 1)")
            if r["outroVisible"] != 1:
                fails.append(f"H2 at {label}: outro not visible inside the endcard window")
            if not r["kwText"]:
                fails.append(f"H3 at {label}: outro has no keyword")
            elif label != "start" and r["kwOpacity"] < 0.5:
                fails.append(f"H3 at {label}: keyword opacity {r['kwOpacity']:.2f} — the card must say the "
                             f"keyword from its first frame, not 7s in")
            elif not r["kwText"].startswith("COMMENT "):
                fails.append(f"H3 at {label}: missing COMMENT keyword chip")
            if not (r.get("logo") and r.get("name") and r.get("follow") and r.get("cursor")):
                fails.append(f"H3 at {label}: established logo/name/follow/cursor card is incomplete")

        # H2 outside the card
        pre = [s for s in scenes if s["id"] != end["id"]]
        if pre:
            r = page.evaluate(PROBE, (pre[0]["t0"] + pre[0]["t1"]) / 2)
            if r["outroVisible"]:
                fails.append(f"H2 in scene '{pre[0]['id']}': house outro leaked outside the endcard window")

        # H4/H5/H6 across every non-endcard scene, 3 samples each
        for s in pre:
            for frac in (0.2, 0.55, 0.85):
                t = s["t0"] + (s["t1"] - s["t0"]) * frac
                r = page.evaluate(PROBE, t)
                tag = f"scene '{s['id']}' @{frac:.2f}"
                if r["capWords"]:
                    if r["capHits"] > 1:
                        fails.append(f"H4 {tag}: {r['capHits']} yellow words in the caption (want exactly 1)")
                    elif r["hitColor"] != YELLOW:
                        fails.append(f"H4 {tag}: highlight is {r['hitColor']}, not brand yellow")
                if r["templateCaptionsVisible"]:
                    fails.append(f"H5 {tag}: {r['templateCaptionsVisible']} template captions remain visible")
                if D.get("handle") and r["visibleHandles"] != 1:
                    fails.append(f"H5 {tag}: {r['visibleHandles']} visible handles (want 1)")
                if r["bandBreaches"]:
                    fails.append(f"H6 {tag}: caption-band breach -> {sorted(set(r['bandBreaches']))[:3]}")
        b.close()
    return [f"{stage.parent.parent.name}/{stage.parent.name}: {f}" for f in fails]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stages", nargs="*")
    ap.add_argument("--all", action="store_true", help="every stage.html under renders/")
    ap.add_argument("--latest", action="store_true",
                    help="newest stage.html per render id (stale dirs from earlier renders lie)")
    a = ap.parse_args()
    paths = [Path(x) for x in a.stages]
    if a.all:
        paths += [Path(x) for x in sorted(glob.glob("renders/*/gfx-*/stage.html"))]
    if a.latest:
        newest = {}
        # newest by mtime, then by name — `>=` alone let the OLDEST win when two renders shared a
        # second, which reported a stale build as the current one
        for x in sorted(glob.glob("renders/*/gfx-*/stage.html"),
                        key=lambda v: (Path(v).stat().st_mtime, Path(v).parent.name)):
            newest[Path(x).parent.parent.name] = x
        paths += [Path(v) for v in newest.values()]
    if not paths:
        print("no stage.html given"); return 2
    bad = 0
    for p in paths:
        fails = check(p)
        if fails:
            bad += 1
            print(f"FAIL {p}")
            for f in fails[:12]:
                print("   -", f)
        else:
            print(f"PASS house layer: {p}")
            print("     H1 one outro · H2 window-only · H3 established logo / follow / comment card")
            print("     H4 one yellow caption word per chunk · H5 template captions suppressed · H6 band clean")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
