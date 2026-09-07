#!/usr/bin/env python3
"""YouTube publish — gated. Never uploads unless every lock is true.

  python3 tools/youtube_publish.py --pack EP_DIR --channel UC… -o approval.json
  python3 tools/youtube_publish.py --auth --channel UC…
  python3 tools/youtube_publish.py approval.json --dry-run
  python3 tools/youtube_publish.py approval.json --upload
  python3 tools/youtube_publish.py --self-test

Safety (all required for --upload):
  - approved is JSON boolean true (not \"true\", not 1)
  - channel_id is a UC… id on the allow-list (youtube_channels.json)
  - video file exists and is a non-empty mp4
  - thumbnail exists (jpg/png) and is a real image
  - metadata has title + description; longs ≤60, shorts ≤50; shorts need #Shorts
  - OAuth 2.0 token for THAT channel_id, stored outside the repo
  - argv contains --upload (dry-run never writes)
  - visibility is private or unlisted (default private). Public is refused.

Never asks for a Gmail password. Never prints tokens.
"""
from __future__ import annotations

import argparse, hashlib, json, os, re, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANNELS_FILE = ROOT / "youtube_channels.json"
VISIBILITY_OK = frozenset({"private", "unlisted"})
CHANNEL_ID_RE = re.compile(r"^UC[\w-]{22}$")
LEGAL = (
    "not investment advice", "not financial advice", "not financial, tax",
    "this is education, not", "education, not investment", "education, not advice",
    "education only", "not a recommendation to buy",
)
SCOPES = (
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly",
)


# ── paths (tokens NEVER in the repo) ─────────────────────────────────────────

def config_dir() -> Path:
    override = os.environ.get("TPR_YOUTUBE_CONFIG")
    if override:
        p = Path(override).expanduser()
    else:
        p = Path.home() / ".config" / "the-public-record" / "youtube"
    p.mkdir(parents=True, mode=0o700, exist_ok=True)
    return p


def token_path(channel_id: str) -> Path:
    return config_dir() / "tokens" / f"{channel_id}.json"


def client_secret_path() -> Path | None:
    env = os.environ.get("TPR_YOUTUBE_CLIENT_SECRET")
    cands = []
    if env:
        cands.append(Path(env).expanduser())
    cands.append(config_dir() / "client_secret.json")
    cands.append(ROOT / "secrets" / "youtube_client_secret.json")
    for p in cands:
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def reports_dir() -> Path:
    d = config_dir() / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── channels allow-list ──────────────────────────────────────────────────────

def load_channels() -> list[dict]:
    if not CHANNELS_FILE.exists():
        sys.exit(f"MISSING {CHANNELS_FILE}")
    data = json.loads(CHANNELS_FILE.read_text(encoding="utf-8"))
    return list(data.get("channels") or [])


def allowlisted() -> dict[str, dict]:
    out = {}
    for ch in load_channels():
        cid = (ch.get("id") or "").strip()
        if CHANNEL_ID_RE.match(cid):
            out[cid] = ch
    return out


def channel_record(channel_id: str) -> dict:
    table = allowlisted()
    if channel_id not in table:
        known = ", ".join(sorted(table)) or "(none — paste UC… ids into youtube_channels.json)"
        sys.exit(f"BLOCK: channel_id {channel_id!r} is not on the allow-list. Known: {known}")
    return table[channel_id]


# ── metadata.md ──────────────────────────────────────────────────────────────

def parse_metadata(md_path: Path) -> dict:
    if not md_path.exists():
        sys.exit(f"BLOCK: missing {md_path}")
    text = md_path.read_text(encoding="utf-8")

    def section(name: str) -> str:
        m = re.search(rf"^## {re.escape(name)}\n(.*?)(?=\n## |\Z)", text, re.S | re.M)
        return (m.group(1).strip() if m else "")

    tm = re.search(r"^## TITLE.*?\*\*(.+?)\*\*", text, re.S | re.M)
    title = tm.group(1).strip() if tm else ""
    desc = section("DESCRIPTION")
    tags_raw = section("TAGS")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
    pin = section("PINNED COMMENT")
    kw = section("PRIMARY KEYWORD")
    parent = section("PARENT")
    shorts = "#shorts" in desc.lower() or bool(parent)
    return {
        "title": title,
        "description": desc,
        "tags": tags,
        "pinned_comment": pin,
        "keyword": kw,
        "shorts": shorts,
        "parent": parent,
        "raw_path": str(md_path),
    }


