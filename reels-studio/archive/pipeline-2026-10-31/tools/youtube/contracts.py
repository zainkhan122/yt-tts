"""Immutable long-form media contract. Heavy assets are Release files, not git."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from PIL import Image

from tools.post.common import ROOT, fingerprint, load_json
from tools.post.media import asset_metadata, public_download
from tools.youtube.seo import tracking_tag, validate as validate_seo

# Shorts cover (custom thumbnail) limits. Google raised the documented image cap and
# confirmed 9:16 Shorts thumbnails in 2026; the vertical Shorts-shelf picture
# (oar2.jpg) is still provider-only and not settable through the Data API.
SHORT_COVER_MIN_HEIGHT = 640
SHORT_COVER_MAX_BYTES = 50_000_000


def cover_digest(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_short_cover(path, approved_digest):
    """Hard gate: a Shorts cover may only be set if it matches the digest the agent
    explicitly reviewed, and it satisfies format/minimum-size limits."""
    p = Path(path)
    if not p.is_file():
        raise ValueError("Short cover image is missing")
    size = p.stat().st_size
    if size > SHORT_COVER_MAX_BYTES:
        raise ValueError("Short cover exceeds the provider image limit")
    digest = cover_digest(p)
    if approved_digest != digest:
        raise ValueError("Short cover does not match the agent-reviewed digest; refusing to set an unreviewed image")
    with Image.open(p) as image:
        fmt, (width, height) = image.format, image.size
    if fmt not in {"JPEG", "PNG"}:
        raise ValueError("Short cover must be JPEG or PNG")
    if height < SHORT_COVER_MIN_HEIGHT:
        raise ValueError("Short cover is below the minimum height for Shorts thumbnails")
    return {"sha256": digest, "format": fmt, "width": width, "height": height, "size_bytes": size}


def fetch_kit_cover(item, root_cfg, work):
    """Extract cover.jpg from the immutable pinned kit Release asset, verifying the
    kit digest and (when present) the reviewed-cover approval recorded in the queue."""
    meta = asset_metadata(root_cfg, item["kit_asset_id"])
    if meta["name"] != item["video_id"] + "-kit.zip":
        raise ValueError("Kit asset name does not match the queue pin")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", item.get("kit_digest", "")):
        raise ValueError("A SHA-256 kit digest is required for cover extraction")
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    zip_path = work / (item["video_id"] + "-kit.zip")
    public_download(meta["browser_download_url"], meta["size"], item["kit_digest"], zip_path)
    member = item["video_id"] + "/cover.jpg"
    try:
        with zipfile.ZipFile(zip_path) as archive:
            if member not in archive.namelist():
                raise ValueError("Kit does not contain the expected reviewed cover")
            data = archive.read(member)
    finally:
        # The zip is a download intermediate, not a cache: public_download verified its digest and
        # the Release stays authoritative. Deleting it keeps the workspace under its size budget (a
        # review pass used to leave ~12 MB of kit zips + copies behind - 2026-10-12 storage audit).
        zip_path.unlink(missing_ok=True)
    cover = work / (item["video_id"] + "-cover.jpg")
    cover.write_bytes(data)
    if item.get("cover_sha256"):
        validate_short_cover(cover, item["cover_sha256"])
    return cover


def fetch_short_cover(item, root_cfg, work):
    """Cover for the enrichment worker: requires explicit agent approval first."""
    if not (item.get("cover_sha256") and item.get("cover_reviewed_at")):
        return None
    cover = fetch_kit_cover(item, root_cfg, work)
    return {"path": cover, "sha256": cover_digest(cover)}


def read_brief(item):
    path = ROOT / "briefs/long" / (item["video_id"] + ".json")
    brief = load_json(path)
    if fingerprint(brief) != item["brief_sha256"]:
        raise ValueError("Long brief changed after queue review; re-approve explicitly")
    return brief


def fetch_asset(ref, root_cfg, dest=None, max_size=None):
    meta = asset_metadata(root_cfg, ref["id"])
    if meta["name"] != ref["name"] or meta["size"] != ref["size"]:
        raise ValueError("Pinned Release asset identity changed")
    if max_size and meta["size"] > max_size:
        raise ValueError("Release asset exceeds local safety budget")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", ref.get("digest", "")):
        raise ValueError("A SHA-256 digest is required for every long-form asset")
    return public_download(meta["browser_download_url"], meta["size"], ref["digest"], dest)


def validate_manifest(manifest, item):
    if manifest.get("id") != item["video_id"] or manifest.get("format") != "long":
        raise ValueError("Wrong long-form render manifest")
    checks = manifest.get("qa", {}).get("checks", {})
    if not checks or not checks.get("approved_voice") or not all(v is True for v in checks.values()):
        raise ValueError("Long render QA / approved Option 3 voice did not pass")
    engine = json.dumps(manifest.get("stages", {}).get("voice", {})).lower()
    if not all(token in engine for token in ("chatterbox", "exag0.7", "cfg0.4", "michael-ref.wav", "flow")):
        raise ValueError("Long video does not use the approved Option 3 continuous-flow narration")
    video = manifest.get("video", {})
    if video.get("sha256") != item["asset_digest"]:
        raise ValueError("Render manifest is not bound to the exact pinned MP4")
    if video.get("width", 0) < 1920 or video.get("height", 0) < 1080 or video["width"]*9 != video["height"]*16:
        raise ValueError("Long video must be landscape 16:9 at 1080p or higher")
    if video.get("video_codec") != "h264" or video.get("audio_codec") != "aac":
        raise ValueError("Long video must use H.264 + AAC")
    if not 180 <= video.get("duration_seconds", 0) <= 1800:
        raise ValueError("Long-video duration outside the configured 3–30 minute safety window")
    return video


def validate_thumbnail(report, ref, cfg, item):
    rules = cfg["thumbnail"]
    if report.get("sha256") != ref["digest"] or report.get("size_bytes") != ref["size"]:
        raise ValueError("Thumbnail review does not match the exact image")
    if not report.get("checks") or not all(v is True for v in report["checks"].values()):
        raise ValueError("Thumbnail QA failed")
    if report.get("width") != rules["width"] or report.get("height") != rules["height"] or report.get("preview_width") != 250:
        raise ValueError("Wrong thumbnail / mobile preview dimensions")
    if min((p.get("height_at_250", 0) for p in report.get("text", [])), default=0) < rules["minimum_text_height_at_250"]:
        raise ValueError("Main headline is too small at 250px")
    if cfg["require_mobile_thumbnail_review"] and not item.get("thumbnail_reviewed_at"):
        raise ValueError("Agent must visually approve the 250px preview before upload")
    if ref["size"] > rules["max_bytes"]:
        raise ValueError("Thumbnail exceeds our conservative image-size budget")


def preflight(item, root_cfg, cfg, work, need_video=False):
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    brief = read_brief(item)
    assets = item["assets"]
    if assets["video"]["digest"] != item["asset_digest"] or assets["video"]["id"] != item["asset_id"]:
        raise ValueError("Inconsistent long-video asset pins")
    _, _, raw = fetch_asset(assets["manifest"], root_cfg, max_size=2_000_000)
    manifest = json.loads(raw)
    video = validate_manifest(manifest, item)
    if abs(video["duration_seconds"] - brief["duration_seconds"]) > 2:
        raise ValueError("Long brief/chapters duration differs from the actual render")
    _, _, raw = fetch_asset(assets["thumbnail_report"], root_cfg, max_size=2_000_000)
    validate_thumbnail(json.loads(raw), assets["thumbnail"], cfg, item)
    thumbnail = work / "thumbnail.jpg"
    fetch_asset(assets["thumbnail"], root_cfg, thumbnail, cfg["thumbnail"]["max_bytes"])
    snippet = validate_seo(brief, "long", tracking_tag(item))
    path = work / (item["video_id"] + ".mp4")
    if need_video:
        if assets["video"]["size"] > cfg["max_video_bytes"]:
            raise ValueError("MP4 exceeds our per-asset operational limit")
        if shutil.disk_usage(work).free < max(cfg["minimum_disk_free_bytes"], assets["video"]["size"]*2):
            raise ValueError("Insufficient runner disk space; no upload started")
        fetch_asset(assets["video"], root_cfg, path, cfg["max_video_bytes"])
    return {"brief": brief, "snippet": snippet, "manifest": manifest, "video_path": path, "thumbnail_path": thumbnail}
