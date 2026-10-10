"""Immutable long-form media contract. Heavy assets are Release files, not git."""
import hashlib
import json
from pathlib import Path
import re
import shutil

from tools.post.common import ROOT, fingerprint, load_json
from tools.post.media import asset_metadata, public_download
from tools.youtube.seo import tracking_tag, validate as validate_seo


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
