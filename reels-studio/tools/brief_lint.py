#!/usr/bin/env python3
"""Brief lint — catch the mistake classes that cost a cloud render run.

Born from the 2026-10-12 batch, where three near-misses were caught by hand:
camera regions that referenced footage below the desktop-top viewport, `item_at`/`at`
sync words that were never spoken, and scene assets whose names did not match the pack.

Checks (errors unless marked warning). Creative and media-coverage rules were retired on 31 Oct
2026 (pipeline plan, decision 6): the agent designs each video, and the code checks files and facts only.
  BL001  JSON parses; required keys (id, capture, scenes, seo) are present
  BL010  file name matches the brief id                                        (warning)
  BL020  capture pack not present locally — asset/region checks skipped         (warning)
  BL030  brief declares scenes
  BL031  scene `type` is one the renderer knows
  BL032  every scene has a `say` line (or an explicit `hold` for silent scenes)
  BL033  clip scenes carry `src`, `in`, `out`
  BL060  asset references (src, image, background.image, figure) exist in the capture pack
  BL070  camera/cursor `region`s exist in the pack's region map
  BL090  seo block has a keyword and a YouTube description
  BL100  licence/legal terms spoken at most once per script (owner rule: no legal text in script)
  BL101  no licence/legal term in the hook scene
  BL102  no licence/legal term in on-screen headline/sub/heading/label
  BL112  brief names the research it used (research_basis)
  BL113  research_basis cites a file that exists
  BL900  brief file readable as JSON

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
# OWNER RULE (2026-10-30): repos with no video use their own still images (no filming). These five briefs are
# allowed still-image proof (BL128/BL110) and still-image media coverage (production gate); cover concepts may share
# the pack's images when the pack is thin.
SCENE_TYPES = {"clip", "clip-montage", "page", "scroll", "steps", "terminal", "verdict", "stat", "image", "endcard"}

REQUIRED_KEYS = ("id", "capture", "scenes", "seo")  # v2: no template field

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
    "BL060": ("error", "scene asset reference exists in the capture pack"),
    "BL070": ("error", "camera/cursor region exists in the pack region map"),
    "BL090": ("error", "seo block: keyword + #Shorts description"),
    "BL100": ("warning", "licence/legal terms spoken at most once per script (PLAYBOOK §4)"),
    "BL101": ("error", "no licence/legal term in the hook scene"),
    "BL102": ("warning", "no licence/legal term in on-screen headline text"),
    "BL112": ("warning", "brief cites the current research it applied (research_basis)"),
    "BL113": ("error", "research_basis cites a file that does not exist"),
    "BL900": ("error", "brief file readable as JSON"),
}


def spoken(say):
    """The text as narrated: {display|spoken} keeps the spoken side."""
    return re.sub(r"\{[^|{}]*\|([^{}]*)\}", r"\1", say or "")


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
        # Accept both "captures/<id>" and "<id>" formats (fix 2026-10-30).
        if not Path(cap).is_absolute() and not cap.startswith("captures/"):
            cap = f"captures/{cap}"
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

    # Viewer-benefit first (owner rule 2026-10-18, PLAYBOOK §4): licence/legal terms are a
    # trust badge, not a headline — at most one spoken mention per script, never in the hook.
    legal = re.compile(r"\b(licen[cs]e[ds]?|mit|apache|gpl|agpl|lgpl|bsd|mpl|openrail)\b", re.I)
    spoken_legal = sum(len(legal.findall(spoken(s.get("say")))) for s in brief.get("scenes") or [])
    if spoken_legal > 1:
        add("BL100", f"licence/legal terms spoken {spoken_legal} times; the limit is one plain "
                     f"mention ('free and open source') at the verdict or close")

    scenes = brief.get("scenes") or []
    if not scenes:
        add("BL030", "no scenes")
    for idx, s in enumerate(scenes):
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
        if idx == 0 and (legal.search(spoken(s.get("say"))) or legal.search(s.get("headline") or "")
                         or legal.search(s.get("sub") or "")):
            add("BL101", f"{where}: licence/legal term in the hook — open on the viewer's "
                         f"pain or outcome instead (PLAYBOOK §4)")
        for key in ("headline", "sub", "heading", "label"):
            v = s.get(key)
            if isinstance(v, str) and legal.search(v):
                add("BL102", f"{where}: licence/legal term in on-screen {key} {v!r} — legal "
                             f"detail belongs in the description's credits block, not on screen")
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

    # Findings-into-production (owner 2026-10-18): every brief must name the current
    # research it applied (latest decode / platform matrix / performance report), so
    # "we used the new data" is checkable instead of asserted. Missing = warning
    # (legacy briefs), citing a nonexistent file = error.
    basis = brief.get("research_basis")
    if not isinstance(basis, list) or not basis:
        add("BL112", "no research_basis: list the current research files this brief "
                     "applies (e.g. research/social/decode-YYYY-MM-DD.md, performance report)")
    else:
        for ref in basis:
            if not isinstance(ref, str) or not (ROOT / ref).exists():
                add("BL113", f"research_basis cites missing file: {ref!r}")

    seo = brief.get("seo") or {}
    if not seo.get("keyword"):
        add("BL090", "seo.keyword missing")
    yt = seo.get("youtube") or {}
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
