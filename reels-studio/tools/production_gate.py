#!/usr/bin/env python3
"""Fail-closed pre-render contract for DISCOVER → SELECT → RESEARCH → SCRIPT → VOICE → ASSETS.

Receipts are repo-relative JSON under research/production/receipts/. This module has no
network/publishing capability; the render plan performs the Buffer snapshot and capture-pack
checks before any render runner is started.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
BUFFER_SNAPSHOT = "reels-studio/tracker/buffer-insights.json"
RECEIPT_PREFIX = "reels-studio/research/production/receipts/"
MIN_TOPIC_SCORE = 60
MIN_CHUNK_MATCH = 0.92
MIN_ENGLISH_OVERALL_MATCH = 0.95
MAX_INSIGHTS_AGE = dt.timedelta(hours=36)
MAX_DISCOVER_AGE = dt.timedelta(hours=36)
MAX_FACT_AGE = dt.timedelta(hours=24)
MAX_SOURCE_AGE = dt.timedelta(hours=72)
SCORE_WEIGHTS = {
    "trend_velocity": 25,
    "demo_ability": 20,
    "audience_breadth": 15,
    "social_proof_gap": 15,
    "free_value": 10,
    "freshness_angle": 15,
}
STAGES = ("discover", "select", "research", "script", "voice", "assets")
METRIC_DECISIONS = ("topic", "script", "voice", "visual")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class ProductionGateError(ValueError):
    """A stage receipt is incomplete, stale, mismatched, or unsafe to render."""


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _repo_path(repo_root: Path, raw: str, *, must_exist: bool = True) -> Path:
    if not isinstance(raw, str) or not raw.strip() or "\\" in raw:
        raise ProductionGateError(f"unsafe/empty repo path: {raw!r}")
    posix = PurePosixPath(raw)
    if posix.is_absolute() or ".." in posix.parts or not posix.parts or ":" in posix.parts[0]:
        raise ProductionGateError(f"unsafe repo path: {raw!r}")
    root = Path(repo_root).resolve()
    candidate = root.joinpath(*posix.parts)
    try:
        resolved = candidate.resolve(strict=must_exist)
    except OSError as exc:
        raise ProductionGateError(f"evidence file is missing: {raw}") from exc
    if not resolved.is_relative_to(root):
        raise ProductionGateError(f"repo path escapes checkout: {raw!r}")
    if must_exist and not resolved.is_file():
        raise ProductionGateError(f"evidence path is not a file: {raw}")
    return resolved


def _load_json(path: Path, label: str) -> tuple[dict, bytes]:
    try:
        raw = Path(path).read_bytes()
        obj = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductionGateError(f"{label} is unreadable/invalid JSON: {path}") from exc
    if not isinstance(obj, dict):
        raise ProductionGateError(f"{label} must be a JSON object")
    return obj, raw


def parse_utc(value: str, label: str) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise ProductionGateError(f"{label} timestamp is missing")
    try:
        stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProductionGateError(f"{label} timestamp is invalid: {value!r}") from exc
    if stamp.tzinfo is None:
        raise ProductionGateError(f"{label} timestamp must include a timezone")
    return stamp.astimezone(dt.timezone.utc)


def require_fresh(value: str, label: str, max_age: dt.timedelta, now: dt.datetime) -> dt.datetime:
    stamp = parse_utc(value, label)
    age = now.astimezone(dt.timezone.utc) - stamp
    if age < -dt.timedelta(minutes=5):
        raise ProductionGateError(f"{label} timestamp is in the future")
    if age > max_age:
        raise ProductionGateError(f"{label} is stale ({age.total_seconds() / 3600:.1f}h; max {max_age.total_seconds() / 3600:.0f}h)")
    return stamp


SCRIPT_MARKUP_RE = re.compile(r"\{([^{}|]+)\|([^{}]+)\}")
SCRIPT_SYMBOL_RE = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]")


def _spoken_script_lines(brief: dict) -> list[dict[str, str]]:
    """Return the same ordered scene text used by SCRIPT hashing and word-count validation."""
    scenes = brief.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ProductionGateError("brief has no scenes for SCRIPT hash")
    lines = []
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise ProductionGateError(f"brief scene {index + 1} is not an object")
        text = scene.get("say", scene.get("spoken", scene.get("text", "")))
        if text is None or text == "":
            continue
        if not isinstance(text, str):
            raise ProductionGateError(f"brief scene {scene.get('id', index)} spoken text is not a string")
        lines.append({"id": str(scene.get("id", index)), "text": text})
    if not lines:
        raise ProductionGateError("brief has no spoken text for SCRIPT hash")
    return lines


def script_sha256(brief: dict) -> str:
    """Hash the exact spoken forms in scene order (including explicit display|spoken markup)."""
    raw = json.dumps(_spoken_script_lines(brief), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(raw)


def script_word_count(brief: dict) -> int:
    """Count spoken tokens exactly as the renderer does after display|spoken markup and emoji removal."""
    count = 0
    for line in _spoken_script_lines(brief):
        text = SCRIPT_MARKUP_RE.sub(lambda match: match.group(2).strip(), line["text"])
        text = SCRIPT_SYMBOL_RE.sub("", text)
        count += len(text.split())
    if count <= 0:
        raise ProductionGateError("brief has no spoken words for SCRIPT word_count")
    return count


def _source_urls(brief: dict) -> set[str]:
    out: set[str] = set()
    for src in brief.get("sources", []) if isinstance(brief.get("sources", []), list) else []:
        if isinstance(src, str) and src.startswith("https://"):
            out.add(src)
        elif isinstance(src, dict):
            for key in ("url", "href", "source_url"):
                val = src.get(key)
                if isinstance(val, str) and val.startswith("https://"):
                    out.add(val)
    return out


def _require_evidence(repo_root: Path, evidence, label: str) -> list[str]:
    if not isinstance(evidence, list) or not evidence:
        raise ProductionGateError(f"{label} evidence list is empty")
    paths = []
    for raw in evidence:
        path = _repo_path(repo_root, raw)
        paths.append(str(raw))
    return paths


def _require_decisions(decisions, label: str) -> dict:
    if not isinstance(decisions, dict):
        raise ProductionGateError(f"{label} metrics_decisions must be an object")
    result = {}
    for key in METRIC_DECISIONS:
        value = decisions.get(key)
        if not isinstance(value, str) or len(value.strip()) < 15:
            raise ProductionGateError(f"{label} must state a substantive metrics decision for {key}")
        if value.strip().lower() in {"todo", "tbd", "n/a", "none"}:
            raise ProductionGateError(f"{label} metrics decision for {key} is a placeholder")
        result[key] = value.strip()
    return result


def _load_backlog(repo_root: Path) -> list[dict]:
    path = _repo_path(repo_root, "reels-studio/topics/backlog.csv")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except OSError as exc:
        raise ProductionGateError("topics/backlog.csv is unreadable") from exc


def _validate_buffer_snapshot(repo_root: Path, receipt: dict, now: dt.datetime) -> tuple[dict, str]:
    ref = receipt.get("buffer_insights")
    if not isinstance(ref, dict):
        raise ProductionGateError("receipt is missing buffer_insights reference")
    path_text = ref.get("path")
    if path_text != BUFFER_SNAPSHOT:
        raise ProductionGateError(f"buffer_insights.path must be {BUFFER_SNAPSHOT}")
    path = _repo_path(repo_root, path_text)
    snapshot, raw = _load_json(path, "Buffer Insights snapshot")
    digest = sha256_bytes(raw)
    if ref.get("sha256") != digest:
        raise ProductionGateError("Buffer Insights snapshot hash does not match the production receipt")
    if snapshot.get("schema_version") != 1 or snapshot.get("complete") is not True:
        raise ProductionGateError("Buffer Insights snapshot is incomplete or has an unsupported schema")
    require_fresh(snapshot.get("fetched_at"), "Buffer Insights snapshot", MAX_INSIGHTS_AGE, now)
    posts = snapshot.get("posts")
    if not isinstance(posts, dict) or not posts:
        raise ProductionGateError("Buffer Insights snapshot contains no video posts")
    if snapshot.get("video_post_count") != len(posts):
        raise ProductionGateError("Buffer Insights post count does not match the saved posts")
    if snapshot.get("missing_expected_post_ids"):
        raise ProductionGateError("Buffer Insights is missing one or more sent posts; refresh Insights before production")
    if snapshot.get("metrics_coverage_ok") is not True:
        raise ProductionGateError("Buffer Insights per-channel metric coverage is incomplete")
    coverage = snapshot.get("coverage_by_platform")
    if not isinstance(coverage, dict) or not coverage:
        raise ProductionGateError("Buffer Insights has no per-platform coverage summary")
    for platform, row in coverage.items():
        if not isinstance(row, dict):
            raise ProductionGateError(f"Buffer Insights coverage for {platform} is invalid")
        total = row.get("total_video_posts")
        fresh = row.get("fresh_metric_posts")
        if (isinstance(total, bool) or not isinstance(total, int) or total < 0
                or isinstance(fresh, bool) or not isinstance(fresh, int) or fresh < 0 or fresh > total):
            raise ProductionGateError(f"Buffer Insights coverage counts for {platform} are invalid")
        if total > 0 and fresh < 1:
            raise ProductionGateError(f"Buffer Insights has no fresh metrics for {platform}")
    return snapshot, digest


def _validate_metrics_review(review: dict, snapshot: dict, snapshot_sha: str) -> None:
    if not isinstance(review, dict):
        raise ProductionGateError("receipt is missing metrics_review")
    if review.get("snapshot_sha256") != snapshot_sha:
        raise ProductionGateError("metrics_review does not reference the current Buffer snapshot")
    expected = len(snapshot["posts"])
    if review.get("reviewed_video_count") != expected:
        raise ProductionGateError(f"metrics_review must cover all {expected} shared videos")
    samples = review.get("sample_post_ids")
    if not isinstance(samples, list) or not samples or any(pid not in snapshot["posts"] for pid in samples):
        raise ProductionGateError("metrics_review sample_post_ids must refer to Buffer posts in the current snapshot")
    findings = review.get("findings")
    if not isinstance(findings, list) or not findings or any(not isinstance(x, str) or len(x.strip()) < 15 for x in findings):
        raise ProductionGateError("metrics_review needs concrete, data-backed findings")
    _require_decisions(review.get("decisions"), "metrics_review")


def validate_receipt(
    repo_root: Path,
    receipt_path: str,
    brief_ids: list[str],
    *,
    now: dt.datetime | None = None,
    verify_assets: bool = False,
) -> dict:
    """Verify fresh Insights, each score/stage, research links, exact script, and optional capture bytes."""
    root = Path(repo_root).resolve()
    if not receipt_path.startswith(RECEIPT_PREFIX):
        raise ProductionGateError(f"production receipt must be under {RECEIPT_PREFIX}")
    receipt_file = _repo_path(root, receipt_path)
    receipt, receipt_raw = _load_json(receipt_file, "production receipt")
    if receipt.get("schema_version") != 1:
        raise ProductionGateError("unsupported production receipt schema_version")
    batch_id = receipt.get("batch_id")
    if not isinstance(batch_id, str) or not batch_id or receipt_file.stem != batch_id:
        raise ProductionGateError("receipt batch_id must match its filename")
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    require_fresh(receipt.get("created_at"), "production receipt", MAX_INSIGHTS_AGE, now)

    snapshot, snapshot_sha = _validate_buffer_snapshot(root, receipt, now)
    _validate_metrics_review(receipt.get("metrics_review"), snapshot, snapshot_sha)
    receipt_briefs = receipt.get("briefs")
    if not isinstance(receipt_briefs, dict) or set(receipt_briefs) != set(brief_ids):
        raise ProductionGateError("receipt brief IDs must exactly match the dispatch batch")
    backlog = _load_backlog(root)
    summary = {"batch_id": batch_id, "receipt_sha256": sha256_bytes(receipt_raw),
               "buffer_insights_sha256": snapshot_sha, "briefs": {}}

    for brief_id in brief_ids:
        item = receipt_briefs.get(brief_id)
        if not isinstance(item, dict):
            raise ProductionGateError(f"receipt entry is missing for {brief_id}")
        brief_path = _repo_path(root, f"reels-studio/briefs/{brief_id}.json")
        brief, brief_raw = _load_json(brief_path, f"brief {brief_id}")
        if brief.get("id") != brief_id:
            raise ProductionGateError(f"brief ID mismatch for {brief_id}")
        actual_brief_sha = sha256_bytes(brief_raw)
        if item.get("brief_sha256") != actual_brief_sha:
            raise ProductionGateError(f"{brief_id}: brief changed after the production stages; refresh the receipt")

        stages = item.get("stages")
        if not isinstance(stages, dict) or set(stages) != set(STAGES):
            raise ProductionGateError(f"{brief_id}: receipt must contain exactly the six production stages")
        for stage_name in STAGES:
            stage = stages[stage_name]
            if not isinstance(stage, dict) or stage.get("status") != "complete":
                raise ProductionGateError(f"{brief_id}: {stage_name.upper()} is not complete")

        discover = stages["discover"]
        require_fresh(discover.get("checked_at"), f"{brief_id} DISCOVER evidence", MAX_DISCOVER_AGE, now)
        discover_evidence = _require_evidence(root, discover.get("evidence"), f"{brief_id} DISCOVER")
        if not any(needle in path for path in discover_evidence for needle in
                   ("reels-studio/research/ideas/", "reels-studio/research/radar/", "reels-studio/research/social/")):
            raise ProductionGateError(f"{brief_id}: DISCOVER must cite an idea feed, radar, or social scan")

        select = stages["select"]
        if select.get("selection_status") != "selected":
            raise ProductionGateError(f"{brief_id}: SELECT must explicitly mark the topic as selected")
        score = select.get("score")
        if isinstance(score, bool) or not isinstance(score, int) or not MIN_TOPIC_SCORE <= score <= 100:
            raise ProductionGateError(f"{brief_id}: topic score must be an integer from {MIN_TOPIC_SCORE} to 100")
        breakdown = select.get("score_breakdown")
        if not isinstance(breakdown, dict) or set(breakdown) != set(SCORE_WEIGHTS):
            raise ProductionGateError(f"{brief_id}: SELECT score_breakdown must use the PIPELINE.md rubric")
        for criterion, maximum in SCORE_WEIGHTS.items():
            value = breakdown.get(criterion)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
                raise ProductionGateError(f"{brief_id}: SELECT {criterion} must be an integer from 0 to {maximum}")
        if sum(breakdown.values()) != score:
            raise ProductionGateError(f"{brief_id}: SELECT score does not equal its rubric breakdown")
        if select.get("metrics_snapshot_sha256") != snapshot_sha:
            raise ProductionGateError(f"{brief_id}: SELECT must reference the current Buffer Insights snapshot")
        basis = select.get("basis_post_ids")
        if not isinstance(basis, list) or not basis or any(pid not in snapshot["posts"] for pid in basis):
            raise ProductionGateError(f"{brief_id}: SELECT must cite Buffer posts used as performance evidence")
        hard = select.get("hard_gates")
        if not isinstance(hard, dict) or any(hard.get(key) is not True for key in
                ("risk_flags_clear", "claim_verifiable", "license_clear")):
            raise ProductionGateError(f"{brief_id}: SELECT has an unresolved automatic hard gate")
        matches = [row for row in backlog if row.get("video_id", "").strip() == brief_id]
        if len(matches) != 1:
            raise ProductionGateError(f"{brief_id}: topics/backlog.csv must have exactly one scored row with video_id={brief_id}")
        try:
            backlog_score = int(matches[0].get("score", ""))
        except (TypeError, ValueError) as exc:
            raise ProductionGateError(f"{brief_id}: backlog score is missing or not numeric") from exc
        if backlog_score != score:
            raise ProductionGateError(f"{brief_id}: backlog score {backlog_score} does not match receipt score {score}")
        if (matches[0].get("status") or "").strip().lower() != "selected":
            raise ProductionGateError(f"{brief_id}: topics/backlog.csv status must be selected before rendering")
        backlog_topic = (matches[0].get("topic") or "").strip()
        if not backlog_topic or select.get("topic") != backlog_topic:
            raise ProductionGateError(f"{brief_id}: SELECT topic must exactly match the selected backlog topic")

        research = stages["research"]
        _require_evidence(root, research.get("evidence"), f"{brief_id} RESEARCH")
        require_fresh(research.get("dynamic_facts_checked_at"), f"{brief_id} dynamic facts", MAX_FACT_AGE, now)
        primary = research.get("primary_sources")
        if not isinstance(primary, list) or not primary:
            raise ProductionGateError(f"{brief_id}: RESEARCH needs at least one verified primary source")
        brief_urls = _source_urls(brief)
        for source in primary:
            if not isinstance(source, dict) or not isinstance(source.get("url"), str) or not source["url"].startswith("https://"):
                raise ProductionGateError(f"{brief_id}: RESEARCH primary source must be an HTTPS URL")
            if source["url"] not in brief_urls:
                raise ProductionGateError(f"{brief_id}: primary source is not recorded in the brief sources list")
            require_fresh(source.get("checked_at"), f"{brief_id} primary source", MAX_SOURCE_AGE, now)
            if not isinstance(source.get("claim"), str) or len(source["claim"].strip()) < 8:
                raise ProductionGateError(f"{brief_id}: primary source must identify the verified claim")

        script = stages["script"]
        exact_script_sha = script_sha256(brief)
        if script.get("script_sha256") != exact_script_sha:
            raise ProductionGateError(f"{brief_id}: SCRIPT hash does not match the brief's spoken lines")
        exact_word_count = script_word_count(brief)
        receipt_word_count = script.get("word_count")
        if (isinstance(receipt_word_count, bool) or not isinstance(receipt_word_count, int)
                or receipt_word_count != exact_word_count):
            raise ProductionGateError(
                f"{brief_id}: SCRIPT word_count must equal the {exact_word_count} spoken words in the current brief"
            )

        voice = stages["voice"]
        thresholds = voice.get("qa_thresholds")
        if not isinstance(thresholds, dict):
            raise ProductionGateError(f"{brief_id}: VOICE must declare immutable QA thresholds")
        if isinstance(thresholds.get("per_chunk"), bool) or isinstance(thresholds.get("overall"), bool):
            raise ProductionGateError(f"{brief_id}: VOICE QA thresholds must be numeric, not booleans")
        try:
            chunk_threshold = float(thresholds.get("per_chunk"))
            overall_threshold = float(thresholds.get("overall"))
        except (TypeError, ValueError) as exc:
            raise ProductionGateError(f"{brief_id}: VOICE QA thresholds must be numeric") from exc
        if not math.isfinite(chunk_threshold) or chunk_threshold > 1.0:
            raise ProductionGateError(f"{brief_id}: VOICE per-chunk threshold must be finite and at most 100%")
        if chunk_threshold < MIN_CHUNK_MATCH:
            raise ProductionGateError(f"{brief_id}: VOICE per-chunk threshold cannot be below 92%")
        language = str(brief.get("lang", "en-us")).lower()
        if language.startswith("en") and brief.get("whisper_qa", True) is False:
            raise ProductionGateError(f"{brief_id}: English Whisper TTS QA cannot be disabled")
        overall_floor = MIN_ENGLISH_OVERALL_MATCH if language.startswith("en") else MIN_CHUNK_MATCH
        if not math.isfinite(overall_threshold) or overall_threshold > 1.0:
            raise ProductionGateError(f"{brief_id}: VOICE overall threshold must be finite and at most 100%")
        if overall_threshold < overall_floor:
            percent = "95%" if language.startswith("en") else "92%"
            raise ProductionGateError(f"{brief_id}: VOICE overall threshold cannot be below {percent}")
        if language.startswith("en") and (voice.get("engine") != "chatterbox" or voice.get("profile") != "option-3"):
            raise ProductionGateError(f"{brief_id}: English VOICE must use the approved Chatterbox Option-3 profile")

        assets = stages["assets"]
        if assets.get("rights_checked") is not True or assets.get("approval_constraints_checked") is not True:
            raise ProductionGateError(f"{brief_id}: ASSETS rights/approval review is incomplete")
        asset_digest = assets.get("manifest_sha256")
        if not isinstance(asset_digest, str) or not SHA_RE.fullmatch(asset_digest):
            raise ProductionGateError(f"{brief_id}: ASSETS manifest_sha256 is missing/invalid")
        capture = brief.get("capture")
        capture_id = Path(str(capture)).name if capture else ""
        if capture_id:
            if assets.get("capture_id") != capture_id:
                raise ProductionGateError(f"{brief_id}: ASSETS capture_id does not match the brief")
            file_hashes = assets.get("files")
            if not isinstance(file_hashes, list) or not file_hashes:
                raise ProductionGateError(f"{brief_id}: ASSETS must hash the files in its capture pack")
            names = set()
            for entry in file_hashes:
                if not isinstance(entry, dict):
                    raise ProductionGateError(f"{brief_id}: ASSETS file hash record is invalid")
                name = entry.get("path")
                digest = entry.get("sha256")
                if not isinstance(name, str) or not name or "\\" in name or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts:
                    raise ProductionGateError(f"{brief_id}: unsafe ASSETS file path")
                if not isinstance(digest, str) or not SHA_RE.fullmatch(digest) or name in names:
                    raise ProductionGateError(f"{brief_id}: ASSETS file hash is missing, invalid, or duplicated")
                names.add(name)
        else:
            if not assets.get("evidence"):
                raise ProductionGateError(f"{brief_id}: ASSETS without a capture pack needs explicit evidence")
            _require_evidence(root, assets.get("evidence"), f"{brief_id} ASSETS")

        decisions = _require_decisions(item.get("metrics_decisions"), brief_id)
        if capture_id:
            asset_file_rows = [{"path": entry["path"], "sha256": entry["sha256"]} for entry in (assets.get("files") or [])]
        else:
            asset_file_rows = [{"path": path, "sha256": sha256_file(_repo_path(root, path))}
                               for path in assets.get("evidence", [])]
        asset_file_rows.sort(key=lambda row: row["path"])
        asset_files_sha = sha256_bytes(json.dumps(asset_file_rows, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        summary["briefs"][brief_id] = {
            "brief_sha256": actual_brief_sha,
            "topic_score": score,
            "script_sha256": exact_script_sha,
            "asset_manifest_sha256": asset_digest,
            "asset_files_sha256": asset_files_sha,
            "capture_id": capture_id or None,
            "metrics_decisions": decisions,
        }

    if verify_assets:
        for brief_id in brief_ids:
            item = receipt_briefs[brief_id]
            brief = json.loads(_repo_path(root, f"reels-studio/briefs/{brief_id}.json").read_text(encoding="utf-8"))
            verify_capture_assets(root, brief_id, brief, item["stages"]["assets"])
    return summary


BLANK_STD_MAX = 4.0      # a flat frame (luma stddev) under this has no structure
BLANK_EDGE_MIN = 0.006   # ...and fewer than this share of strong edges: an empty pane
BLANK_SHARE_MAX = 0.10   # more than 10% blank samples in the used range = not shippable


def _sample_blank_share(video: Path, start: float, end: float, samples: int = 8) -> float | None:
    """Share of sampled frames inside [start, end] that are near-blank.

    Ownership: on 2026-10-20 the fx0 demo clip opened on ~0.3 s of pure white and spent
    seconds showing an EMPTY preview pane while the agent thought. Every automated check
    passed (frame 0 of the final video is the designed cover) and the blank pane shipped
    into the render. A demo clip is product evidence: if the pane is empty, there is no
    evidence. Needs ffmpeg + Pillow; returns None (skipped, never a silent pass) if either
    is missing, and callers log that.
    """
    try:
        import subprocess
        import tempfile
        from PIL import Image, ImageStat
    except Exception:
        return None
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe = "ffmpeg"
    span = max(0.05, end - start)
    blank = 0
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(samples):
            t = start + span * (i + 0.5) / samples
            out = Path(tmp) / f"s{i}.png"
            r = subprocess.run([exe, "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video),
                                "-frames:v", "1", "-vf", "scale=320:-2", str(out)],
                               capture_output=True)
            if r.returncode != 0 or not out.exists():
                return None
            with Image.open(out) as im:
                g = im.convert("L")
                std = ImageStat.Stat(g).stddev[0]
                data = list(g.get_flattened_data() if hasattr(g, "get_flattened_data") else g.getdata())
                w = g.width
                edges = sum(1 for y in range(g.height) for x in range(1, w)
                            if abs(data[y * w + x] - data[y * w + x - 1]) > 12)
                edge = edges / max(1, g.width * g.height)
            if std < BLANK_STD_MAX and edge < BLANK_EDGE_MIN:
                blank += 1
    return blank / samples


def verify_media_is_not_blank(repo_root: Path, brief_id: str, brief: dict) -> dict:
    """Fail the dispatch when a demo clip's used range is mostly an empty stage."""
    capture = brief.get("capture")
    if not capture:
        return {"checked": 0, "skipped": "no capture"}
    capture_id = Path(str(capture)).name
    checked, blank_issues, skipped = 0, [], []
    for scene in brief.get("scenes") or []:
        if scene.get("type") not in ("clip", "clip-montage"):
            continue
        src = scene.get("src")
        if not src:
            continue
        video = _repo_path(repo_root, f"reels-studio/captures/{capture_id}/{src}")
        spans = ([(float(scene.get("in", 0.0)), float(scene.get("out", 0.0)))]
                 if scene.get("type") == "clip"
                 else [(float(c.get("in", 0.0)), float(c.get("out", 0.0))) for c in scene.get("cuts") or []])
        for start, end in spans:
            if end <= start:
                continue
            share = _sample_blank_share(video, start, end)
            if share is None:
                skipped.append(f"{src} ({start:.2f}-{end:.2f}s): sampler unavailable")
                continue
            checked += 1
            if share > BLANK_SHARE_MAX:
                blank_issues.append(f"{src} {start:.2f}-{end:.2f}s is {share:.0%} blank frames")
    if blank_issues:
        raise ProductionGateError(
            f"{brief_id}: demo footage is an empty stage - {'; '.join(blank_issues)}. "
            f"A clip must show the product doing something in every second it is on screen "
            f"(trim the thinking/publishing dead time or recapture).")
    return {"brief_id": brief_id, "checked": checked, "skipped": skipped,
            "blank_share_max": BLANK_SHARE_MAX}




