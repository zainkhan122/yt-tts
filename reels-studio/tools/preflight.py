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


def check_motion(brief_id, brief_path):
    """Lesson 2026-10-31: focus boxes must not cut labels; no scene may hold still > 4.5 s."""
    import subprocess
    script = ROOT / "tools" / "motion" / "focus_check.py"
    r = subprocess.run([sys.executable, str(script), str(brief_path)], capture_output=True, text=True)
    if r.returncode == 0:
        return [_result("motion", "PASS", "focus boxes keep labels whole; no long holds")]
    detail = (r.stdout.strip().splitlines() or ["focus check failed"])[0]
    return [_result("motion", "BLOCK", detail, "fix focus boxes or scene timing in the brief")]


def check_dispatch_head(brief_id, receipt_rel):
    """Lesson 2026-10-31: cloud renders run from origin main. Brief and receipt must be pushed first."""
    import subprocess
    git = ["git", "-C", str(ROOT.parent)]
    try:
        head = subprocess.run(git + ["ls-remote", "origin", "main"], capture_output=True, text=True, timeout=60)
    except Exception as exc:
        return [_result("dispatch_head", "BLOCK", f"cannot reach origin: {exc}", "fix the origin remote, then dispatch")]
    if head.returncode != 0 or not head.stdout.strip():
        # A cloud run renders origin main. If origin cannot be read we cannot prove it is the code we
        # reviewed, so this is a BLOCK (lesson 6, 1 Nov: origin lost after a restore).
        return [_result("dispatch_head", "BLOCK", "origin main not readable (remote or token)", "re-add origin without credentials; confirm GH token; then dispatch")]
    remote_sha = head.stdout.split()[0]
    local = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if remote_sha != local:
        return [_result("dispatch_head", "BLOCK", f"origin main {remote_sha[:7]} != local {local[:7]}", "push before dispatch")]
    rel = f"reels-studio/briefs/{brief_id}.json"
    for path in (rel, f"reels-studio/{receipt_rel}"):
        diff = subprocess.run(git + ["diff", "--quiet", "HEAD", "--", path], capture_output=True)
        if diff.returncode != 0:
            return [_result("dispatch_head", "BLOCK", f"{path} has uncommitted changes", "commit and push")]
    return [_result("dispatch_head", "PASS", "origin main matches local; brief and receipt committed")]


def check_media_aspect(brief_id, brief):
    """Lesson 14: media for 9:16 cards must be portrait, or the lower frame stays empty."""
    from PIL import Image
    out = []
    if int(brief.get("motion_standard") or 0) < 2:  # earlier briefs were published under the older standard
        return [_result("media_aspect", "PASS", "not applicable (motion_standard < 2)")]
    cap = ROOT / "captures" / brief_id
    seen = set()
    for s in brief.get("scenes") or []:
        if s.get("type") != "image" or not s.get("image") or s["image"] in seen:
            continue
        seen.add(s["image"])
        path = cap / s["image"]
        if not path.exists():
            out.append(_result("media_aspect", "BLOCK", f"{s['image']} missing from capture pack", "rebuild the kit"))
            continue
        w_, h_ = Image.open(path).size
        if w_ > h_ and not brief.get("media_aspect_landscape_ok"):
            out.append(_result("media_aspect", "BLOCK",
                               f"{s['image']} is landscape {w_}x{h_}; the card leaves the lower frame empty",
                               "rebuild at 1080x1440 (portrait) or set media_aspect_landscape_ok with a reason"))
    if not out:
        out.append(_result("media_aspect", "PASS", "image scenes use portrait media"))
    return out


