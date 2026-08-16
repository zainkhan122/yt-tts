#!/usr/bin/env python3
"""vault_push.py — push files to GitHub via the Git Data API (no local git, no .git dir).

Usage:
  python3 tools/vault_push.py OWNER/REPO "commit message" PATH1 LOCAL1 [PATH2 LOCAL2 ...]
"""
import base64, json, os, sys, urllib.request, urllib.error

def api(method, url, token, data=None, timeout=600):
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
        print("HTTP", e.code, "->", e.read().decode()[:300])
        raise

def push(owner, repo, files, msg, token):
    info = api("GET", f"https://api.github.com/repos/{owner}/{repo}", token)
    branch = info["default_branch"]
    head = api("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}", token)
    base_sha = head["object"]["sha"]
    base_commit = api("GET", f"https://api.github.com/repos/{owner}/{repo}/git/commits/{base_sha}", token)
    base_tree = base_commit["tree"]["sha"]
    items = []
    for path, local in files.items():
        with open(local, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        blob = api("POST", f"https://api.github.com/repos/{owner}/{repo}/git/blobs", token,
                   {"content": content, "encoding": "base64"})
        items.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print("  blob:", path)
    tree = api("POST", f"https://api.github.com/repos/{owner}/{repo}/git/trees", token,
               {"base_tree": base_tree, "tree": items})
    commit = api("POST", f"https://api.github.com/repos/{owner}/{repo}/git/commits", token,
                 {"message": msg, "tree": tree["sha"], "parents": [base_sha]})
    api("PATCH", f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}", token,
        {"sha": commit["sha"], "force": False})
    print("PUSHED ->", branch)

if __name__ == "__main__":
    token = open(os.path.expanduser("~/secrets/github_pat.txt")).read().strip()
    owner_repo = sys.argv[1]
    msg = sys.argv[2]
    pairs = sys.argv[3:]
    if len(pairs) % 2 != 0:
        print("path/local pairs must be even"); sys.exit(1)
    files = {pairs[i]: pairs[i+1] for i in range(0, len(pairs), 2)}
    push(owner_repo.split("/")[0], owner_repo.split("/")[1], files, msg, token)
