#!/usr/bin/env python3
"""Ship guard: one place that proves a queued Short is the Short that was reviewed.

Invariant (owner, 5 Nov 2026): the bytes that get scheduled are the bytes that were
reviewed. Every other link is also pinned by hash: brief -> receipt -> queue item ->
release asset -> review record -> viewer panel.

Commands:
  python3 tools/ship.py review <video_id> --mp4 <file> --run <actions_run_id> [--cover <file>]
      Record the reviewed artifact: sha256 of the MP4 (and optional cover), the Actions run.
  python3 tools/ship.py check <video_id> [--json]
      Exit 0 only if every link agrees. Exit 1 with the list of drifts otherwise.

Gates stay in code. Vision and human notes stay advisory. Free text is never a verdict:
the panel verdict is read from its own "Panel result:" line only.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "post"))
from common import fingerprint  # noqa: E402  (same canonical hash the queue uses)

RECEIPTS = ROOT / "research" / "production" / "receipts"
VALID_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{2,80}$")
PANEL_LINE = re.compile(r"^Panel result:\s*(PASS|FAIL)\b", re.MULTILINE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _valid(video_id: str) -> str:
    if not VALID_ID.match(video_id):
        raise SystemExit(f"bad video id: {video_id!r}")
    return video_id


def panel_verdict(video_id: str, root: Path = ROOT) -> str | None:
    """PASS / FAIL from the panel file's own verdict line. None if no file or no line."""
    files = sorted((root / "research" / "production").glob(f"viewer-panel-*{video_id}*.md"))
    if not files:
        return None
    found = PANEL_LINE.findall(files[-1].read_text(encoding="utf-8", errors="replace"))
    return found[-1] if found else None


def review(video_id: str, mp4: Path, run_id: str, cover: Path | None = None, *, root: Path = ROOT) -> dict:
    _valid(video_id)
    if not mp4.is_file():
        raise SystemExit(f"no such file: {mp4}")
    if not run_id.isdigit():
        raise SystemExit("--run must be the numeric Actions run id")
    record = {
        "video_id": video_id,
        "mp4_sha256": sha256_file(mp4),
        "mp4_bytes": mp4.stat().st_size,
        "run_id": run_id,
        "cover_sha256": sha256_file(cover) if cover else None,
    }
    reviewed_dir = root / "research" / "production" / "reviewed"
    reviewed_dir.mkdir(parents=True, exist_ok=True)
    (reviewed_dir / f"{video_id}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def check(video_id: str, *, root: Path = ROOT) -> list[str]:
    """Return a list of drift errors. Empty list means every link agrees."""
    _valid(video_id)
    errors: list[str] = []

    brief_path = root / "briefs" / f"{video_id}.json"
    if not brief_path.exists():
        return [f"brief missing: briefs/{video_id}.json"]
    # Two hash definitions exist in the system and both are pinned on purpose:
    #   receipts pin the raw file bytes (receipt_build.py), the queue pins the canonical JSON (common.fingerprint).
    # Each link is compared with its own definition, never across them.
    brief_file_sha = sha256_file(brief_path)
    brief_canon_sha = fingerprint(_load(brief_path))

    # 1. the latest receipt that pins this brief governs (older batches are history)
    pinned = []
    for rp in sorted((root / "research" / "production" / "receipts").glob("*.json")):
        entry = (_load(rp).get("briefs") or {}).get(video_id)
        if entry:
            pinned.append((rp.name, entry.get("brief_sha256")))
    if not pinned:
        errors.append("receipt: no receipt pins this brief")
    else:
        name, sha = pinned[-1]
        if sha != brief_file_sha:
            errors.append(f"receipt {name}: brief_sha256 {str(sha)[:12]} != brief file {brief_file_sha[:12]} (brief edited after receipt)")

    # 2. queue item: pinned brief and the release asset that is actually scheduled
    queue = _load(root / "queue" / "publish.json") if (root / "queue" / "publish.json").exists() else {"items": []}
    item = next((i for i in queue.get("items", []) if i.get("video_id") == video_id), None)
    if item is None:
        errors.append("queue: item not queued (nothing to ship yet)")
        return errors
    if item.get("brief_sha256") != brief_canon_sha:
        errors.append(f"queue: brief_sha256 {str(item.get('brief_sha256'))[:12]} != brief canonical {brief_canon_sha[:12]}")

    # 3. the scheduled bytes are the reviewed bytes
    rev_path = root / "research" / "production" / "reviewed" / f"{video_id}.json"
    if not rev_path.exists():
        errors.append("review: no review record (the scheduled file was never reviewed)")
        reviewed = None
    else:
        reviewed = _load(rev_path)
        digest = item.get("asset_digest") or ""
        want = "sha256:" + reviewed["mp4_sha256"]
        if digest != want:
            errors.append(f"artifact: release asset {digest[:19]}... != reviewed mp4 {want[:19]}... (scheduled file differs from reviewed file)")

    # 4. cover: the scheduled cover is the reviewed cover
    if item.get("cover_sha256") is None and "youtube" in (item.get("platforms") or []):
        errors.append("cover: youtube is scheduled but no cover is approved")
    elif reviewed and reviewed.get("cover_sha256") and item.get("cover_sha256") != reviewed["cover_sha256"]:
        errors.append("cover: queued cover differs from the reviewed cover")

    # 5. viewer panel verdict (PASS or FAIL; an owner override is recorded in the panel file itself)
    verdict = panel_verdict(video_id, root)
    if verdict != "PASS":
        errors.append(f"panel: verdict is {verdict or 'missing'} (queue approval needs PASS)")
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("review")
    r.add_argument("video_id")
    r.add_argument("--mp4", required=True, type=Path)
    r.add_argument("--run", required=True)
    r.add_argument("--cover", type=Path)
    c = sub.add_parser("check")
    c.add_argument("video_id")
    c.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "review":
        rec = review(args.video_id, args.mp4, args.run, args.cover)
        print(json.dumps(rec, indent=2))
        return 0
    errors = check(args.video_id)
    if args.json:
        print(json.dumps({"video_id": args.video_id, "ok": not errors, "errors": errors}, indent=2))
    else:
        print("OK: scheduled file == reviewed file; brief, receipt, cover and panel agree" if not errors
              else "DRIFT:\n  - " + "\n  - ".join(errors))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
