#!/usr/bin/env python3
"""
Reels Studio - professional vertical-video generator (HyperFrames + free tools)

  python3 reels.py doctor                                   # is everything installed + healthy?
  python3 reels.py radar  [--days 14] [--brief]             # trending AI repos/models/apps -> idea sheet (+ draft brief)
  python3 reels.py capture <id> --url <site-or-repo>        # site/repo -> credited asset pack in captures/<id>/
  python3 reels.py social --account <tiktok/yt url> --top 2  # competitors' scripts, hooks, pacing, CTAs -> research/social/
  python3 tools/channel_study.py meta|visual|transcribe|report # deep study of benchmark accounts (20-30 videos each)
  python3 tools/idea_feed.py --days 7                        # topics the watchlist channels are covering (consensus) -> backlog
  python3 reels.py make   briefs/x.json --quality looks --crf 26
  python3 reels.py make   briefs/x.json --no-render         # fast iteration: build + lint + check only
  python3 reels.py batch  briefs/a.json briefs/b.json ...   # a week of videos in one go
  python3 reels.py publish [renders/<id>/<id>.mp4 ...]      # upload renders to a GitHub Release, update RENDERS.md
  python3 reels.py sync   -m "message"                      # commit + push reels-studio/ (the single source of truth)
  python3 reels.py templates | new <template> briefs/new.json

Renders: renders/<id>/ (local, git-ignored) + GitHub Releases (permanent). Intermediates: /var/tmp/reels/.
Token for publish/sync (session only): env GH_TOKEN or /var/tmp/gh/token. Never committed, never printed.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from lib import pipeline  # noqa: E402

REPO = ROOT.parent
TOKEN_FILE = Path("/var/tmp/gh/token")


def token():
    from lib.secrets import gh_token
    return gh_token()


def git(*args, check=True, auth=False):
    cmd = ["git", "-C", str(REPO)]
    if auth:  # credential helper reads the token at call time; nothing is written to disk
        cmd += ["-c", "credential.helper=",
                "-c", "credential.helper=!f() { echo username=x-access-token; echo \"password=${GH_TOKEN:-$(cat /var/tmp/gh/token 2>/dev/null || cat $HOME/.config/reels-studio/gh_token 2>/dev/null)}\"; }; f"]
    p = subprocess.run(cmd + list(args), capture_output=True, text=True)
    if check and p.returncode != 0:
        raise SystemExit(f"git {' '.join(args[:2])} failed: {(p.stderr or p.stdout).strip()[-400:]}")
    return p.stdout.strip()


def cmd_doctor(a):
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
    row("(opt) GitHub token (session)", token() is not None, "present" if token() else "needed only for publish/sync")
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
    git("add", "-A", "--", "reels-studio")
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
    git("push", "-q", "origin", "HEAD:main", auth=True)
    print("pushed:", git("log", "--oneline", "-1"))


def cmd_publish(a):
    t = token()
    if not t:
        raise SystemExit("publish needs GH_TOKEN (or /var/tmp/gh/token)")
    files = [Path(f) for f in a.files] or sorted((ROOT / "renders").glob("*/*.mp4"))
    subprocess.run([sys.executable, str(ROOT / "tools/publish_release.py"), "--tag", a.tag, *map(str, files)], check=True)


def cmd_capture(a):
    args = [sys.executable, str(ROOT / "tools/capture.py"), a.id, "--url", a.url] + (["--repo", a.repo] if a.repo else [])
    subprocess.run(args, check=True)


def cmd_social(rest):
    subprocess.run([sys.executable, "-u", str(ROOT / "tools/social_scan.py"), *rest], check=True)  # -u: live log


def cmd_radar(a):
    args = [sys.executable, str(ROOT / "tools/trend_radar.py"), "--days", str(a.days)]
    if a.brief:
        args.append("--brief")
    subprocess.run(args, check=True)


def main():
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
    sub.add_parser("templates")
    sub.add_parser("doctor")
    p = sub.add_parser("new")
    p.add_argument("template")
    p.add_argument("dest")
    p = sub.add_parser("sync")
    p.add_argument("-m", "--message", default="reels-studio: update")
    p = sub.add_parser("publish")
    p.add_argument("files", nargs="*")
    p.add_argument("--tag", default=time.strftime("renders-%Y-%m-%d"))
    p = sub.add_parser("capture")
    p.add_argument("id")
    p.add_argument("--url", required=True)
    p.add_argument("--repo")
    p = sub.add_parser("radar")
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--brief", action="store_true", help="also write a draft ranked-list brief from the top repos")
    if len(sys.argv) > 1 and sys.argv[1] == "social":  # pass-through to tools/social_scan.py
        return cmd_social(sys.argv[2:])
    a = ap.parse_args()

    if a.cmd == "doctor":
        return cmd_doctor(a)
    if a.cmd == "sync":
        return cmd_sync(a)
    if a.cmd == "publish":
        return cmd_publish(a)
    if a.cmd == "radar":
        return cmd_radar(a)
    if a.cmd == "capture":
        return cmd_capture(a)
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

    results, t0 = [], time.time()
    for bp in a.briefs:
        try:
            job = pipeline.Job(bp, quality=a.quality, crf=a.crf, check=not a.no_check, render=not a.no_render, keep_work=a.keep_work)
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
    main()
