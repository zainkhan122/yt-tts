#!/usr/bin/env python3
"""Covered topics: one registry every recommender must consult.

Owner rule (7 Nov 2026): a topic we have already scheduled or published is never recommended again, and the
radar skips it. Before this, `idea_feed.py` and `trend_radar.py` deduped only against their own output, so a
tool that already had a brief could come back as a fresh idea — and did.

The registry is derived, never typed: it is rebuilt from the things that actually exist — and it
is ADDITIVE. A rebuild never removes an entry, so deleting a brief or a plan cannot quietly
un-cover a topic that was already made (or published). Coverage is permanent.

  briefs/<id>.json              a video in production (id + title + keywords + lexicon)
  videos/<id>/plan.json         the plan a brief was built from (tool, title, answer)
  topics/backlog.csv            status selected / scheduled / published / covered
  tracker/publications.json     what is queued or live on a platform

  python3 tools/topics_covered.py build            # rewrite tracker/topics-covered.json
  python3 tools/topics_covered.py list             # what is covered, and where that came from
  python3 tools/topics_covered.py check <name>...   # exit 1 if any name is already covered
  python3 tools/topics_covered.py filter           # stdin: one candidate name per line -> uncovered only

Library use (recommenders):

    from topics_covered import is_covered, filter_names, rebuild
    rebuild()                      # keeps the file honest at the start of a run
    if is_covered("unslop"): skip
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # reels-studio/
REGISTRY = ROOT / "tracker" / "topics-covered.json"
COVERED_STATUS = {"selected", "scheduled", "published", "covered", "in-production", "rendering", "approved"}
# words that describe a topic instead of naming it; they must never become a key on their own
GENERIC = {"repo", "tool", "ai", "app", "skill", "agent", "design", "claude", "codex", "code", "cli",
           "model", "models", "video", "image", "open", "source", "new", "free", "the", "and"}


def key(name: str) -> str:
    """Normalise a tool or topic to one comparable key: lowercase alphanumerics, no video-id suffix."""
    k = re.sub(r"[^a-z0-9]+", "", str(name or "").lower())
    return re.sub(r"(?:0[1-9]|[1-9]\d)$", "", k) if len(k) > 6 else k


def _topic_key(topic: str) -> str:
    """'unslop: every AI screen looks the same' -> 'unslop'."""
    head = re.split(r"[:—–-]", str(topic or ""), maxsplit=1)[0]
    k = key(head)
    return k if k and k not in GENERIC else key(topic)


def _add(reg: dict, name: str, status: str, source: str, video_id: str = "") -> None:
    k = key(name)
    if not k or k in GENERIC:
        return
    row = reg.setdefault(k, {"keys": [], "names": [], "status": status, "sources": [], "videos": []})
    if name and name not in row["names"]:
        row["names"].append(name)
    if source not in row["sources"]:
        row["sources"].append(source)
    if video_id and video_id not in row["videos"]:
        row["videos"].append(video_id)
    if status == "covered":
        row["status"] = "covered"
    elif row["status"] != "covered":
        row["status"] = status


def collect() -> dict:
    reg: dict = {}

    for brief_path in sorted((ROOT / "briefs").glob("*.json")):
        try:
            brief = json.loads(brief_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(brief, dict) or brief.get("draft"):
            continue
        vid = brief.get("id") or brief_path.stem
        slug = re.sub(r"^(repo|tool)-", "", str(vid))
        # the tool, not its keyword list: keywords describe the topic ("AI agents", "accuracy") and would
        # swallow unrelated candidates. The id slug is the name the video was actually made about.
        _add(reg, slug, "covered", f"briefs/{brief_path.name}", vid)
        for kw in brief.get("keywords") or []:
            if key(kw) and key(kw) == key(slug):
                _add(reg, kw, "covered", f"briefs/{brief_path.name}", vid)

    for plan_path in sorted((ROOT / "videos").glob("*/plan.json")):
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        vid = plan.get("id") or plan_path.parent.name
        for field in ("tool", "topic", "title"):
            if plan.get(field):
                _add(reg, plan[field], "covered", f"videos/{plan_path.parent.name}/plan.json", vid)

    backlog = ROOT / "topics" / "backlog.csv"
    if backlog.exists():
        with backlog.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if str(row.get("status", "")).strip().lower() in COVERED_STATUS:
                    _add(reg, _topic_key(row.get("topic", "")), "covered",
                         "topics/backlog.csv", row.get("video_id", ""))
                    _add(reg, re.sub(r"^(repo|tool)-", "", str(row.get("video_id", ""))), "covered",
                         "topics/backlog.csv", row.get("video_id", ""))

    pubs = ROOT / "tracker" / "publications.json"
    if pubs.exists():
        try:
            data = json.loads(pubs.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        records = data.get("records") if isinstance(data, dict) else data
        if isinstance(records, dict):
            records = list(records.values())
        for rec in records or []:
            if not isinstance(rec, dict):
                continue
            vid = str(rec.get("video_id") or rec.get("brief") or rec.get("id") or "")
            if vid and not vid.startswith("draft"):
                _add(reg, re.sub(r"^(repo|tool)-", "", vid), "covered",
                     "tracker/publications.json", vid)
    # A cleaned-up brief/queue can disappear while its successful render remains.
    # Treat actual completed work as in-production (not proof of publication).
    history = ROOT / "tracker" / "render-attempts.json"
    if history.exists():
        try:
            data = json.loads(history.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        attempts = data.get("attempts") or {}
        entries = list(attempts.values()) if isinstance(attempts, dict) else attempts
        entries += data.get("legacy_completed_briefs") or []
        completed = {"success", "render_only_success", "render_succeeded_publish_failed", "scene_rebuild_success", "verified_success"}
        for row in entries:
            if not isinstance(row, dict) or row.get("status") not in completed:
                continue
            vid = str(row.get("brief_id") or "")
            if vid:
                slug = re.sub(r"^(repo|tool|model|news)-", "", vid)
                _add(reg, slug, "rendered", "tracker/render-attempts.json", vid)
    return reg


def _merge(existing: dict, fresh: dict) -> dict:
    """Union the previous registry with the freshly collected one.

    The rebuild is ADDITIVE on purpose. It used to overwrite the file with whatever still exists
    on disk, so deleting a brief or a plan quietly un-covered its topic — and four published
    shorts (repo-autoloop-01, repo-superagent-01, repo-poki-01, repo-vork-01) had already been
    forgotten that way. A topic that was ever covered stays covered: the only cost of a stale
    entry is that we do not make the same short twice, and that is the guarantee we owe.
    """
    out: dict = {}
    for k, row in existing.items():
        if not isinstance(row, dict):
            continue
        out[k] = {"keys": list(row.get("keys") or []),
                  "names": list(row.get("names") or []),
                  "status": row.get("status") or "covered",
                  "sources": list(row.get("sources") or []),
                  "videos": list(row.get("videos") or [])}
    for k, row in fresh.items():
        if k not in out:
            out[k] = dict(row)
            continue
        old = out[k]
        for field in ("names", "sources", "videos", "keys"):
            for item in row.get(field) or []:
                if item not in old[field]:
                    old[field].append(item)
        if row.get("status") == "covered":
            old["status"] = "covered"
    return out


def rebuild() -> dict:
    reg = _merge(load_raw(), collect())
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps({"schema": 1, "built_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    "count": len(reg), "topics": reg}, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    return reg


def load_raw() -> dict:
    """The registry's topic rows, without triggering a rebuild."""
    if not REGISTRY.exists():
        return {}
    try:
        return json.loads(REGISTRY.read_text(encoding="utf-8")).get("topics") or {}
    except Exception:
        return {}