def verify_capture_assets(repo_root: Path, brief_id: str, brief: dict, stage: dict) -> dict:
    """After capture_store.py pull-for, verify the exact manifest and every declared file hash."""
    capture = brief.get("capture")
    if not capture:
        return {"brief_id": brief_id, "capture": None, "verified_files": 0}
    capture_id = Path(str(capture)).name
    pack = _repo_path(repo_root, f"reels-studio/captures/{capture_id}/manifest.json")
    manifest, raw = _load_json(pack, f"capture manifest for {brief_id}")
    actual_manifest_sha = sha256_bytes(raw)
    if actual_manifest_sha != stage.get("manifest_sha256"):
        raise ProductionGateError(f"{brief_id}: downloaded capture manifest digest changed")
    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, dict) or not manifest_files:
        raise ProductionGateError(f"{brief_id}: capture manifest lists no assets")
    file_hashes = stage.get("files") or []
    declared = {entry["path"]: entry["sha256"] for entry in file_hashes}
    required = set()
    for entry in manifest_files.values():
        if not isinstance(entry, dict) or not isinstance(entry.get("file"), str):
            raise ProductionGateError(f"{brief_id}: capture manifest contains an invalid file entry")
        required.add(entry["file"])
    missing = sorted(required - set(declared))
    if missing:
        raise ProductionGateError(f"{brief_id}: production receipt does not hash capture files: {', '.join(missing[:8])}")
    for name, expected_sha in declared.items():
        path = _repo_path(repo_root, f"reels-studio/captures/{capture_id}/{name}")
        if sha256_file(path) != expected_sha:
            raise ProductionGateError(f"{brief_id}: capture asset digest mismatch for {name}")
    # Media standard (owner, 2026-10-18): no card-only videos. The capture pack must
    # contain real product media (our own page captures or official demo media/images —
    # capture.py kinds), and the brief must stage it: at least two media scenes, at
    # least one of them motion/page (clip, clip-montage, page or scroll). Generated
    # text cards (kind "image"/"card") are support graphics, never the main visual.
    real_files = {entry["file"] for entry in manifest_files.values()
                  if isinstance(entry, dict) and str(entry.get("kind", "")).startswith(
                      ("own capture", "official demo media", "official image"))}
    if not real_files:
        raise ProductionGateError(
            f"{brief_id}: capture pack has no real product media (own capture / official "
            f"demo media) — card-only videos are not shippable; run capture.py on the "
            f"product page and include its demo media")
    motion_types = {"clip", "clip-montage", "page", "scroll"}
    media_scenes, motion_scenes = 0, 0
    for scene in brief.get("scenes") or []:
        refs = {scene.get("image"), scene.get("src"), scene.get("figure"),
                (scene.get("background") or {}).get("img"),
                (scene.get("background") or {}).get("image")}
        refs.discard(None)
        if scene.get("type") in motion_types:
            motion_scenes += 1
            media_scenes += 1
        elif refs & real_files:
            media_scenes += 1
    if media_scenes < 2 or motion_scenes < 1:
        raise ProductionGateError(
            f"{brief_id}: media coverage too thin ({media_scenes} media scenes, "
            f"{motion_scenes} motion/page scenes; need >=2 and >=1) — show the product "
            f"working, not just cards (PLAYBOOK media standard 2026-10-18)")
    blank = verify_media_is_not_blank(repo_root, brief_id, brief)
    return {"brief_id": brief_id, "capture": capture_id, "manifest_sha256": actual_manifest_sha,
            "verified_files": len(declared), "real_media_files": len(real_files),
            "media_scenes": media_scenes, "motion_scenes": motion_scenes,
            "clip_ranges_checked": blank["checked"], "clip_sampler_skipped": blank["skipped"]}


