"""Credentials live in GitHub Actions secrets or chmod-600 files OUTSIDE the repo.
Never print them or commit them. GH_TOKEN / BUFFER_API_KEY override local files.
"""
import os
import re
from pathlib import Path

PATHS = [Path("/var/tmp/gh/token"), Path.home() / ".config/reels-studio/gh_token"]
BUFFER_PATH = Path.home() / ".config/reels-studio/buffer_token"
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


def _known_values():
    values = [gh_token(), buffer_token()]
    for path in [*PATHS, BUFFER_PATH]:
        if path.exists():
            values.append(path.read_text().strip())
    return [v for v in set(values) if v and len(v) >= 12]


def contains_secret(text):
    text = text or ""
    return bool(PATTERN.search(text)) or any(v in text for v in _known_values())


def redact(text):
    result = PATTERN.sub("[REDACTED]", str(text))
    for value in _known_values():
        result = result.replace(value, "[REDACTED]")
    return result
