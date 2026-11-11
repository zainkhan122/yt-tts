#!/usr/bin/env python3
"""Reviewed cover packs live in the same GitHub Release as capture packs, not in git.

Why: `covers/` is gitignored (the media belongs to the capture pack), but the renderer
now fails closed unless `covers/<id>/selection.json` + `cover-selected.jpg` exist and
hash-match. Before this store, a cover could be reviewed locally and then make every
cloud render of that brief fail closed - the exact cover contract, applied in the wrong
place. The bytes the panel picked are the bytes that ship:

  cover_store.py push <id> [<id> ...]     covers/<id>/ -> release asset <id>-covers.tar
  cover_store.py pull <id>                release asset -> covers/<id>/ (skips if present)
  cover_store.py pull-for <brief.json>    pull the cover pack the brief needs
  cover_store.py list                     cover packs in the store
  cover_store.py verify <id>              selection.json vs cover-selected.jpg hash

Token: lib/secrets.gh_token() (env GH_TOKEN in GitHub Actions). Never printed.
"""
import hashlib
import io
import json
import sys
import tarfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib.secrets import gh_token  # noqa: E402

REPO = "zainkhan122/yt-tts"
API = f"https://api.github.com/repos/{REPO}"
TAG = "capture-packs"  # one release for all media assets (captures + covers)


def call(method, url, data=None, raw=None, headers=None, accept="application/vnd.github+json"):
    h = {"Authorization": f"Bearer {gh_token()}", "Accept": accept, "X-GitHub-Api-Version": "2022-11-28",
         "User-Agent": "reels-studio", **(headers or {})}
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    if data is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            payload = r.read()
            return r.status, (payload if accept == "application/octet-stream" else json.loads(payload or b"{}"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def release():
    st, rel = call("GET", f"{API}/releases/tags/{TAG}")
    if st == 404:
        st, rel = call("POST", f"{API}/releases", {"tag_name": TAG, "target_commitish": "main",
                                                   "name": "capture-packs",
                                                   "body": "Product media packs (captures + reviewed covers)."})
    if st >= 300:
        raise SystemExit(f"release lookup failed ({st}): {rel.get('message')}")
    return rel


def verify_dir(cid):
    d = ROOT / "covers" / cid
    sel, img = d / "selection.json", d / "cover-selected.jpg"
    if not sel.exists() or not img.exists():
        raise SystemExit(f"covers/{cid}: selection.json and cover-selected.jpg are both required "
                         f"(run tools/cover_lab.py briefs/{cid}.json --apply)")
    data = json.loads(sel.read_text())
    if data.get("brief") != cid:
        raise SystemExit(f"covers/{cid}/selection.json belongs to {data.get('brief')!r}")
    digest = hashlib.sha256(img.read_bytes()).hexdigest()
    if digest != data.get("sha256"):
        raise SystemExit(f"covers/{cid}/cover-selected.jpg changed after selection; re-run --apply")
    return data


def push(ids):
    rel = release()
    have = {a["name"]: a for a in rel.get("assets", [])}
    for cid in ids:
        verify_dir(cid)
        src = ROOT / "covers" / cid
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tf:
            tf.add(src, arcname=f"{cid}")
        name = f"{cid}-covers.tar"
        if name in have:
            call("DELETE", have[name]["url"])
        up = rel["upload_url"].split("{")[0] + "?name=" + urllib.parse.quote(name)
        st, asset = call("POST", up, raw=buf.getvalue(), headers={"Content-Type": "application/x-tar"})
        if st >= 300:
            raise SystemExit(f"upload failed for {name} ({st}): {asset.get('message')}")
        print(f"pushed {name} ({len(buf.getvalue()) / 1e3:.0f} KB)")


def pull(cid):
    dst = ROOT / "covers" / cid
    if (dst / "selection.json").exists() and (dst / "cover-selected.jpg").exists():
        print(f"covers/{cid} already present")
        return
    rel = release()
    asset = next((a for a in rel.get("assets", []) if a["name"] == f"{cid}-covers.tar"), None)
    if not asset:
        raise SystemExit(f"cover pack {cid}-covers.tar is not in the store; run tools/cover_lab.py "
                         f"briefs/{cid}.json --apply and cover_store.py push {cid}")
    st, blob = call("GET", asset["url"], accept="application/octet-stream")
    if st >= 300:
        raise SystemExit(f"download failed ({st})")
    (ROOT / "covers").mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r") as tf:
        for member in tf.getmembers():  # the tar stores the pack as "covers/<id>/"
            if member.name.split("/")[0] == "covers":
                member.name = "/".join(member.name.split("/")[1:])
            tf.extract(member, ROOT / "covers", filter="data")
    print(f"pulled covers/{cid} ({len(blob) / 1e3:.0f} KB)")
    verify_dir(cid)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "push":
        push(args)
    elif cmd == "pull":
        for cid in args:
            pull(cid)
    elif cmd == "pull-for":
        brief = json.loads(Path(args[0]).read_text())
        if (brief.get("treatment") or {}).get("archetype"):
            pull(brief["id"])
        else:
            print(f"{brief.get('id')}: legacy brief without a treatment, no cover pack needed")
    elif cmd == "verify":
        for cid in args:
            print(json.dumps(verify_dir(cid), indent=1)[:400])
    elif cmd == "list":
        rel = release()
        names = sorted(a["name"] for a in rel.get("assets", []) if a["name"].endswith("-covers.tar"))
        print("\n".join(f"{n:40s} {next(a['size'] for a in rel['assets'] if a['name'] == n) / 1e3:8.0f} KB"
                        for n in names) or "no cover packs")
    else:
        raise SystemExit(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
