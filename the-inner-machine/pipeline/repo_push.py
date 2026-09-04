#!/usr/bin/env python3
"""Push THIS folder to GitHub as a SINGLE commit via the Git Data API.

No clone. Preserves all other repo content (vault/, finance/, ...): it reads the
current branch tip, adds only this folder's files on top of the existing tree, and
fast-forwards the branch. Excludes large/regenerable files (*.mp4) and scratch.

Auth: token is read from env GITHUB_PAT (fallback: /tmp/pat). It is NEVER hardcoded
and NEVER written to the workspace. If access is lost, stop and re-ask for it.

Usage:
  GITHUB_PAT=... python3 repo_push.py [--repo OWNER/NAME] [--branch main] [--dry-run]
"""
import os, sys, json, base64, argparse, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                 # this channel folder
FOLDER = os.path.basename(ROOT)              # e.g. "the-inner-machine"
API = "https://api.github.com"
EXCLUDE_DIRS = {".work", "__pycache__", ".git"}
EXCLUDE_EXT = {".mp4", ".part", ".jpg", ".jpeg", ".png"}   # media is opt-in; video is never pushed
INCLUDE_MEDIA = False


def token():
    t = os.environ.get("GITHUB_PAT")
    if not t and os.path.exists("/tmp/pat"):
        t = open("/tmp/pat").read().strip()
    if not t:
        sys.exit("No token. Set GITHUB_PAT in the environment (do NOT hardcode it).")
    return t


def req(method, path, tok, body=None):
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", "Bearer " + tok)
    r.add_header("Accept", "application/vnd.github+json")
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"API {method} {path} -> {e.code}: {e.read().decode()[:400]}")


def files():
    out = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in EXCLUDE_DIRS]
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in EXCLUDE_EXT and not (INCLUDE_MEDIA and os.path.splitext(fn)[1].lower() in {'.jpg','.jpeg','.png'}):
                continue
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            out.append((f"{FOLDER}/{rel}", full))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="zainkhan122/yt-tts")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--include-media", action="store_true", help="include active jpg/jpeg/png assets; never include video")
    ap.add_argument("--message", default=f"Add {FOLDER}/ standalone pipeline (separate from vault/)")
    a = ap.parse_args()
    global INCLUDE_MEDIA
    INCLUDE_MEDIA = a.include_media
    fl = files()
    print(f"{a.repo} @ {a.branch}: {len(fl)} files under {FOLDER}/")
    for p, _ in fl:
        print("  +", p)
    if a.dry_run:
        return
    tok = token()
    base_commit = req("GET", f"/repos/{a.repo}/git/ref/heads/{a.branch}", tok)["object"]["sha"]
    base_tree = req("GET", f"/repos/{a.repo}/git/commits/{base_commit}", tok)["tree"]["sha"]
    tree = []
    for path, full in fl:
        b64 = base64.b64encode(open(full, "rb").read()).decode()
        sha = req("POST", f"/repos/{a.repo}/git/blobs", tok,
                  {"content": b64, "encoding": "base64"})["sha"]
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": sha})
        print("  blob", path, sha[:8])
        time.sleep(0.3)  # stay well under secondary rate limits on large payloads
    new_tree = req("POST", f"/repos/{a.repo}/git/trees", tok,
                   {"base_tree": base_tree, "tree": tree})["sha"]
    commit = req("POST", f"/repos/{a.repo}/git/commits", tok,
                 {"message": a.message, "tree": new_tree, "parents": [base_commit]})["sha"]
    req("PATCH", f"/repos/{a.repo}/git/refs/heads/{a.branch}", tok,
        {"sha": commit, "force": False})
    print("PUSHED", commit[:10], "->",
          f"https://github.com/{a.repo}/tree/{a.branch}/{FOLDER}")


if __name__ == "__main__":
    main()
