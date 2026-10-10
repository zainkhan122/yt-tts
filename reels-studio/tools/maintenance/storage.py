#!/usr/bin/env python3
"""Workspace/repo budget audit and VERIFIED local capture pruning.

Never delete Releases, research, briefs, credentials, trackers, or another project.
A capture directory is deleted only when EVERY local byte exists in the archived
Release tar whose own SHA-256 was verified. Default operation is read-only.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.post.common import config, iso, now_utc, save_json, valid_id
from tools.post.media import public_download
from tools.gh_actions import api

EXCLUDED = {".arena", ".cache", ".local", ".mypy_cache", ".next", ".nox", ".npm", ".nuxt", ".output", ".parcel-cache", ".pytest_cache", ".ruff_cache", ".svelte-kit", ".tox", ".turbo", ".venv", ".vite", "__pycache__", "build", "coverage", "dist", "node_modules", "out", "target"}


def saved_usage(root):
    total, count = 0, 0
    for directory, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED]
        for name in files:
            path = Path(directory)/name
            if path.is_symlink():
                continue
            try:
                total += path.stat().st_size
                count += 1
            except FileNotFoundError:
                pass
    return total, count


def audit():
    total, count = saved_usage(ROOT.parent if os.environ.get("GITHUB_ACTIONS") == "true" else Path.home())
    paths = subprocess.check_output(["git", "ls-files", "-z", "--", "reels-studio/", ".github/workflows/"], cwd=ROOT.parent).split(b"\0")
    tracked = [ROOT.parent/p.decode() for p in paths if p]
    large = [str(p.relative_to(ROOT.parent)) for p in tracked if p.is_file() and p.stat().st_size > 5_000_000]
    videos = [str(p.relative_to(ROOT.parent)) for p in tracked if p.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}]
    source = sum(p.stat().st_size for p in tracked if p.is_file())
    return {"observed_at": iso(now_utc()), "workspace_saved_bytes": total, "workspace_saved_files": count,
            "workspace_budget_bytes":128_000_000,"workspace_warning_bytes":100_000_000,
            "studio_tracked_bytes": source, "studio_source_budget_bytes":20_000_000,
            "tracked_video_files":videos,"tracked_files_over_5mb":large,
            "ok":total<100_000_000 and count<9000 and source<20_000_000 and not videos and not large,
            "scope":"Only Reels Studio/workflows. Unrelated projects and remote git history are never removed."}


def verify_capture_tar(local, archive, pack):
    local = Path(local)
    checked, total = 0, 0
    with tarfile.open(archive,"r") as tf:
        members = {m.name:m for m in tf.getmembers() if m.isfile()}
        for path in local.rglob("*"):
            if path.is_symlink():
                raise ValueError("Capture has a symlink; refusing automatic deletion")
            if not path.is_file():
                continue
            name = pack+"/"+path.relative_to(local).as_posix()
            member = members.get(name)
            if not member or member.size != path.stat().st_size:
                raise ValueError("Capture file is not safely archived: "+name)
            a, b = hashlib.sha256(), hashlib.sha256()
            with path.open("rb") as f:
                for block in iter(lambda:f.read(1024*1024),b""):a.update(block)
            with tf.extractfile(member) as f:
                for block in iter(lambda:f.read(1024*1024),b""):b.update(block)
            if a.digest() != b.digest():
                raise ValueError("Capture archive content differs: "+name)
            checked += 1
            total += member.size
    if not checked:
        raise ValueError("Empty capture directory")
    return checked, total


def prune_capture(pack, apply=False):
    valid_id(pack)
    local = ROOT/"captures"/pack
    if not local.is_dir() or local.resolve().parent != (ROOT/"captures").resolve():
        raise ValueError("Not a local capture pack")
    status, release = api("GET", "/releases/tags/capture-packs")
    if status != 200:
        raise ValueError("Cannot verify capture archive; nothing deleted")
    asset = next((a for a in release["assets"] if a["name"] == pack+".tar"), None)
    if not asset or not asset.get("digest"):
        raise ValueError("Capture archive/digest missing; nothing deleted")
    with tempfile.TemporaryDirectory(prefix="hypeless-archive-check-", dir="/var/tmp") as work:
        path=Path(work)/"archive.tar"
        public_download(asset["browser_download_url"],asset["size"],asset["digest"],path)
        checked,total=verify_capture_tar(local,path,pack)
    result={"pack":pack,"files_verified":checked,"bytes_verified":total,"archive_id":asset["id"],"archive_digest":asset["digest"],"deleted":False}
    if apply:
        shutil.rmtree(local)
        result["deleted"]=True
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command",choices=["audit","prune-capture"])
    ap.add_argument("pack",nargs="?")
    ap.add_argument("--apply",action="store_true")
    ap.add_argument("--report")
    a=ap.parse_args()
    result=audit() if a.command=="audit" else prune_capture(a.pack,a.apply)
    if a.report:save_json(a.report,result)
    print(json.dumps(result,indent=2))
    return 0 if result.get("ok",True) else 1


if __name__=="__main__":
    raise SystemExit(main())
