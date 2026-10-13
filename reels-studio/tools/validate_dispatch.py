#!/usr/bin/env python3
"""Fail-closed validator used by both GitHub Actions dispatch planning and tests."""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.delivery import DeliveryError, validate_ids  # noqa: E402

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
    briefs_root: Path | None = None,
    today: datetime.date | None = None,
) -> dict:
    """Validate workflow inputs and every named brief before any render runner starts."""
    briefs_root = Path(briefs_root or ROOT / "briefs")
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

    loaded = {}
    for brief_id in ids:
        path = briefs_root / f"{brief_id}.json"
        if not path.is_file():
            raise ValueError(f"unknown brief ID: {brief_id}")
        try:
            brief = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"brief is unreadable: {path}: {exc}") from exc
        if not isinstance(brief, dict) or brief.get("id") != brief_id:
            raise ValueError(f"brief ID mismatch in {path}")
        loaded[brief_id] = brief

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
        day = today or datetime.datetime.now(datetime.timezone.utc).date()
        tag = "renders-" + day.strftime("%Y-%m-%d")
    return {"briefs": ids, "tag": tag, "quality": quality, "crf": crf_value,
            "rebuild_scenes": scenes, "from_tag": from_tag}


def main() -> int:
    import os
    try:
        plan = plan_dispatch(
            os.environ.get("BRIEFS", ""),
            tag=os.environ.get("TAG", ""),
            quality=os.environ.get("QUALITY", "looks"),
            crf=os.environ.get("CRF", "23"),
            rebuild_scenes=os.environ.get("REBUILD_SCENES", ""),
            rebuild_reason=os.environ.get("REBUILD_REASON", ""),
            from_tag=os.environ.get("FROM_TAG", ""),
        )
    except ValueError as exc:
        print(f"dispatch rejected: {exc}", file=sys.stderr)
        return 2
    print("briefs=" + json.dumps(plan["briefs"]))
    print("tag=" + plan["tag"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
