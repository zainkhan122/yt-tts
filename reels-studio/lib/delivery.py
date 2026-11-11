"""Fail-closed verification and promotion of cloud render artifacts.

A green workflow is not a delivered render: verify the complete post kit and every
manifest gate before placing anything under renders/<id> or deleting the source artifact.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path


CORE_CHECKS = {
    "1080x1920",
    "30fps",
    "h264+aac",
    "duration_matches",
    "loudness_-14±1",
    "peak<=-1dBFS",
    "frame0_visible",
}
REQUIRED_FILES = ("cover.jpg", "contact.jpg", "captions.srt", "post.md", "seo.md", "manifest.json")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SNAPSHOT_EXCLUDED_DIRS = {
    ".arena", ".cache", ".local", ".mypy_cache", ".next", ".nox", ".npm", ".nuxt",
    ".output", ".parcel-cache", ".pytest_cache", ".ruff_cache", ".svelte-kit", ".tox",
    ".turbo", ".venv", ".vite", "__pycache__", "build", "coverage", "dist",
    "node_modules", "out", "target",
}
SNAPSHOT_LIMIT_BYTES = 128_000_000
SNAPSHOT_RESERVE_BYTES = 8_000_000


class DeliveryError(ValueError):
    """An artifact is incomplete, unsafe to install, or did not pass its manifest gates."""


def validate_ids(ids: list[str], *, max_batch: int = 10) -> list[str]:
    """Require a non-empty, unique, safe batch within the owner-authorized daily cap."""
    if not ids:
        raise DeliveryError("no brief IDs supplied")
    if len(ids) > max_batch:
        raise DeliveryError(f"batch has {len(ids)} briefs; daily cap is {max_batch}")
    bad = [x for x in ids if not isinstance(x, str) or not ID_RE.fullmatch(x)]
    if bad:
        raise DeliveryError(f"unsafe brief ID(s): {bad!r}")
    if len(ids) != len(set(ids)):
        raise DeliveryError("duplicate brief IDs would collide in the render folder")
    return list(ids)


def workspace_size_bytes(root: Path | None = None) -> int:
    """Count snapshot-relevant bytes; match Arena's excluded cache/build directory policy."""
    root = Path(root or Path.home())
    total = 0
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if name not in SNAPSHOT_EXCLUDED_DIRS]
        for name in files:
            try:
                total += (Path(current) / name).lstat().st_size
            except OSError:
                continue
    return total


def require_workspace_capacity(
    root: Path,
    additional_bytes: int,
    *,
    limit_bytes: int = SNAPSHOT_LIMIT_BYTES,
    reserve_bytes: int = SNAPSHOT_RESERVE_BYTES,
) -> dict:
    """Stop before an artifact download would exceed the snapshot budget or its safety reserve."""
    if additional_bytes < 0 or reserve_bytes < 0 or limit_bytes <= reserve_bytes:
        raise DeliveryError("invalid workspace capacity parameters")
    used = workspace_size_bytes(root)
    projected = used + additional_bytes
    safe_limit = limit_bytes - reserve_bytes
    if projected > safe_limit:
        raise DeliveryError(
            f"workspace would exceed its safe budget: {used / 1e6:.1f} MB used + "
            f"{additional_bytes / 1e6:.1f} MB estimated > {safe_limit / 1e6:.1f} MB "
            f"(snapshot limit {limit_bytes / 1e6:.0f} MB; {reserve_bytes / 1e6:.0f} MB reserved)"
        )
    return {"used_bytes": used, "additional_bytes": additional_bytes,
            "projected_bytes": projected, "safe_limit_bytes": safe_limit}


def require_success(result: str | None) -> None:
    """Do not let a failed or timed-out Actions run exit as a successful delivery."""
    if result != "success":
        status = "timed out / still running" if result is None else str(result)
        raise DeliveryError(f"cloud workflow result is {status}; no render delivery is confirmed")


def ensure_destinations_unused(render_root: Path, ids: list[str]) -> None:
    """Refuse to merge an artifact into stale files or overwrite a previous render."""
    root = Path(render_root)
    validate_ids(ids)
    for brief_id in ids:
        dest = root / brief_id
        if dest.is_symlink():
            raise DeliveryError(f"refusing symlink destination: {dest}")
        if dest.exists():
            raise DeliveryError(f"render destination already exists; refusing to merge/overwrite: {dest}")