def load() -> dict:
    # Never trust a stale persisted registry by itself; deleted briefs can still
    # be backed by durable render history or new publication records.
    return _merge(load_raw(), collect())


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", str(text or "").lower()) if t]


def is_covered(name: str, reg: dict | None = None) -> dict | None:
    """Return the registry row when this candidate is already covered, else None.

    Matches on the normalised key, and on a covered key appearing as a whole token of the candidate
    ('clean-your-tv' covers 'CleanYourTV', 'unslop skill' covers 'unslop'). Keys shorter than four
    characters must match exactly, so 'rea' cannot eat 'reasoning'."""
    reg = load() if reg is None else reg
    # Repository-qualified references should also match the exact repository
    # basename. This is intentionally not fuzzy substring matching.
    repo = str(name or '').strip().rstrip('/').removesuffix('.git')
    if '/' in repo:
        basename = repo.rsplit('/', 1)[-1]
        basename_key = key(basename)
        if len(basename_key) >= 4 and basename_key in reg:
            return reg[basename_key]
    k = key(name)
    if not k:
        return None
    if k in reg:
        return reg[k]
    toks = _tokens(name)
    flat = "".join(toks)
    for ck, row in reg.items():
        if len(ck) < 4:
            continue
        if ck == k or ck in toks or ck == flat:
            return row
    return None


def filter_names(names: list[str]) -> tuple[list[str], list[tuple[str, dict]]]:
    reg = load()
    keep, dropped = [], []
    for n in names:
        hit = is_covered(n, reg)
        (dropped.append((n, hit)) if hit else keep.append(n))
    return keep, dropped


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "list"
    if cmd == "build":
        reg = rebuild()
        print(f"covered topics: {len(reg)} -> {REGISTRY.relative_to(ROOT)}")
        return 0
    if cmd == "list":
        reg = load()
        for k, row in sorted(reg.items(), key=lambda kv: kv[0]):
            print(f"{k:24s} {row.get('status', ''):12s} {', '.join(row.get('names', [])[:3])}"
                  f"  <- {', '.join(row.get('sources', [])[:2])}")
        print(f"\n{len(reg)} covered topics")
        return 0
    if cmd == "check":
        reg = load()
        bad = [(n, r) for n in argv[1:] if (r := is_covered(n, reg))]
        for n, row in bad:
            print(f"COVERED {n} (from {', '.join(row.get('videos') or row.get('sources', [])[:1])})")
        print("ok" if not bad else f"{len(bad)} already covered")
        return 1 if bad else 0
    if cmd == "filter":
        keep, dropped = filter_names([ln.strip() for ln in sys.stdin if ln.strip()])
        for n, row in dropped:
            print(f"# covered: {n}", file=sys.stderr)
        for n in keep:
            print(n)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
