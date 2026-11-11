#!/usr/bin/env python3
"""Sync captures/<id>/manifest.json 'files' map against what's actually on disk.

BL060 bites when a pack's manifest never got re-recorded after a clip/image was added
(the fetchable tar had the media but the ledger said it didn't). This walk makes the
manifest match reality: any .mp4/.jpg payloads on disk become manifest entries.
Style mirrors build_plan_kit: exactly what articles the renderer needs (file, sha256, kind).
"""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIND = {".mp4": "page recording (screen capture of the real tool)",
        ".jpg": "image (page capture)"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sync(vid: str):
    d = ROOT / "captures" / vid
    manifest_path = d / "manifest.json"
    m = json.loads(manifest_path.read_text())
    files = m.setdefault("files", {})
    added = []
    for media in sorted(d.glob("*")):
        if media.suffix.lower() not in KIND or media.is_dir():
            continue
        # Handle plan_kit layout names (receipt/stack/terminal) too
        candidates = [media.stem] if media.stem in files else None
        # Always ensure the payload exists keyed by stem (or by its role alias if already mapped)
        key = media.stem
        existing = files.get(key, {})
        entry = {"file": media.name, "sha256": sha256(media), "kind": KIND[media.suffix.lower()]}
        if files.get(key) == entry:
            continue
        files[key] = entry
        added.append(key)
    if added:
        manifest_path.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n")
    print(f"{vid}: synced ({len(files)} roles total); touched: {added or 'none'}")


if __name__ == "__main__":
    for vid in sys.argv[1:]:
        sync(vid)
