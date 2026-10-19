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
    "BL100": ("warning", "licence/legal terms spoken at most once per script (PLAYBOOK §4)"),
    "BL101": ("error", "no licence/legal term in the hook scene"),
    "BL102": ("warning", "no licence/legal term in on-screen headline text"),
    "BL110": ("warning", "spotlight needs >=2 real-media scenes incl. >=1 motion/page scene"),
    "BL111": ("warning", "scene stages no media at all (empty-stage risk)"),
    "BL112": ("warning", "brief cites the current research it applied (research_basis)"),
    "BL113": ("error", "research_basis cites a file that does not exist"),
    "BL120": ("warning", "creative treatment present (viewer-first stage, PLAYBOOK §8A)"),
    "BL121": ("error", "treatment names one audience, viewer job and intent"),
    "BL122": ("error", "treatment archetype is a known format"),
    "BL123": ("error", "treatment open loop plants and pays off in a real scene"),
    "BL124": ("error", "treatment proof moment is a real scene"),
    "BL125": ("error", "treatment carries exactly 3 distinct cover concepts"),
    "BL126": ("error", "cover concept text is <= 4 words (tap-test readable)"),
    "BL127": ("error", "treatment selected_cover picks one of the concepts"),
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
        if idx == 0 and (legal.search(spoken(s.get("say"))) or legal.search(s.get("headline") or "")
                         or legal.search(s.get("sub") or "")):
            add("BL101", f"{where}: licence/legal term in the hook — open on the viewer's "
                         f"pain or outcome instead (PLAYBOOK §4)")
        for key in ("headline", "sub", "heading", "label"):
            v = s.get(key)
            if isinstance(v, str) and legal.search(v):
                add("BL102", f"{where}: licence/legal term in on-screen {key} {v!r} — legal "
                             f"detail belongs in the description's credits block, not on screen")
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

    # Media standard (owner 2026-10-18): winners show the product working. Generated
    # cards are support graphics; a spotlight needs real captured/demo media on stage.
    # (Hard enforcement lives in production_gate.verify_capture_assets; these are the
    # early warnings. When the pack is absent locally, scene types alone are counted.)
    real_files = {v.get("file") for v in (manifest.get("files") or {}).values()
                  if isinstance(v, dict) and str(v.get("kind", "")).startswith(
                      ("own capture", "official demo media", "official image"))}
    motion_types = {"clip", "clip-montage", "page", "scroll"}
    media_scenes = motion_scenes = 0
    for s in scenes:
        refs = {s.get("image"), s.get("src"), s.get("figure"),
                (s.get("background") or {}).get("img"), (s.get("background") or {}).get("image")}
        refs.discard(None)
        if s.get("type") in motion_types:
            motion_scenes += 1
            media_scenes += 1
        elif refs & real_files or (not manifest and refs):
            media_scenes += 1
        if s.get("type") in ("steps", "image", "stat") and not refs and not (
                (s.get("background") or {}).get("img")):
            add("BL111", f"scene {s.get('id', '?')}: {s.get('type')} scene stages no media — "
                         f"empty-stage risk; give it captured product media or a background")
    if scenes and (media_scenes < 2 or motion_scenes < 1):
        add("BL110", f"only {media_scenes} media scene(s), {motion_scenes} motion/page — "
                     f"card-only videos do not ship; capture the real product (capture.py) "
                     f"and stage it in at least two scenes")

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

    # Creative treatment (owner 2026-10-19): gates are the floor, not the target.
    # Every new brief is designed for ONE viewer with a format that fits the
    # material before any scene is written. Missing = warning (legacy briefs);
    # present-but-sloppy = error, because a half-filled treatment is how the
    # template sneaks back in. See PLAYBOOK §8A.
    ARCHETYPES = {"demo-first", "duel", "myth-bust", "quest", "warning",
                  "workflow", "spotlight"}
    tr = brief.get("treatment")
    if not isinstance(tr, dict):
        add("BL120", "no treatment: design this Short for one viewer first "
                     "(audience, viewer job, format archetype, open loop, proof "
                     "moment, 3 cover concepts) — PLAYBOOK §8A")
    else:
        if not all(isinstance(tr.get(k), str) and tr[k].strip()
                   for k in ("audience", "viewer_job", "hook_mechanic")) \
                or tr.get("intent") not in ("browse", "search", "hybrid"):
            add("BL121", "treatment needs audience, viewer_job, hook_mechanic and "
                         "intent in browse/search/hybrid")
        if tr.get("archetype") not in ARCHETYPES:
            add("BL122", f"treatment.archetype {tr.get('archetype')!r} not in "
                         f"{sorted(ARCHETYPES)}")
        scene_ids = {s.get("id") for s in scenes}
        loop = tr.get("open_loop") or {}
        if not loop.get("plant") or loop.get("payoff_scene") not in scene_ids:
            add("BL123", "treatment.open_loop needs a plant (second-one question) "
                         "and a payoff_scene that exists in scenes")
        if tr.get("proof_moment") not in scene_ids:
            add("BL124", "treatment.proof_moment must name a scene id where the "
                         "skeptic converts (real product evidence on screen)")
        covers = tr.get("cover_concepts")
        if not isinstance(covers, list) or len(covers) != 3:
            add("BL125", "treatment.cover_concepts must carry exactly 3 concepts "
                         "for the cover lab")
        else:
            texts = []
            for c in covers:
                if not isinstance(c, dict) or not c.get("visual") or not c.get("gap"):
                    add("BL125", "each cover concept needs visual (real media) + "
                                 "gap (the curiosity it opens)")
                    continue
                texts.append(str(c.get("text", "")).strip())
                if len(str(c.get("text", "")).split()) > 4:
                    add("BL126", f"cover text {c.get('text')!r} is over 4 words — "
                                 f"unreadable at feed size")
            if len(set(texts)) != len(texts):
                add("BL125", "cover concept texts must be distinct")
        sel = tr.get("selected_cover")
        if not isinstance(sel, int) or isinstance(sel, bool) or not 0 <= sel <= 2:
            add("BL127", "treatment.selected_cover must be 0, 1 or 2 (the concept "
                         "the panel picked)")

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
