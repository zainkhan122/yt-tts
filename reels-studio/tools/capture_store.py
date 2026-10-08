#!/usr/bin/env python3
"""Capture packs live in ONE GitHub Release ("capture-packs"), not in git (images/clips are MBs each).

  capture_store.py push <id> [<id> ...]     captures/<id>/ -> release asset <id>.tar (replaces an older one)
  capture_store.py pull <id>                release asset -> captures/<id>/ (skips if already present)
  capture_store.py pull-for <brief.json>    pull whatever capture pack the brief references (used by the cloud render)
  capture_store.py list                     packs in the store

Token: lib/secrets.gh_token() (env GH_TOKEN in GitHub Actions). Never printed.
"""
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
TAG = "capture-packs"


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
    if st == 200:
        return rel
    st, rel = call("POST", f"{API}/releases", {"tag_name": TAG, "target_commitish": "main", "name": "Capture packs (reels-studio)",
                                               "body": "Own page captures + makers' official media used by the video briefs. "
                                                       "Managed by reels-studio/tools/capture_store.py.", "prerelease": True})
    if st >= 300:
        raise SystemExit(f"cannot create release {TAG} ({st}): {rel.get('message')}")
    return rel


def push(ids):
    rel = release()
    have = {a["name"]: a for a in rel.get("assets", [])}
    for cid in ids:
        src = ROOT / "captures" / cid
        if not (src / "manifest.json").exists():
            raise SystemExit(f"no capture pack at {src}")
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tf:
            tf.add(src, arcname=cid)
        name = f"{cid}.tar"
        if name in have:
            call("DELETE", have[name]["url"])
        up = rel["upload_url"].split("{")[0] + "?name=" + urllib.parse.quote(name)
        st, asset = call("POST", up, raw=buf.getvalue(), headers={"Content-Type": "application/x-tar"})
        if st >= 300:
            raise SystemExit(f"upload failed for {name} ({st}): {asset.get('message')}")
        print(f"pushed {name} ({len(buf.getvalue()) / 1e6:.1f} MB)")


def pull(cid):
    dst = ROOT / "captures" / cid
    if (dst / "manifest.json").exists():
        print(f"captures/{cid} already present")
        return
    rel = release()
    asset = next((a for a in rel.get("assets", []) if a["name"] == f"{cid}.tar"), None)
    if not asset:
        raise SystemExit(f"capture pack {cid}.tar is not in the store (push it first)")
    st, blob = call("GET", asset["url"], accept="application/octet-stream")
    if st >= 300:
        raise SystemExit(f"download failed ({st})")
    (ROOT / "captures").mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r") as tf:
        tf.extractall(ROOT / "captures", filter="data")
    print(f"pulled captures/{cid} ({len(blob) / 1e6:.1f} MB)")


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
        b = json.loads(Path(args[0]).read_text())
        if b.get("capture"):
            pull(Path(b["capture"]).name)
        else:
            print("brief has no capture pack")
    elif cmd == "list":
        for a in release().get("assets", []):
            print(f"{a['name']:40s} {a['size'] / 1e6:6.1f} MB  {a['updated_at'][:10]}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
