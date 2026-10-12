#!/usr/bin/env python3
"""Brief lint — catch the mistake classes that cost a cloud render run.

Born from the 2026-10-12 batch, where three near-misses were caught by hand:
camera regions that referenced footage below the desktop-top viewport, `item_at`/`at`
sync words that were never spoken, and scene assets whose names did not match the pack.

Checks (errors unless marked warning):
  - JSON parses; required keys (id, template, capture, scenes, seo) are present
  - scene `type` is one the spotlight template renders
  - every scene has a `say` line (or an explicit `hold` for silent scenes)
  - clip scenes carry `src`, `in`, `out`
  - `*highlight*` markers pair up in headline/sub/heading/label/keyword (unbalanced `*`
    makes the renderer abort)
  - verdict scenes: item_at (narration sync) length == cons + pros, or present at all (warning)
  - asset references (src, image, background.image, figure) exist in the capture pack
    (only checked when the pack is present locally; otherwise a warning)
  - camera/cursor `region`s exist in the pack's region map (same pack rule)
  - `at` / `item_at` words appear in the scene's spoken line  (warning — timing polish)
  - seo block has keyword + youtube description with #Shorts (error, mirrors seo_pack gate)

Usage:
  python3 tools/brief_lint.py briefs/<id>.json [more briefs...]   # exit 1 on errors
  python3 reels.py lint <brief-id> [...]                          # same, via the CLI
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENE_TYPES = {"clip", "clip-montage", "page", "scroll", "steps", "terminal", "verdict", "stat", "image", "endcard"}
REQUIRED_KEYS = ("id", "template", "capture", "scenes", "seo")


def spoken(say):
    """The text as narrated: {display|spoken} keeps the spoken side."""
    return re.sub(r"\{[^|{}]*\|([^{}]*)\}", r"\1", say or "")


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def check(brief_path):
    errors, warns = [], []
    path = Path(brief_path)
    brief = json.loads(path.read_text())
    bid = brief.get("id") or path.stem
    for k in REQUIRED_KEYS:
        if not brief.get(k):
            errors.append(f"{k}: missing")
    if brief.get("id") and path.stem != brief["id"]:
        warns.append(f"file name {path.stem}.json != id {brief['id']}")

    pack, manifest = None, {}
    cap = brief.get("capture")
    if cap:
        pack = Path(cap)
        if not pack.is_absolute():
            pack = ROOT / pack
        if (pack / "manifest.json").exists():
            manifest = json.loads((pack / "manifest.json").read_text())
        else:
            pack = None
            warns.append(f"capture pack {cap} not present locally — asset/region checks skipped")
    files = set()
    if manifest:
        files = {v.get("file") for v in manifest.get("files", {}).values() if v.get("file")} | {"contact.jpg"}
    regions = set((manifest.get("regions_css") or {}).keys())

    scenes = brief.get("scenes") or []
    if not scenes:
        errors.append("no scenes")
    for s in scenes:
        sid = s.get("id", "?")
        where = f"scene {sid}"
        if s.get("type") not in SCENE_TYPES:
            errors.append(f"{where}: unknown type {s.get('type')!r}")
        if not s.get("say") and not s.get("hold"):
            errors.append(f"{where}: no say line (and no hold)")
        if s.get("type") == "clip":
            if not s.get("src"):
                errors.append(f"{where}: clip without src")
            if "in" not in s or "out" not in s:
                errors.append(f"{where}: clip without in/out")
        if s.get("type") == "verdict":
            # item_at is narration-sync polish only: the renderer staggers the items by default,
            # so a missing or partial mapping never breaks a render (batch-1 briefs shipped without it).
            items = len(s.get("cons", [])) + len(s.get("pros", []))
            if s.get("item_at") and len(s["item_at"]) != items:
                warns.append(f"{where}: item_at has {len(s['item_at'])} entries for {items} items")
            elif items and not s.get("item_at"):
                warns.append(f"{where}: no item_at — items reveal on the default stagger, not the narration")
        for key in ("headline", "sub", "heading", "label", "keyword"):
            v = s.get(key)
            if isinstance(v, str) and v.count("*") % 2:
                errors.append(f"{where}: unbalanced * in {key} {v!r}")
        say = norm(spoken(s.get("say")))
        for key in ("at", "item_at"):
            v = s.get(key)
            for w in (v if isinstance(v, list) else [v] if v else []):
                wn = norm(w)
                if wn and wn not in say:
                    warns.append(f"{where}: {key}={w!r} not present in the spoken line")
        if pack:
            for key in ("src", "image"):
                if s.get(key) and s[key] not in files:
                    errors.append(f"{where}: {key}={s[key]!r} not in the capture pack")
            bg = (s.get("background") or {}).get("image")
            if bg and bg not in files:
                errors.append(f"{where}: background {bg!r} not in the capture pack")
            if s.get("figure") and s["figure"] not in files:
                errors.append(f"{where}: figure {s['figure']!r} not in the capture pack")
            for c in (s.get("camera") or []) + (s.get("cursor") or []):
                if c.get("region") and c["region"] not in regions:
                    errors.append(f"{where}: region {c['region']!r} not in the pack region map")

    seo = brief.get("seo") or {}
    if not seo.get("keyword"):
        errors.append("seo.keyword missing")
    yt = seo.get("youtube") or {}
    if "#shorts" not in [t.lower() for t in yt.get("hashtags", [])]:
        errors.append("seo.youtube.hashtags: #Shorts missing")
    if not yt.get("description"):
        errors.append("seo.youtube.description missing")
    return bid, errors, warns


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    bad = 0
    for a in args:
        path = Path(a)
        if not path.exists():
            path = ROOT / "briefs" / f"{Path(a).stem}.json"
        try:
            bid, errors, warns = check(path)
        except Exception as e:  # malformed JSON etc. is an error, not a crash
            print(f"❌ {a}: {e}")
            bad += 1
            continue
        print(f"{'❌' if errors else '✅'} {bid}: {len(errors)} error(s), {len(warns)} warning(s)")
        for e in errors:
            print(f"   ❌ {e}")
        for w in warns:
            print(f"   ⚠ {w}")
        bad += bool(errors)
    print("brief lint: OK" if not bad else f"brief lint: {bad} brief(s) with errors")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
