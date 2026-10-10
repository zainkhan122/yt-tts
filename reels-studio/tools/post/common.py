"""Shared publishing helpers. No TTS/render dependencies are imported here."""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UTC = dt.timezone.utc
TERMINAL = {"sent", "published_manual"}
# Anything except an explicitly rejected/deferred request blocks another createPost.
RETRYABLE = {"retry_wait"}
PENDING = {"scheduled", "sending", "draft", "needs_approval"}
UNCERTAIN = {"submitting", "uncertain"}


def now_utc():
    return dt.datetime.now(UTC)


def iso(value):
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(value):
    if not value:
        return None
    result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Dates must include a timezone")
    return result.astimezone(UTC)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def config():
    return load_json(ROOT / "config/publishing.json")


def queue():
    return load_json(ROOT / "queue/publish.json")["items"]


def key(video_id, platform):
    return f"{video_id}:{platform}"


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def media_url(item, cfg):
    return cfg["media"]["base_url"].rstrip("/") + "/" + item["media_path"]


def valid_id(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,95}", value):
        raise ValueError("Invalid video ID")
    return value


def check_manifest(manifest, video_id):
    checks = manifest.get("qa", {}).get("checks", {})
    required = {"1080x1920", "30fps", "h264+aac", "duration_matches", "loudness_-14±1", "peak<=-1dBFS", "approved_voice"}
    if manifest.get("id") != video_id or not required.issubset(checks) or not all(v is True for v in checks.values()):
        raise ValueError(f"{video_id}: render QA or approved Option 3 voice gate failed")
    # Defence in depth: a stale/mislabelled approved_voice boolean is not sufficient.
    stages = manifest.get("stages", {})
    voice = stages.get("voice") if isinstance(stages, dict) else next((s for s in stages if s.get("stage") == "voice" or s.get("name") == "voice"), None)
    if voice is None:
        raise ValueError(f"{video_id}: missing voice audit")
    text = json.dumps(voice).lower()
    if not all(v in text for v in ("chatterbox", "exag0.7", "cfg0.4", "michael-ref.wav", "flow")):
        raise ValueError(f"{video_id}: narration is not the approved Option 3 configuration")
    return checks
