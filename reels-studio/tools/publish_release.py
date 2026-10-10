#!/usr/bin/env python3
"""
Publish finished videos to a GitHub Release (permanent storage outside git history and the workspace).

  python3 tools/publish_release.py --tag renders-2026-10-08 --kit renders/<id> [--kit renders/<id2>]
      -> <id>.mp4 + <id>-kit.zip (post.md, seo.md, captions.srt, cover.jpg, contact.jpg, manifest.json, voiceover.mp3)
  python3 tools/publish_release.py --tag <tag> [--replace] file1 file2 ...     (any files)
  python3 tools/publish_release.py --list                                       (all render releases)

Assets with the same name are skipped unless --replace (kits always replace: same download link, new file).
Token: lib/secrets.gh_token() (env GH_TOKEN in GitHub Actions); never printed or committed.
"""
import argparse
import hashlib
import io
import json
import mimetypes
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

OWNER_REPO = "zainkhan122/yt-tts"
ROOT = Path(__file__).resolve().parent.parent
API = f"https://api.github.com/repos/{OWNER_REPO}"
KIT_FILES = ("post.md", "seo.md", "captions.srt", "cover.jpg", "contact.jpg", "manifest.json", "voiceover.mp3")


def tok():
    sys.path.insert(0, str(ROOT))
    from lib.secrets import gh_token
    t = gh_token() or ""
    if not t:
        raise SystemExit("no token: export GH_TOKEN (cloud) or keep ~/.config/reels-studio/gh_token (sandbox)")
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
    st, rel = call("POST", f"{API}/releases", {"tag_name": tag, "target_commitish": "main", "name": (f"Reels Studio renders: {tag}" if tag.startswith("renders-") else f"Reels Studio: {tag}"),
                                               "body": "Rendered by reels-studio. Each video = <id>.mp4 + <id>-kit.zip "
                                                       "(titles/captions/hashtags per platform, subtitles, cover)."})
    if st in (409, 422):
        # Parallel cloud renders can race to create the same dated Release.
        retry_status, existing = call("GET", f"{API}/releases/tags/{urllib.parse.quote(tag)}")
        if retry_status == 200:
            return existing
    if st >= 300:
        raise SystemExit(f"cannot create release ({st}): {rel.get('message')}. Token needs Contents: Read and write.")
    return rel


def upload(rel, name, payload, replace):
    have = {x["name"]: x for x in rel.get("assets", [])}
    if name in have:
        if not replace:
            print(f"  = {name} (already on release)")
            return have[name]["browser_download_url"]
        # Finished render assets are immutable: queues pin their IDs/digests.
        # Re-render into a fresh date/revision tag instead of breaking in-flight media.
        if rel.get("tag_name", "").startswith(("renders-", "long-renders-")):
            digest = "sha256:" + hashlib.sha256(payload).hexdigest()
            if have[name].get("digest") == digest:
                print(f"  = {name} (identical immutable asset)")
                return have[name]["browser_download_url"]
            raise SystemExit(f"Refusing to replace immutable render asset {name}. Use a fresh release tag, e.g. {rel['tag_name']}-r2. Existing queued URLs/QA pins must stay valid.")
        st, _ = call("DELETE", have[name]["url"])
        if st >= 300:
            raise SystemExit(f"could not delete old {name} ({st})")
    up = rel["upload_url"].split("{")[0] + "?name=" + urllib.parse.quote(name)
    st, asset = call("POST", up, raw=payload, headers={"Content-Type": mimetypes.guess_type(name)[0] or "application/octet-stream"})
    if st >= 300:
        raise SystemExit(f"upload failed for {name} ({st}): {asset.get('message')}")
    print(f"  + {name} ({len(payload) / 1e6:.1f} MB)")
    return asset["browser_download_url"]


def kit_zip(d):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in KIT_FILES:
            if (d / f).exists():
                z.write(d / f, f"{d.name}/{f}")
    return buf.getvalue()


def list_renders():
    page, rows = 1, []
    while True:
        st, rels = call("GET", f"{API}/releases?per_page=50&page={page}")
        if st != 200 or not rels:
            break
        rows += [r for r in rels if r["tag_name"].startswith("renders-")]
        page += 1
    for r in sorted(rows, key=lambda r: r["tag_name"], reverse=True):
        print(f"\n{r['tag_name']}  {r['html_url']}")
        for a in sorted(r.get("assets", []), key=lambda a: a["name"]):
            print(f"  {a['name']:44s} {a['size'] / 1e6:6.1f} MB  {a['browser_download_url']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag")
    ap.add_argument("--kit", action="append", default=[], help="renders/<id> folder -> <id>.mp4 + <id>-kit.zip")
    ap.add_argument("--replace", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    if a.list:
        return list_renders()
    if not a.tag:
        raise SystemExit("--tag is required")
    rel = release(a.tag)
    for d in map(Path, a.kit):
        mp4 = d / f"{d.name}.mp4"
        if not mp4.exists():
            raise SystemExit(f"missing {mp4}")
        print(upload(rel, mp4.name, mp4.read_bytes(), True))
        print(upload(rel, f"{d.name}-kit.zip", kit_zip(d), True))
        st, rel = call("GET", f"{API}/releases/{rel['id']}")  # refresh asset list
    for f in map(Path, a.files):
        name = f.name
        if f.parent.parent.name == "renders" and not name.startswith(f.parent.name):
            name = f"{f.parent.name}-{name}"  # renders/<id>/cover.jpg -> <id>-cover.jpg
        print(upload(rel, name, f.read_bytes(), a.replace))
    print(f"release: {rel.get('html_url')}")


if __name__ == "__main__":
    main()
