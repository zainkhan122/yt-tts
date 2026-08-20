#!/usr/bin/env python3
"""git_push.py v3 — push files to GitHub, robust on a 2GB/993MB-tmpfs box.

Two paths, chosen by file size:
  1. FILES <= 35MB  -> Git Data API (blob + tree-with-base_tree + commit + ref).
     No git clone, no /tmp usage. The API blob ceiling is ~37MB raw (verified).
  2. FILES >  35MB  -> shallow FULL clone (`git clone --depth 1`, NO
     --filter=blob:none) + git add + commit + push. The partial-clone
     (blob:none) path is BANNED: on git 2.47 write-tree lazy-fetches a ~600MB
     promisor pack (fills /tmp). A shallow full clone (~600MB) has all objects
     and commits/pushes normally.

The shallow-clone path frees /tmp/stock* first if /tmp is tight (stock is
re-fetchable; the render loop re-fetches it before the next chunk).

Usage:
  python3 tools/git_push.py "commit message" REPO/PATH1 LOCAL1 [REPO/PATH2 LOCAL2 ...]
"""
import base64, json, os, sys, subprocess, shutil, time, urllib.request, urllib.error

TOKEN = open(os.path.expanduser("~/secrets/github_pat.txt")).read().strip()
REPO = "zainkhan122/yt-tts"
CLONE = "/tmp/yt-tts-vault"
API_LIMIT = 35_000_000   # raw bytes; base64 stays under GitHub's body ceiling


def api(method, url, data=None, retries=8):
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, method=method)
        req.add_header("Authorization", f"Bearer {TOKEN}")
        req.add_header("User-Agent", "git-push-v3")
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            req.add_header("Content-Type", "application/json")
        try:
            r = urllib.request.urlopen(req, body, timeout=600)
            if r.status == 204:
                return {}
            return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(3 * (2 ** attempt)); continue
            print("API HTTP", e.code, "->", e.read().decode()[:300]); raise
        except (urllib.error.URLError, ConnectionResetError, TimeoutError, OSError) as e:
            last = e
            time.sleep(3 * (2 ** attempt)); continue
    raise last


def push_api(msg, files):
    """Git Data API path — for files all <= ~35MB."""
    ref = api("GET", "https://api.github.com/repos/zainkhan122/yt-tts/git/ref/heads/main")
    head = ref["object"]["sha"]
    commit = api("GET", f"https://api.github.com/repos/zainkhan122/yt-tts/git/commits/{head}")
    root_tree = commit["tree"]["sha"]
    items = []
    for path, local in files.items():
        with open(local, "rb") as f:
            b = base64.b64encode(f.read()).decode()
        blob = api("POST", "https://api.github.com/repos/zainkhan122/yt-tts/git/blobs",
                   {"content": b, "encoding": "base64"})
        items.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print("  blob:", path, blob["sha"][:10])
    tree = api("POST", "https://api.github.com/repos/zainkhan122/yt-tts/git/trees",
               {"base_tree": root_tree, "tree": items})
    new_commit = api("POST", "https://api.github.com/repos/zainkhan122/yt-tts/git/commits",
                     {"message": msg, "tree": tree["sha"], "parents": [head]})
    for attempt in range(8):
        try:
            api("PATCH", "https://api.github.com/repos/zainkhan122/yt-tts/git/refs/heads/main",
                {"sha": new_commit["sha"], "force": False})
            print("PUSHED -> main (API)")
            return
        except urllib.error.HTTPError as e:
            if e.code == 422:
                # ref moved under us — re-read and rebuild
                ref = api("GET", "https://api.github.com/repos/zainkhan122/yt-tts/git/ref/heads/main")
                head = ref["object"]["sha"]
                commit = api("GET", f"https://api.github.com/repos/zainkhan122/yt-tts/git/commits/{head}")
                root_tree = commit["tree"]["sha"]
                tree = api("POST", "https://api.github.com/repos/zainkhan122/yt-tts/git/trees",
                           {"base_tree": root_tree, "tree": items})
                new_commit = api("POST", "https://api.github.com/repos/zainkhan122/yt-tts/git/commits",
                                 {"message": msg, "tree": tree["sha"], "parents": [head]})
                time.sleep(2 * (attempt + 1)); continue
            raise


def free_tmp(need_mb):
    """Delete re-fetchable /tmp/stock* dirs if free space is below need_mb."""
    free = shutil.disk_usage("/tmp").free // (1024 * 1024)
    if free >= need_mb:
        return
    for name in os.listdir("/tmp"):
        if name.startswith("stock") and os.path.isdir(f"/tmp/{name}"):
            shutil.rmtree(f"/tmp/{name}", ignore_errors=True)
            print(f"  freed /tmp/{name}")


def ensure_clone():
    if os.path.isdir(CLONE):
        shutil.rmtree(CLONE, ignore_errors=True)
    url = f"https://x-access-token:{TOKEN}@github.com/{REPO}.git"
    r = subprocess.run(["git", "clone", "--depth", "1", "--no-checkout",
                        url, CLONE], capture_output=True, text=True)
    if r.returncode != 0:
        print("clone failed:", r.stderr[-800:]); sys.exit(1)
    r = subprocess.run(["git", "-C", CLONE, "read-tree", "HEAD"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("read-tree failed:", r.stderr[-500:]); sys.exit(1)


def push_shallow(msg, files):
    """Shallow FULL clone path — for files > 35MB. No partial-clone filter."""
    free_tmp(750)
    ensure_clone()
    for repo_path, local in files.items():
        dest = os.path.join(CLONE, repo_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(local, dest)
        subprocess.run(["git", "-C", CLONE, "add", "-f", "--", repo_path],
                       check=True, capture_output=True, text=True)
        print("  staged:", repo_path)
    r = subprocess.run(["git", "-C", CLONE,
                        "-c", "gc.auto=0",
                        "-c", "user.name=agent", "-c", "user.email=agent@local",
                        "commit", "-m", msg], capture_output=True, text=True)
    if r.returncode != 0:
        print("commit failed:", r.stderr[-500:]); sys.exit(1)
    print(r.stdout.strip().splitlines()[0] if r.stdout.strip() else "committed")
    r = subprocess.run(["git", "-C", CLONE,
                        "-c", "pack.window=0", "-c", "pack.depth=0",
                        "-c", "http.postBuffer=536870912",
                        "push", "origin", "HEAD:main"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("push failed:", r.stderr[-800:]); sys.exit(1)
    print("PUSHED -> main (shallow clone)")


def main():
    msg = sys.argv[1]
    pairs = sys.argv[2:]
    if len(pairs) % 2:
        print("need even repo_path/local pairs"); sys.exit(1)
    files = {pairs[i]: pairs[i+1] for i in range(0, len(pairs), 2)}
    biggest = max(os.path.getsize(local) for local in files.values())
    try:
        if biggest <= API_LIMIT:
            push_api(msg, files)
        else:
            print(f"  (largest file {biggest/1e6:.1f}MB > 35MB -> shallow clone path)")
            push_shallow(msg, files)
    finally:
        shutil.rmtree(CLONE, ignore_errors=True)


if __name__ == "__main__":
    main()
