#!/usr/bin/env python3
"""repo_sync.py — keep important files in GitHub finance/ ; workspace is scratch.
Never full-clones the psychology vault.

Usage:
  python3 tools/repo_sync.py push ["commit message"]
  python3 tools/repo_sync.py pull
  python3 tools/repo_sync.py status
"""
import json, os, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER, REPO, PREFIX = "zainkhan122", "yt-tts", "finance"
SKIP_DIRS = {".git", "secrets", "__pycache__", "output", "previews"}
SKIP_SUFFIX = {".pyc", ".mp4", ".mp3", ".wav"}
TEXT_OK = {".md", ".py", ".json", ".txt", ".csv", ".svg"}

def token():
    for p in [ROOT / "secrets/github_pat.txt", Path.home() / "secrets/github_pat.txt"]:
        if p.exists() and p.stat().st_size > 0:
            return p.read_text().strip()
    sys.exit("MISSING GitHub PAT. Paste it to secrets/github_pat.txt — do not commit it.")

def api(method, url, tok, data=None, timeout=120):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("User-Agent", "public-record")
    req.add_header("Accept", "application/vnd.github+json")
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    try:
        r = urllib.request.urlopen(req, body, timeout=timeout)
        if r.status == 204:
            return {}
        return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:500])
        raise

def local_files():
    files = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if any(part in SKIP_DIRS for part in Path(rel).parts):
            continue
        if p.suffix in SKIP_SUFFIX:
            continue
        if p.stat().st_size > 20_000_000:
            print("skip large", rel); continue
        files.append(p)
    return files

def put_file(tok, rel, data: bytes, msg):
    import base64
    path = f"{PREFIX}/{rel}"
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    payload = {"message": msg, "content": base64.b64encode(data).decode()}
    try:
        existing = api("GET", url, tok)
        payload["sha"] = existing["sha"]
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    return api("PUT", url, tok, payload)

def push(msg="public-record: sync"):
    tok = token()
    files = local_files()
    print(f"pushing {len(files)} files -> {OWNER}/{REPO}/{PREFIX}/")
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        put_file(tok, rel, p.read_bytes(), f"{msg} ({rel})")
        print("  +", rel)
    print("PUSH DONE")

def pull():
    tok = token()
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PREFIX}"
    def walk(u, dest_prefix=""):
        items = api("GET", u, tok)
        if isinstance(items, dict) and items.get("type") == "file":
            items = [items]
        for it in items:
            if it["type"] == "dir":
                walk(it["url"], dest_prefix)
            elif it["type"] == "file":
                rel = it["path"][len(PREFIX) + 1:]
                target = ROOT / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                import base64
                blob = api("GET", it["url"], tok)
                target.write_bytes(base64.b64decode(blob["content"]))
                print("  <-", rel)
    walk(url)
    print("PULL DONE")

def status():
    print("workspace", ROOT)
    print("files", len(local_files()))
    pat = (ROOT / "secrets/github_pat.txt").exists()
    print("PAT", "present" if pat else "MISSING")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "push":
        push(sys.argv[2] if len(sys.argv) > 2 else "threshold: sync finance/")
    elif cmd == "pull":
        pull()
    elif cmd == "status":
        status()
    else:
        sys.exit("push | pull | status")
