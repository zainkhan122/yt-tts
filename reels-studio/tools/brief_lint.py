#!/usr/bin/env python3
"""Brief lint — catch the mistake classes that cost a cloud render run.

Born from the 2026-10-12 batch, where three near-misses were caught by hand:
camera regions that referenced footage below the desktop-top viewport, `item_at`/`at`
sync words that were never spoken, and scene assets whose names did not match the pack.

Checks (errors unless marked warning) — every one carries a stable rule ID, so the same
finding can be tracked across runs and compared by ID instead of by prose:
  BL001  JSON parses; required keys (id, template, capture, scenes, seo) are present
  BL010  file name matches the brief id                                        (warning)
  BL020  capture pack not present locally — asset/region checks skipped         (warning)
  BL030  brief declares no scenes
  BL031  scene `type` is one the spotlight template renders
  BL032  every scene has a `say` line (or an explicit `hold` for silent scenes)
  BL033  clip scenes carry `src`, `in`, `out`
  BL040  `*highlight*` markers pair up in headline/sub/heading/label/keyword
  BL050  verdict: item_at length == cons + pros                                 (warning)
  BL051  verdict: item_at present at all                                        (warning)
  BL060  asset references (src, image, background.image, figure) exist in the capture pack
  BL070  camera/cursor `region`s exist in the pack's region map
  BL080  `at` / `item_at` words appear in the scene's spoken line               (warning)
  BL081  every clip-montage cut anchor is an exact spoken word                 (error)
  BL090  seo block has keyword + youtube description with #Shorts

Usage:
  python3 tools/brief_lint.py briefs/<id>.json [more briefs...]   # exit 1 on errors
  python3 tools/brief_lint.py --json briefs/<id>.json [...]       # machine-readable findings
  python3 reels.py lint <brief-id> [...]                          # same, via the CLI
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENE_TYPES = {"clip", "clip-montage", "page", "scroll", "steps", "terminal", "verdict", "stat", "image", "endcard"}
REQUIRED_KEYS = ("id", "template", "capture", "scenes", "seo")

# Stable rule IDs: code -> (severity, one-line meaning). Receipts store code + exact message;
# this table is the reference the project reads when deciding whether a run got worse.
RULES = {
    "BL001": ("error", "required keys present"),
    "BL010": ("warning", "file name matches the brief id"),
    "BL020": ("warning", "capture pack present locally"),
    "BL030": ("error", "brief declares scenes"),
    "BL031": ("error", "scene type known to the renderer"),
    "BL032": ("error", "scene has a say line or an explicit hold"),
    "BL033": ("error", "clip scene carries src, in, out"),
    "BL040": ("error", "highlight markers balanced"),
    "BL050": ("warning", "verdict item_at length matches cons + pros"),
    "BL051": ("warning", "verdict item_at present (narration sync)"),
    "BL060": ("error", "scene asset reference exists in the capture pack"),
    "BL070": ("error", "camera/cursor region exists in the pack region map"),
    "BL080": ("warning", "at/item_at word appears in the spoken line"),
    "BL081": ("error", "clip-montage cut anchor is an exact spoken word"),
    "BL090": ("error", "seo block: keyword + #Shorts description"),
    "BL900": ("error", "brief file readable as JSON"),
}


def spoken(say):
    """The text as narrated: {display|spoken} keeps the spoken side."""
    return re.sub(r"\{[^|{}]*\|([^{}]*)\}", r"\1", say or "")


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def _spoken_anchor(say, pattern):
    """Mirror the renderer's exact normalized-word/regex match for a montage cut anchor."""
    if not isinstance(pattern, str) or not pattern.strip():
        return False
    words = [re.sub(r"[^a-z0-9]", "", word.lower()) for word in re.findall(r"\S+", spoken(say))]
    words = [word for word in words if word]
    try:
        if any(re.fullmatch(pattern, word, re.I) for word in words):
            return True
    except re.error:
        pass
    normalized = re.sub(r"[^a-z0-9]", "", pattern.lower())
    return bool(normalized and normalized in words)


