#!/usr/bin/env python3
"""One local preflight for a brief, run before any cloud dispatch or Buffer action.

Replaces the chain of separate checks that used to fail one at a time, late, in the cloud:
  1. brief lint        tools/brief_lint.py   (structure, scenes, captions, SEO, treatment)
  2. studio rules      studio/rules.py       (brief rules B0xx and copy rules C0xx on final text)
  3. queue pin         queue/publish.json    (brief hash matches what was approved)
  4. render artefacts  renders/<id>/         (QA-passed video present when publishing)

Every result is a BLOCK (stop) or a NOTE (advisory). A NOTE never stops the run.
Exit 0 = nothing blocks. Exit 1 = at least one BLOCK. Exit 2 = usage error.

Usage:
  python3 tools/preflight.py repo-edge0-01 repo-deeptutor-01      # by brief id
  python3 tools/preflight.py --all --json                          # every brief, machine-readable
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import brief_lint  # noqa: E402
from studio import rules  # noqa: E402
from tools.post.common import fingerprint  # noqa: E402

QUEUE = ROOT / "queue" / "publish.json"
RENDERS = ROOT / "renders"


def _result(check, status, detail, fix=""):
    return {"check": check, "status": status, "detail": detail, "fix": fix}


def check_lint(brief_id, brief_path):
    out = []
    try:
        bid, errors, warns, _ = brief_lint.check(brief_path)
    except Exception as exc:  # the lint itself must never crash the preflight
        return [_result("brief_lint", "BLOCK", f"lint crashed: {exc}", "fix the brief JSON")]
    for e in errors:
        out.append(_result("brief_lint", "BLOCK", e, "edit the brief"))
    for w in warns:
        out.append(_result("brief_lint", "NOTE", w, "advisory"))
    if not errors:
        out.append(_result("brief_lint", "PASS", f"{len(warns)} advisory note(s)"))
    return out


def check_studio_rules(brief):
    out = []
    try:
        findings = rules.check_brief(brief, today=dt.date.today()) + rules.check_copy(brief)
    except Exception as exc:
        return [_result("studio_rules", "BLOCK", f"rules crashed: {exc}", "fix the brief JSON")]
    blocks = [f for f in findings if f.level == "error"]
    notes = [f for f in findings if f.level != "error"]
    for f in blocks:
        out.append(_result("studio_rules", "BLOCK", f"{f.code} {f.message}", "edit the copy or brief"))
    for f in notes:
        out.append(_result("studio_rules", "NOTE", f"{f.code} {f.message}", "advisory"))
    if not blocks:
        out.append(_result("studio_rules", "PASS", f"{len(notes)} advisory note(s)"))
    return out


def check_queue_pin(brief_id, brief):
    if not QUEUE.exists():
        return [_result("queue_pin", "NOTE", "no queue file", "")]
    items = json.loads(QUEUE.read_text(encoding="utf-8")).get("items", [])
    mine = [i for i in items if i.get("video_id") == brief_id]
    if not mine:
        return [_result("queue_pin", "NOTE", "not queued (fine for review; needed to publish)", "")]
    now = fingerprint(brief)
    stale = [i for i in mine if i.get("brief_sha256") != now]
    if stale:
        return [_result("queue_pin", "BLOCK", "brief changed since queue approval",
                        "copy changed after approval: owner must re-review, then refresh the pin and approve again")]
    return [_result("queue_pin", "PASS", "queue pin matches current brief")]


def check_render(brief_id):
    d = RENDERS / brief_id
    mp4s = sorted(d.glob("*.mp4")) if d.exists() else []
    if not mp4s:
        return [_result("render", "NOTE", "no rendered video yet (fine before render)", "")]
    manifests = sorted(d.glob("*manifest*.json"))
    if not manifests:
        return [_result("render", "BLOCK", "video present but no QA manifest", "re-run QA on the render")]
    return [_result("render", "PASS", f"{mp4s[0].name} with QA manifest")]


def preflight(brief_id):
    path = ROOT / "briefs" / f"{brief_id}.json"
    if not path.exists():
        return {"id": brief_id, "verdict": "BLOCK", "results": [_result("brief", "BLOCK", "brief file not found", "check the id")]}
    try:
        brief = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"id": brief_id, "verdict": "BLOCK", "results": [_result("brief", "BLOCK", f"unreadable: {exc}", "fix the JSON")]}
    results = (check_lint(brief_id, path) + check_studio_rules(brief)
               + check_queue_pin(brief_id, brief) + check_render(brief_id))
    verdict = "BLOCK" if any(r["status"] == "BLOCK" for r in results) else "PASS"
    return {"id": brief_id, "verdict": verdict, "results": results}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    ids = args.ids
    if args.all:
        ids = sorted(p.stem for p in (ROOT / "briefs").glob("*.json"))
    if not ids:
        ap.print_usage()
        return 2
    reports = [preflight(i) for i in ids]
    if args.json:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    else:
        for r in reports:
            print(f"{'PASS' if r['verdict'] == 'PASS' else 'BLOCK'}  {r['id']}")
            for x in r["results"]:
                tail = f"  -> {x['fix']}" if x["fix"] and x["status"] == "BLOCK" else ""
                print(f"   {x['status']:5} {x['check']:12} {x['detail']}{tail}")
    return 1 if any(r["verdict"] == "BLOCK" for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
