#!/usr/bin/env python3
"""Fail-closed validation and preflight for Actions and local cloud-render dispatches."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
from tools import production_gate, render_attempts  # noqa: E402

MAX_BATCH = 10
QUALITY = {"draft", "looks", "delivery", "standard", "high"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
SCENE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def _brief_id(token: str) -> str:
    if not isinstance(token, str) or not token or token != token.strip() or chr(92) in token:
        raise ValueError(f"invalid brief token: {token!r}")
    if ID_RE.fullmatch(token):
        return token
    path = PurePosixPath(token)
    if (path.is_absolute() or path.as_posix() != token or ".." in path.parts
            or ":" in path.parts[0] or not token.endswith(".json")):
        raise ValueError(f"brief input must be an ID or a repository briefs/<id>.json path: {token!r}")
    allowed = len(path.parts) == 2 and path.parts[0] == "briefs"
    allowed |= len(path.parts) == 3 and path.parts[:2] == ("reels-studio", "briefs")
    if not allowed:
        raise ValueError(f"brief input must be an ID or a repository briefs/<id>.json path: {token!r}")
    brief_id = path.name[:-5]
    if not ID_RE.fullmatch(brief_id):
        raise ValueError(f"unsafe brief ID: {brief_id!r}")
    return brief_id


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
    today: dt.date | None = None,
    now: dt.datetime | None = None,
) -> dict:
    """Validate the complete input plan before capture download or any render runner starts."""
    root = Path(repo_root or REPO_ROOT).resolve()
    brief_root = Path(briefs_root or (root / "reels-studio/briefs")).resolve()
    tokens = str(raw_briefs).replace(",", " ").split()
    ids = [_brief_id(token) for token in tokens]
    if not ids:
        raise ValueError("no brief IDs supplied")
    if len(ids) > MAX_BATCH:
        raise ValueError(f"batch has {len(ids)} briefs; daily cap is {MAX_BATCH}")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate brief IDs would collide in the render folder")

    loaded: dict[str, dict] = {}
    brief_hashes: dict[str, str] = {}
    for brief_id in ids:
        path = brief_root / f"{brief_id}.json"
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"unknown or unsafe brief ID: {brief_id}")
        try:
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(brief_root):
                raise ValueError(f"brief path escapes briefs directory: {brief_id}")
            raw = resolved.read_bytes()
            brief = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"brief is unreadable: {path}: {exc}") from exc
        if not isinstance(brief, dict) or brief.get("id") != brief_id:
            raise ValueError(f"brief ID mismatch in {path}")
        loaded[brief_id] = brief
        brief_hashes[brief_id] = hashlib.sha256(raw).hexdigest()

    quality = str(quality).strip()
    if quality not in QUALITY:
        raise ValueError(f"quality must be one of {', '.join(sorted(QUALITY))}")
    if isinstance(crf, bool):
        raise ValueError("CRF must be an integer from 0 through 51")
    try:
        crf_value = int(crf)
    except (TypeError, ValueError) as exc:
        raise ValueError("CRF must be an integer from 0 through 51") from exc
    if str(crf).strip() not in {str(crf_value), f"+{crf_value}"} or not 0 <= crf_value <= 51:
        raise ValueError("CRF must be an integer from 0 through 51")

    tag = str(tag or "").strip()
    from_tag = str(from_tag or "").strip()
    for label, value in (("tag", tag), ("from_tag", from_tag)):
        if value and not TAG_RE.fullmatch(value):
            raise ValueError(f"invalid {label}")
    if not tag:
        day = today or dt.datetime.now(ZoneInfo("Asia/Karachi")).date()
        tag = "renders-" + day.strftime("%Y-%m-%d")

    scenes = str(rebuild_scenes or "").replace(",", " ").split()
    reason = str(rebuild_reason or "").strip()
    receipt = str(production_receipt or "").strip()
    if scenes:
        if len(ids) != 1 or not reason:
            raise ValueError("scene rebuild requires exactly one brief and a non-empty rebuild reason")
        if len(reason) < 4 or len(reason) > 240 or any(ord(ch) < 32 or ord(ch) == 127 for ch in reason):
            raise ValueError("rebuild reason must be 4-240 printable characters")
        if len(scenes) != len(set(scenes)) or any(not SCENE_RE.fullmatch(scene) for scene in scenes):
            raise ValueError("scene IDs must be safe and unique")
        available = {scene.get("id") for scene in loaded[ids[0]].get("scenes", []) if isinstance(scene, dict)}
        missing = sorted(set(scenes) - available)
        if missing:
            raise ValueError(f"unknown scene ID(s) for {ids[0]}: {', '.join(missing)}")
        if receipt:
            raise ValueError("production_receipt is for full renders; scene rebuilds use their published source kit")
    else:
        if reason or from_tag:
            raise ValueError("rebuild_reason/from_tag require rebuild_scenes")
        if not receipt:
            raise ValueError("new renders require a six-stage production receipt")

    asset_hashes: dict[str, dict] = {}
    if not scenes:
        result = production_gate.validate_receipt(root, receipt, ids, now=now)
        asset_hashes = {
            brief_id: {
                "manifest_sha256": row["asset_manifest_sha256"],
                "files_sha256": row["asset_files_sha256"],
                "capture_id": row["capture_id"],
            }
            for brief_id, row in result["briefs"].items()
        }

    plan = {
        "briefs": ids,
        "tag": tag,
        "quality": quality,
        "crf": crf_value,
        "rebuild_scenes": scenes,
        "rebuild_reason": reason,
        "from_tag": from_tag,
        "production_receipt": receipt if not scenes else "",
    }
    plan["attempts"] = render_attempts.make_attempts(root, plan, loaded, brief_hashes, asset_hashes)
    return plan


def main() -> int:
    try:
        if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
            if os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
                raise ValueError("render plan accepts workflow_dispatch only")
            if os.environ.get("GITHUB_REF") != "refs/heads/main":
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
        if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
            render_attempts.check_remote(plan["attempts"])
        if os.environ.get("RECORD_ATTEMPT", "").lower() == "true":
            run_id = os.environ.get("GITHUB_RUN_ID", "")
            render_attempts.reserve_remote(plan["attempts"], run_id)
            fingerprints = [attempt["fingerprint"] for attempt in plan["attempts"]]
            print("attempt_fingerprints=" + json.dumps(fingerprints, separators=(",", ":")))
    except (ValueError, RuntimeError, OSError, TypeError, KeyError) as exc:
        print(f"dispatch rejected: {exc}", file=sys.stderr)
        return 2

    print("briefs=" + json.dumps(plan["briefs"], separators=(",", ":")))
    print("tag=" + plan["tag"])
    print("quality=" + plan["quality"])
    print("crf=" + str(plan["crf"]))
    print("rebuild_scenes=" + " ".join(plan["rebuild_scenes"]))
    print("from_tag=" + plan["from_tag"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
