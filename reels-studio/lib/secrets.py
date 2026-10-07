"""Single place to find the GitHub token. Never print it, never commit it.
Lookup order: env GH_TOKEN -> /var/tmp/gh/token (session) -> ~/.config/reels-studio/gh_token (persistent, chmod 600,
outside the git working tree so `git add` can never pick it up)."""
import os
import re
from pathlib import Path

PATHS = [Path("/var/tmp/gh/token"), Path.home() / ".config/reels-studio/gh_token"]
PATTERN = re.compile(r"github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{30,}")


def gh_token():
    t = os.environ.get("GH_TOKEN", "").strip()
    if t:
        return t
    for p in PATHS:
        if p.exists() and p.read_text().strip():
            return p.read_text().strip()
    return None


def contains_secret(text):
    return bool(PATTERN.search(text or ""))
