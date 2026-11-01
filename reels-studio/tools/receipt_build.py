#!/usr/bin/env python3
"""Build the production receipt for one or more briefs from the briefs themselves.

Before this tool, receipts were typed by hand after each brief edit, and a stale receipt
(brief sha, script hash or word count) failed the cloud gate. This writes the receipt from:
  * briefs/<id>.json                  -> brief_sha256, script_sha256, word_count (production_gate helpers)
  * captures/<capture>/manifest.json  -> manifest_sha256 and every asset sha256 (production_gate.asset_digest_receipt)
  * covers/<id>/selection.json        -> cover_sha256
Then it runs production_gate.validate_receipt(verify_assets=True) and refuses to write a receipt that
does not pass. A receipt is written only once every brief in the batch validates.

Usage:
  python3 tools/receipt_build.py <batch-id> repo-ifixai-01 [repo-x-01 ...]
  -> research/production/receipts/<batch-id>.json   (batch id must equal the file name)
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # reels-studio/
REPO = ROOT.parent                                  # the git repo that holds reels-studio/
sys.path.insert(0, str(ROOT / "tools"))

import production_gate as pg  # noqa: E402

RECEIPTS = ROOT / "research" / "production" / "receipts"
BATCH_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9][a-z0-9-]{0,60}$")


class ReceiptError(SystemExit):
    pass


def build_brief_entry(brief_id: str) -> dict:
    brief_path = ROOT / "briefs" / f"{brief_id}.json"
    if not brief_path.exists():
        raise ReceiptError(f"{brief_id}: brief not found at {brief_path.relative_to(REPO)}")
    raw = brief_path.read_bytes()
    brief = json.loads(raw)
    capture = (brief.get("capture") or "").strip().rstrip("/").split("/")[-1]
    if not capture:
        raise ReceiptError(f"{brief_id}: brief has no capture pack id")
    try:
        assets = pg.asset_digest_receipt(REPO, capture)
    except pg.ProductionGateError as exc:
        raise ReceiptError(f"{brief_id}: asset digests failed: {exc}") from exc
    sel_path = ROOT / "covers" / brief_id / "selection.json"
    if not sel_path.exists():
        raise ReceiptError(f"{brief_id}: no reviewed cover (covers/{brief_id}/selection.json)")
    cover_sha = json.loads(sel_path.read_text(encoding="utf-8")).get("sha256")
    assets["cover_sha256"] = cover_sha
    assets["status"] = "complete"
    assets["evidence"] = [f"reels-studio/captures/{capture}/manifest.json"]
    return {
        "brief_sha256": hashlib.sha256(raw).hexdigest(),
        "stages": {
            "script": {
                "status": "complete",
                "script_sha256": pg.script_sha256(brief),
                "word_count": pg.script_word_count(brief),
            },
            "assets": assets,
        },
    }


def build(batch_id: str, brief_ids: list[str], *, now: dt.datetime | None = None) -> Path:
    if not BATCH_RE.match(batch_id):
        raise ReceiptError(f"batch id {batch_id!r} must look like 2026-11-01-ifixai-01")
    receipt = {
        "schema_version": 1,
        "batch_id": batch_id,
        "created_at": (now or dt.datetime.now(dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "briefs": {bid: build_brief_entry(bid) for bid in brief_ids},
    }
    out = RECEIPTS / f"{batch_id}.json"
    text = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
    # The validator reads the receipt from disk, so write it, validate the file, and remove it if it fails.
    # A receipt that does not validate never stays in the repo.
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    try:
        pg.validate_receipt(REPO, f"reels-studio/research/production/receipts/{batch_id}.json", brief_ids,
                            now=now, verify_assets=True)
    except pg.ProductionGateError as exc:
        out.unlink(missing_ok=True)
        raise ReceiptError(f"receipt does not validate: {exc}") from exc
    return out


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) < 2:
        print(__doc__)
        return 2
    batch, ids = args[0], args[1:]
    try:
        out = build(batch, ids)
    except ReceiptError as exc:
        print(f"receipt_build: {exc}", file=sys.stderr)
        return 1
    print(f"receipt validated -> {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
