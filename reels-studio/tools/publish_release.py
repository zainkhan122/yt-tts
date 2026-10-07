#!/usr/bin/env python3
"""
Upload rendered videos to a GitHub Release (permanent storage outside git history and outside the
128 MB workspace) and record them in RENDERS.md. Idempotent: assets already on the release are skipped.

  python3 tools/publish_release.py --tag renders-2026-10-07 renders/*/*.mp4
Token: env GH_TOKEN or /var/tmp/gh/token (session only; never printed or committed).
"""
import argparse
import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OWNER_REPO = "zainkhan122/yt-tts"
ROOT = Path(__file__).resolve().parent.parent
API = f"https://api.github.com/repos/{OWNER_REPO}"


def tok():
    t = os.environ.get("GH_TOKEN") or (Path("/var/tmp/gh/token").read_text().strip() if Path("/var/tmp/gh/token").exists() else "")
    if not t:
        raise SystemExit("no token: export GH_TOKEN or write /var/tmp/gh/token")
    return t


def call(method, url, data=None, headers=None, raw=None):
    h = {"Authorization": f"Bearer {tok()}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", **(headers or {})}
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    if data is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def release(tag):
    st, rel = call("GET", f"{API}/releases/tags/{urllib.parse.quote(tag)}")
    if st == 200:
        return rel
    st, rel = call("POST", f"{API}/releases", {"tag_name": tag, "target_commitish": "main", "name": f"Reels Studio renders: {tag}",
                                               "body": "Rendered by reels-studio (HyperFrames + free tools). Index: reels-studio/RENDERS.md"})
    if st >= 300:
        raise SystemExit(f"cannot create release ({st}): {rel.get('message')}. Fine-grained tokens need Contents: Read and write.")
    return rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    rel = release(a.tag)
    have = {x["name"]: x for x in rel.get("assets", [])}
    rows = []
    for f in map(Path, a.files):
        name = f.name
        if name in have:
            print(f"  = {name} (already on release)")
            rows.append((name, have[name]["size"], have[name]["browser_download_url"]))
            continue
        up = rel["upload_url"].split("{")[0] + "?name=" + urllib.parse.quote(name)
        st, asset = call("POST", up, raw=f.read_bytes(), headers={"Content-Type": mimetypes.guess_type(name)[0] or "application/octet-stream"})
        if st >= 300:
            raise SystemExit(f"upload failed for {name} ({st}): {asset.get('message')}")
        print(f"  + {name} ({f.stat().st_size / 1e6:.1f} MB)")
        rows.append((name, asset["size"], asset["browser_download_url"]))
    idx = ROOT / "RENDERS.md"
    text = idx.read_text() if idx.exists() else ("# Renders (stored in GitHub Releases, not in git)\n\n"
                                                 "| File | Size | Release | Download |\n|---|---|---|---|\n")
    for name, size, url in rows:
        if url not in text:
            text += f"| `{name}` | {size / 1e6:.1f} MB | `{a.tag}` | [download]({url}) |\n"
    idx.write_text(text)
    print(f"release: {rel.get('html_url')}  ({len(rows)} files) -> RENDERS.md updated")


if __name__ == "__main__":
    main()