def find_video(d: Path) -> Path | None:
    named = d / f"{d.name}.mp4"
    if named.exists():
        return named
    mp4s = sorted(p for p in d.glob("*.mp4") if p.is_file())
    if len(mp4s) == 1:
        return mp4s[0]
    return None


def find_thumb(d: Path) -> Path | None:
    for name in ("thumbnail.jpg", "thumbnail.jpeg", "thumbnail.png"):
        p = d / name
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


# ── gates ────────────────────────────────────────────────────────────────────

class GateError(Exception):
    pass


def fail(msg: str) -> None:
    raise GateError("BLOCK: " + msg)


def check_image(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ImportError:
        fail("Pillow is required to inspect thumbnails (pip install pillow)")
    try:
        im = Image.open(path)
        im.load()
    except Exception as e:
        fail(f"thumbnail is not a readable image: {path} ({e})")
    w, h = im.size
    if w < 640 or h < 360:
        fail(f"thumbnail too small {w}x{h} (need at least 640x360)")
    if path.stat().st_size > 2_000_000:
        fail(f"thumbnail {path.stat().st_size} bytes > 2MB YouTube limit")
    return w, h


def check_video(path: Path) -> None:
    if path.suffix.lower() != ".mp4":
        fail(f"video must be .mp4, got {path.suffix}")
    if path.stat().st_size < 80_000:
        fail(f"video looks empty/tiny: {path} ({path.stat().st_size} bytes)")


def check_meta(item: dict) -> None:
    title = (item.get("title") or "").strip()
    desc = (item.get("description") or "").strip()
    shorts = bool(item.get("shorts"))
    if not title:
        fail("missing title")
    tmax = 50 if shorts else 100  # YouTube hard 100; our pack uses 60/50
    if len(title) > 100:
        fail(f"title {len(title)} > 100 (YouTube hard limit)")
    if shorts and len(title) > 50:
        fail(f"Shorts title {len(title)} > 50")
    if not shorts and len(title) > 60:
        fail(f"long title {len(title)} > 60 (channel pack rule)")
    if not desc:
        fail("missing description")
    low = desc.lower()
    if shorts:
        if "#shorts" not in low:
            fail("Shorts description missing #Shorts")
        for d in LEGAL:
            if d in low:
                fail(f"Shorts description contains legal phrase {d!r}")
    else:
        if not any(x in low for x in ("not financial", "not investment advice")):
            fail("long description missing education/not-advice disclaimer (last block)")


def load_approval(path: Path) -> dict:
    if not path.exists():
        fail(f"approval file missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"approval.json is not valid JSON: {e}")
    if not isinstance(data, dict):
        fail("approval.json must be an object")
    return data


def validate_approval(data: dict, *, for_upload: bool) -> list[dict]:
    """Return normalized items. Raises GateError."""
    if for_upload:
        if data.get("approved") is not True:
            fail("approved is not JSON boolean true. Set \"approved\": true after you have read the dry-run.")
    cid = (data.get("channel_id") or "").strip()
    if not CHANNEL_ID_RE.match(cid):
        fail(f"channel_id {cid!r} is not a YouTube channel id (UC + 22 chars)")
    vis = (data.get("visibility") or "private").strip().lower()
    if vis not in VISIBILITY_OK:
        fail(f"visibility {vis!r} refused. Allowed: private, unlisted. Public is never sent by this tool.")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        fail("approval.json has no items[]")
    out = []
    for i, raw in enumerate(items):
        if not isinstance(raw, dict):
            fail(f"items[{i}] is not an object")
        video = Path(raw.get("video") or "")
        thumb = Path(raw.get("thumbnail") or "")
        if not video.is_file():
            fail(f"items[{i}] video missing: {video}")
        if not thumb.is_file():
            fail(f"items[{i}] thumbnail missing: {thumb}")
        check_video(video)
        tw, th = check_image(thumb)
        item = {
            "kind": raw.get("kind") or ("shorts" if raw.get("shorts") else "long"),
            "shorts": bool(raw.get("shorts")),
            "video": video.resolve(),
            "thumbnail": thumb.resolve(),
            "title": (raw.get("title") or "").strip(),
            "description": (raw.get("description") or "").strip(),
            "tags": list(raw.get("tags") or []),
            "category_id": str(raw.get("category_id") or "27"),
            "language": raw.get("language") or "en",
            "pinned_comment": (raw.get("pinned_comment") or "").strip(),
            "made_for_kids": False,
            "contains_synthetic_media": True,
            "thumb_size": (tw, th),
            "video_bytes": video.stat().st_size,
            "sha256": sha256_head(video),
        }
        check_meta(item)
        out.append(item)
    # allow-list last so file/meta errors surface first
    ch = channel_record(cid)
    data["_channel"] = ch
    data["_visibility"] = vis
    return out


def sha256_head(path: Path, n: int = 1_048_576) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read(n))
        h.update(str(path.stat().st_size).encode())
    return h.hexdigest()[:16]


# ── pack ─────────────────────────────────────────────────────────────────────

def pack_dir(d: Path, shorts: bool | None = None) -> dict:
    d = d.resolve()
    meta = parse_metadata(d / "metadata.md")
    if shorts is True:
        meta["shorts"] = True
    video = find_video(d)
    thumb = find_thumb(d)
    if not video:
        fail(f"no final .mp4 in {d}")
    if not thumb:
        fail(f"no thumbnail.jpg in {d}")
    return {
        "kind": "shorts" if meta["shorts"] else "long",
        "shorts": meta["shorts"],
        "video": str(video),
        "thumbnail": str(thumb),
        "title": meta["title"],
        "description": meta["description"],
        "tags": meta["tags"],
        "category_id": "27",
        "language": "en",
        "pinned_comment": meta["pinned_comment"],
        "keyword": meta["keyword"],
        "parent": meta["parent"],
        "source_dir": str(d),
    }


def cmd_pack(ep: Path, channel_id: str, out: Path, include_shorts: bool) -> None:
    channel_record(channel_id)
    items = [pack_dir(ep)]
    if include_shorts:
        shorts_root = ep / "shorts"
        if shorts_root.is_dir():
            for sub in sorted(p for p in shorts_root.iterdir() if p.is_dir()):
                if find_video(sub) and (sub / "metadata.md").exists():
                    items.append(pack_dir(sub, shorts=True))
    doc = {
        "schema": "tpr.youtube.approval.v1",
        "approved": False,
        "channel_id": channel_id,
        "visibility": "private",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "episode": str(ep.resolve()),
        "items": items,
        "_read_me": "Read the dry-run. If it is the right channel, title, files: set approved to boolean true, then run with --upload. Default visibility is private.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {out}  items={len(items)}  approved=false  visibility=private")
    print("Next: python3 tools/youtube_publish.py", out, "--dry-run")


# ── OAuth ────────────────────────────────────────────────────────────────────

def load_creds(channel_id: str):
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        fail("OAuth libraries missing. pip install google-auth google-auth-oauthlib google-api-python-client")
    tp = token_path(channel_id)
    if not tp.exists():
        fail(f"no OAuth token for {channel_id}. Run: python3 tools/youtube_publish.py --auth --channel {channel_id}")
    creds = Credentials.from_authorized_user_file(str(tp), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_creds(channel_id, creds)
    if not creds or not creds.valid:
        fail("OAuth token invalid. Re-run --auth")
    return creds


def save_creds(channel_id: str, creds) -> None:
    tp = token_path(channel_id)
    tp.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    tp.write_text(creds.to_json())
    os.chmod(tp, 0o600)


def cmd_auth(channel_id: str) -> None:
    channel_record(channel_id)
    secret = client_secret_path()
    if not secret:
        sys.exit(
            "BLOCK: no OAuth client secret.\n"
            "  1. Google Cloud Console → APIs → YouTube Data API v3 → enable\n"
            "  2. Credentials → OAuth client (Desktop app)\n"
            "  3. Save the JSON to ~/.config/the-public-record/youtube/client_secret.json\n"
            "     (or secrets/youtube_client_secret.json — gitignored)\n"
            "Never put this file in git. This tool never asks for a Gmail password."
        )
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit("pip install google-auth google-auth-oauthlib google-api-python-client")
    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    creds = None
    try:
        creds = flow.run_local_server(port=0, prompt="consent", open_browser=True)
    except Exception as e:
        print(f"Local browser flow failed ({e}). Copy-paste flow:", flush=True)
    if creds is None:
        auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
        print("\n1. Open this URL in a browser signed into the Google account that OWNS the channel:")
        print(auth_url)
        print("2. Paste the code (or the full redirect URL) here.")
        code = input("code: ").strip()
        if "code=" in code:
            from urllib.parse import parse_qs, urlparse
            code = parse_qs(urlparse(code).query).get("code", [code])[0]
        flow.fetch_token(code=code)
        creds = flow.credentials
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    mine = yt.channels().list(part="id,snippet", mine=True).execute()
    items = mine.get("items") or []
    if not items:
        sys.exit("BLOCK: this Google login has no YouTube channel.")
    got = items[0]["id"]
    title = items[0]["snippet"]["title"]
    if got != channel_id:
        sys.exit(
            f"BLOCK: token is for channel {got} ({title!r}), not {channel_id}.\n"
            "Switch brand account in the Google consent screen, or pass the id that actually signed in."
        )
    save_creds(channel_id, creds)
    print(f"AUTH OK  {channel_id}  {title!r}")
    print("token:", token_path(channel_id), "(outside the repo)")


def youtube_client(channel_id: str):
    from googleapiclient.discovery import build
    creds = load_creds(channel_id)
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def assert_token_matches(yt, channel_id: str) -> str:
    mine = yt.channels().list(part="id,snippet", mine=True).execute()
    items = mine.get("items") or []
    if not items:
        fail("OAuth token has no YouTube channel")
    got = items[0]["id"]
    name = items[0]["snippet"]["title"]
    if got != channel_id:
        fail(f"token channel {got} ({name!r}) != approval channel {channel_id}")
    return name


# ── dry-run / upload ─────────────────────────────────────────────────────────

def print_preview(data: dict, items: list[dict]) -> None:
    ch = data["_channel"]
    print("== DRY RUN (no upload) ==")
    print(f"  channel     {data['channel_id']}  {ch.get('name')}  {ch.get('handle')}")
    print(f"  visibility  {data['_visibility']}")
    print(f"  approved    {data.get('approved')!r}")
    print(f"  items       {len(items)}")
    for i, it in enumerate(items):
        print(f"\n  [{i}] {it['kind']}")
        print(f"      title      {it['title']!r}  ({len(it['title'])} chars)")
        print(f"      video      {it['video']}  ({it['video_bytes']} bytes)")
        print(f"      thumbnail  {it['thumbnail']}  {it['thumb_size'][0]}x{it['thumb_size'][1]}")
        print(f"      tags       {len(it['tags'])}  sha {it['sha256']}")
        print(f"      desc[0:90] {it['description'][:90]!r}")
        if it["pinned_comment"]:
            print(f"      comment    {it['pinned_comment'][:80]!r}")
    print("\nIf this is correct: set \"approved\": true in the JSON, then:")
    print("  python3 tools/youtube_publish.py APPROVAL.json --upload")


def upload_one(yt, item: dict, visibility: str) -> dict:
    from googleapiclient.http import MediaFileUpload
    body = {
        "snippet": {
            "title": item["title"],
            "description": item["description"],
            "tags": item["tags"][:30],
            "categoryId": item["category_id"],
            "defaultLanguage": item["language"],
            "defaultAudioLanguage": item["language"],
        },
        "status": {
            "privacyStatus": visibility,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "license": "youtube",
        },
    }
    media = MediaFileUpload(str(item["video"]), mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    print(f"  uploading {item['video'].name} …", flush=True)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"    {int(status.progress() * 100)}%", flush=True)
    vid = resp["id"]
    url = f"https://youtu.be/{vid}"
    print(f"  video_id {vid}  {url}", flush=True)

    thumb_ok = False
    try:
        yt.thumbnails().set(
            videoId=vid,
            media_body=MediaFileUpload(str(item["thumbnail"]), mimetype="image/jpeg"),
        ).execute()
        thumb_ok = True
        print("  thumbnail set", flush=True)
    except Exception as e:
        print(f"  thumbnail FAIL: {e}", flush=True)

    # synthetic-media flag — not all API versions accept it
    try:
        yt.videos().update(
            part="status",
            body={"id": vid, "status": {"containsSyntheticMedia": True, "privacyStatus": visibility,
                                        "selfDeclaredMadeForKids": False}},
        ).execute()
    except Exception:
        pass

    comment_id = None
    if item["pinned_comment"]:
        try:
            c = yt.commentThreads().insert(
                part="snippet",
                body={"snippet": {"videoId": vid, "topLevelComment": {
                    "snippet": {"textOriginal": item["pinned_comment"]}}}},
            ).execute()
            comment_id = c["id"]
            print("  comment posted (pin it in Studio — Data API cannot pin)", flush=True)
        except Exception as e:
            print(f"  comment FAIL: {e}", flush=True)

    return {
        "kind": item["kind"],
        "title": item["title"],
        "video_id": vid,
        "url": url,
        "studio": f"https://studio.youtube.com/video/{vid}/edit",
        "thumbnail_set": thumb_ok,
        "comment_id": comment_id,
        "pin": "studio-manual" if comment_id else None,
        "visibility": visibility,
    }


def cmd_run(approval_path: Path, *, upload: bool) -> None:
    data = load_approval(approval_path)
    try:
        items = validate_approval(data, for_upload=upload)
    except GateError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not upload:
        print_preview(data, items)
        secret = client_secret_path()
        tok = token_path(data["channel_id"])
        print("\n  oauth client ", "present" if secret else "MISSING")
        print("  oauth token  ", "present" if tok.exists() else "MISSING — run --auth")
        return

    yt = youtube_client(data["channel_id"])
    live_name = assert_token_matches(yt, data["channel_id"])
    print(f"UPLOAD → {data['channel_id']} ({live_name!r})  visibility={data['_visibility']}")
    results = []
    for it in items:
        results.append(upload_one(yt, it, data["_visibility"]))
    report = {
        "ok": True,
        "when": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "channel_id": data["channel_id"],
        "channel_name": live_name,
        "visibility": data["_visibility"],
        "approval": str(approval_path.resolve()),
        "items": results,
    }
    rp = reports_dir() / f"upload_{time.strftime('%Y%m%d_%H%M%S')}.json"
    rp.write_text(json.dumps(report, indent=2) + "\n")
    print("\n== REPORT ==")
    for r in results:
        print(f"  {r['kind']:6}  {r['url']}  {r['title']!r}")
    print("wrote", rp)


# ── self-test (no network, no OAuth) ─────────────────────────────────────────

def cmd_self_test() -> None:
    fails = 0

    def expect_block(fn, needle: str):
        nonlocal fails
        try:
            fn()
            print(f"  FAIL expected block containing {needle!r}")
            fails += 1
        except (GateError, SystemExit) as e:
            msg = str(e)
            if needle.lower() not in msg.lower():
                print(f"  FAIL block text {msg!r} missing {needle!r}")
                fails += 1
            else:
                print(f"  ok  blocked: {needle}")

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        vid = td / "x.mp4"
        vid.write_bytes(b"\x00" * 120_000)
        from PIL import Image
        thumb = td / "thumbnail.jpg"
        Image.new("RGB", (1280, 720), (20, 20, 20)).save(thumb, quality=80)
        md = td / "metadata.md"
        md.write_text(
            "## TITLE\n**TestCo Died In A Year**\n\n"
            "## DESCRIPTION\nTestCo died in a year.\n\nMore words here to pass the long description floor. "
            + ("word " * 220)
            + "\n\nDISCLAIMER: This video is education only. It is not financial, tax, or investment advice. "
            "Nothing here is a recommendation to buy or sell any security.\n\n"
            "## TAGS\nTestCo\n\n## PINNED COMMENT\nHello\n\n## PRIMARY KEYWORD\nTestCo\n"
        )
        good_item = {
            "kind": "long", "shorts": False,
            "video": str(vid), "thumbnail": str(thumb),
            "title": "TestCo Died In A Year",
            "description": md.read_text().split("## DESCRIPTION", 1)[1].split("## TAGS")[0].strip(),
            "tags": ["TestCo"], "category_id": "27", "language": "en",
            "pinned_comment": "Hello",
        }
        # unapproved
        expect_block(
            lambda: validate_approval(
                {"approved": False, "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
                 "visibility": "private", "items": [good_item]},
                for_upload=True,
            ),
            "approved",
        )
        # string true
        expect_block(
            lambda: validate_approval(
                {"approved": "true", "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
                 "visibility": "private", "items": [good_item]},
                for_upload=True,
            ),
            "approved",
        )
        # public
        expect_block(
            lambda: validate_approval(
                {"approved": True, "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
                 "visibility": "public", "items": [good_item]},
                for_upload=True,
            ),
            "visibility",
        )
        # bad channel format
        expect_block(
            lambda: validate_approval(
                {"approved": True, "channel_id": "not-a-channel",
                 "visibility": "private", "items": [good_item]},
                for_upload=True,
            ),
            "channel_id",
        )
        # missing video
        bad = dict(good_item, video=str(td / "nope.mp4"))
        expect_block(
            lambda: validate_approval(
                {"approved": True, "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
                 "visibility": "private", "items": [bad]},
                for_upload=True,
            ),
            "video missing",
        )
    if fails:
        print(f"SELF-TEST {fails} failure(s)")
        sys.exit(1)
    print("SELF-TEST OK")


# ── cli ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Gated YouTube upload. Default visibility: private. Never public.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("approval", nargs="?", help="approval.json from --pack")
    ap.add_argument("--dry-run", action="store_true", help="preview only; never upload")
    ap.add_argument("--upload", action="store_true", help="EXPLICIT upload command")
    ap.add_argument("--pack", metavar="EP_DIR", help="build approval.json (approved=false)")
    ap.add_argument("--channel", help="UC… channel id (allow-listed)")
    ap.add_argument("-o", "--out", help="path for --pack output")
    ap.add_argument("--no-shorts", action="store_true", help="pack long only")
    ap.add_argument("--auth", action="store_true", help="OAuth for --channel (browser / copy-paste)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--list-channels", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        cmd_self_test()
        return
    if args.list_channels:
        for ch in load_channels():
            cid = (ch.get("id") or "").strip()
            ok = "READY" if CHANNEL_ID_RE.match(cid) else "NO ID"
            print(f"  {ok:6}  {ch.get('slug')}  {ch.get('name')}  {cid or '—'}")
        return
    if args.auth:
        if not args.channel:
            sys.exit("--auth requires --channel UC…")
        cmd_auth(args.channel.strip())
        return
    if args.pack:
        if not args.channel:
            sys.exit("--pack requires --channel UC…")
        ep = Path(args.pack)
        if not ep.is_dir():
            sys.exit(f"not a directory: {ep}")
        out = Path(args.out) if args.out else ep / "approval.json"
        try:
            cmd_pack(ep, args.channel.strip(), out, include_shorts=not args.no_shorts)
        except GateError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        return
    if not args.approval:
        ap.print_help()
        sys.exit(2)
    if args.upload and args.dry_run:
        sys.exit("pick one: --dry-run or --upload")
    if not args.upload and not args.dry_run:
        sys.exit("refusing to run without --dry-run or --upload")
    cmd_run(Path(args.approval), upload=bool(args.upload))


if __name__ == "__main__":
    main()
