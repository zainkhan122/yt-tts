#!/usr/bin/env python3
"""repo_squash.py — purge history blobs via the API (orphan root commit, no clone).
Creates a new root commit containing ONLY the cleaned tree; old blobs become
unreachable and GitHub GC reclaims them.
Usage: python3 tools/repo_squash.py "commit message" --delete prefix1 prefix2 ... --add repo_path local ...
"""
import base64, json, os, sys, urllib.request, urllib.error

def api(method, url, token, data=None, timeout=600):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "vault-squash")
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

def main():
    token = open(os.path.expanduser("~/secrets/github_pat.txt")).read().strip()
    OWNER, REPO = "zainkhan122", "yt-tts"
    msg = sys.argv[1]
    deletes, adds = [], {}
    args = sys.argv[2:]
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

    ref = api("GET", f"https://api.github.com/repos/{OWNER}/{REPO}/git/ref/heads/main", token)
    head = ref["object"]["sha"]
    commit = api("GET", f"https://api.github.com/repos/{OWNER}/{REPO}/git/commits/{head}", token)
    tree_sha = commit["tree"]["sha"]
    t = api("GET", f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/{tree_sha}?recursive=1", token)
    if t.get("truncated"):
        print("tree truncated"); sys.exit(1)
    flat = {e["path"]: e["sha"] for e in t["tree"] if e["type"] == "blob"}

    for d in deletes:
        for p in list(flat):
            if p == d or p.startswith(d + "/"):
                del flat[p]

    def blob(local):
        b = base64.b64encode(open(local, "rb").read()).decode()
        return api("POST", f"https://api.github.com/repos/{OWNER}/{REPO}/git/blobs", token,
                   {"content": b, "encoding": "base64"})["sha"]
    for repo_path, local in adds.items():
        flat[repo_path] = blob(local)
        print("  blob:", repo_path)

    def build(prefix):
        entries, subdirs, blobs = [], set(), []
        for p, sha in flat.items():
            if prefix:
                if not p.startswith(prefix + "/"):
                    continue
                rel = p[len(prefix)+1:]
            else:
                rel = p
            if "/" in rel:
                subdirs.add(rel.split("/")[0])
            else:
                blobs.append((rel, sha))
        for d in sorted(subdirs):
            child = prefix + "/" + d if prefix else d
            cs = build(child)
            if cs:
                entries.append({"path": d, "mode": "040000", "type": "tree", "sha": cs})
        for name, sha in sorted(blobs):
            entries.append({"path": name, "mode": "100644", "type": "blob", "sha": sha})
        if not entries:
            return None
        return api("POST", f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees", token,
                   {"tree": entries})["sha"]

    new_tree = build("")
    nc = api("POST", f"https://api.github.com/repos/{OWNER}/{REPO}/git/commits", token,
             {"message": msg, "tree": new_tree, "parents": []})   # ROOT commit (orphan)
    api("PATCH", f"https://api.github.com/repos/{OWNER}/{REPO}/git/refs/heads/main", token,
        {"sha": nc["sha"], "force": True})
    print("SQUASHED ->", nc["sha"][:10])

if __name__ == "__main__":
    main()
