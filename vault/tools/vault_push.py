#!/usr/bin/env python3
"""vault_push.py — push files to GitHub via the Git Data API (no local git, no .git dir).

Usage:
  python3 tools/vault_push.py OWNER/REPO "commit message" PATH1 LOCAL1 [PATH2 LOCAL2 ...]
"""
import base64, json, os, sys, time, urllib.request, urllib.error

def api(method, url, token, data=None, timeout=600, retries=8):
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, method=method)
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("User-Agent", "vault-push")
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            req.add_header("Content-Type", "application/json")
        try:
            resp = urllib.request.urlopen(req, body, timeout=timeout)
            if resp.status == 204:
                return {}
            return json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                wait = 3 * (2 ** attempt)
                print(f"  ⏳ HTTP {e.code}, retry {attempt+1}/{retries} in {wait:.0f}s")
                time.sleep(wait)
                continue
            print("HTTP", e.code, "->", e.read().decode()[:300])
            raise
        except (urllib.error.URLError, ConnectionResetError, TimeoutError, OSError) as e:
            last = e
            wait = 3 * (2 ** attempt)
            print(f"  ⏳ net error, retry {attempt+1}/{retries} in {wait:.0f}s")
            time.sleep(wait)
            continue
    raise last

def push(owner, repo, files, msg, token):
    info = api("GET", f"https://api.github.com/repos/{owner}/{repo}", token)
    branch = info["default_branch"]
    # Build blobs ONCE (immutable). The ref-update part below can race other
    # pushes (GitHub eventual consistency -> 422 "not a fast forward"), so we
    # re-read the ref and rebuild the commit when that happens.
    items = []
    for path, local in files.items():
        with open(local, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        blob = api("POST", f"https://api.github.com/repos/{owner}/{repo}/git/blobs", token,
                   {"content": content, "encoding": "base64"})
        items.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print("  blob:", path)
    last = None
    for attempt in range(8):
        head = api("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}", token)
        base_sha = head["object"]["sha"]
        base_commit = api("GET", f"https://api.github.com/repos/{owner}/{repo}/git/commits/{base_sha}", token)
        base_tree = base_commit["tree"]["sha"]
        tree = api("POST", f"https://api.github.com/repos/{owner}/{repo}/git/trees", token,
                   {"base_tree": base_tree, "tree": items})
        commit = api("POST", f"https://api.github.com/repos/{owner}/{repo}/git/commits", token,
                     {"message": msg, "tree": tree["sha"], "parents": [base_sha]})
        try:
            api("PATCH", f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}", token,
                {"sha": commit["sha"], "force": False})
            print("PUSHED ->", branch)
            return
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 422:
                print(f"  ⏳ 422 (ref moved), re-basing retry {attempt+1}/8")
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise last

if __name__ == "__main__":
    token = open(os.path.expanduser("~/secrets/github_pat.txt")).read().strip()
    owner_repo = sys.argv[1]
    msg = sys.argv[2]
    pairs = sys.argv[3:]
    if len(pairs) % 2 != 0:
        print("path/local pairs must be even"); sys.exit(1)
    files = {pairs[i]: pairs[i+1] for i in range(0, len(pairs), 2)}
    push(owner_repo.split("/")[0], owner_repo.split("/")[1], files, msg, token)