def check_layout(brief_id, brief_path):
    """Lessons 15, 16 (1 Nov): the layout audit runs locally in a real browser before any cloud dispatch.
    No browser or any layout problem (overlap, empty stage, scrim over media) blocks the dispatch."""
    import subprocess
    script = ROOT / "tools" / "layout_audit.py"
    try:
        r = subprocess.run([sys.executable, str(script), str(brief_path)], capture_output=True, text=True,
                           timeout=900, env=_browser_env())
    except subprocess.TimeoutExpired:
        return [_result("layout", "BLOCK", "layout audit timed out", "run tools/layout_audit.py locally and fix the scene")]
    out = (r.stdout + r.stderr).strip()
    if r.returncode == 0 and "FAIL" not in r.stdout:
        return [_result("layout", "PASS", "local browser layout audit: no overlap, no empty stage, no scrim over media")]
    if "playwright" in out.lower() and ("ModuleNotFoundError" in out or "Executable doesn't exist" in out or "error while loading shared libraries" in out):
        return [_result("layout", "BLOCK", "local browser unavailable for the layout audit",
                        "run tools/browser_setup.py once (user-space Chromium), then re-run preflight")]
    fails = [ln.strip() for ln in r.stdout.splitlines() if ln.strip().startswith("FAIL")]
    return [_result("layout", "BLOCK", fails[0] if fails else (out.splitlines() or ["layout audit failed"])[-1],
                    "fix the scene and re-run tools/layout_audit.py until it prints OK")]


def _browser_env():
    import os
    env = dict(os.environ)
    libs = Path.home() / ".local" / "share" / "reels-browser" / "root"
    if libs.exists():  # user-space system libraries for headless Chromium (tools/browser_setup.py)
        found = sorted({str(p.parent) for p in libs.rglob("*.so*")})
        env["LD_LIBRARY_PATH"] = ":".join(found + [env.get("LD_LIBRARY_PATH", "")])
    return env


def check_policy(brief_id, brief):
    """Lessons 18, 19: new briefs use the current motion standard; a queued copy with a pending pin is blocked."""
    out = []
    queued = [i for i in (json.loads(QUEUE.read_text(encoding="utf-8")).get("items", []) if QUEUE.exists() else [])
              if i.get("video_id") == brief_id]
    if not queued and int(brief.get("motion_standard") or 0) < 2:
        out.append(_result("policy", "BLOCK", "new brief without motion_standard: 2",
                           "set \"motion_standard\": 2 so the hold, label and media-aspect rules apply"))
    for item in queued:
        if item.get("copy_pin_pending"):
            out.append(_result("policy", "BLOCK", f"copy pin pending: {item['copy_pin_pending']}",
                               "owner decision needed before this video can be dispatched or scheduled"))
    if not out:
        out.append(_result("policy", "PASS", "motion standard and copy pins in order"))
    return out


def check_tracked(brief_id):
    """Lesson 9: gitignored spec/selection files are silently skipped by `git add`.

    Every file a cloud run reads must be tracked (or be a machine-written file that is
    deliberately ignored, which is not listed here). `git ls-files` reports tracked files
    only, so an ignored or untracked spec is caught before dispatch.
    """
    import subprocess
    required = [f"briefs/{brief_id}.json", "queue/publish.json", "config/selection.json"]
    required += [str(p.relative_to(ROOT)) for p in (ROOT / "research" / "production" / "receipts").glob(f"*{brief_id.replace('repo-', '')}*.json")]
    missing = []
    for rel in required:
        if not (ROOT / rel).exists():
            continue
        out = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=ROOT,
                             capture_output=True, text=True)
        if out.returncode != 0:
            missing.append(rel)
    if missing:
        return [_result("tracked", "BLOCK", "not tracked by git (ignored or untracked): " + ", ".join(missing),
                        "git add -f the listed files, commit and push before dispatch")]
    return [_result("tracked", "PASS", f"{len(required)} spec files tracked")]


def check_workspace(brief_id):
    """Lesson 12: the workspace snapshot cap (128 MB / 10,000 files) is a hard gate, not a note."""
    sys.path.insert(0, str(ROOT / "tools" / "maintenance"))
    try:
        import storage  # noqa: E402
        report = storage.audit()
    except Exception as exc:  # the audit itself must not pass silently
        return [_result("workspace", "BLOCK", f"storage audit failed to run: {exc}", "fix tools/maintenance/storage.py")]
    if not report.get("ok"):
        return [_result("workspace", "BLOCK",
                        f"workspace {report.get('workspace_saved_bytes')} bytes over budget or limit",
                        "python3 tools/maintenance/storage.py audit; remove local MP4s/frames already in a release")]
    return [_result("workspace", "PASS", f"workspace {report.get('workspace_saved_bytes')} bytes within budget")]


