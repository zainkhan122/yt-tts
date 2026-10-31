#!/usr/bin/env python3
"""Performance analytics for published Shorts: Buffer metrics in, decisions out.

The Buffer Insights snapshot (`tracker/buffer-insights.json`) already contains per-post
metrics and bounded history, but on its own it is raw numbers. This module joins it to
what we control — brief (hook, template, niche), queue category, backlog candidates —
and produces:

  * tracker/performance.json  - machine-readable findings + topic advice for SELECT
  * research/performance/performance-<date>.md - human report with recommended changes

Rules honoured throughout:
  * Metrics are ranked WITHIN a platform, never compared across platforms.
  * Posts younger than 2 days are "too early" and never judged; verdicts about
    winners/losers use mature posts (>= 7 days) only. Dimension findings need n >= 4
    (slots n >= 3) or they are reported as descriptive only, never as recommendations.
  * Every recommendation cites its evidence (n + medians). Correlation is labelled
    as correlation; nothing here claims a creative choice *caused* a result.

Read-only and offline: it never calls Buffer or any network API.

  python3 tools/post/performance.py                 # writes both outputs
  python3 tools/post/performance.py --check         # print report, write nothing
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
ET = ZoneInfo("America/New_York")

EARLY_DAYS = 2.0        # younger than this: listed, never judged
MATURE_DAYS = 7.0       # winner/loser verdicts only at or beyond this age
MIN_N_DIMENSION = 4     # evidence floor for dimension findings/recommendations
MIN_N_SLOT = 3

# Buffer metric groups (mirrors tools/post/buffer_insights.py taxonomy).
METRIC_GROUPS = {
    "views": {"views"}, "reach": {"reach"}, "impressions": {"impressions"},
    "engagement": {"engagementrate"}, "reactions": {"reactions"}, "likes": {"likes"},
    "comments": {"comments"}, "shares": {"shares"}, "reposts": {"reposts"},
    "saves": {"saves"}, "avg_watch": {"averagetimewatched"},
    "total_watch": {"totaltimewatched"}, "follows": {"follows"},
    "viewers": {"viewers"}, "quotes": {"quotes"}, "clicks": {"clicks"},
}
STOPWORDS = set("the a an and or for with your you our this that from into are was were has have had "
                "its it's new free open source ai tool tools model models app apps video videos".split())


def parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(dt.timezone.utc) if parsed.tzinfo else None


def metric_number(metrics, group):
    accepted = METRIC_GROUPS.get(group, {group})
    for metric in metrics or []:
        key = re.sub(r"[^a-z0-9]", "", str(metric.get("type") or metric.get("name") or "").lower())
        if key in accepted:
            try:
                return float(metric.get("value"))
            except (TypeError, ValueError):
                return None
    return None


def primary_from_metrics(metrics):
    """Platforms expose different reach metrics: views, else impressions, else reach."""
    for group in ("views", "impressions", "reach"):
        value = metric_number(metrics, group)
        if value is not None:
            return value, group
    return None, None


def percentile_ranks(values: dict) -> dict:
    """key -> 0..100 percentile of its value among the given mapping (ties share the mean rank)."""
    items = sorted((v, k) for k, v in values.items() if v is not None)
    out = {}
    n = len(items)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and items[j + 1][0] == items[i][0]:
            j += 1
        pct = 100.0 * ((i + j) / 2.0) / (n - 1) if n > 1 else 100.0
        for t in range(i, j + 1):
            out[items[t][1]] = round(pct, 1)
        i = j + 1
    return out


def median(nums):
    vals = sorted(v for v in nums if v is not None)
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2.0


def _round(value, digits=1):
    return None if value is None else round(float(value), digits)


# --------------------------------------------------------------------------- #
# Loading / joining
# --------------------------------------------------------------------------- #
def load_json(path: Path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def brief_facts(briefs_root: Path, video_id: str) -> dict:
    brief = load_json(Path(briefs_root) / f"{video_id}.json", {})
    scenes = brief.get("scenes") or []
    says = [str(s.get("say") or "") for s in scenes if isinstance(s, dict)]
    hook = says[0] if says else ""
    heading = str(scenes[0].get("heading") or "") if scenes and isinstance(scenes[0], dict) else ""
    return {
        "title": brief.get("title") or video_id,
        "template": brief.get("template") or "unknown",
        "production_category": brief.get("production_category") or "unknown",
        "niche": brief.get("niche") or "",
        "hook": hook,
        "hook_heading": heading,
        "hook_style": classify_hook(hook, heading),
        "has_comment_cta": any("comment" in s.lower() for s in says[-2:]) if says else False,
        "scene_count": len(scenes),
    }


def classify_hook(hook: str, heading: str = "") -> str:
    text = (hook or "").strip().lower()
    if "?" in text or re.match(r"^(what|why|how|would|do|does|did|can|could|is|are|want)\b", text):
        return "question"
    if re.match(r"^(meet|introducing|this is|say hello)\b", text) or heading.lower().startswith("meet "):
        return "introducing"
    return "statement"


def build_video_records(snapshot: dict, briefs_root: Path, queue: dict, now: dt.datetime) -> dict:
    """video_id -> {facts, category, platforms: {platform: post record}}"""
    queue_cat = {i.get("video_id"): i.get("category") for i in queue.get("items") or [] if isinstance(i, dict)}
    videos: dict[str, dict] = {}
    for post in (snapshot.get("posts") or {}).values():
        vid = post.get("video_id")
        if not vid:
            continue
        rec = videos.setdefault(vid, {"video_id": vid, "platforms": {}})
        sent = parse_time(post.get("sent_at"))
        age = (now - sent).total_seconds() / 86400.0 if sent else None
        metrics = post.get("metrics") or []
        entry = {
            "post_id": post.get("post_id"),
            "platform": post.get("platform") or "unknown",
            "sent_at": post.get("sent_at"),
            "age_days": _round(age, 2),
            "maturity": "unknown" if age is None else ("early" if age < EARLY_DAYS else "developing" if age < MATURE_DAYS else "mature"),
            "external_url": post.get("external_url"),
            "views": metric_number(metrics, "views"),
            "primary_views": primary_from_metrics(metrics)[0],
            "primary_metric": primary_from_metrics(metrics)[1],
            "engagement_rate": metric_number(metrics, "engagement"),
            "comments": metric_number(metrics, "comments"),
            "shares": metric_number(metrics, "shares"),
            "saves": metric_number(metrics, "saves"),
            "follows": metric_number(metrics, "follows"),
            "avg_watch_s": metric_number(metrics, "avg_watch"),
            "metrics_status": post.get("metrics_status"),
            "history": post.get("history") or [],
        }
        entry["engagement_actions"] = sum(v for v in (entry["comments"], entry["shares"], entry["saves"], entry["follows"]) if v is not None) \
            if any(v is not None for v in (entry["comments"], entry["shares"], entry["saves"], entry["follows"])) else None
        rec["platforms"][entry["platform"]] = entry
    for vid, rec in videos.items():
        rec.update(brief_facts(briefs_root, vid))
        rec["category"] = queue_cat.get(vid) or rec["production_category"]
    return videos


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def add_percentiles(videos: dict) -> None:
    platforms = sorted({p for rec in videos.values() for p in rec["platforms"]})
    for platform in platforms:
        views = {vid: rec["platforms"][platform]["primary_views"] for vid, rec in videos.items()
                 if platform in rec["platforms"] and rec["platforms"][platform].get("primary_views") is not None}
        ranks = percentile_ranks(views)
        for vid, pct in ranks.items():
            videos[vid]["platforms"][platform]["views_percentile"] = pct
    for rec in videos.values():
        pcts = [p["views_percentile"] for p in rec["platforms"].values() if p.get("views_percentile") is not None]
        rec["composite_percentile"] = _round(sum(pcts) / len(pcts), 1) if pcts else None
        ages = [p["age_days"] for p in rec["platforms"].values() if p.get("age_days") is not None]
        rec["age_days"] = min(ages) if ages else None
        rec["maturity"] = ("mature" if ages and min(ages) >= MATURE_DAYS else
                           "developing" if ages and min(ages) >= EARLY_DAYS else "early" if ages else "unknown")


def add_velocity(videos: dict) -> None:
    """Views/day gained between the last two history points that both carry views."""
    for rec in videos.values():
        for entry in rec["platforms"].values():
            entry["views_per_day_recent"] = None
            hist = [h for h in entry.get("history") or [] if primary_from_metrics(h.get("metrics"))[0] is not None]
            if len(hist) < 2:
                continue
            (prev, last) = hist[-2], hist[-1]
            t0, t1 = parse_time(prev.get("fetched_at")), parse_time(last.get("fetched_at"))
            if not t0 or not t1 or t1 <= t0:
                continue
            days = (t1 - t0).total_seconds() / 86400.0
            gained = primary_from_metrics(last.get("metrics"))[0] - primary_from_metrics(prev.get("metrics"))[0]
            entry["views_per_day_recent"] = _round(gained / days, 2)


def _judged(videos: dict, maturities=("developing", "mature")) -> list:
    return [r for r in videos.values() if r["maturity"] in maturities and r["composite_percentile"] is not None]


def dimension_findings(videos: dict) -> list:
    """Median composite percentile by brief/queue dimension; findings only at n >= MIN_N_DIMENSION."""
    judged = _judged(videos)
    findings = []
    for field in ("category", "production_category", "template", "hook_style"):
        groups: dict[str, list] = {}
        for rec in judged:
            groups.setdefault(str(rec.get(field) or "unknown"), []).append(rec["composite_percentile"])
        rows = [{"group": g, "n": len(v), "median_percentile": _round(median(v))}
                for g, v in groups.items() if len(v) >= 2]
        rows.sort(key=lambda r: (r["median_percentile"] is None, -(r["median_percentile"] or 0)))
        strong = [r for r in rows if r["n"] >= MIN_N_DIMENSION and (r["median_percentile"] or 0) >= 65]
        weak = [r for r in rows if r["n"] >= MIN_N_DIMENSION and (r["median_percentile"] or 100) <= 35]
        findings.append({"dimension": field, "rows": rows,
                         "strong": strong, "weak": weak,
                         "evidence_ok": any(r["n"] >= MIN_N_DIMENSION for r in rows)})
    cta = [{"group": "comment CTA" if r["has_comment_cta"] else "no comment CTA",
            "pct": r["composite_percentile"]} for r in judged]
    groups: dict[str, list] = {}
    for row in cta:
        groups.setdefault(row["group"], []).append(row["pct"])
    rows = [{"group": g, "n": len(v), "median_percentile": _round(median(v))} for g, v in groups.items() if len(v) >= 2]
    findings.append({"dimension": "call_to_action", "rows": sorted(rows, key=lambda r: -(r["median_percentile"] or 0)),
                     "strong": [], "weak": [], "evidence_ok": any(r["n"] >= MIN_N_DIMENSION for r in rows)})
    return findings


def slot_findings(videos: dict) -> list:
    """Median views by platform x ET daypart, judged posts only (n >= MIN_N_SLOT to recommend)."""
    buckets = {}
    for rec in videos.values():
        for platform, entry in rec["platforms"].items():
            if entry["maturity"] not in ("developing", "mature") or entry.get("primary_views") is None:
                continue
            sent = parse_time(entry["sent_at"])
            if not sent:
                continue
            hour = sent.astimezone(ET).hour
            daypart = ("morning" if 6 <= hour < 11 else "midday" if 11 <= hour < 16 else
                       "evening" if 16 <= hour < 22 else "night")
            buckets.setdefault((platform, daypart), []).append(entry["primary_views"])
    out = []
    for (platform, daypart), vals in sorted(buckets.items()):
        out.append({"platform": platform, "daypart": daypart, "n": len(vals),
                    "median_views": _round(median(vals), 0), "evidence_ok": len(vals) >= MIN_N_SLOT})
    return out


def build_recommendations(videos: dict, dims: list, slots: list) -> list:
    recs = []
    mature = [r for r in videos.values() if r["maturity"] == "mature" and r["composite_percentile"] is not None]
    for finding in dims:
        for row in finding["strong"]:
            recs.append({
                "action": f"Prioritise more '{row['group']}' topics ({finding['dimension']}) in the next batch.",
                "evidence": f"n={row['n']} judged videos, median cross-platform views percentile {row['median_percentile']}.",
                "confidence": "medium" if row["n"] >= 6 else "low",
            })
        for row in finding["weak"]:
            recs.append({
                "action": f"Reduce or rework '{row['group']}' topics ({finding['dimension']}) until the hook/format changes.",
                "evidence": f"n={row['n']} judged videos, median cross-platform views percentile {row['median_percentile']}.",
                "confidence": "medium" if row["n"] >= 6 else "low",
            })
    by_platform: dict[str, list] = {}
    for row in slots:
        if row["evidence_ok"]:
            by_platform.setdefault(row["platform"], []).append(row)
    for platform, rows in by_platform.items():
        best = max(rows, key=lambda r: r["median_views"] or 0)
        if len(rows) >= 2:
            recs.append({
                "action": f"Prefer the {best['daypart']} ET window for {platform} posts.",
                "evidence": f"{platform}/{best['daypart']} median views {best['median_views']} across n={best['n']} judged posts (best of {len(rows)} windows with evidence).",
                "confidence": "low",
            })
    winners = sorted((r for r in mature if r["composite_percentile"] >= 75), key=lambda r: -r["composite_percentile"])
    if winners:
        names = ", ".join(f"`{r['video_id']}`" for r in winners[:4])
        recs.append({
            "action": f"Study and reuse the hook/structure of the mature winners: {names}.",
            "evidence": f"{len(winners)} mature video(s) at or above the 75th cross-platform percentile.",
            "confidence": "medium",
        })
    losers = sorted((r for r in mature if r["composite_percentile"] <= 25), key=lambda r: r["composite_percentile"])
    if losers:
        names = ", ".join(f"`{r['video_id']}`" for r in losers[:4])
        recs.append({
            "action": f"Do not repeat the topics/angles of the mature underperformers without a new angle: {names}.",
            "evidence": f"{len(losers)} mature video(s) at or below the 25th cross-platform percentile.",
            "confidence": "medium",
        })
    return recs


# --------------------------------------------------------------------------- #
# Topic advice: trending candidates re-ranked by what performs for us
# --------------------------------------------------------------------------- #
def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9.+-]*", (text or "").lower()) if len(t) > 2 and t not in STOPWORDS}


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


TYPE_TO_CATEGORY = {"repo-spotlight": "repo", "news": "news", "model-spotlight": "tool",
                    "tool-spotlight": "tool", "ranked-list": "tool"}


def topic_advice(backlog_rows: list, videos: dict, dims: list) -> dict:
    cat_row = next((f for f in dims if f["dimension"] == "category"), {"rows": []})
    cat_pct = {r["group"]: r["median_percentile"] for r in cat_row["rows"] if r["median_percentile"] is not None}
    published = []
    for rec in videos.values():
        published.append((rec["video_id"], _tokens(f"{rec.get('title', '')} {rec.get('niche', '')}")))
    candidates, blocked = [], []
    for row in backlog_rows:
        if (row.get("status") or "").strip() != "idea":
            continue
        topic = (row.get("topic") or "").strip()
        if not topic:
            continue
        try:
            base = float(row.get("score") or 0)
        except ValueError:
            base = 0.0
        derived = False
        if base <= 0:
            # Idea-feed rows carry consensus/views in trend_signal instead of a score.
            sig = row.get("trend_signal") or ""
            channels = re.search(r"(\d+)\s+watchlist channels", sig)
            views_m = re.search(r"([\d,]+)\s+views", sig)
            if channels or views_m:
                base = 30.0 + 10.0 * max(0, int(channels.group(1)) - 1 if channels else 0) \
                    + min(20.0, int(views_m.group(1).replace(",", "")) / 5000.0 if views_m else 0.0)
                derived = True
        risk = (row.get("risk_flags") or "").strip()
        category = TYPE_TO_CATEGORY.get((row.get("type") or "").strip(), "tool")
        pct = cat_pct.get(category)
        multiplier = 0.8 + 0.4 * (pct / 100.0) if pct is not None else 1.0
        reasons = [f"category '{category}' median percentile {pct}" if pct is not None else "no category evidence yet"]
        if derived:
            reasons.append("base score derived from watchlist consensus/views (unscored idea-feed row)")
        adjusted = base * multiplier
        tokens = _tokens(topic)
        similar = max((( _jaccard(tokens, pt), pid) for pid, pt in published), default=(0.0, None))
        if similar[0] >= 0.35:
            adjusted *= 0.5
            reasons.append(f"similar to already-published `{similar[1]}` (overlap {similar[0]:.2f}) — needs a clearly new angle")
        entry = {"topic": topic, "type": row.get("type"), "url": row.get("url"),
                 "base_score": base, "adjusted_score": _round(adjusted, 1),
                 "trend_signal": (row.get("trend_signal") or "")[:160], "reasons": reasons}
        (blocked if risk else candidates).append(entry | ({"risk_flags": risk} if risk else {}))
    candidates.sort(key=lambda e: -(e["adjusted_score"] or 0))
    return {"category_percentiles": cat_pct, "top_candidates": candidates[:10], "blocked_by_risk_flags": blocked[:10]}


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _fmt(value, suffix=""):
    return "—" if value is None else f"{value:,.0f}{suffix}" if float(value) == int(float(value)) else f"{value:,.1f}{suffix}"


def render_report(a: dict) -> str:
    videos = a["videos"]
    lines = [f"# Shorts performance — {a['generated_for_date']}", "",
             f"Source: Buffer Insights snapshot `{a['snapshot_fetched_at']}` (complete: **{a['snapshot_complete']}**) · "
             f"videos analysed: **{len(videos)}** · mature (≥{int(MATURE_DAYS)}d): **{a['counts']['mature']}** · "
             f"developing: **{a['counts']['developing']}** · too early (<{int(EARLY_DAYS)}d): **{a['counts']['early']}**", "",
             "Metrics are ranked within each platform and never compared across platforms. "
             "Verdicts use mature videos only; everything else is labelled descriptive.", ""]
    if a["snapshot_stale"]:
        lines += ["> ⚠️ Snapshot is older than 36 hours — refresh Buffer Insights before acting on this report.", ""]
    for platform in a["platforms"]:
        rows = [r for r in videos if platform in r["platforms"] and r["platforms"][platform].get("primary_views") is not None]
        rows.sort(key=lambda r: -(r["platforms"][platform]["primary_views"] or 0))
        metric_name = rows[0]["platforms"][platform].get("primary_metric") if rows else "views"
        lines += [f"## {platform} — top by {metric_name}", "",
                  "| Video | Age | Primary | Eng. rate | Comments | Shares | Saves | Views/day (recent) |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for r in rows[:5]:
            e = r["platforms"][platform]
            lines.append(f"| `{r['video_id']}` ({e['maturity']}) | {_fmt(e['age_days'],'d')} | {_fmt(e['primary_views'])} | "
                         f"{_fmt(e['engagement_rate'],'%')} | {_fmt(e['comments'])} | {_fmt(e['shares'])} | "
                         f"{_fmt(e['saves'])} | {_fmt(e['views_per_day_recent'])} |")
        lines.append("")
    mature = sorted((r for r in videos if r["maturity"] == "mature" and r["composite_percentile"] is not None),
                    key=lambda r: -r["composite_percentile"])
    lines += ["## Winners and underperformers (mature, cross-platform percentile)", ""]
    if mature:
        lines += ["**Winners (≥75th percentile):** " + (", ".join(f"`{r['video_id']}` ({r['composite_percentile']})" for r in mature if r["composite_percentile"] >= 75) or "none yet"), "",
                  "**Underperformers (≤25th percentile):** " + (", ".join(f"`{r['video_id']}` ({r['composite_percentile']})" for r in mature if r["composite_percentile"] <= 25) or "none yet"), ""]
    else:
        lines += ["No mature videos yet — winners/losers open up once posts pass 7 days.", ""]
    lines += ["## What the data says by dimension (judged = developing + mature)", "",
              "| Dimension | Group | n | Median percentile | Signal |", "|---|---|---:|---:|---|"]
    for f in a["dimension_findings"]:
        for row in f["rows"]:
            signal = ("strong" if row in f["strong"] else "weak" if row in f["weak"]
                      else "evidence" if row["n"] >= MIN_N_DIMENSION else "descriptive only")
            lines.append(f"| {f['dimension']} | {row['group']} | {row['n']} | {_fmt(row['median_percentile'])} | {signal} |")
    lines += ["", "## Publishing windows (median views, judged posts)", "",
              "| Platform | Window (ET) | n | Median views |", "|---|---|---:|---:|"]
    for row in a["slot_findings"]:
        lines.append(f"| {row['platform']} | {row['daypart']} | {row['n']} | {_fmt(row['median_views'])} |")
    lines += ["", "## Recommended changes", ""]
    if a["recommendations"]:
        for i, rec in enumerate(a["recommendations"], 1):
            lines.append(f"{i}. **{rec['action']}** — {rec['evidence']} (confidence: {rec['confidence']})")
    else:
        lines.append("No recommendation clears the evidence floor yet. Keep collecting data; do not change the format on hunches.")
    lines += ["", "## Trending topics, re-ranked by our own performance", "",
              "Backlog candidates re-scored: base topic score × category performance (0.8–1.2), with a 0.5× "
              "penalty when a candidate overlaps a video we already published.", ""]
    if a["topic_advice"]["top_candidates"]:
        lines += ["| # | Topic | Type | Base | Adjusted | Why |", "|---:|---|---|---:|---:|---|"]
        for i, c in enumerate(a["topic_advice"]["top_candidates"], 1):
            lines.append(f"| {i} | {c['topic'][:80]} | {c['type']} | {_fmt(c['base_score'])} | {_fmt(c['adjusted_score'])} | {'; '.join(c['reasons'])} |")
    else:
        lines.append("No unscored backlog candidates found.")
    if a["topic_advice"]["blocked_by_risk_flags"]:
        lines += ["", "**Blocked by risk flags (never promote):** " +
                  ", ".join(f"{c['topic'][:50]} ({c['risk_flags']})" for c in a["topic_advice"]["blocked_by_risk_flags"][:5]), ""]
    early = [r for r in videos if r["maturity"] == "early"]
    if early:
        lines += ["", "## Too early to judge (<2 days old)", "",
                  ", ".join(f"`{r['video_id']}`" for r in sorted(early, key=lambda r: r["video_id"])), ""]
    lines += ["", "## Guardrails", "",
              "- Buffer metrics refresh about daily and can lag the network by a day; recency is judged on `metrics_updated_at`, not fetch time.",
              "- A percentile says how a video did relative to our own catalogue on that platform — not why. Before changing voice or format, check the actual hook, first frame and audio QA of the specific winners and losers.",
              "- Recommendations under the evidence floor (n < 4, slots n < 3) are withheld rather than guessed.", ""]
    return "\n".join(lines)


def analyze(snapshot: dict, briefs_root: Path, queue: dict, backlog_rows: list,
            now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    videos_map = build_video_records(snapshot, briefs_root, queue, now)
    add_percentiles(videos_map)
    add_velocity(videos_map)
    videos = sorted(videos_map.values(), key=lambda r: r["video_id"])
    dims = dimension_findings(videos_map)
    slots = slot_findings(videos_map)
    fetched = parse_time(snapshot.get("fetched_at"))
    return {
        "schema_version": 1,
        "generated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generated_for_date": now.astimezone(ET).date().isoformat(),
        "snapshot_fetched_at": snapshot.get("fetched_at"),
        "snapshot_complete": bool(snapshot.get("complete")),
        "snapshot_stale": (fetched is None or (now - fetched) > dt.timedelta(hours=36)),
        "platforms": sorted({p for r in videos for p in r["platforms"]}),
        "counts": {m: sum(1 for r in videos if r["maturity"] == m) for m in ("mature", "developing", "early")},
        "videos": videos,
        "dimension_findings": dims,
        "slot_findings": slots,
        "recommendations": build_recommendations(videos_map, dims, slots),
        "topic_advice": topic_advice(backlog_rows, videos_map, dims),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", type=Path, default=ROOT / "tracker/buffer-insights.json")
    ap.add_argument("--briefs", type=Path, default=ROOT / "briefs")
    ap.add_argument("--queue", type=Path, default=ROOT / "queue/publish.json")
    ap.add_argument("--backlog", type=Path, default=ROOT / "topics/backlog.csv")
    ap.add_argument("--out-json", type=Path, default=ROOT / "tracker/performance.json")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "research/performance")
    ap.add_argument("--check", action="store_true", help="print the report without writing files")
    args = ap.parse_args(argv)
    snapshot = load_json(args.snapshot, {})
    if not snapshot.get("posts"):
        print("performance: no Buffer Insights snapshot posts found; run Buffer Insights first", file=sys.stderr)
        return 2
    queue = load_json(args.queue, {"items": []})
    with open(args.backlog, newline="", encoding="utf-8") as f:
        backlog_rows = list(csv.DictReader(f))
    result = analyze(snapshot, args.briefs, queue, backlog_rows)
    report = render_report(result)
    if args.check:
        print(report)
        return 0
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    md_path = args.out_dir / f"performance-{result['generated_for_date']}.md"
    md_path.write_text(report, encoding="utf-8")
    print(f"performance: wrote {args.out_json} and {md_path} "
          f"({len(result['videos'])} videos, {len(result['recommendations'])} recommendations, "
          f"{len(result['topic_advice']['top_candidates'])} ranked candidates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
