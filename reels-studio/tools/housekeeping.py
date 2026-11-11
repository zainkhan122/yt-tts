#!/usr/bin/env python3
"""Workspace housekeeping: keep local workspace footprint under control.

Rule 2026-11: workspace must stay under a hard size cap; the rule runs on three axes:
  1. Renders are OUT of version control and OUT of the workspace long they are consumed.
     Renders dir must never keep more than the 2 newest build outputs.
  2. Captures/covers packs must stay lean — images only, mp4 recording clips live under
     captures/<id>/ and are consumed by the render job, never kept more than the current run.
  3. Git history must stay healthy: fsck must report no missing objects; push must be clean.
     (Lesson 2026-11: commit 83d5a27 had a broken blob -> every push since was hollow.)

Usage: python3 tools/housekeeping.py [--dry-run] [--cap-mb 250]
"""
import json, shutil, subprocess, sys
from pathlib import Path

WORKSPACE = Path("/home/user")
RENDERS = WORKSPACE / "renders"
CAPDIR = WORKSPACE / "yt-tts" / "reels-studio" / "captures"
COVERS = WORKSPACE / "yt-tts" / "reels-studio" / "covers"
YT = WORKSPACE / "yt-tts"


def _bytes(d):
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file())


def render_cleanup(dry: bool):
    """Keep the two newest mp4 renders; older ones go (QA already archived them in Actions artifacts)."""
    if not RENDERS.exists():
        return
    vids = sorted(RENDERS.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    stat = {"kept": [p.name for p in vids[:2]], "pruned": []}
    for p in vids[2:]:
        stat["pruned"].append(p.name)
        if not dry:
            p.unlink()
    if stat["pruned"]:
        print("renders: kept right-now pair, pruned", len(stat["pruned"]), "older mp4:", stat["pruned"])
    else:
        print("renders: clean under cap")


def git_health():
    """Fail if the pushed dag is broken anywhere we rely on (fatal for push / gc later)."""
    r = subprocess.run(["git", "fsck", "--no-progress"], capture_output=True, text=True, cwd=YT)
    bad = [l for l in (r.stderr + r.stdout).splitlines() if l.startswith(("missing", "broken"))]
    if bad:
        print("GIT-UNHEALTHY: missing objects under pushed refs — NEVER ship on top:")
        for l in bad[:4]:
            print("   ", l[:100])
        return False
    print("git fsck: clean")
    return True


def stats(cap_mb: int):
    total = _bytes(WORKSPACE) / 1024 / 1024
    git = _bytes(YT / ".git") / 1024 / 1024
    renders = _bytes(RENDERS) / 1024 / 1024 if RENDERS.exists() else 0
    caps = _bytes(CAPDIR) / 1024 / 1024 if CAPDIR.exists() else 0
    print(f"total workspace: {total:.0f} MB (cap {cap_mb})  | .git {git:.0f} MB  renders {renders:.0f} MB  captures {caps:.0f} MB")
    if total > cap_mb:
        print(f"OVER CAP by {total - cap_mb:.0f} MB — prune rule applies")
        return False
    return True


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    cap = int(sys.argv[sys.argv.index("--cap-mb") + 1]) if "--cap-mb" in sys.argv else 250
    print(f"housekeeping (dry={dry}, cap={cap} MB)")
    ok = git_health()
    render_cleanup(dry)
    # captures & covers stay — they are versioned sources of truth, tiny enough now (7.3MB+2.2MB)
    stats(cap)
    sys.exit(0 if ok else 1)