MEDIA_EXT = (".mp4", ".jpg", ".jpeg", ".png", ".webp", ".mp3", ".wav", ".svg", ".gif")


def _asset_refs(node, out):
    """Every local media file a brief references (scene image/src, capture files)."""
    if isinstance(node, dict):
        for v in node.values():
            _asset_refs(v, out)
    elif isinstance(node, list):
        for v in node:
            _asset_refs(v, out)
    elif isinstance(node, str) and node.lower().endswith(MEDIA_EXT) and "/" not in node and "://" not in node:
        out.add(node)
    return out


def _capture_id(brief):
    """Briefs store `capture` as captures/<id> or <id>; the pack id is the last path part."""
    raw = (brief.get("capture") or "").strip().rstrip("/")
    return raw.split("/")[-1] if raw else ""


def _push_record(cap):
    path = ROOT / "tracker" / "capture-pushes.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get(cap)


def check_assets_present(brief_id, brief):
    """Failure 1 Nov (run 41311570435): anim-point4.mp4 was missing from the checkout. The cloud renders from
    the capture-packs release, so a file is safe when the pushed pack records it (tracker/capture-pushes.json).
    A file absent locally but recorded in the pushed pack is pulled by the build stage; a file neither local
    nor recorded in a push is a BLOCK (the render would have nothing to read)."""
    cap = _capture_id(brief)
    if not cap:
        return [_result("assets", "BLOCK", "brief has no capture pack id", "set capture to captures/<id>")]
    refs = sorted(_asset_refs({k: v for k, v in brief.items() if k in ("scenes", "cover", "post", "seo")}, set()))
    base = ROOT / "captures" / cap
    missing = [r for r in refs if not (base / r).exists()]
    if not missing:
        return [_result("assets", "PASS", f"{len(refs)} referenced media file(s) on disk")]
    record = _push_record(cap)
    recorded = set(record["files"]) if record else set()
    unproven = [m for m in missing if m not in recorded]
    if unproven:
        return [_result("assets", "BLOCK",
                        f"missing in captures/{cap} and not in its pushed release pack: " + ", ".join(unproven),
                        f"rebuild the asset, or push the pack after it exists: python3 tools/capture_store.py push {cap}")]
    return [_result("assets", "NOTE", f"{len(missing)} file(s) absent locally, recorded in the pushed pack; "
                                      "the build stage pulls them", "")]


def check_capture_pack_release(brief_id, brief, fetch_release=None):
    """The cloud render pulls captures from the capture-packs release, not from git. Two proofs:
    1. the release asset exists (presence);
    2. the local files match the bytes last pushed (tracker/capture-pushes.json, written by capture_store push).
    Content, not mtime: a workspace restore changes mtimes without changing the files."""
    cap = _capture_id(brief)
    if not cap:
        return []
    try:
        rel = (fetch_release or _capture_release)()
    except Exception as exc:
        return [_result("capture_release", "BLOCK", f"capture-packs release unreadable: {exc}",
                        "check the GitHub token, then re-run preflight")]
    if not any(a.get("name") == f"{cap}.tar" for a in rel.get("assets", [])):
        return [_result("capture_release", "BLOCK", f"{cap}.tar is not in the capture-packs release",
                        f"python3 tools/capture_store.py push {cap}")]
    pushes_path = ROOT / "tracker" / "capture-pushes.json"
    pushes = json.loads(pushes_path.read_text(encoding="utf-8")) if pushes_path.exists() else {}
    record = pushes.get(cap)
    if not record:
        return [_result("capture_release", "NOTE", f"{cap}.tar in release; no push record yet (content not proven)",
                        f"python3 tools/capture_store.py push {cap} once to record the content")]
    import capture_store  # noqa: E402  (digest helper shared with the push)
    local = capture_store.file_digests(ROOT / "captures" / cap) if (ROOT / "captures" / cap).exists() else {}
    changed = sorted(k for k in set(local) | set(record["files"]) if local.get(k) != record["files"].get(k))
    if changed:
        return [_result("capture_release", "BLOCK",
                        f"captures/{cap} differs from the pushed release copy: " + ", ".join(changed[:6]),
                        f"python3 tools/capture_store.py push {cap} (a stale pack would render old media)")]
    return [_result("capture_release", "PASS", f"{cap}.tar in release; local files match the pushed bytes")]


