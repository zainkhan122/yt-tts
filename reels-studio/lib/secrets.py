"""Credentials live in GitHub Actions secrets or chmod-600 files OUTSIDE the repo.
Never print them or commit them. GH_TOKEN / BUFFER_API_KEY override local files.
"""
import os
import json
import re
from pathlib import Path

PATHS = [Path("/var/tmp/gh/token"), Path.home() / ".config/reels-studio/gh_token"]
BUFFER_PATH = Path.home() / ".config/reels-studio/buffer_token"
YOUTUBE_PATH = Path.home() / ".config/reels-studio/youtube_oauth.json"
YOUTUBE_KEY_PATH = Path.home() / ".config/reels-studio/youtube_state_key"
_RUNTIME = set()
PATTERN = re.compile(r"github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{30,}")


def gh_token():
    t = os.environ.get("GH_TOKEN", "").strip()
    if t:
        return t
    for p in PATHS:
        if p.exists() and p.read_text().strip():
            return p.read_text().strip()
    return None


def buffer_token():
    token = os.environ.get("BUFFER_API_KEY", "").strip()
    if token:
        return token
    if BUFFER_PATH.exists():
        return BUFFER_PATH.read_text().strip() or None
    return None


def youtube_credentials():
    raw = os.environ.get("YOUTUBE_OAUTH_JSON", "").strip()
    if not raw and YOUTUBE_PATH.exists():
        raw = YOUTUBE_PATH.read_text()
    value = json.loads(raw) if raw else None
    if value is not None and not isinstance(value, dict):
        raise ValueError("YouTube OAuth configuration must be a JSON object")
    return value


def youtube_state_key():
    value = os.environ.get("YOUTUBE_STATE_KEY", "").strip()
    return value or (YOUTUBE_KEY_PATH.read_text().strip() if YOUTUBE_KEY_PATH.exists() else None)


def register_sensitive(value):
    if value:
        _RUNTIME.add(str(value))


def _known_values():
    values = [gh_token(), buffer_token(), youtube_state_key(), *_RUNTIME]
    try:
        creds = youtube_credentials() or {}
        values += [creds.get(k) for k in ("client_secret", "refresh_token", "access_token")]
    except (ValueError, OSError):
        pass
    for path in [*PATHS, BUFFER_PATH]:
        if path.exists():
            values.append(path.read_text().strip())
    return [v for v in set(values) if v and len(v) >= 12]


def contains_secret(text):
    text = text or ""
    return bool(PATTERN.search(text)) or any(v in text for v in _known_values())


def redact(text):
    result = PATTERN.sub("[REDACTED]", str(text))
    result = re.sub(r"([?&]upload_id=)[^&\s]+", r"\1[REDACTED]", result)
    for value in _known_values():
        result = result.replace(value, "[REDACTED]")
    return result
