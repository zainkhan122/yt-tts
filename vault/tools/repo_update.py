#!/usr/bin/env python3
"""repo_update.py — delete + add/update files in a GitHub repo via the Git Data API.
No local clone, no downloads (works where git clone is unreliable).

Usage:
  python3 tools/repo_update.py OWNER/REPO "commit msg" \
      --delete path1 path2 ... \
      --add repo_path1 local1 repo_path2 local2 ...
"""
import base64, json, os, sys, urllib.request, urllib.error

def api(method, url, token, data=None, timeout=600):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "vault-update")
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
        print("HTTP", e.code, "->", e.read().decode()[:400]); raise

def blob(token, owner, repo, local):
    with open(local, "rb") as f:
        b = base64.b64encode(f.read()).decode()
    return api("POST", f"https://api.github.com/repos/{owner}/{repo}/git/blobs", token,
               {"content": b, "encoding": "base64"})["sha"]

def main():
    token = open(os.path.expanduser("~/secrets/github_pat.txt")).read().strip()
    owner, repo = sys.argv[1].split("/")
    msg = sys.argv[2]
    deletes, adds = [], {}
    args = sys.argv[3:]
    i = 0
    while i < len(args):
        if args[i] == "--delete":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                deletes.append(args[i]); i += 1
        elif args[i] == "--add":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                adds[args[i]] = args[i+1]; i += 2
        else:
            i += 1

    ref = api("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/main", token)
    head = ref["object"]["sha"]
    commit = api("GET", f"https://api.github.com/repos/{owner}/{repo}/git/commits/{head}", token)
    root_tree = commit["tree"]["sha"]

    # recursive listing -> {path: (sha, type)}
    flat = {}
    t = api("GET", f"https://api.github.com/repos/{owner}/{repo}/git/trees/{root_tree}?recursive=1", token)
    if t.get("truncated"):
        print("tree truncated"); sys.exit(1)
    for e in t["tree"]:
        if e["type"] == "blob":
            flat[e["path"]] = (e["sha"], "blob")

    # deletes
    for d in deletes:
        for p in list(flat):
            if p == d or p.startswith(d + "/"):
                del flat[p]

    # adds
    for repo_path, local in adds.items():
        flat[repo_path] = (blob(token, owner, repo, local), "blob")
        print("  blob:", repo_path)

    # rebuild tree bottom-up
    def build(prefix):
        entries, subdirs, blobs = [], set(), []
        for p, (sha, typ) in flat.items():
            if prefix:
                if not p.startswith(prefix + "/"):
                    continue
                rel = p[len(prefix)+1:]
            else:
                rel = p
            if "/" in rel:
                subdirs.add(rel.split("/")[0])
            else:
                blobs.append((rel, sha, typ))
        for d in sorted(subdirs):
            child = prefix + "/" + d if prefix else d
            cs = build(child)
            if cs:
                entries.append({"path": d, "mode": "040000", "type": "tree", "sha": cs})
        for name, sha, typ in sorted(blobs):
            entries.append({"path": name, "mode": "100644", "type": "blob", "sha": sha})
        if not entries:
            return None
        return api("POST", f"https://api.github.com/repos/{owner}/{repo}/git/trees", token,
                   {"tree": entries})["sha"]

    new_root = build("")
    nc = api("POST", f"https://api.github.com/repos/{owner}/{repo}/git/commits", token,
             {"message": msg, "tree": new_root, "parents": [head]})
    api("PATCH", f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/main", token,
        {"sha": nc["sha"], "force": False})
    print("UPDATED ->", nc["sha"][:10])

if __name__ == "__main__":
    main()
