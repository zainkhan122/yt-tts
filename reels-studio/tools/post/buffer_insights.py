#!/usr/bin/env python3
"""Read-only Buffer per-post Insights snapshot for all sent video posts on configured channels.

Uses the existing quota-aware BufferClient; this module issues GraphQL queries only and never
creates, edits, deletes, schedules, or publishes a Buffer post.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.post.buffer_api import BufferClient, BufferError  # noqa: E402

INSIGHTS_QUERY = """query BufferSentPostInsights($input: PostsInput!, $after: String) {
  posts(first: 100, after: $after, input: $input) {
    edges { node {
      id channelId status dueAt sentAt createdAt externalLink text
      assets { source mimeType }
      metrics { type name value unit }
      metricsUpdatedAt
    } }
    pageInfo { endCursor hasNextPage }
  }
}"""
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}
MAX_HISTORY = 7
MAX_PAGES_HARD = 100
METRIC_GROUPS = {
    "views": {"views"},
    "reach": {"reach"},
    "impressions": {"impressions"},
    "engagement": {"engagementrate"},
    "reactions": {"reactions"},
    "likes": {"likes"},
    "comments": {"comments"},
    "shares": {"shares"},
    "reposts": {"reposts"},
    "saves": {"saves"},
    "avg_watch": {"averagetimewatched"},
    "total_watch": {"totaltimewatched"},
    "follows": {"follows"},
    "viewers": {"viewers"},
    "quotes": {"quotes"},
    "clicks": {"clicks"},
}


def now_iso(now: dt.datetime | None = None) -> str:
    return (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str | None) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def _safe_text(value, limit=240) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.replace("\x00", " ").split())[:limit]


def _video_asset(post: dict) -> bool:
    for asset in post.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        mime = str(asset.get("mimeType") or "").lower()
        source = str(asset.get("source") or "")
        ext = Path(urlsplit(source).path).suffix.lower()
        if mime.startswith("video/") or ext in VIDEO_SUFFIXES:
            return True
    return False


def publication_index(publications: dict) -> dict[str, dict]:
    records = publications.get("records") or {}
    result = {}
    if not isinstance(records, dict):
        return result
    for key, row in records.items():
        if not isinstance(row, dict) or row.get("state") != "sent":
            continue
        post_id = row.get("buffer_post_id")
        if not post_id:
            continue
        result[str(post_id)] = {
            "video_id": row.get("video_id") or str(key).split(":", 1)[0],
            "platform": row.get("platform", "unknown"),
            "title": row.get("title") or row.get("video_id") or str(key),
            "sent_at": row.get("sent_at"),
            "external_url": row.get("external_url"),
        }
    return result


def query_sent_posts(client, settings: dict, *, max_pages: int | None = None) -> tuple[list[dict], int]:
    channels = settings.get("channels") or {}
    channel_ids = [row.get("buffer_id") for row in channels.values() if isinstance(row, dict) and row.get("buffer_id")]
    if not settings.get("organization_id") or not channel_ids:
        raise BufferError("Buffer organization/channels are not configured", "CONFIG")
    channel_alias = {row["buffer_id"]: name for name, row in channels.items() if isinstance(row, dict) and row.get("buffer_id")}
    input_filter = {
        "organizationId": settings["organization_id"],
        "filter": {"status": ["sent"], "channelIds": channel_ids},
        "sort": [{"field": "createdAt", "direction": "desc"}],
    }
    limit = min(max_pages or int(settings.get("max_pages", 10)), MAX_PAGES_HARD)
    cursor = None
    seen_cursors = set()
    seen_posts = set()
    posts = []
    pages = 0
    while True:
        data = client.request(INSIGHTS_QUERY, {"input": input_filter, "after": cursor})
        page = data.get("posts") or {}
        edges = page.get("edges") or []
        for edge in edges:
            node = (edge or {}).get("node") or {}
            pid = node.get("id")
            if not pid:
                raise BufferError("Buffer Insights returned a post without an ID", "BAD_RESPONSE")
            pid = str(pid)
            if pid in seen_posts:
                raise BufferError("Buffer Insights pagination repeated a post; refusing an incomplete snapshot", "PAGINATION")
            seen_posts.add(pid)
            post = dict(node)
            post["_channel_alias"] = channel_alias.get(node.get("channelId"), "unknown")
            posts.append(post)
        pages += 1
        info = page.get("pageInfo") or {}
        if not info.get("hasNextPage"):
            break
        next_cursor = info.get("endCursor")
        if not next_cursor or next_cursor in seen_cursors or pages >= limit:
            raise BufferError("Buffer Insights pagination did not complete; no partial snapshot saved", "PAGINATION")
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    return posts, pages


def _metric_key(metric: dict) -> str:
    return re.sub(r"[^a-z0-9]", "", str(metric.get("type") or metric.get("name") or "").lower())


def normalize_metrics(raw_metrics) -> list[dict]:
    out = []
    if not isinstance(raw_metrics, list):
        return out
    for metric in raw_metrics:
        if not isinstance(metric, dict):
            continue
        out.append({
            "type": str(metric.get("type") or ""),
            "name": str(metric.get("name") or metric.get("type") or ""),
            "value": metric.get("value"),
            "unit": str(metric.get("unit") or ""),
        })
    return sorted(out, key=lambda m: (m["type"].lower(), m["name"].lower()))


def _metric_number(metrics: list[dict], group: str):
    accepted = METRIC_GROUPS.get(group, {group})
    for metric in metrics:
        key = _metric_key(metric)
        if key not in accepted:
            continue
        try:
            return float(metric.get("value"))
        except (TypeError, ValueError):
            return None
    return None


def build_snapshot(
    sent_posts: list[dict],
    *,
    publication_records: dict,
    fetched_at: str | None = None,
    previous: dict | None = None,
    expected_post_ids: list[str] | None = None,
    pages: int = 1,
) -> dict:
    fetched_at = fetched_at or now_iso()
    fetched_dt = parse_time(fetched_at) or dt.datetime.now(dt.timezone.utc)
    index = publication_index(publication_records)
    expected = set(expected_post_ids if expected_post_ids is not None else index)
    returned = {str(p.get("id")) for p in sent_posts if p.get("id")}
    missing = sorted(expected - returned)
    posts: dict[str, dict] = {}
    for raw in sent_posts:
        post_id = str(raw["id"])
        tracked = index.get(post_id, {})
        if not tracked and not _video_asset(raw):
            continue
        platform = tracked.get("platform") or raw.get("_channel_alias") or "unknown"
        metrics = normalize_metrics(raw.get("metrics"))
        metrics_updated_at = raw.get("metricsUpdatedAt")
        updated_dt = parse_time(metrics_updated_at)
        sent_at = raw.get("sentAt") or tracked.get("sent_at") or raw.get("dueAt")
        sent_dt = parse_time(sent_at)
        if metrics:
            age = fetched_dt - updated_dt if updated_dt is not None else None
            if age is not None and -dt.timedelta(minutes=5) <= age <= dt.timedelta(hours=48):
                metric_status = "fresh"
            elif age is not None and age > dt.timedelta(hours=48):
                metric_status = "stale"
            elif updated_dt is not None:
                metric_status = "invalid_future_timestamp"
            else:
                metric_status = "available_timestamp_missing"
        elif sent_dt is not None and (fetched_dt - sent_dt) < dt.timedelta(hours=48):
            metric_status = "awaiting_buffer_refresh"
        else:
            metric_status = "unavailable_or_unsupported"
        title = _safe_text(tracked.get("title") or raw.get("text") or post_id, 160)
        excerpt = _safe_text(raw.get("text"), 240)
        record = {
            "post_id": post_id,
            "video_id": tracked.get("video_id"),
            "platform": platform,
            "channel_id": raw.get("channelId"),
            "sent_at": sent_at,
            "external_url": raw.get("externalLink") or tracked.get("external_url"),
            "title": title,
            "caption_excerpt": excerpt,
            "metrics": metrics,
            "metrics_updated_at": metrics_updated_at,
            "metrics_status": metric_status,
        }
        old = ((previous or {}).get("posts") or {}).get(post_id) or {}
        history = list(old.get("history") or [])
        point = {"fetched_at": fetched_at, "metrics_updated_at": metrics_updated_at, "metrics": metrics}
        if not history or history[-1].get("metrics_updated_at") != metrics_updated_at or history[-1].get("metrics") != metrics:
            history.append(point)
        else:
            history[-1] = point
        record["history"] = history[-MAX_HISTORY:]
        posts[post_id] = record

    coverage = {}
    aliases = sorted(set([p.get("_channel_alias", "unknown") for p in sent_posts]))
    for platform in sorted(set(row["platform"] for row in posts.values()) | set(aliases)):
        rows = [p for p in posts.values() if p["platform"] == platform]
        total = len(rows)
        available = sum(bool(p.get("metrics")) for p in rows)
        fresh = sum(p.get("metrics_status") == "fresh" for p in rows)
        coverage[platform] = {
            "total_video_posts": total,
            "metrics_available_posts": available,
            "fresh_metric_posts": fresh,
            "awaiting_posts": sum(p.get("metrics_status") == "awaiting_buffer_refresh" for p in rows),
            "stale_posts": sum(p.get("metrics_status") == "stale" for p in rows),
            "untimestamped_posts": sum(p.get("metrics_status") == "available_timestamp_missing" for p in rows),
            "invalid_timestamp_posts": sum(p.get("metrics_status") == "invalid_future_timestamp" for p in rows),
        }

    # Coverage is based on all known configured channels, including one with no sent video yet.
    for name in (publication_records.get("configured_channels") or []):
        coverage.setdefault(name, {"total_video_posts": 0, "metrics_available_posts": 0, "fresh_metric_posts": 0,
                                   "awaiting_posts": 0, "stale_posts": 0, "untimestamped_posts": 0,
                                   "invalid_timestamp_posts": 0})
    complete = not missing
    coverage_ok = all(row["total_video_posts"] == 0 or row["fresh_metric_posts"] > 0 for row in coverage.values())
    return {
        "schema_version": 1,
        "source": "Buffer GraphQL Post.metrics (read-only)",
        "fetched_at": fetched_at,
        "complete": complete,
        "pagination_pages": pages,
        "sent_post_count": len(sent_posts),
        "video_post_count": len(posts),
        "expected_tracked_sent_posts": len(expected),
        "missing_expected_post_ids": missing,
        "metrics_coverage_ok": coverage_ok,
        "coverage_by_platform": coverage,
        "posts": dict(sorted(posts.items(), key=lambda pair: (pair[1].get("sent_at") or "", pair[0]))),
    }


def _value(post: dict, group: str):
    value = _metric_number(post.get("metrics") or [], group)
    return value


def _fmt_metric(value, unit="") -> str:
    if value is None:
        return "—"
    shown = f"{value:,.2f}" if value % 1 else f"{int(value):,}"
    return f"{shown}%" if unit == "%" else f"{shown} {unit}".strip()


def render_report(snapshot: dict) -> str:
    posts = list((snapshot.get("posts") or {}).values())
    coverage = snapshot.get("coverage_by_platform") or {}
    lines = [
        "# Buffer Insights — read-only snapshot",
        "",
        f"Fetched: `{snapshot.get('fetched_at')}` · pagination complete: **{bool(snapshot.get('complete'))}** · ",
        f"videos: **{snapshot.get('video_post_count', 0)}** / sent posts scanned: **{snapshot.get('sent_post_count', 0)}**",
        "",
        "## Coverage by channel",
        "",
        "| Channel | Video posts | Metrics available | Fresh metrics | Awaiting refresh | Stale | Missing timestamp | Invalid timestamp |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for platform, row in sorted(coverage.items()):
        lines.append(f"| {platform} | {row.get('total_video_posts', 0)} | {row.get('metrics_available_posts', 0)} | {row.get('fresh_metric_posts', 0)} | {row.get('awaiting_posts', 0)} | {row.get('stale_posts', 0)} | {row.get('untimestamped_posts', 0)} | {row.get('invalid_timestamp_posts', 0)} |")
    lines += ["", "## Highest post-level metrics (ranked within each channel)", "",
              "Counts are not compared across channels. Buffer may omit metrics that a social network does not expose.", ""]
    for platform in sorted(coverage):
        rows = [p for p in posts if p.get("platform") == platform and p.get("metrics")]
        if not rows:
            lines += [f"### {platform}", "", "No post metrics returned in this snapshot.", ""]
            continue
        lines += [f"### {platform}", ""]
        metric_rows = (
            ("views", "views"), ("reach", "reach"), ("impressions", "impressions"),
            ("reactions", "reactions"), ("likes", "Facebook likes"), ("comments", "comments"),
            ("shares", "shares/forwards"), ("reposts", "reposts"), ("engagement", "engagement rate"), ("saves", "saves"),
            ("follows", "follows"), ("viewers", "unique video viewers"), ("quotes", "quotes"),
            ("clicks", "clicks"), ("avg_watch", "average watch time"), ("total_watch", "total watch time"),
        )
        for group, label in metric_rows:
            ranked = [( _value(p, group), p) for p in rows]
            ranked = [(v, p) for v, p in ranked if v is not None]
            if not ranked:
                continue
            ranked.sort(key=lambda x: x[0], reverse=True)
            lines.append(f"**Top by {label}**")
            for value, post in ranked[:3]:
                vid = post.get("video_id") or post.get("post_id")
                title = post.get("title") or vid
                url = post.get("external_url") or ""
                link_title = f"[{title}]({url})" if url.startswith("https://") else str(title)
                # Buffer's engagementRate is already 0–100 (not a 0–1 ratio); watch units follow its taxonomy.
                unit = {"engagement": "%", "avg_watch": "s", "total_watch": "min"}.get(group, "")
                lines.append(f"- `{vid}` — {link_title}: **{_fmt_metric(value, unit)}**; metrics updated `{post.get('metrics_updated_at') or 'unknown'}`")
            lines.append("")
    lines += [
        "## Interpretation guardrails",
        "",
        "- The API returns per-post platform metrics; it does not prove which individual creative choice caused a result.",
        "- Use average watch time/retention metrics where the channel exposes them. If absent, keep the approved Chatterbox Option-3 settings; do not infer a voice change from view counts alone.",
        "- Before a new batch, compare leading posts' topic, opening hook, caption, actual audio QA, first frame/cover, and visual format. Record explicit topic/script/voice/visual decisions in the six-stage production receipt.",
        "- Buffer Insights refresh daily and may lag the social network by up to a day; rely on `metrics_updated_at`, not the fetch time alone.",
    ]
    if snapshot.get("missing_expected_post_ids"):
        lines += ["", "**Coverage warning:** expected sent posts are missing from the Buffer response; do not use this snapshot to pass the production gate."]
    if not snapshot.get("metrics_coverage_ok"):
        lines += ["", "**Metrics warning:** at least one channel has video posts but no fresh metrics; refresh before production."]
    return "\n".join(lines) + "\n"


def write_snapshot(path: Path, snapshot: dict) -> bytes:
    raw = (json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return raw


def _read_remote_bytes(gh_actions, path: str, branch: str) -> bytes:
    """Exact remote bytes for the compare-and-swap read.

    The Contents API only inlines files up to 1 MiB and answers with an empty
    `content` field beyond that, which silently read as "the tracker changed"
    and failed every snapshot once it grew past the limit. Fall back to the
    blob API, which returns the full object.
    """
    status, remote = gh_actions.api("GET", f"/contents/{path}?ref={branch}")
    if status != 200:
        raise RuntimeError(f"cannot read remote Buffer Insights tracker (HTTP {status})")
    if remote.get("content"):
        return base64.b64decode(remote["content"])
    status, blob = gh_actions.api("GET", f"/git/blobs/{remote['sha']}")
    if status != 200:
        raise RuntimeError(f"cannot read remote Buffer Insights blob (HTTP {status})")
    return base64.b64decode(blob.get("content", ""))


def commit_snapshot_remote(new_raw: bytes, previous_raw: bytes | None, *, branch="main") -> None:
    """Commit through GitHub's compare-and-swap Contents API; never overwrite a concurrent update."""
    from tools import gh_actions
    path = "reels-studio/tracker/buffer-insights.json"
    remote_raw = _read_remote_bytes(gh_actions, path, branch)
    if previous_raw is not None and remote_raw != previous_raw:
        raise RuntimeError("Buffer Insights tracker changed during this run; refusing to overwrite it")
    message = "analytics: refresh read-only Buffer Insights " + dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    status, remote = gh_actions.api("GET", f"/contents/{path}?ref={branch}")
    if status != 200:
        raise RuntimeError(f"cannot read remote Buffer Insights tracker (HTTP {status})")
    payload = {"message": message, "branch": branch, "sha": remote["sha"],
               "content": base64.b64encode(new_raw).decode("ascii")}
    status, result = gh_actions.api("PUT", f"/contents/{path}", payload)
    if status == 200:
        return
    detail = result.get("message", "") if isinstance(result, dict) else str(result)
    if len(new_raw) <= 1_048_576:
        raise RuntimeError(f"Buffer Insights tracker write failed/conflicted (HTTP {status}); snapshot not committed")
    # The Contents API refuses payloads over 1 MiB outright ("file is too large"),
    # which is not a conflict: the compare-and-swap read above already proved the
    # remote blob is unchanged, so commit the same bytes through the git data API.
    if "too large" not in detail.lower():
        raise RuntimeError(f"Buffer Insights tracker write failed/conflicted (HTTP {status}); snapshot not committed")
    _commit_blob(gh_actions, path, message, new_raw, branch=branch)


