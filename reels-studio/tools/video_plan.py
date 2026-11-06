#!/usr/bin/env python3
"""Validate an agent-written video plan. The plan is the brain; this file only checks it.

A plan lives at videos/<id>/plan.json and is written by the agent from the tool's own material.
Nothing in the plan is supplied by a template. The checks below enforce the owner's rules:

  * a viewer-first hook: question, problem, true contrast, or command
  * 1 to 5 points, numbered 1..n, each with a claim, a spoken line and a source URL (https)
  * spoken lines: no URLs or legal/licence/terms/privacy words; figures need source review,
    at most 180 characters
  * every point has a visual of a known kind with the fields that kind needs
  * an asset named in a plan must exist in the workspace
  * a catch line (the cost, limit or what it cannot do)

Exit 0 = PASS, 1 = BLOCK. Usage:
  python3 tools/video_plan.py videos/repo-ifixai-01/plan.json
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
VISUAL_KINDS = {
    "findings": ("rows",),
    "chips": ("chips",),
    "steps": ("steps",),
    "chart": ("asset",),
    "tiers": ("tiers",),
    "clip": ("asset",),
    "diagram": ("intent",),
    "animation": ("animation",),
}
LEGAL = re.compile(r"\b(licen[cs]e[ds]?|licensing|terms|privacy|legal|copyright|gdpr|tos)\b", re.I)
MAX_CHARS = 180


def check(plan):
    res = []

    def add(ok, msg):
        res.append(("PASS" if ok else "BLOCK", msg))

    q = plan.get("question", "")
    add(isinstance(q, str) and bool(q.strip()), "viewer-first hook present (question, problem, contrast, or command)")
    pts = plan.get("points", [])
    add(1 <= len(pts) <= 5, f"points: {len(pts)} (must be 1 to 5)")
    add([p.get("n") for p in pts] == list(range(1, len(pts) + 1)), "points numbered 1..n in order")
    for p in pts:
        n = p.get("n")
        spoken = p.get("spoken", "")
        add(bool(p.get("claim")), f"point {n}: claim written")
        add(bool(spoken), f"point {n}: spoken line written")
        add("http" not in spoken and "www." not in spoken, f"point {n}: no URL in spoken line")
        add(not LEGAL.search(spoken), f"point {n}: no legal/licence/terms wording in spoken line")
        add(len(spoken) <= MAX_CHARS, f"point {n}: spoken line within {MAX_CHARS} characters")
        src = p.get("source", "")
        add(src.startswith("https://"), f"point {n}: source is https")
        vis = p.get("visual") or {}
        kind = vis.get("kind")
        add(kind in VISUAL_KINDS, f"point {n}: visual kind '{kind}' is known")
        for field in VISUAL_KINDS.get(kind, ()):
            ok = bool(vis.get(field)) if field in ("intent", "animation") else bool(p.get(field))
            add(ok, f"point {n}: visual has '{field}'")
        sub = p.get("sub", "")
        add(bool(sub) and len(sub) <= 90 and sub.rstrip()[-1:] in ".!?", f"point {n}: sub-line written, complete, at most 90 characters")
        if p.get("asset"):
            add((ROOT / p["asset"]).exists(), f"point {n}: asset exists {p['asset']}")
    cv = plan.get("catch_visual") or {}
    add(cv.get("kind") in VISUAL_KINDS, "catch visual kind is known")
    add(bool(plan.get("catch_sub")), "catch sub-line written")
    catch = plan.get("catch", "")
    add(bool(catch), "catch line written (cost, limit or what it cannot do)")
    add(not re.search(r"https?://", catch), "no URL in catch line")
    res += check_packaging(plan)
    return res


PACKAGING_KEYS = ("brand_line", "seo", "brief_meta", "cover", "cta", "cta_keyword")


def check_packaging(plan):
    """Everything brief_from_plan needs, checked here so a plan fails at authoring time, not at build.

    The copy itself is run through the studio's own copy rules (studio/rules.py), so the wording
    that reaches preflight has already been checked.
    """
    res = []

    def add(ok, msg):
        res.append(("PASS" if ok else "BLOCK", msg))

    for key in PACKAGING_KEYS:
        add(bool(plan.get(key)), f"packaging: '{key}' written")
    bl = plan.get("brand_line", "")
    add(isinstance(bl, str) and 0 < len(bl) <= 40, "packaging: brand_line 1-40 characters")
    kw = plan.get("cta_keyword", "")
    add(isinstance(kw, str) and bool(re.fullmatch(r"[A-Z]{2,12}", kw)), "packaging: cta_keyword is one capital word, 2-12 letters")
    cta = plan.get("cta", "")
    add(isinstance(cta, str) and 0 < len(cta) <= 140 and not re.search(r"https?://", cta), "packaging: cta written, no URL, at most 140 characters")
    # Cover rules live in tools/cover_rules.py (COVER-RULES.md). Three concepts, 4-5 word all-caps
    # headlines, one usable tool asset or a designed graphic per concept. Checked here, at authoring.
    try:
        from tools import cover_rules
    except ModuleNotFoundError:
        import cover_rules
    pid = str(plan.get("id", ""))
    cover_problems = cover_rules.plan_cover_problems(plan, ROOT / "captures" / pid, ROOT / "covers" / pid)
    add(not cover_problems, "packaging: cover rules (COVER-RULES.md): " + ("; ".join(cover_problems) or "ok"))

    seo = plan.get("seo") or {}
    add(isinstance(seo.get("keyword"), str) and bool(seo.get("keyword")), "packaging: seo.keyword present")
    add(isinstance(seo.get("onscreen_first3s"), str) and 0 < len(seo.get("onscreen_first3s", "")) <= 30, "packaging: seo.onscreen_first3s 1-30 characters")
    for platform in ("youtube", "tiktok", "instagram", "facebook", "x"):
        block = seo.get(platform)
        add(isinstance(block, dict), f"packaging: seo.{platform} present")
    yt = seo.get("youtube") or {}
    add(isinstance(yt.get("title"), str) and bool(yt.get("title")), "packaging: seo.youtube.title present")
    add(isinstance(yt.get("description"), str) and bool(yt.get("description")), "packaging: seo.youtube.description present")
    add(isinstance(yt.get("tags"), list) and len(yt.get("tags", [])) >= 3, "packaging: seo.youtube.tags at least 3")

    meta = plan.get("brief_meta") or {}
    for key in ("title", "niche", "idea"):
        add(bool(meta.get(key)), f"packaging: brief_meta.{key} present")
    add(isinstance(meta.get("keywords"), list) and len(meta.get("keywords", [])) >= 2, "packaging: brief_meta.keywords at least 2")
    viewer = meta.get("viewer") or {}
    add(all(viewer.get(k) for k in ("who", "problem", "job")), "packaging: brief_meta.viewer has who, problem and job")

    # Platform copy rules (length, hashtags, credit words, placeholders, https links).
    try:
        import sys as _sys
        from pathlib import Path as _P
        _sys.path.insert(0, str(ROOT))
        from studio import rules as _rules
        findings = _rules.check_copy({"id": plan.get("id", "?"), "seo": seo, "voice": {"synthetic": True}, "qa_gates": True})  # new plans are new batches (owner, 4 Nov)
        errors = [f for f in findings if f.level == "error"]
        add(not errors, f"copy rules: {len(errors)} problem(s)" + ("" if not errors else ": " + "; ".join(f.code + " " + f.message for f in errors[:4])))
    except Exception as exc:  # the checker itself must not hide a failure
        add(False, f"copy rules could not run: {exc}")
    return res


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    path = Path(argv[1])
    plan = json.loads(path.read_text(encoding="utf-8"))
    results = check(plan)
    for status, msg in results:
        print(f"{status:5} {msg}")
    blocked = [m for s, m in results if s == "BLOCK"]
    print("PLAN", "PASS" if not blocked else f"BLOCK ({len(blocked)} problem(s))")
    return 0 if not blocked else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