def check(brief_path):
    """-> (brief id, error strings, warning strings, findings).

    Error/warning strings are unchanged apart from a leading "[BLxxx] "; `findings` is the
    structured form [{"id", "severity", "message"}] that receipts persist.
    """
    errors, warns, findings = [], [], []

    def add(code, message):
        severity = RULES[code][0]
        (errors if severity == "error" else warns).append(f"[{code}] {message}")
        findings.append({"id": code, "severity": severity, "message": message})

    path = Path(brief_path)
    try:
        brief = json.loads(path.read_text())
    except Exception as exc:
        add("BL900", f"{path.name}: {exc}")
        return path.stem, errors, warns, findings
    bid = brief.get("id") or path.stem
    for k in REQUIRED_KEYS:
        if not brief.get(k):
            add("BL001", f"{k}: missing")
    if brief.get("id") and path.stem != brief["id"]:
        add("BL010", f"file name {path.stem}.json != id {brief['id']}")

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
            add("BL020", f"capture pack {cap} not present locally — asset/region checks skipped")
    files = set()
    if manifest:
        files = {v.get("file") for v in manifest.get("files", {}).values() if v.get("file")} | {"contact.jpg"}
    regions = set((manifest.get("regions_css") or {}).keys())

    scenes = brief.get("scenes") or []
    if not scenes:
        add("BL030", "no scenes")
    for s in scenes:
        sid = s.get("id", "?")
        where = f"scene {sid}"
        if s.get("type") not in SCENE_TYPES:
            add("BL031", f"{where}: unknown type {s.get('type')!r}")
        if not s.get("say") and not s.get("hold"):
            add("BL032", f"{where}: no say line (and no hold)")
        if s.get("type") == "clip":
            if not s.get("src"):
                add("BL033", f"{where}: clip without src")
            if "in" not in s or "out" not in s:
                add("BL033", f"{where}: clip without in/out")
        if s.get("type") == "verdict":
            # item_at is narration-sync polish only: the renderer staggers the items by default,
            # so a missing or partial mapping never breaks a render (batch-1 briefs shipped without it).
            items = len(s.get("cons", [])) + len(s.get("pros", []))
            if s.get("item_at") and len(s["item_at"]) != items:
                add("BL050", f"{where}: item_at has {len(s['item_at'])} entries for {items} items")
            elif items and not s.get("item_at"):
                add("BL051", f"{where}: no item_at — items reveal on the default stagger, not the narration")
        for key in ("headline", "sub", "heading", "label", "keyword"):
            v = s.get(key)
            if isinstance(v, str) and v.count("*") % 2:
                add("BL040", f"{where}: unbalanced * in {key} {v!r}")
        say = norm(spoken(s.get("say")))
        for key in ("at", "item_at"):
            v = s.get(key)
            for w in (v if isinstance(v, list) else [v] if v else []):
                wn = norm(w)
                if wn and wn not in say:
                    add("BL080", f"{where}: {key}={w!r} not present in the spoken line")
        if s.get("type") == "clip-montage":
            for k, cut in enumerate(s.get("cuts") or []):
                anchor = cut.get("at")
                if anchor and not _spoken_anchor(s.get("say"), anchor):
                    add("BL081", f"{where}: cuts[{k}].at={anchor!r} is not an exact spoken word")
        if pack:
            for key in ("src", "image"):
                if s.get(key) and s[key] not in files:
                    add("BL060", f"{where}: {key}={s[key]!r} not in the capture pack")
            bg = (s.get("background") or {}).get("image")
            if bg and bg not in files:
                add("BL060", f"{where}: background {bg!r} not in the capture pack")
            if s.get("figure") and s["figure"] not in files:
                add("BL060", f"{where}: figure {s['figure']!r} not in the capture pack")
            for c in (s.get("camera") or []) + (s.get("cursor") or []):
                if c.get("region") and c["region"] not in regions:
                    add("BL070", f"{where}: region {c['region']!r} not in the pack region map")

    seo = brief.get("seo") or {}
    if not seo.get("keyword"):
        add("BL090", "seo.keyword missing")
    yt = seo.get("youtube") or {}
    if "#shorts" not in [t.lower() for t in yt.get("hashtags", [])]:
        add("BL090", "seo.youtube.hashtags: #Shorts missing")
    if not yt.get("description"):
        add("BL090", "seo.youtube.description missing")
    return bid, errors, warns, findings


def main():
    argv = sys.argv[1:]
    as_json = "--json" in argv
    args = [a for a in argv if a != "--json"]
    if not args:
        print(__doc__)
        return 2
    report, bad = {}, 0
    for a in args:
        path = Path(a)
        if not path.exists():
            path = ROOT / "briefs" / f"{Path(a).stem}.json"
        try:
            bid, errors, warns, findings = check(path)
        except Exception as e:  # unexpected: still an error, never a crash
            print(f"❌ {a}: {e}")
            bad += 1
            continue
        report[bid] = {"errors": errors, "warnings": warns, "findings": findings}
        if as_json:
            bad += bool(errors)
            continue
        print(f"{'❌' if errors else '✅'} {bid}: {len(errors)} error(s), {len(warns)} warning(s)")
        for e in errors:
            print(f"   ❌ {e}")
        for w in warns:
            print(f"   ⚠ {w}")
        bad += bool(errors)
    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print("brief lint: OK" if not bad else f"brief lint: {bad} brief(s) with errors")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
