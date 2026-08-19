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
    # ALWAYS fresh BLOBLESS partial clone — tiny (no blob download), avoids /tmp
    # overflow. NO --depth: a shallow blobless clone can be missing subtree
    # objects, which makes write-tree/commit lazy-fetch a huge pack. Full-history
    # blobless (commits+trees only) is still tiny and fetch-free.
    if os.path.isdir(CLONE):
        shutil.rmtree(CLONE, ignore_errors=True)
    url = f"https://x-access-token:{TOKEN}@github.com/{REPO}.git"
    r = subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout",
                        url, CLONE], capture_output=True, text=True)
    if r.returncode != 0:
        print("clone failed:", r.stderr[-800:]); sys.exit(1)
    # populate the INDEX from HEAD's tree WITHOUT downloading blobs (read-tree)
    # — this makes commits preserve all existing files (no accidental deletes).
    r = subprocess.run(["git", "-C", CLONE, "read-tree", "HEAD"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("read-tree failed:", r.stderr[-500:]); sys.exit(1)

def main():
    msg = sys.argv[1]
    pairs = sys.argv[2:]
    if len(pairs) % 2:
        print("need even repo_path/local pairs"); sys.exit(1)
    files = {pairs[i]: pairs[i+1] for i in range(0, len(pairs), 2)}
    env = dict(os.environ,
               GIT_AUTHOR_NAME="agent", GIT_AUTHOR_EMAIL="agent@local",
               GIT_COMMITTER_NAME="agent", GIT_COMMITTER_EMAIL="agent@local")
    try:
        ensure_clone()
        for repo_path, local in files.items():
            dest = os.path.join(CLONE, repo_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(local, dest)
            subprocess.run(["git", "-C", CLONE, "add", "-f", "--", repo_path],
                           check=True, capture_output=True, text=True)
            print("  staged:", repo_path)
        # PLUMBING path (write-tree + commit-tree + update-ref), NOT `git commit`:
        # in a partial clone, `git commit` lazy-fetches a huge promisor pack
        # (~600MB of blobs) which can fill /tmp. The plumbing avoids it — a
        # blobless clone stays tiny and the push is a clean fast-forward.
        tree = subprocess.check_output(["git", "-C", CLONE, "write-tree"],
                                       text=True).strip()
        base = subprocess.check_output(["git", "-C", CLONE, "rev-parse", "HEAD"],
                                       text=True).strip()
        commit = subprocess.check_output(
            ["git", "-C", CLONE, "commit-tree", tree, "-p", base, "-m", msg],
            env=env, text=True).strip()
        subprocess.run(["git", "-C", CLONE, "update-ref", "refs/heads/main", commit],
                       check=True)
        print("  commit:", commit[:12])
        r = subprocess.run(["git", "-C", CLONE,
                            "-c", "pack.window=0", "-c", "pack.depth=0",
                            "-c", "http.postBuffer=536870912",
                            "push", "origin", f"{commit}:refs/heads/main"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("push failed:", r.stderr[-800:]); sys.exit(1)
        print("PUSHED -> main")
    finally:
        # clean the clone on SUCCESS and FAILURE (it accumulates pack objects
        # and can fill /tmp, starving later builds)
        shutil.rmtree(CLONE, ignore_errors=True)

if __name__ == "__main__":
    main()
