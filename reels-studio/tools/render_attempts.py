#!/usr/bin/env python3
"""Persistent idempotency guard for full renders and scene repairs.

A failed or completed input fingerprint cannot be dispatched again unchanged. A substantive
brief/voice-seed/asset/renderer change produces a new fingerprint. Commits use GitHub's
compare-and-swap Contents API; concurrency or write uncertainty fails closed.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

REGISTRY_PATH = "reels-studio/tracker/render-attempts.json"
RENDER_CODE_FIXED = (
    ".github/workflows/render.yml",
    "reels-studio/reels.py",
    "reels-studio/lib/pipeline.py",
    "reels-studio/lib/scenes.py",
    "reels-studio/lib/framecheck.py",
    "reels-studio/lib/synth.py",
    "reels-studio/lib/gates.py",
    "reels-studio/config/channel.json",
    "reels-studio/cloud/setup-render.sh",
    "reels-studio/setup/setup-whisper.sh",
    "reels-studio/setup/setup-sandbox.sh",
    "reels-studio/tools/capture_store.py",
    "reels-studio/tools/seo_pack.py",
    "reels-studio/tools/production_gate.py",
    "reels-studio/tools/publish_verified_batch.py",
    "reels-studio/brand/voice/michael-ref.wav",
)


class DuplicateRenderError(ValueError):
    """The exact same render inputs already have a durable attempt receipt."""


def iso_now(now: dt.datetime | None = None) -> str:
    return (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def renderer_fingerprint(repo_root: Path) -> str:
    root = Path(repo_root).resolve()
    rows = []
    paths = list(RENDER_CODE_FIXED)
    template_root = root / "reels-studio/templates"
    if not template_root.is_dir():
        raise ValueError("renderer fingerprint cannot find reels-studio/templates")
    for path in template_root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"renderer fingerprint input is an unsafe symlink: {path.relative_to(root)}")
        if path.is_file():
            paths.append(path.relative_to(root).as_posix())
    for rel in sorted(set(paths)):
        path = root / rel
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"renderer fingerprint input missing/unsafe: {rel}")
        rows.append({"path": rel, "sha256": _sha(path.read_bytes())})
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha(encoded)


def make_attempts(repo_root: Path, plan: dict, loaded_briefs: dict[str, dict], brief_hashes: dict[str, str],
                  asset_hashes: dict[str, object] | None = None) -> list[dict]:
    code_sha = renderer_fingerprint(repo_root)
    asset_hashes = asset_hashes or {}
    attempts = []
    for brief_id in plan["briefs"]:
        brief = loaded_briefs[brief_id]
        raw_seed = brief.get("voice_seed", 0)
        if isinstance(raw_seed, bool) or not isinstance(raw_seed, int):
            raise ValueError(f"{brief_id}: voice_seed must be a non-negative integer")
        voice_seed = raw_seed
        if not 0 <= voice_seed <= 1_000_000:
            raise ValueError(f"{brief_id}: voice_seed must be between 0 and 1000000")
        asset = asset_hashes.get(brief_id)
        if isinstance(asset, dict):
            asset_manifest_sha = asset.get("manifest_sha256")
            asset_files_sha = asset.get("files_sha256")
            capture_id = asset.get("capture_id")
        else:  # supports scene-rebuild tests and older local callers; new-render plans pass all three fields
            asset_manifest_sha = asset
            asset_files_sha = None
            capture_id = None
        payload = {
            "brief_id": brief_id,
            "brief_sha256": brief_hashes[brief_id],
            "voice_seed": voice_seed,
            "renderer_sha256": code_sha,
            "quality": plan["quality"],
            "crf": int(plan["crf"]),
            "asset_manifest_sha256": asset_manifest_sha,
            "asset_files_sha256": asset_files_sha,
            "capture_id": capture_id,
            "cover_sha256": asset.get("cover_sha256") if isinstance(asset, dict) else None,
            "rebuild_scenes": list(plan.get("rebuild_scenes") or []),
            "from_tag": plan.get("from_tag", ""),
        }
        fingerprint = _sha(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        attempts.append({**payload, "fingerprint": fingerprint})
    return attempts


def _registry_defaults(registry: dict) -> dict:
    if not isinstance(registry, dict) or registry.get("schema_version") != 1:
        raise ValueError("render attempt registry has an unsupported schema")
    if not isinstance(registry.get("attempts"), dict):
        raise ValueError("render attempt registry attempts field must be an object")
    if not isinstance(registry.get("legacy_completed_briefs", []), list):
        raise ValueError("render attempt registry legacy_completed_briefs must be a list")
    return registry


def check_registry(registry: dict, attempts: list[dict]) -> None:
    registry = _registry_defaults(registry)
    known = registry["attempts"]
    legacy = registry.get("legacy_completed_briefs", [])
    for candidate in attempts:
        is_scene_rebuild = bool(candidate.get("rebuild_scenes"))
        if not is_scene_rebuild:
            for old in legacy:
                if (old.get("brief_sha256") == candidate.get("brief_sha256")
                        and int(old.get("voice_seed", 0)) == int(candidate.get("voice_seed", 0))):
                    raise DuplicateRenderError(
                        f"{candidate['brief_id']}: identical brief/voice seed already has a verified render "
                        f"(run {old.get('run_id', 'unknown')}, release {old.get('release_tag', 'unknown')}); "
                        "edit the content/voice seed for a new version, or use the reasoned scene-rebuild path"
                    )
        previous = known.get(candidate["fingerprint"])
        if previous:
            kind = "scene rebuild" if is_scene_rebuild else "render"
            recovery = ("correct the scene source or renderer before another rebuild" if is_scene_rebuild else
                        "correct the source, change the approved voice seed, or fix the renderer before a new dispatch")
            raise DuplicateRenderError(
                f"{candidate['brief_id']}: identical {kind} inputs already attempted in run "
                f"{previous.get('run_id', 'unknown')} ({previous.get('status', 'unknown')}); "
                f"do not retry the same inputs: {recovery}"
            )


def reserve_in_registry(registry: dict, attempts: list[dict], run_id: str, *, now: dt.datetime | None = None) -> dict:
    registry = _registry_defaults(json.loads(json.dumps(registry)))
    check_registry(registry, attempts)
    if not re.fullmatch(r"[0-9]{1,24}", str(run_id)):
        raise ValueError("run_id must be a numeric GitHub Actions ID")
    started = iso_now(now)
    for row in attempts:
        registry["attempts"][row["fingerprint"]] = {
            **row,
            "run_id": str(run_id),
            "status": "started",
            "started_at": started,
            "finished_at": None,
            "failure_conclusion": None,
        }
    return registry


def finish_in_registry(registry: dict, run_id: str, status: str, *, conclusion: str | None = None,
                       now: dt.datetime | None = None) -> dict:
    registry = _registry_defaults(json.loads(json.dumps(registry)))
    if status not in {"success", "render_only_success", "failed", "render_succeeded_publish_failed", "scene_rebuild_success", "cancelled"}:
        raise ValueError(f"invalid attempt completion status: {status}")
    changed = 0
    for row in registry["attempts"].values():
        if str(row.get("run_id")) == str(run_id) and row.get("status") == "started":
            row["status"] = status
            row["finished_at"] = iso_now(now)
            row["failure_conclusion"] = conclusion
            changed += 1
    if not changed:
        raise ValueError(f"no started render attempt found for run {run_id}")
    return registry


def _remote_registry(branch="main"):
    parent = str(Path(__file__).resolve().parents[1])  # reels-studio/: makes `tools` importable when run as a script
    if parent not in sys.path:
        sys.path.insert(0, parent)
    from tools import gh_actions
    status, body = gh_actions.api("GET", f"/contents/{REGISTRY_PATH}?ref={branch}")
    if status != 200:
        raise RuntimeError(f"cannot read render attempt registry from {branch} (HTTP {status})")
    try:
        raw = base64.b64decode(body.get("content", ""))
        registry = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("remote render attempt registry is unreadable") from exc
    return gh_actions, registry, body.get("sha"), raw


def _save_remote(gh_actions, registry: dict, sha: str, *, branch="main", message="render: update attempt registry") -> None:
    raw = (json.dumps(registry, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    payload = {"message": message[:120], "branch": branch, "sha": sha,
               "content": base64.b64encode(raw).decode("ascii")}
    status, body = gh_actions.api("PUT", f"/contents/{REGISTRY_PATH}", payload)
    if status != 200:
        raise RuntimeError(f"render attempt registry update failed/conflicted (HTTP {status}); no render may start")


def check_remote(attempts: list[dict], *, branch="main") -> None:
    _, registry, _, _ = _remote_registry(branch)
    check_registry(registry, attempts)


def reserve_remote(attempts: list[dict], run_id: str, *, branch="main", now: dt.datetime | None = None) -> None:
    gh_actions, registry, sha, _ = _remote_registry(branch)
    updated = reserve_in_registry(registry, attempts, run_id, now=now)
    _save_remote(gh_actions, updated, sha, branch=branch, message=f"render: reserve attempt(s) for Actions run {run_id}")


def finish_remote(run_id: str, status: str, *, conclusion: str | None = None, branch="main",
                  now: dt.datetime | None = None) -> None:
    gh_actions, registry, sha, _ = _remote_registry(branch)
    updated = finish_in_registry(registry, run_id, status, conclusion=conclusion, now=now)
    _save_remote(gh_actions, updated, sha, branch=branch, message=f"render: record {status} for Actions run {run_id}")


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("finish", help="finalize reserved attempt fingerprints from a completed render workflow")
    p.add_argument("--run-id", required=True)
    p.add_argument("--status", required=True, choices=["success", "render_only_success", "failed", "render_succeeded_publish_failed", "scene_rebuild_success", "cancelled"])
    p.add_argument("--conclusion", default="")
    args = parser.parse_args(argv)
    try:
        finish_remote(args.run_id, args.status, conclusion=args.conclusion or None)
    except Exception as exc:
        print(f"render attempt ledger update failed safely: {type(exc).__name__}: {exc}", file=__import__("sys").stderr)
        return 2
    print(f"render attempt ledger updated for run {args.run_id}: {args.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
