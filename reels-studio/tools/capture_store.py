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
import os
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib.secrets import gh_token  # noqa: E402

REPO = "zainkhan122/yt-tts"
API = f"https://api.github.com/repos/{REPO}"
TAG = "capture-packs"
MAX_CAPTURE_TAR_BYTES = 256_000_000
MAX_CAPTURE_EXPANDED_BYTES = 512_000_000
MAX_CAPTURE_TAR_ENTRIES = 2000
CAPTURE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
SIGNED_ASSET_HOSTS = {"release-assets.githubusercontent.com", "objects.githubusercontent.com"}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _require_capture_id(cid):
    if not isinstance(cid, str) or not CAPTURE_ID_RE.fullmatch(cid) or cid in {".", ".."}:
        raise SystemExit(f"unsafe capture ID: {cid!r}")
    return cid


def _validate_api_url(url):
    parsed = urllib.parse.urlsplit(url)
    decoded_path = urllib.parse.unquote(parsed.path)
    try:
        port = parsed.port
    except ValueError as exc:
        raise SystemExit("refusing a malformed GitHub API URL") from exc
    allowed_hosts = {"api.github.com", "uploads.github.com"}
    prefix = f"/repos/{REPO}/"
    if (parsed.scheme != "https" or parsed.hostname not in allowed_hosts or parsed.username is not None
            or parsed.password is not None or port is not None or parsed.fragment
            or not decoded_path.startswith(prefix)
            or any(part in {".", ".."} for part in PurePosixPath(decoded_path).parts)):
        raise SystemExit("refusing a GitHub API URL outside the configured repository")


def call(method, url, data=None, raw=None, headers=None, accept="application/vnd.github+json", max_bytes=None):
    _validate_api_url(url)
    h = {"Authorization": f"Bearer {gh_token()}", "Accept": accept, "X-GitHub-Api-Version": "2022-11-28",
         "User-Agent": "reels-studio", **(headers or {})}
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    if data is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        opener = urllib.request.build_opener(_NoRedirect())
        with opener.open(req, timeout=600) as r:
            if max_bytes is not None:
                length = r.headers.get("Content-Length")
                if length and int(length) > max_bytes:
                    raise SystemExit(f"GitHub response exceeds the configured limit ({length} bytes)")
                payload = r.read(max_bytes + 1)
                if len(payload) > max_bytes:
                    raise SystemExit(f"GitHub response exceeds the configured limit ({len(payload)} bytes)")
            else:
                payload = r.read()
            return r.status, (payload if accept == "application/octet-stream" else json.loads(payload or b"{}"))
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            return e.code, {"location": e.headers.get("Location", "")}
        return e.code, json.loads(e.read() or b"{}")


def _download_signed_asset(url, max_bytes):
    parsed = urllib.parse.urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise SystemExit("capture asset redirect is malformed") from exc
    if (parsed.scheme != "https" or parsed.hostname not in SIGNED_ASSET_HOSTS
            or parsed.username is not None or parsed.password is not None or port is not None
            or not parsed.query or parsed.fragment):
        raise SystemExit("capture asset redirect is not a trusted signed GitHub download URL")
    req = urllib.request.Request(url, headers={"Accept": "application/octet-stream", "User-Agent": "reels-studio"})
    try:
        opener = urllib.request.build_opener(_NoRedirect())
        with opener.open(req, timeout=600) as r:
            length = r.headers.get("Content-Length")
            if length and int(length) > max_bytes:
                raise SystemExit(f"capture tar exceeds the size limit ({length} bytes)")
            blob = r.read(max_bytes + 1)
            if len(blob) > max_bytes:
                raise SystemExit(f"capture tar exceeds the size limit ({len(blob)} bytes)")
            return blob
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"capture asset download failed without authentication ({exc.code})") from exc


def release(*, create=False):
    """Read the capture-pack store; only an explicit push command may create its prerelease."""
    st, rel = call("GET", f"{API}/releases/tags/{TAG}")
    if st == 200:
        return rel
    if st != 404:
        raise SystemExit(f"cannot read capture-pack store {TAG} ({st}): {rel.get('message')}")
    if not create:
        raise SystemExit(f"capture-pack store {TAG} is missing; read-only pull will not create a public Release")
    st, rel = call("POST", f"{API}/releases", {"tag_name": TAG, "target_commitish": "main", "name": "Capture packs (reels-studio)",
                                               "body": "Own page captures + makers' official media used by the video briefs. "
                                                       "Managed by reels-studio/tools/capture_store.py.", "prerelease": True})
    if st >= 300:
        raise SystemExit(f"cannot create release {TAG} ({st}): {rel.get('message')}")
    return rel


def push(ids):
    ids = [_require_capture_id(cid) for cid in ids]
    rel = release(create=True)
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