def _capture_release():
    sys.path.insert(0, str(ROOT / "tools"))
    import capture_store
    return capture_store.release()


def check_cover(brief_id):
    """Failure 1 Nov: the cloud gate requires the brief cover text to equal the selected cover text, and
    the cover file must be the one that was reviewed (sha256). Both are checked before dispatch."""
    import hashlib
    sel_path = ROOT / "covers" / brief_id / "selection.json"
    if not sel_path.exists():
        return [_result("cover", "BLOCK", "no reviewed cover selection", "extract and approve the cover, then re-run")]
    sel = json.loads(sel_path.read_text(encoding="utf-8"))
    cover = ROOT / "covers" / brief_id / sel.get("file", "cover-selected.jpg")
    if not cover.exists():
        return [_result("cover", "BLOCK", f"selected cover file missing: {cover.name}", "re-run the cover system")]
    digest = hashlib.sha256(cover.read_bytes()).hexdigest()
    if digest != sel.get("sha256"):
        return [_result("cover", "BLOCK", "cover file changed since it was reviewed (sha mismatch)",
                        "review the new cover and update selection.json")]
    plan_path = ROOT / "videos" / brief_id / "plan.json"
    if plan_path.exists():
        plan_text = (json.loads(plan_path.read_text(encoding="utf-8")).get("cover") or {}).get("text")
        if plan_text != sel.get("text"):
            return [_result("cover", "BLOCK", f"plan cover text {plan_text!r} != selected cover {sel.get('text')!r}",
                            "set plan.cover.text to the reviewed cover text and regenerate the brief")]
    return [_result("cover", "PASS", "selected cover matches the reviewed sha and plan text")]


def legacy_ids():
    path = ROOT / "config" / "legacy-briefs.json"
    return set(json.loads(path.read_text(encoding="utf-8")).get("briefs", {})) if path.exists() else set()


def _cloud_source_checks(brief_id, brief):
    """Assets, capture-pack release and cover. For a LEGACY brief (its video already went out) these are
    NOTE, not BLOCK: it is not re-dispatched from the old brief, and a new render is a new decision."""
    results = check_assets_present(brief_id, brief) + check_capture_pack_release(brief_id, brief) + check_cover(brief_id)
    if brief_id not in legacy_ids():
        return results
    for r in results:
        if r["status"] == "BLOCK":
            r["status"] = "NOTE"
            r["detail"] = "legacy (already published): " + r["detail"]
            r["fix"] = "only needed if this brief is ever re-rendered"
    return results


def preflight(brief_id):
    path = ROOT / "briefs" / f"{brief_id}.json"
    if not path.exists():
        return {"id": brief_id, "verdict": "BLOCK", "results": [_result("brief", "BLOCK", "brief file not found", "check the id")]}
    try:
        brief = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"id": brief_id, "verdict": "BLOCK", "results": [_result("brief", "BLOCK", f"unreadable: {exc}", "fix the JSON")]}
    results = (check_lint(brief_id, path) + check_studio_rules(brief)
               + check_queue_pin(brief_id, brief) + check_render(brief_id)
               + check_motion(brief_id, path) + check_media_aspect(brief_id, brief)
               + check_policy(brief_id, brief) + check_layout(brief_id, path)
               + check_tracked(brief_id) + check_workspace(brief_id)
               + _cloud_source_checks(brief_id, brief))
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
