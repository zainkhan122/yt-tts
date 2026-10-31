#!/usr/bin/env python3
"""Validate a complete cloud batch, publish it as one GitHub Release, then remove staging artifacts.

The video files are only ever downloaded on the ephemeral Actions runner. They are not copied
into the user's workspace or committed to Git history. The Release is public for this repository.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.delivery import DeliveryError, validate_ids, validate_render_dir  # noqa: E402
from tools import gh_actions, publish_release  # noqa: E402

TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


def _load_brief(briefs_root: Path, brief_id: str) -> dict:
    path = briefs_root / f"{brief_id}.json"
    try:
        brief = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeliveryError(f"{brief_id}: brief is missing or invalid: {exc}") from exc
    if not isinstance(brief, dict) or brief.get("id") != brief_id:
        raise DeliveryError(f"{brief_id}: brief identity mismatch")
    return brief


def prepare_assets(brief_ids: list[str], tag: str, artifact_root: Path, briefs_root: Path) -> list[dict]:
    """Validate the entire batch before any Release is created or any temporary artifact is deleted."""
    ids = validate_ids(brief_ids)
    if not TAG_RE.fullmatch(tag):
        raise DeliveryError(f"invalid GitHub Release tag: {tag!r}")
    artifact_root, briefs_root = Path(artifact_root), Path(briefs_root)
    prepared = []
    for brief_id in ids:
        brief = _load_brief(briefs_root, brief_id)
        tts = brief.get("tts") or {}
        need_voice = bool(tts.get("engine")) and brief.get("voice") != "files"
        folder = artifact_root / f"render-{brief_id}"
        qa = validate_render_dir(folder, brief_id, require_approved_voice=need_voice)
        mp4_path = folder / f"{brief_id}.mp4"
        mp4 = mp4_path.read_bytes()
        kit_mem = io.BytesIO()
        with zipfile.ZipFile(kit_mem, "w", zipfile.ZIP_DEFLATED) as kit:
            for name in publish_release.KIT_FILES:
                path = folder / name
                if path.is_symlink():
                    raise DeliveryError(f"{brief_id}: refusing symlink in post kit: {name}")
                if path.is_file():
                    try:
                        path.resolve().relative_to(folder.resolve())
                    except ValueError as exc:
                        raise DeliveryError(f"{brief_id}: post-kit path escapes its artifact: {name}") from exc
                    kit.write(path, f"{brief_id}/{name}")
        kit_bytes = kit_mem.getvalue()
        if not kit_bytes:
            raise DeliveryError(f"{brief_id}: generated post kit is empty")
        prepared.append({
            "id": brief_id,
            "qa": qa,
            "assets": [
                {"name": f"{brief_id}.mp4", "bytes": mp4},
                {"name": f"{brief_id}-kit.zip", "bytes": kit_bytes},
            ],
        })
    return prepared


def _release_for_tag(tag: str, body: str) -> tuple[dict, bool]:
    """Return (release, is_draft). New releases start as drafts so partial uploads aren't public."""
    url = f"{publish_release.API}/releases/tags/{quote(tag, safe='')}"
    status, rel = publish_release.call("GET", url)
    if status == 200:
        return rel, bool(rel.get("draft"))
    if status != 404:
        raise SystemExit(f"release lookup failed: HTTP {status}: {rel.get('message', '')}")
    status, rel = publish_release.call("POST", f"{publish_release.API}/releases", {
        "tag_name": tag,
        "target_commitish": "main",
        "name": f"Daily Shorts — {tag.removeprefix('renders-')}",
        "body": body,
        "draft": True,
        "prerelease": False,
    })
    if status in (409, 422):  # race-safe retry if another workflow created the tag first
        status, rel = publish_release.call("GET", url)
        if status == 200:
            return rel, bool(rel.get("draft"))
    if status >= 300:
        raise SystemExit(f"could not create draft Release: HTTP {status}: {rel.get('message', '')}")
    return rel, True


