#!/usr/bin/env python3
"""
Reels Studio - professional vertical-video generator (HyperFrames + free tools)

  python3 reels.py doctor                                   # is everything installed + healthy?
  python3 reels.py radar  [--days 14] [--brief]             # trending AI repos/models/apps -> idea sheet (+ draft brief)
  python3 reels.py capture <id> --url <site-or-repo>        # site/repo -> credited asset pack in captures/<id>/
  python3 reels.py social --account <tiktok/yt url> --top 2  # competitors' scripts, hooks, pacing, CTAs -> research/social/
  python3 tools/channel_study.py meta|visual|transcribe|report # deep study of benchmark accounts (20-30 videos each)
  python3 tools/idea_feed.py --days 7                        # topics the watchlist channels are covering (consensus) -> backlog
  python3 reels.py make   briefs/x.json --quality looks --crf 26 --production-receipt reels-studio/research/production/receipts/<batch>.json
  python3 reels.py make   briefs/x.json --no-render         # layout iteration: build + lint + check only; receipt exempt
  python3 reels.py batch  briefs/a.json briefs/b.json ... --production-receipt reels-studio/research/production/receipts/<batch>.json
  python3 reels.py cloud  <brief-id> [...] --production-receipt reels-studio/research/production/receipts/<batch>.json [--wait]  # one-day artifact
  python3 reels.py scenes <id> [<id> ...] [--tag T] [--json]    # per-scene manifest of a published render (window, digests, assets)
  python3 reels.py rebuild <brief-id> --scenes <id,id> --reason "..." [--dry-run] [--local]
      # repair scene(s) of a published video: re-render only those, reuse the published audio
      # bit-for-bit, prove unchanged scenes stayed identical; refuses when narration changed
  python3 reels.py post [<id>] --dry-run                    # read-only Buffer queue / pacing preview
  python3 reels.py renders                                   # every published video + post kit (download links)
  python3 reels.py publish renders/<id> [renders/<id2> ...]  # upload a local render: <id>.mp4 + <id>-kit.zip
  python3 reels.py sync   -m "message"                      # commit + push reels-studio/ (the single source of truth)
  python3 reels.py templates | new <template> briefs/new.json

Cloud renders: one-day GitHub Actions artifacts; `reels.py cloud --wait` downloads them to renders/<id>/ and removes the temporary artifact. Permanent GitHub Releases are a separate, explicit `reels.py publish` action. Capture packs: GitHub Release "capture-packs" (tools/capture_store.py). Intermediates: /var/tmp/reels/.
Token: ~/.config/reels-studio/gh_token (sandbox) or env GH_TOKEN (cloud). Never committed, never printed.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

REPO = ROOT.parent
TOKEN_FILE = Path("/var/tmp/gh/token")


def token():
    from lib.secrets import gh_token
    return gh_token()


def ensure_git_config():
    """The workspace snapshot can drop .git/config (it is excluded by design). Restore the
    public partial-clone/identity template instead of failing every git call with
    "'origin' does not appear to be a git repository"."""
    cfg = REPO / ".git" / "config"
    tpl = ROOT / "setup" / "git-config.template"
    if not cfg.exists() and tpl.exists():
        cfg.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(tpl, cfg)
        print("restored .git/config from setup/git-config.template")


def git(*args, check=True, auth=False):
    ensure_git_config()
    cmd = ["git", "-C", str(REPO)]
    if auth:  # credential helper reads the token at call time; nothing is written to disk
        cmd += ["-c", "credential.helper=",
                "-c", "credential.helper=!f() { echo username=x-access-token; echo \"password=${GH_TOKEN:-$(cat /var/tmp/gh/token 2>/dev/null || cat $HOME/.config/reels-studio/gh_token 2>/dev/null)}\"; }; f"]
    p = subprocess.run(cmd + list(args), capture_output=True, text=True)
    if check and p.returncode != 0:
        raise SystemExit(f"git {' '.join(args[:2])} failed: {(p.stderr or p.stdout).strip()[-400:]}")
    return p.stdout.strip()


def cmd_doctor(a):
    from lib import pipeline
    ok_all = True

    def row(name, ok, info=""):
        nonlocal ok_all
        ok_all &= bool(ok) or name.startswith("(opt)")
        print(f"  {'✓' if ok else '✗'} {name:28s} {info}")

    def out(c):
        try:
            return subprocess.run(c, capture_output=True, text=True, timeout=60, env=pipeline.hf_env()).stdout.strip()
        except Exception:
            return ""
    print("Reels Studio doctor")
    node = out(["node", "-v"])
    row("node >= 22", node.startswith(("v22", "v23", "v24", "v25", "v26")), node)
    hv = out(["hyperframes", "--version"]).splitlines()
    row("hyperframes CLI 0.8.137", bool(hv) and hv[-1].strip() == "0.8.137", hv[-1] if hv else "missing")
    row("ffmpeg", shutil.which("ffmpeg") is not None)
    mods = [m for m in ("numpy", "scipy", "soundfile", "kokoro_onnx") if subprocess.run([sys.executable, "-c", f"import {m}"], capture_output=True).returncode != 0]
    row("python deps", not mods, "missing: " + ",".join(mods) if mods else "numpy scipy soundfile kokoro_onnx")
    row("(opt) Kokoro model cached", pipeline.KOKORO_MODEL.exists(), "auto-downloads on first make" if not pipeline.KOKORO_MODEL.exists() else "")
    row("(opt) yt-dlp (social scan)", shutil.which("yt-dlp") is not None, "" if shutil.which("yt-dlp") else "pip install yt-dlp")
    row("(opt) tesseract (on-screen text)", shutil.which("tesseract") is not None, "" if shutil.which("tesseract") else "apt-get install tesseract-ocr")
    wc = pipeline.HF_CACHE / "whisper/whisper.cpp/build/bin/whisper-cli"
    row("whisper-cli (QA)", wc.exists(), "" if wc.exists() else "run setup/setup-whisper.sh")
    row("fonts", all((pipeline.BASE_DIR / "fonts" / f).exists() for f, _ in pipeline.FONT_FILES.values()))
    row("templates", len(pipeline.list_templates()) >= 4, ", ".join(pipeline.list_templates()))
    remote = git("config", "--get", "remote.origin.url", check=False)
    row("git working copy", bool(remote), remote or "run bootstrap.sh")
    if remote:
        dirty = git("status", "--porcelain", "--", "reels-studio", check=False)
        row("(opt) SSOT synced", not dirty, f"{len(dirty.splitlines())} local change(s) -> reels.py sync" if dirty else "clean")
    row("(opt) GitHub token (session)", token() is not None, "present" if token() else "needed for cloud dispatch, sync, or publish")
    used = 0
    excl = {".cache", ".local", ".npm", "node_modules", "out", "build", "dist", "target", "__pycache__", ".venv", "coverage"}
    for r, ds, fs in os.walk(Path.home()):
        ds[:] = [d for d in ds if d not in excl]
        for f in fs:
            try:
                used += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    row("(opt) workspace < 100 MB", used < 100e6, f"{used / 1e6:.1f} MB saved of ~128 MB limit" + ("" if used < 100e6 else " -> publish renders, then delete local copies"))
    print("READY" if ok_all else "NOT READY - run: bash bootstrap.sh")
    sys.exit(0 if ok_all else 1)


def cmd_sync(a):
    git("add", "-A", "--", "reels-studio", *([".github"] if (ROOT.parent / ".github").exists() else []))
    from lib.secrets import contains_secret
    if contains_secret(git("diff", "--cached", check=False)):
        git("reset", "-q", check=False)
        raise SystemExit("ABORTED: a token-like string is in the staged changes. Nothing was committed.")
    if not git("diff", "--cached", "--name-only", check=False):
        print("nothing to sync")
        return
    git("commit", "-q", "-m", a.message)
    if not token():
        raise SystemExit("committed locally; set GH_TOKEN (or /var/tmp/gh/token) to push")
    git("pull", "-q", "--rebase", "origin", "main", auth=True)  # cloud jobs (github-actions[bot]) also commit
    git("push", "-q", "origin", "HEAD:main", auth=True)
    print("pushed:", git("log", "--oneline", "-1"))


def _brief_path(name):
    p = Path(name)
    if p.exists() and p.suffix == ".json":
        return p
    return ROOT / "briefs" / f"{Path(name).stem}.json"


def cmd_gates(a):
    """Run both gates, print findings by rule ID, and store them in the render manifests."""
    sys.path.insert(0, str(ROOT))
    from lib import gates
    reports, failed = [], 0
    for name in a.briefs:
        bp = _brief_path(name)
        if not bp.exists():
            print(f"x {name}: no brief at {bp}")
            failed += 1
            continue
        report = gates.run(bp)
        report["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        manifest = ROOT / "renders" / bp.stem / "manifest.json"
        if not a.no_record and manifest.exists():
            gates.record(manifest, report)
            report["recorded_in"] = str(manifest.relative_to(ROOT))
        reports.append(report)
        if not a.json:
            for line in gates.summary_lines(report):
                print(line)
            if report.get("recorded_in"):
                print(f"  recorded -> {report['recorded_in']}")
        failed += bool(report["rollup"]["errors"])
    if a.json:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    return 1 if failed else 0


def cmd_publish(a):
    args = [sys.executable, str(ROOT / "tools" / "publish_release.py"), "--tag", a.tag]
    for k in a.kits:
        args += ["--kit", k]
    return subprocess.run(args).returncode


def preflight_local_render(briefs, receipt_path, *, no_render=False, scene_rebuild=False,
                          repo_root=None, batch_briefs=None):
    """Require a current six-stage receipt before any full render; previews/scene repairs are exempt."""
    if no_render or scene_rebuild:
        return None
    if not isinstance(receipt_path, str) or not receipt_path.strip():
        raise SystemExit("a full render requires --production-receipt <repo-relative JSON path>")
    root = Path(repo_root or REPO).resolve()
    brief_root = root / "reels-studio/briefs"

    def normalize(token):
        raw = str(token)
        if (not raw or raw != raw.strip() or "\\" in raw
                or any(ord(char) < 32 or ord(char) == 127 for char in raw)):
            raise SystemExit(f"unsafe brief path for production preflight: {token!r}")
        if raw.endswith(".json"):
            path = PurePosixPath(raw)
            if path.is_absolute() or ".." in path.parts or not path.parts or ":" in path.parts[0]:
                raise SystemExit(f"unsafe brief path for production preflight: {token!r}")
            allowed = len(path.parts) == 1
            allowed |= len(path.parts) == 2 and path.parts[0] == "briefs"
            allowed |= len(path.parts) == 3 and path.parts[:2] == ("reels-studio", "briefs")
            if not allowed:
                raise SystemExit(f"brief path must be an ID or canonical briefs/<id>.json path: {token!r}")
            brief_id = path.name[:-5]
        else:
            if "/" in raw or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", raw):
                raise SystemExit(f"unsafe brief ID for production preflight: {token!r}")
            brief_id = raw
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", brief_id):
            raise SystemExit(f"unsafe brief ID for production preflight: {token!r}")
        canonical = brief_root / f"{brief_id}.json"
        if canonical.is_symlink() or not canonical.is_file():
            raise SystemExit(f"brief is missing or unsafe for production preflight: {brief_id}")
        if not canonical.resolve(strict=True).is_relative_to(brief_root.resolve()):
            raise SystemExit(f"brief path escapes the canonical briefs directory: {brief_id}")
        return brief_id

    actual_ids = [normalize(value) for value in briefs]
    if not actual_ids or len(actual_ids) > 10 or len(actual_ids) != len(set(actual_ids)):
        raise SystemExit("production preflight needs 1-10 unique brief IDs")
    if batch_briefs is None or batch_briefs == "":
        batch_ids = actual_ids
    elif isinstance(batch_briefs, str):
        try:
            parsed = json.loads(batch_briefs) if batch_briefs.lstrip().startswith("[") else batch_briefs.split()
        except json.JSONDecodeError as exc:
            raise SystemExit("--production-batch-briefs must be a JSON array or a whitespace-separated list") from exc
        if not isinstance(parsed, list):
            raise SystemExit("--production-batch-briefs must be a JSON array or a whitespace-separated list")
        batch_ids = [normalize(value) for value in parsed]
    elif isinstance(batch_briefs, list):
        batch_ids = [normalize(value) for value in batch_briefs]
    else:
        raise SystemExit("--production-batch-briefs must be a JSON array or a whitespace-separated list")
    if (not batch_ids or len(batch_ids) > 10 or len(batch_ids) != len(set(batch_ids))
            or not set(actual_ids) <= set(batch_ids)):
        raise SystemExit("production receipt batch IDs must be unique (maximum 10) and contain every render brief")

    sys.path.insert(0, str(ROOT))
    from tools.production_gate import ProductionGateError, sha256_bytes, validate_receipt, verify_capture_assets
    try:
        clean_receipt_path = receipt_path.strip()
        result = validate_receipt(root, clean_receipt_path, batch_ids, verify_assets=False)
        receipt_file = root / clean_receipt_path
        receipt_raw = receipt_file.read_bytes()
        if sha256_bytes(receipt_raw) != result.get("receipt_sha256"):
            raise ProductionGateError("production receipt changed during local preflight")
        receipt_data = json.loads(receipt_raw.decode("utf-8"))
        for brief_id in actual_ids:
            brief_file = brief_root / f"{brief_id}.json"
            brief_raw = brief_file.read_bytes()
            if sha256_bytes(brief_raw) != result["briefs"][brief_id]["brief_sha256"]:
                raise ProductionGateError(f"{brief_id}: brief changed during local preflight")
            brief_data = json.loads(brief_raw.decode("utf-8"))
            stage = receipt_data["briefs"][brief_id]["stages"]["assets"]
            verify_capture_assets(root, brief_id, brief_data, stage)
    except (ProductionGateError, OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
        raise SystemExit(f"production preflight rejected: {exc}") from exc
    return result


def cmd_cloud(a):
    sys.path.insert(0, str(ROOT / "tools"))
    import gh_actions
    sys.path.insert(0, str(ROOT))
    from tools.validate_dispatch import plan_dispatch
    try:
        plan = plan_dispatch(" ".join(a.briefs), tag=a.tag, quality=a.quality, crf=a.crf,
                             production_receipt=a.production_receipt, repo_root=REPO)
    except (ValueError, RuntimeError, OSError) as exc:
        raise SystemExit(f"cloud render preflight rejected: {exc}") from exc
    ids = plan["briefs"]
    sys.path.insert(0, str(ROOT))
    from lib import gates
    reports, gates_failed = [], 0
    for i in ids:
        report = gates.run(ROOT / "briefs" / f"{i}.json")
        report["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        reports.append(report)
        gates_failed += bool(report["rollup"]["errors"])
        for line in gates.summary_lines(report):
            print(line)
    stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    receipt = ROOT / "research/maintenance/gates" / f"{stamp}-cloud-{len(ids)}briefs.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({"dispatched": ids, "gates": reports}, indent=2, ensure_ascii=False) + "\n")
    print(f"gate receipt -> {receipt.relative_to(ROOT)}")
    if gates_failed:
        raise SystemExit("gates found errors — fix them before spending cloud runners")
    run_id = gh_actions.dispatch("render.yml", {
        "briefs": " ".join(ids), "tag": plan["tag"], "quality": plan["quality"], "crf": str(plan["crf"]),
        "production_receipt": a.production_receipt,
    })
    receipt.write_text(json.dumps({"dispatched": ids, "run_id": run_id, "gates": reports}, indent=2, ensure_ascii=False) + "\n")
    print(f"cloud render started: https://github.com/{gh_actions.REPO}/actions/runs/{run_id}  ({len(ids)} video(s))")
    if a.wait:
        result = gh_actions.wait(run_id, 5400)
        print("result:", result)
        if result == "success":
            for i in ids:
                artifact = f"render-{i}"
                dest = ROOT / "renders" / i
                gh_actions.download(run_id, artifact, str(dest))
                gh_actions.delete_artifact(run_id, artifact)
    return 0


def _scenes_tool():
    sys.path.insert(0, str(ROOT))
    from lib import scenes as scenelib
    return scenelib


def load_rebuild(brief_arg, scenes, reason, from_tag):
    """Fetch the published kit + mp4 a rebuild starts from (the Release is the immutable record)."""
    sys.path.insert(0, str(ROOT / "tools"))
    import publish_release as pr
    import zipfile
    brief_path = Path(brief_arg) if Path(brief_arg).exists() else ROOT / "briefs" / f"{Path(brief_arg).stem}.json"
    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    vid = brief["id"]
    tag = from_tag or time.strftime("renders-%Y-%m-%d")
    work = Path(os.environ.get("REELS_WORK", "/var/tmp/reels")) / vid / "rebuild-src"
    work.mkdir(parents=True, exist_ok=True)
    kit = pr.download(tag, f"{vid}-kit.zip", work / f"{vid}-kit.zip")
    mp4 = pr.download(tag, f"{vid}.mp4", work / f"{vid}.mp4")
    with zipfile.ZipFile(kit) as z:
        manifest = json.loads(z.read(f"{vid}/manifest.json"))
        (work / "voiceover.mp3").write_bytes(z.read(f"{vid}/voiceover.mp3"))
    return {"scenes": list(scenes), "reason": reason, "manifest": manifest, "mp4": mp4,
            "voiceover": work / "voiceover.mp3", "from_tag": tag}


def cmd_scenes(a):
    scenelib = _scenes_tool()
    sys.path.insert(0, str(ROOT / "tools"))
    for target in a.targets:
        manifest = None
        if Path(target).suffix == ".json" and Path(target).exists():
            manifest = json.loads(Path(target).read_text(encoding="utf-8"))
        elif a.tag:
            import publish_release as pr
            import zipfile
            work = Path(os.environ.get("REELS_WORK", "/var/tmp/reels")) / target / "scenes-src"
            work.mkdir(parents=True, exist_ok=True)
            kit = pr.download(a.tag, f"{target}-kit.zip", work / f"{target}-kit.zip")
            with zipfile.ZipFile(kit) as z:
                manifest = json.loads(z.read(f"{target}/manifest.json"))
        else:
            local = ROOT / "renders" / target / "manifest.json"
            if not local.exists():
                raise SystemExit(f"no local manifest for {target} (pass --tag to read the published kit, or a manifest.json path)")
            manifest = json.loads(local.read_text(encoding="utf-8"))
        if a.json:
            print(json.dumps({k: manifest.get(k) for k in ("id", "revision", "duration", "brief_sha256", "audio_sha256", "scenes", "rebuilds", "rebuild")}, indent=2, ensure_ascii=False))
            continue
        sc = manifest.get("scenes")
        if not sc:
            raise SystemExit(f"{manifest.get('id')}: manifest has no scenes (rendered before scene manifests; run a full render)")
        print(f"{manifest.get('id')}  revision {manifest.get('revision', 0)}  {manifest.get('duration', 0):.2f}s  {len(sc)} scenes  brief {str(manifest.get('brief_sha256'))[-12:]}")
        for s in sc:
            assets = ",".join(a["name"] for a in s.get("assets", [])) or "-"
            print(f"  {s['index']} {s['id']:10s} {s['type']:8s} {s['start']:7.2f}-{s['end']:7.2f}s  "
                  f"spec {str(s.get('spec_sha256'))[-8:]}  narr {str(s.get('narration_sha256'))[-8:]}  {assets}")
        for r in manifest.get("rebuilds", []):
            print(f"  rebuild rev {r.get('revision')} {r.get('scenes')} ({r.get('reason')}) verified={r.get('verification_ok')} at {r.get('at')}")


def cmd_rebuild(a):
    scenes = [s for chunk in a.scenes for s in chunk.replace(",", " ").split()]
    if not scenes:
        raise SystemExit("--scenes needs at least one scene id (see: python3 reels.py scenes <id>)")
    brief_path = Path(a.brief) if Path(a.brief).exists() else ROOT / "briefs" / f"{Path(a.brief).stem}.json"
    if a.dry_run:
        # plan only: says whether the rebuild is allowed (and what it will re-render) before a runner is spent
        from lib import pipeline, scenes as scenelib
        rebuild = load_rebuild(a.brief, scenes, a.reason, a.from_tag)
        job = pipeline.Job(brief_path, render=False)
        segs = job.prepare_texts()
        new_narration = {s["id"]: pipeline.spoken_clean(s.get("spoken") or "") for s in segs}
        new_specs = {s.get("id"): s for s in job.brief.get("scenes", [])}
        plan = scenelib.plan_rebuild(rebuild["manifest"], new_specs, new_narration, scenes)
        plan["from_tag"] = rebuild["from_tag"]
        print(json.dumps(plan, indent=2))
        return 0 if plan["ok"] else 1
    if a.local:
        rebuild = load_rebuild(a.brief, scenes, a.reason, a.from_tag)
        from lib import pipeline
        job = pipeline.Job(brief_path, quality=a.quality, crf=a.crf, rebuild=rebuild)
        m = job.run_all()
        print(json.dumps({"revision": m.get("revision"), "rebuild": m.get("rebuild", {}).get("verification")}, indent=2))
        return
    sys.path.insert(0, str(ROOT / "tools"))
    import gh_actions
    brief_path = Path(a.brief)
    brief_id = brief_path.stem if brief_path.suffix == ".json" else brief_path.name
    inputs = {"briefs": brief_id, "tag": a.tag or time.strftime("renders-%Y-%m-%d"),
              "quality": a.quality, "crf": str(a.crf), "rebuild_scenes": " ".join(scenes),
              "rebuild_reason": a.reason or "scene repair", "from_tag": a.from_tag or ""}
    run_id = gh_actions.dispatch("render.yml", inputs)
    print(f"rebuild dispatched: https://github.com/{gh_actions.REPO}/actions/runs/{run_id}  "
          f"({brief_id}: {', '.join(scenes)} - audio reused, unchanged scenes verified)")
    if a.wait:
        print("result:", gh_actions.wait(run_id, 5400))


def cmd_capture(a):
    args = [sys.executable, str(ROOT / "tools/capture.py"), a.id, "--url", a.url] + (["--repo", a.repo] if a.repo else [])
    subprocess.run(args, check=True)


def cmd_social(rest):
    subprocess.run([sys.executable, "-u", str(ROOT / "tools/social_scan.py"), *rest], check=True)  # -u: live log


def cmd_radar(a):
    """Both discovery scans: AI tools + AI news from the watchlist channels (idea feed), then GitHub/HF repos.
    Daily mix (PIPELINE.md §1): not hardcoded — strongest researched topics win; owner approves."""
    if not a.repos_only:
        subprocess.run([sys.executable, str(ROOT / "tools/idea_feed.py"), "--days", str(min(a.days, 7)), "--per-channel", "15"], check=True)
    if not a.tools_only:
        args = [sys.executable, str(ROOT / "tools/trend_radar.py"), "--days", str(a.days)]
        if a.brief:
            args.append("--brief")
        subprocess.run(args, check=True)
    print("\nmix rule: editorial (no fixed split). Shortlist -> owner approval -> briefs.")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "post":
        return subprocess.call([sys.executable, str(ROOT / "tools/post/publisher.py"), *sys.argv[2:]])
    if len(sys.argv) > 1 and sys.argv[1] == "youtube":
        return subprocess.call([sys.executable, str(ROOT / "tools/youtube/runner.py"), *sys.argv[2:]])
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("make", "batch"):
        p = sub.add_parser(name)
        p.add_argument("briefs", nargs="+")
        p.add_argument("--quality", default="draft", choices=["draft", "looks", "delivery", "standard", "high"])
        p.add_argument("--crf", type=int, default=None, help="override encoder CRF (e.g. 26 = ~5 MB per 40 s)")
        p.add_argument("--no-check", action="store_true")
        p.add_argument("--no-render", action="store_true")
        p.add_argument("--keep-work", action="store_true")
        p.add_argument("--rebuild-scenes", default="", help="re-render only these scene ids (cloud rebuild mode)")
        p.add_argument("--rebuild-reason", default="", help="why this rebuild (recorded in the manifest)")
        p.add_argument("--from-tag", default="", help="release tag holding the previous kit+mp4 for a rebuild")
        p.add_argument("--production-receipt", default="", help="six-stage receipt required for a full render")
        p.add_argument("--production-batch-briefs", default="", help=argparse.SUPPRESS)
    sub.add_parser("templates")
    sub.add_parser("doctor")
    p = sub.add_parser("new")
    p.add_argument("template")
    p.add_argument("dest")
    p = sub.add_parser("sync")
    p.add_argument("-m", "--message", default="reels-studio: update")
    p = sub.add_parser("publish")
    p.add_argument("kits", nargs="+", help="renders/<id> folders")
    p.add_argument("--tag", default=time.strftime("renders-%Y-%m-%d"))
    p = sub.add_parser("lint", help="validate briefs (assets, regions, sync words, SEO) before rendering")
    p.add_argument("briefs", nargs="+", help="brief ids or paths")
    p = sub.add_parser("gates", help="run brief lint + SEO gate with stable rule IDs and record them in each render's manifest")
    p.add_argument("briefs", nargs="+", help="brief ids or paths")
    p.add_argument("--json", action="store_true", help="print the receipt JSON")
    p.add_argument("--no-record", action="store_true", help="print only; do not write manifests/<id>/manifest.json")
    p = sub.add_parser("cloud", help="render briefs on GitHub Actions -> temporary artifacts (one runner each, up to 10 in parallel)")
    p.add_argument("briefs", nargs="+", help="brief IDs or paths (briefs/<id>.json)")
    p.add_argument("--tag", default="", help="validated output tag (no public Release is created)")
    p.add_argument("--production-receipt", required=True, help="fresh receipt at reels-studio/research/production/receipts/<batch>.json")
    p.add_argument("--quality", default="looks")
    p.add_argument("--crf", default="23")
    p.add_argument("--wait", action="store_true", help="wait, download artifacts to renders/<id>/, and delete temporary artifacts")
    p = sub.add_parser("scenes", help="per-scene manifest of a published render (windows, digests, assets)")
    p.add_argument("targets", nargs="+", help="video ids, or paths to a manifest.json")
    p.add_argument("--tag", default="", help="read the manifest from this release's kit instead of renders/<id>/")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("rebuild", help="repair scene(s) of a published video (published audio reused, unchanged scenes verified)")
    p.add_argument("brief", help="brief id or path")
    p.add_argument("--scenes", action="append", required=True, help="scene ids (comma/space separated; repeatable)")
    p.add_argument("--reason", default="", help="why (kept in the manifest's rebuild history)")
    p.add_argument("--from-tag", default="", help="release tag holding the published kit+mp4 to repair")
    p.add_argument("--tag", default="", help="release tag for the new output (default renders-YYYY-MM-DD)")
    p.add_argument("--quality", default="looks")
    p.add_argument("--crf", default="23")
    p.add_argument("--dry-run", action="store_true", help="print the rebuild plan only (no runner spent)")
    p.add_argument("--local", action="store_true", help="run here instead of dispatching (needs the render toolchain)")
    p.add_argument("--wait", action="store_true")
    sub.add_parser("renders", help="list published videos + kits")
    p = sub.add_parser("capture")
    p.add_argument("id")
    p.add_argument("--url", required=True)
    p.add_argument("--repo")
    p = sub.add_parser("radar")
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--brief", action="store_true", help="also write a draft ranked-list brief from the top repos")
    p.add_argument("--tools-only", action="store_true", help="only the watchlist idea feed (AI tools + news)")
    p.add_argument("--repos-only", action="store_true", help="only the GitHub/HF repo radar")
    if len(sys.argv) > 1 and sys.argv[1] == "social":  # pass-through to tools/social_scan.py
        return cmd_social(sys.argv[2:])
    a = ap.parse_args()

    if a.cmd == "doctor":
        return cmd_doctor(a)
    if a.cmd == "scenes":
        return cmd_scenes(a)
    if a.cmd == "rebuild":
        return cmd_rebuild(a)
    if a.cmd == "sync":
        return cmd_sync(a)
    if a.cmd == "publish":
        return cmd_publish(a)
    if a.cmd == "cloud":
        return cmd_cloud(a)
    if a.cmd == "lint":
        return subprocess.call([sys.executable, str(ROOT / "tools" / "brief_lint.py"), *a.briefs])
    if a.cmd == "gates":
        return cmd_gates(a)
    if a.cmd == "renders":
        return subprocess.run([sys.executable, str(ROOT / "tools" / "publish_release.py"), "--list"]).returncode
    if a.cmd == "radar":
        return cmd_radar(a)
    if a.cmd == "capture":
        return cmd_capture(a)
    if a.cmd in ("make", "batch"):
        preflight_local_render(
            a.briefs,
            a.production_receipt,
            no_render=a.no_render,
            scene_rebuild=bool(a.rebuild_scenes),
            repo_root=REPO,
            batch_briefs=a.production_batch_briefs or None,
        )
    from lib import pipeline  # only render/template commands need the heavy voice dependencies
    if a.cmd == "templates":
        for name in pipeline.list_templates():
            t = pipeline.load_template(name)
            print(f"- {name}: {t.__doc__.strip().splitlines()[0] if t.__doc__ else ''}")
        return
    if a.cmd == "new":
        t = pipeline.load_template(a.template)
        src = t.DIR / "example.json"
        if not src.exists():
            src = next((ROOT / "briefs").glob("*.json"))
        shutil.copy2(src, a.dest)
        print(f"wrote {a.dest} from {src}")
        return

    rebuild = None
    if getattr(a, "rebuild_scenes", ""):
        if len(a.briefs) != 1:
            raise SystemExit("rebuild mode renders one video at a time: pass a single brief")
        rebuild = load_rebuild(a.briefs[0], a.rebuild_scenes.replace(",", " ").split(), a.rebuild_reason or "scene repair", a.from_tag)
        print(f"rebuild: {rebuild['manifest'].get('id')} revision {rebuild['manifest'].get('revision', 0)} from {rebuild['from_tag']}")
    results, t0 = [], time.time()
    for bp in a.briefs:
        try:
            job = pipeline.Job(bp, quality=a.quality, crf=a.crf, check=not a.no_check, render=not a.no_render, keep_work=a.keep_work, rebuild=rebuild)
            m = job.run_all()
            results.append((bp, "ok", m.get("qa", {}).get("checks")))
        except (SystemExit, Exception) as e:
            results.append((bp, f"FAILED: {e}", None))
            if a.cmd == "make":
                raise
    if a.cmd == "batch":
        print(f"\nbatch finished in {time.time() - t0:.0f}s")
        for bp, status, checks in results:
            print(f"  {bp}: {status} {json.dumps(checks) if checks else ''}")


if __name__ == "__main__":
    sys.exit(main())