def asset_digest_receipt(repo_root: Path, capture_id: str) -> dict:
    """Create the ASSETS digest fields for a production receipt after a capture pack is present."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", capture_id):
        raise ProductionGateError("unsafe capture ID")
    manifest_path = _repo_path(repo_root, f"reels-studio/captures/{capture_id}/manifest.json")
    manifest, raw = _load_json(manifest_path, f"capture manifest for {capture_id}")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ProductionGateError(f"capture manifest for {capture_id} contains no assets")
    rows = []
    for entry in files.values():
        if not isinstance(entry, dict) or not isinstance(entry.get("file"), str):
            raise ProductionGateError(f"capture manifest for {capture_id} has an invalid asset record")
        name = entry["file"]
        file_path = _repo_path(repo_root, f"reels-studio/captures/{capture_id}/{name}")
        rows.append({"path": name, "sha256": sha256_file(file_path)})
    return {"capture_id": capture_id, "manifest_sha256": sha256_bytes(raw), "files": rows}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="validate a six-stage receipt without downloading capture packs")
    p.add_argument("receipt")
    p.add_argument("briefs", nargs="+", help="brief IDs")
    p = sub.add_parser("assets", help="verify downloaded capture packs against a receipt")
    p.add_argument("receipt")
    p.add_argument("briefs", nargs="+", help="brief IDs from the batch")
    p = sub.add_parser("asset-digests", help="print hashes for a locally present capture pack")
    p.add_argument("capture_id")
    args = parser.parse_args(argv)
    try:
        if args.command == "asset-digests":
            print(json.dumps(asset_digest_receipt(REPO_ROOT, args.capture_id), indent=2))
            return 0
        if args.command == "check":
            result = validate_receipt(REPO_ROOT, args.receipt, args.briefs)
            print(json.dumps({"ok": True, "batch_id": result["batch_id"], "briefs": result["briefs"]}, indent=2))
            return 0
        result = validate_receipt(REPO_ROOT, args.receipt, args.briefs, verify_assets=True)
        print(json.dumps({"ok": True, "batch_id": result["batch_id"], "assets": result["briefs"]}, indent=2))
        return 0
    except ProductionGateError as exc:
        print(f"production gate rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