def _verify_published_release(rel: dict, prepared: list[dict]) -> str:
    existing = {asset["name"]: asset for asset in rel.get("assets", [])}
    for item in prepared:
        for expected in item["assets"]:
            asset = existing.get(expected["name"])
            digest = "sha256:" + hashlib.sha256(expected["bytes"]).hexdigest()
            if not asset or asset.get("digest") != digest:
                raise SystemExit(
                    f"Release tag {rel.get('tag_name')} is already public but {expected['name']} "
                    "is missing or differs; refusing to mutate a published daily release. Use a new tag."
                )
    return rel["html_url"]


def _publish(prepared: list[dict], tag: str) -> str:
    details = [f"- `{x['id']}` — {x['qa']['duration_s']:.2f}s, "
               f"QA {x['qa']['qa_passed']}/{x['qa']['qa_total']}, "
               f"MP4 SHA-256 `{x['qa']['mp4_sha256'][:16]}…`" for x in prepared]
    body = (
        "QA-verified daily Shorts rendered by Reels Studio. Videos and post kits are attached below.\n\n"
        + "\n".join(details)
        + "\n\nThese are repository assets only; no Buffer scheduling or platform posting was performed."
    )
    rel, is_draft = _release_for_tag(tag, body)
    if not is_draft:
        return _verify_published_release(rel, prepared)

    for item in prepared:
        for asset in item["assets"]:
            publish_release.upload(rel, asset["name"], asset["bytes"], replace=True)
            status, rel = publish_release.call("GET", f"{publish_release.API}/releases/{rel['id']}")
            if status != 200:
                raise SystemExit(f"could not refresh draft Release assets: HTTP {status}")

    status, published = publish_release.call("PATCH", f"{publish_release.API}/releases/{rel['id']}",
                                              {"draft": False, "body": body})
    if status >= 300 or published.get("draft") is not False or not published.get("html_url"):
        raise SystemExit(f"could not publish completed draft Release: HTTP {status}: {published.get('message', '')}")
    status, published = publish_release.call("GET", f"{publish_release.API}/releases/{rel['id']}")
    if status != 200 or published.get("draft") is not False:
        raise SystemExit(f"published GitHub Release could not be verified: HTTP {status}")
    return _verify_published_release(published, prepared)


def finalize_batch(brief_ids: list[str], tag: str, artifact_root: Path, briefs_root: Path,
                   run_id: str | None = None) -> str:
    """Validate all artifacts, publish the immutable daily Release, then delete temporary copies."""
    prepared = prepare_assets(brief_ids, tag, artifact_root, briefs_root)
    url = _publish(prepared, tag)
    cleanup_warnings = []
    if run_id:
        for brief_id in brief_ids:
            try:
                gh_actions.delete_artifact(run_id, f"render-{brief_id}")
            except SystemExit as exc:
                cleanup_warnings.append(f"{brief_id}: {exc}")
    lines = [f"## Daily Shorts published to GitHub", f"Release: [{tag}]({url})", "",
             "MP4s were not downloaded into the user's workspace. No Buffer writes or social posts were made.", "",
             "| Short | Duration | Technical QA | SHA-256 |", "|---|---:|---:|---|"]
    lines.extend(f"| `{x['id']}` | {x['qa']['duration_s']:.2f}s | "
                 f"{x['qa']['qa_passed']}/{x['qa']['qa_total']} | `{x['qa']['mp4_sha256'][:16]}…` |" for x in prepared)
    if cleanup_warnings:
        lines += ["", "Temporary Actions artifact cleanup warning(s):", *[f"- {x}" for x in cleanup_warnings]]
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    print(f"GitHub Release: {url}")
    if cleanup_warnings:
        print("Warning: the Release is complete; one or more temporary Actions artifacts remain until expiry.")
    return url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--briefs-json", required=True, help="JSON list from the workflow plan job")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        brief_ids = json.loads(args.briefs_json)
        if not isinstance(brief_ids, list):
            raise ValueError("briefs-json must be a JSON array")
        finalize_batch(brief_ids, args.tag, args.artifact_root, ROOT / "briefs", args.run_id)
    except (ValueError, DeliveryError) as exc:
        raise SystemExit(f"batch publication refused: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
