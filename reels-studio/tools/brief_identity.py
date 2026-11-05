"""The one definition of a brief's identity.

identity(brief) = sha256 of the brief's canonical JSON (sorted keys, no spaces).
Formatting, key order and whitespace in the file do not change it. Any content change does.

Used by: receipt_build (writes `brief_identity_sha256`), tools/ship.py (checks it),
and tools/post/common.fingerprint (the queue), which must stay the same formula.
"""
import hashlib
import json
from pathlib import Path


def identity(brief: dict) -> str:
    return hashlib.sha256(json.dumps(brief, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def identity_of_file(path: Path) -> str:
    return identity(json.loads(Path(path).read_text(encoding="utf-8")))
