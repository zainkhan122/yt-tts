#!/usr/bin/env python3
"""Fail-closed validator used by GitHub Actions and the local cloud-render command."""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
from lib.delivery import DeliveryError, validate_ids  # noqa: E402
from tools import production_gate, render_attempts  # noqa: E402

QUALITY = {"draft", "looks", "delivery", "standard", "high"}
TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
SCENE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def plan_dispatch(
    raw_briefs: str,
    *,
    tag: str = "",
    quality: str = "looks",
    crf: str | int = "23",
    rebuild_scenes: str = "",
    rebuild_reason: str = "",
    from_tag: str = "",
    production_receipt: str = "",
    briefs_root: Path | None = None,
    repo_root: Path | None = None,
    today: datetime.date | None = None,
    now: datetime.datetime | None = None,
) -> dict:
    """Validate inputs, production receipts, assets metadata and deterministic attempt keys."""
    briefs_root = Path(briefs_root or ROOT / "briefs")
    repo_root = Path(repo_root or REPO_ROOT).resolve()
    raw = raw_briefs.replace(",", " ").split()
    ids = []
    for item in raw:
        parts = Path(item).parts
        if (item.startswith(("/", "\\")) or "\\" in item or ".." in parts
                or (len(parts) > 1 and parts[-2] != "briefs")):
            raise ValueError(f"brief input must be an ID or a path under briefs/: {item!r}")
        ids.append(Path(item).name.removesuffix(".json"))
    try:
        validate_ids(ids, max_batch=10)
    except DeliveryError as exc:
        raise ValueError(str(exc)) from exc

    loaded, brief_hashes = {}, {}
    for brief_id in ids:
        path = briefs_root / f"{brief_id}.json"
        if not path.is_file():
            raise ValueError(f"unknown brief ID: {brief_id}")
        try:
            brief_raw = path.read_bytes()
            brief = json.loads(brief_raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"brief is unreadable: {path}: {exc}") from exc
        if not isinstance(brief, dict) or brief.get("id") != brief_id:
            raise ValueError(f"brief ID mismatch in {path}")
        loaded[brief_id] = brief
        import hashlib
        brief_hashes[brief_id] = hashlib.sha256(brief_raw).hexdigest()

    if quality not in QUALITY:
        raise ValueError(f"quality must be one of {', '.join(sorted(QUALITY))}")
    try:
        crf_value = int(crf)
    except (TypeError, ValueError) as exc:
        raise ValueError("CRF must be an integer from 0 through 51") from exc
    if not 0 <= crf_value <= 51:
        raise ValueError("CRF must be an integer from 0 through 51")

    tag = tag.strip()
    from_tag = from_tag.strip()
    for label, value in (("tag", tag), ("from_tag", from_tag)):
        if value and not TAG_RE.fullmatch(value):
            raise ValueError(f"invalid {label}")

    scenes = rebuild_scenes.replace(",", " ").split()
    reason = rebuild_reason.strip()
    if scenes:
        if len(ids) != 1 or not reason:
            raise ValueError("scene rebuild requires exactly one brief and a non-empty rebuild reason")
        if len(scenes) != len(set(scenes)) or any(not SCENE_RE.fullmatch(s) for s in scenes):
            raise ValueError("scene IDs must be safe and unique")
        available = {s.get("id") for s in loaded[ids[0]].get("scenes", []) if isinstance(s, dict)}
        missing = sorted(set(scenes) - available)
        if missing:
            raise ValueError(f"unknown scene ID(s) for {ids[0]}: {', '.join(missing)}")
    elif reason or from_tag:
        raise ValueError("rebuild_reason/from_tag require rebuild_scenes")

    if not tag:
        day = today or datetime.datetime.now(ZoneInfo("Asia/Karachi")).date()
        tag = "renders-" + day.strftime("%Y-%m-%d")

    if scenes:
        asset_hashes = {}
    else:
        if not production_receipt.strip():
            raise ValueError("new renders require a production receipt (script, voice, assets); scene rebuilds are exempt")
        result = production_gate.validate_receipt(repo_root, production_receipt.strip(), ids, now=now)
        asset_hashes = {
            brief_id: {"manifest_sha256": row["asset_manifest_sha256"],
                       "files_sha256": row["asset_files_sha256"], "capture_id": row["capture_id"]}
            for brief_id, row in result["briefs"].items()
        }

    plan = {"briefs": ids, "tag": tag, "quality": quality, "crf": crf_value,
            "rebuild_scenes": scenes, "rebuild_reason": reason, "from_tag": from_tag,
            "production_receipt": production_receipt.strip() if not scenes else ""}
    plan["attempts"] = render_attempts.make_attempts(repo_root, plan, loaded, brief_hashes, asset_hashes)
    return plan


def main() -> int:
    try:
        if os.environ.get("GITHUB_ACTIONS", "").lower() == "true" and os.environ.get("GITHUB_REF") != "refs/heads/main":
            raise ValueError("production render dispatches must use the protected main branch")
        plan = plan_dispatch(
            os.environ.get("BRIEFS", ""),
            tag=os.environ.get("TAG", ""),
            quality=os.environ.get("QUALITY", "looks"),
            crf=os.environ.get("CRF", "23"),
            rebuild_scenes=os.environ.get("REBUILD_SCENES", ""),
            rebuild_reason=os.environ.get("REBUILD_REASON", ""),
            from_tag=os.environ.get("FROM_TAG", ""),
            production_receipt=os.environ.get("PRODUCTION_RECEIPT", ""),
        )
        # Read-only duplicate check before assets are fetched; the second dispatch-plan call
        # uses a Contents-API compare-and-swap to reserve the same fingerprints durably.
        if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
            render_attempts.check_remote(plan["attempts"])
        if os.environ.get("RECORD_ATTEMPT", "").lower() == "true":
            run_id = os.environ.get("GITHUB_RUN_ID", "")
            render_attempts.reserve_remote(plan["attempts"], run_id)
            print("attempt_fingerprints=" + json.dumps([a["fingerprint"] for a in plan["attempts"]], separators=(",", ":")))
    except (ValueError, RuntimeError) as exc:
        print(f"dispatch rejected: {exc}", file=sys.stderr)
        return 2
    print("briefs=" + json.dumps(plan["briefs"], separators=(",", ":")))
    print("tag=" + plan["tag"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