def _commit_blob(gh_actions, path: str, message: str, new_raw: bytes, *, branch: str) -> None:
    """Commit one file over 1 MiB with the git data API (blob -> tree -> commit -> ref)."""
    status, blob = gh_actions.api("POST", "/git/blobs",
                                  {"content": base64.b64encode(new_raw).decode("ascii"), "encoding": "base64"})
    if status != 201:
        raise RuntimeError(f"Buffer Insights blob upload failed (HTTP {status}); snapshot not committed")
    status, ref = gh_actions.api("GET", f"/git/ref/heads/{branch}")
    if status != 200:
        raise RuntimeError(f"cannot read branch {branch} (HTTP {status}); snapshot not committed")
    base = ref["object"]["sha"]
    status, tree = gh_actions.api("POST", "/git/trees", {
        "base_tree": base,
        "tree": [{"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]}],
    })
    if status != 201:
        raise RuntimeError(f"Buffer Insights tree failed (HTTP {status}); snapshot not committed")
    status, commit = gh_actions.api("POST", "/git/commits",
                                    {"message": message, "tree": tree["sha"], "parents": [base]})
    if status != 201:
        raise RuntimeError(f"Buffer Insights commit failed (HTTP {status}); snapshot not committed")
    status, _ = gh_actions.api("PATCH", f"/git/refs/heads/{branch}", {"sha": commit["sha"], "force": False})
    if status != 200:
        raise RuntimeError(f"Buffer Insights ref update conflicted (HTTP {status}); snapshot not committed")


def run_snapshot(*, output: Path, settings_path: Path | None = None, publications_path: Path | None = None,
                 now: dt.datetime | None = None, commit: bool = False, summary_path: Path | None = None) -> dict:
    settings_path = settings_path or ROOT / "config/publishing.json"
    publications_path = publications_path or ROOT / "tracker/publications.json"
    output = Path(output)
    previous_raw = output.read_bytes() if output.exists() else None
    previous = json.loads(previous_raw.decode("utf-8")) if previous_raw else {}
    config = json.loads(Path(settings_path).read_text(encoding="utf-8"))
    settings = config.get("buffer") or {}
    publications = json.loads(Path(publications_path).read_text(encoding="utf-8"))
    index = publication_index(publications)
    client = BufferClient(settings)
    sent, pages = query_sent_posts(client, settings)
    snapshot_records = dict(publications)
    snapshot_records["configured_channels"] = [
        name for name, row in (settings.get("channels") or {}).items()
        if isinstance(row, dict) and row.get("buffer_id")
    ]
    snapshot = build_snapshot(sent, publication_records=snapshot_records, fetched_at=now_iso(now), previous=previous,
                              expected_post_ids=list(index), pages=pages)
    new_raw = write_snapshot(output, snapshot)
    report = render_report(snapshot)
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as f:
            f.write(report)
            f.write("\n")
    if commit:
        commit_snapshot_remote(new_raw, previous_raw)
    return snapshot


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "tracker/buffer-insights.json")
    parser.add_argument("--commit", action="store_true", help="write the snapshot to the configured GitHub repo (not to Buffer)")
    parser.add_argument("--summary", type=Path, help="append the Markdown report to this file")
    args = parser.parse_args(argv)
    try:
        snapshot = run_snapshot(output=args.output, commit=args.commit, summary_path=args.summary)
    except Exception as exc:
        # BufferClient exceptions redact credentials; avoid printing raw requests/headers.
        print(f"Buffer Insights failed safely: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(render_report(snapshot))
    print(f"read-only Buffer requests: {snapshot.get('pagination_pages', 0)} page(s); no Buffer mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