def _safe_archive_members(tf, cid):
    members = tf.getmembers()
    if len(members) > MAX_CAPTURE_TAR_ENTRIES:
        raise SystemExit(f"capture tar contains too many entries ({len(members)})")
    seen, expanded = set(), 0
    manifest_found = False
    for member in members:
        name = member.name
        rel = PurePosixPath(name)
        if (not name or chr(92) in name or rel.is_absolute() or not rel.parts
                or rel.parts[0] != cid or any(part in {".", ".."} for part in rel.parts)):
            raise SystemExit(f"unsafe capture tar path: {name!r}")
        if member.issym() or member.islnk() or not (member.isdir() or member.isfile()):
            raise SystemExit(f"unsupported link/device in capture tar: {name!r}")
        normalized = rel.as_posix()
        if normalized in seen:
            raise SystemExit(f"duplicate capture tar path: {name!r}")
        seen.add(normalized)
        if member.isfile():
            if member.size < 0:
                raise SystemExit(f"invalid capture tar file size: {name!r}")
            expanded += member.size
            if expanded > MAX_CAPTURE_EXPANDED_BYTES:
                raise SystemExit(f"capture tar expands beyond the size limit ({expanded} bytes)")
        if normalized == f"{cid}/manifest.json" and member.isfile():
            manifest_found = True
    if not manifest_found:
        raise SystemExit("capture tar has no regular manifest.json")
    return members, expanded


def pull(cid):
    cid = _require_capture_id(cid)
    captures = ROOT / "captures"
    if captures.is_symlink():
        raise SystemExit(f"refusing symlink capture directory: {captures}")
    captures.mkdir(exist_ok=True)
    dst = captures / cid
    if dst.is_symlink():
        raise SystemExit(f"refusing symlink capture pack: {dst}")
    if dst.exists():
        manifest = dst / "manifest.json"
        if manifest.is_symlink():
            raise SystemExit(f"refusing symlink capture manifest: {manifest}")
        if manifest.is_file():
            print(f"captures/{cid} already present (the production asset gate will re-verify its digests)")
            return
        raise SystemExit(f"capture directory is incomplete; refusing to overwrite: {dst}")

    rel = release()
    asset = next((a for a in rel.get("assets", []) if a.get("name") == f"{cid}.tar"), None)
    if not asset:
        raise SystemExit(f"capture pack {cid}.tar is not in the store (push it first)")
    st, blob = call("GET", asset.get("url", ""), accept="application/octet-stream", max_bytes=MAX_CAPTURE_TAR_BYTES)
    if st in (301, 302, 303, 307, 308) and isinstance(blob, dict) and blob.get("location"):
        blob = _download_signed_asset(blob["location"], MAX_CAPTURE_TAR_BYTES)
        st = 200
    if st != 200 or not isinstance(blob, bytes):
        raise SystemExit(f"capture download failed ({st})")
    if not blob or len(blob) > MAX_CAPTURE_TAR_BYTES:
        raise SystemExit(f"capture tar size is invalid or exceeds the limit ({len(blob)} bytes)")

    staging = Path(tempfile.mkdtemp(prefix=f".{cid}.pull-", dir=captures))
    try:
        try:
            with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tf:
                members, expanded = _safe_archive_members(tf, cid)
                tf.extractall(staging, members=members, filter="data")
        except (tarfile.TarError, OSError) as exc:
            raise SystemExit(f"capture tar is invalid or could not be extracted: {exc}") from exc
        extracted = staging / cid
        manifest = extracted / "manifest.json"
        if extracted.is_symlink() or manifest.is_symlink() or not manifest.is_file():
            raise SystemExit("extracted capture pack is incomplete or unsafe")
        if dst.exists() or dst.is_symlink():
            raise SystemExit(f"capture destination appeared during download; refusing overwrite: {dst}")
        os.replace(extracted, dst)
    finally:
        if staging.exists() and not staging.is_symlink():
            shutil.rmtree(staging)
    print(f"pulled captures/{cid} ({len(blob) / 1e6:.1f} MB; {expanded / 1e6:.1f} MB expanded)")


def pull_for(brief_arg):
    brief_path = Path(brief_arg)
    if not brief_path.is_absolute():
        brief_path = ROOT.parent / brief_path
    briefs_root = (ROOT / "briefs").resolve()
    if brief_path.is_symlink() or not brief_path.is_file():
        raise SystemExit(f"brief is missing or unsafe: {brief_path}")
    try:
        resolved = brief_path.resolve(strict=True)
        resolved.relative_to(briefs_root)
        brief = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"brief is unreadable or outside briefs/: {brief_path}: {exc}") from exc
    if not isinstance(brief, dict):
        raise SystemExit(f"brief must be a JSON object: {brief_path}")
    capture = brief.get("capture")
    if not capture:
        print("brief has no capture pack")
        return
    if not isinstance(capture, str) or chr(92) in capture:
        raise SystemExit(f"unsafe capture path in {brief_path}")
    parts = PurePosixPath(capture).parts
    if PurePosixPath(capture).is_absolute() or len(parts) != 2 or parts[0] != "captures":
        raise SystemExit(f"capture must be a captures/<capture-id> path in {brief_path}")
    pull(_require_capture_id(parts[1]))


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
        if len(args) != 1:
            raise SystemExit("pull-for needs exactly one brief path")
        pull_for(args[0])
    elif cmd == "list":
        for a in release().get("assets", []):
            print(f"{a['name']:40s} {a['size'] / 1e6:6.1f} MB  {a['updated_at'][:10]}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
