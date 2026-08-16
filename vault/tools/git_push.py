#!/usr/bin/env python3
"""git_push.py — push files (any size) to GitHub via a blobless local clone in /tmp.

The Git Data API rejects blob bodies >~50MB. This tool uses a real git clone
(kept OUTSIDE the workspace in /tmp, so it never bloats the snapshot) and pushes
the native way. Perfect for final videos.

Usage:
  python3 tools/git_push.py "commit message" REPO/PATH1 LOCAL1 [REPO/PATH2 LOCAL2 ...]
"""
import os, sys, subprocess, shutil

TOKEN = open(os.path.expanduser("~/secrets/github_pat.txt")).read().strip()
REPO = "zainkhan122/yt-tts"
CLONE = "/tmp/yt-tts-vault"

def ensure_clone():
    if os.path.isdir(os.path.join(CLONE, ".git")):
        subprocess.run(["git", "-C", CLONE, "fetch", "--depth", "1", "origin", "main"],
                       capture_output=True, text=True)
        # re-sync working tree with fresh main
        subprocess.run(["git", "-C", CLONE, "reset", "--hard", "origin/main"],
                       capture_output=True, text=True)
        return
    url = f"https://x-access-token:{TOKEN}@github.com/{REPO}.git"
    # FULL checkout (not --no-checkout) so the index + working tree contain the
    # complete tree — commits then preserve existing files.
    r = subprocess.run(["git", "clone", "--depth", "1", url, CLONE],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("clone failed:", r.stderr[-800:]); sys.exit(1)

def main():
    msg = sys.argv[1]
    pairs = sys.argv[2:]
    if len(pairs) % 2:
        print("need even repo_path/local pairs"); sys.exit(1)
    files = {pairs[i]: pairs[i+1] for i in range(0, len(pairs), 2)}
    ensure_clone()
    for repo_path, local in files.items():
        dest = os.path.join(CLONE, repo_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(local, dest)
        subprocess.run(["git", "-C", CLONE, "add", "-f", "--", repo_path],
                       check=True, capture_output=True, text=True)
        print("  staged:", repo_path)
    r = subprocess.run(["git", "-C", CLONE,
                        "-c", "user.name=agent", "-c", "user.email=agent@local",
                        "commit", "-m", msg], capture_output=True, text=True)
    print(r.stdout.strip()); print(r.stderr.strip()[-300:] if r.returncode else "")
    if r.returncode != 0:
        print("commit failed (maybe nothing new)"); sys.exit(1)
    r = subprocess.run(["git", "-C", CLONE, "push", "origin", "HEAD:main"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("push failed:", r.stderr[-800:]); sys.exit(1)
    print("PUSHED -> main")

if __name__ == "__main__":
    main()