def validate_render_dir(directory: Path, brief_id: str, *, require_approved_voice: bool = False) -> dict:
    """Check required files, identity, and all QA booleans; return a compact integrity record."""
    validate_ids([brief_id])
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise DeliveryError(f"render artifact directory missing or unsafe: {directory}")

    required = [f"{brief_id}.mp4", *REQUIRED_FILES]
    files: dict[str, Path] = {}
    for name in required:
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
            raise DeliveryError(f"{brief_id}: required artifact file missing/empty/unsafe: {name}")
        files[name] = path

    if files[f"{brief_id}.mp4"].stat().st_size < 1_000_000:
        raise DeliveryError(f"{brief_id}: MP4 is unexpectedly small; refusing incomplete artifact")

    try:
        manifest = json.loads(files["manifest.json"].read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeliveryError(f"{brief_id}: manifest is unreadable or invalid JSON: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("id") != brief_id:
        raise DeliveryError(f"{brief_id}: manifest identity mismatch")

    qa = manifest.get("qa")
    checks = qa.get("checks") if isinstance(qa, dict) else None
    if not isinstance(checks, dict):
        raise DeliveryError(f"{brief_id}: manifest has no QA checks")
    missing = sorted(CORE_CHECKS - checks.keys())
    if missing:
        raise DeliveryError(f"{brief_id}: manifest omits required QA check(s): {', '.join(missing)}")
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    if failed:
        raise DeliveryError(f"{brief_id}: manifest QA failed: {', '.join(failed)}")
    if require_approved_voice and checks.get("approved_voice") is not True:
        raise DeliveryError(f"{brief_id}: approved-voice gate is missing or false")

    try:
        duration = float(qa["duration"])
        size_mb = float(qa["size_mb"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DeliveryError(f"{brief_id}: manifest lacks valid duration/size metrics") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise DeliveryError(f"{brief_id}: invalid duration in manifest")
    actual_mb = files[f"{brief_id}.mp4"].stat().st_size / 1_000_000
    if not math.isfinite(size_mb) or size_mb <= 0 or abs(size_mb - actual_mb) > 0.15:
        raise DeliveryError(f"{brief_id}: manifest size does not match downloaded MP4 ({size_mb} vs {actual_mb:.2f} MB)")

    digest = hashlib.sha256()
    with files[f"{brief_id}.mp4"].open("rb") as video:
        for chunk in iter(lambda: video.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "id": brief_id,
        "duration_s": round(duration, 3),
        "mp4_bytes": files[f"{brief_id}.mp4"].stat().st_size,
        "mp4_sha256": digest.hexdigest(),
        "qa_passed": len(checks),
        "qa_total": len(checks),
    }


def promote_verified_batch(
    staging_root: Path,
    render_root: Path,
    ids: list[str],
    *,
    require_approved_voice_ids: set[str] | None = None,
) -> list[dict]:
    """Verify every staged artifact, then atomically install the whole batch or none of it."""
    ids = validate_ids(ids)
    require_approved_voice_ids = require_approved_voice_ids or set()
    if not require_approved_voice_ids <= set(ids):
        raise DeliveryError("approved-voice requirements contain an unknown brief ID")
    staging_root, render_root = Path(staging_root), Path(render_root)
    if staging_root.is_symlink() or not staging_root.is_dir():
        raise DeliveryError(f"unsafe staging directory: {staging_root}")
    ensure_destinations_unused(render_root, ids)

    sources = [staging_root / brief_id for brief_id in ids]
    receipts = []
    for brief_id, source in zip(ids, sources):
        if source.is_symlink() or not source.is_dir():
            raise DeliveryError(f"staged directory missing/unsafe: {source}")
        try:
            source.resolve().relative_to(staging_root.resolve())
        except ValueError as exc:
            raise DeliveryError(f"staged path escapes temporary root: {source}") from exc
        receipts.append(validate_render_dir(source, brief_id,
                                            require_approved_voice=brief_id in require_approved_voice_ids))

    render_root.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    try:
        for brief_id in ids:
            os.replace(staging_root / brief_id, render_root / brief_id)
            moved.append(brief_id)
    except OSError as exc:
        for brief_id in reversed(moved):
            os.replace(render_root / brief_id, staging_root / brief_id)
        raise DeliveryError(f"could not atomically install verified batch: {exc}") from exc
    return receipts
