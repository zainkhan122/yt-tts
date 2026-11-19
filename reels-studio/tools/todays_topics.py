#!/usr/bin/env python3
"""Today's topics — EVERY registered source, rolling last 24 h, deduped by topic.

Owner rule (14 Nov 2026): "get topics" means every source in research/sources.csv — the TikTok
channels, the YouTube channels, the RSS feeds and gittrend.io — and only what they published in
the last 24 hours. The sheet is the one command that proves it: it prints, per source, how many
items it contributed inside the window, and it never recommends a topic we already covered.

  python3 tools/sources.py scan --latest 15   # refresh research/sources/posts.csv (all sources)
  python3 tools/todays_topics.py              # -> research/topics/daily-<today>.md + .json
  python3 tools/todays_topics.py --hours 12 --show-covered

What the sheet does:
  1. Rolling window: 0 <= now - published <= hours. The stored stamp is a full ISO timestamp, so
     "last 24 h" is a real rolling window, not a calendar day.
  2. Consensus dedup: the same tool mentioned by five channels is ONE row with five sources — it
     is never five ideas, and it never becomes five shorts.
  3. Covered filter: a topic with a brief, a plan, a backlog row in production, or a published
     post is excluded (tools/topics_covered.py), so no duplicate short can start from this sheet.

Exit codes: 0 = sheet written; 2 = the sources scan looks stale, so an empty lane cannot pass
silently.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

POSTS = ROOT / "research" / "sources" / "posts.csv"
OUT_DIR = ROOT / "research" / "topics"
STALE_AFTER_H = 26  # no row touched in the last 26 h => the scan is missing or stale


def parse_ts(raw):
    """ISO 8601 (or a legacy date-only stamp) -> aware datetime."""
    if not raw:
        return None
    raw = str(raw).strip()
    try:
        t = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            t = dt.datetime.strptime(raw[:10], "%Y-%m-%d")
        except ValueError:
            return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def source_kind(row, registry):
    """The registry type of a row: tiktok | youtube | rss | web."""
    st = (row.get("source_type") or "").strip().lower()
    if st:
        return st
    handle = (row.get("source") or "").strip()
    if handle in registry:
        return registry[handle].get("type") or "rss"
    plat = (row.get("platform") or "").lower()
    if plat.startswith("youtube"):
        return "youtube"
    if plat.startswith("tiktok"):
        return "tiktok"
    return "web"


# ---- how a post names the thing it is about --------------------------------------------
# The posts the registry reads have recognisable shapes, and each one names the product in a
# different place. Reading the URL instead of the title is what produced junk topics like
# "TJ2GD_w" (a YouTube id) and "ASDSTE100" (noise in a TikTok caption).
REPO_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([\w.-]+)/([\w.-]+)", re.I)
# An owner/repo written without the github.com prefix ("acme/other-tool"). The owner may not
# contain a dot: that keeps a truncated "github.com/o" from becoming a topic called "github.com/o".
REPO_SLUG_RE = re.compile(r"(?<![\w/.])([\w-]{2,40})/([\w.-]{2,60})(?![\w/])")
LEAD_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][\w .+&'/-]{1,48}?)\s*:\s+\S")
TRAILING_RE = re.compile(
    r"\s+(?:is here|just (?:released|launched|dropped|shipped)|released|launched|now live|is out|"
    r"hits \d+.*|reaches \d+.*)\b.*$", re.I)
# Words that describe a topic instead of naming it.
GENERIC_WORDS = {
    "our", "this", "that", "the", "a", "an", "it", "its", "how", "why", "what", "when", "new",
    "best", "top", "free", "open", "source", "now", "just", "here", "today", "you", "your", "we",
    "they", "ai", "app", "apps", "tool", "tools", "video", "model", "models", "agent", "agents",
    "code", "repo", "repos", "github", "release", "version", "update", "launch", "launches",
    "introducing", "announcing", "built", "make", "makes", "using", "use", "first", "one", "two",
}
# Ordinary English words that a headline capitalises. A candidate made only of these is a
# sentence, not a product ("Build", "Look", "Replay", "Weight Space Programming for Quantization").
COMMON_WORDS = GENERIC_WORDS | {
    "build", "look", "replay", "drops", "happens", "physics", "businesses", "business", "default",
    "tamer", "semantics", "instead", "lowering", "gpu", "weight", "space", "programming",
    "quantization", "helping", "image", "news", "fight", "fighting", "employees", "employee",
    "nvidia", "builds", "built", "write", "writes", "writing", "reads", "read", "readme", "guide",
    "guides", "tutorial", "tips", "tricks", "review", "reviews", "benchmark", "benchmarks",
    "release", "released", "launch", "launched", "dropped", "shipped", "arrives", "arrived",
    "starts", "start", "stop", "stops", "ends", "begin", "begins", "gets", "got", "get", "goes",
    "going", "gone", "come", "comes", "coming", "make", "makes", "made", "making", "take",
    "takes", "taking", "give", "gives", "giving", "get", "try", "trying", "tries", "need",
    "needs", "want", "wants", "can", "could", "would", "should", "will", "shall", "may", "might",
    "must", "not", "no", "yes", "still", "even", "also", "only", "always", "never", "again",
    "back", "down", "off", "out", "over", "under", "up", "into", "onto", "from", "with", "without",
    "about", "after", "before", "while", "because", "just", "very", "more", "most", "than",
    "then", "every", "each", "last", "next", "every", "other", "some", "any", "all", "both",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "many", "much",
    "there", "here", "when", "where", "which", "who", "whom", "whose", "been", "being", "was",
    "were", "are", "has", "have", "had", "does", "did", "doing", "let", "lets", "really", "never",
    "top", "best", "free", "new", "old", "big", "small", "new", "great", "good", "bad", "long",
    "short", "fast", "slow", "easy", "hard", "right", "wrong", "real", "true", "false", "full",
}
VERSION_RE = re.compile(r"\bv(\d+(?:\.\d+)*)\b", re.I)
PH_URL_RE = re.compile(r"producthunt\.com/products/", re.I)


def canonical_key(name: str) -> str:
    """One comparable key per topic: 'llama.cpp v1.0' and 'llama.cpp v1.0.0' are the SAME topic."""
    s = str(name or "").lower().strip()
    s = re.sub(r"[-_](?:src|sources?|examples?|demo|demos)$", "", s)      # modern-web-guidance(-src)
    s = VERSION_RE.sub(lambda m: "v" + m.group(1).split(".")[0], s)       # v1.0.0 -> v1
    return re.sub(r"[^a-z0-9]+", "", s)


def _plausible(name: str) -> bool:
    """A topic is a product/repo name, not a headline, a sentence or a person's name."""
    n = str(name or "").strip()
    if not n or len(n) > 60:
        return False
    words = [w for w in re.split(r"[\s/]+", n) if w]
    if not words or len(words) > 5:
        return False
    if any(w.endswith("'s") or w.endswith("’s") for w in words):
        return False                      # "Andrej Karpathy's ..." is a person, not a product
    if all(w.isupper() for w in words):
        return False                      # "LET GO of your $20 tasks." is a headline
    if not any(w[:1].isupper() or re.search(r"[.\d]", w) for w in words):
        return False
    plain = [w.lower().strip(".,!?:") for w in words]
    common = sum(1 for w in plain if w in COMMON_WORDS)
    if common == len(plain):
        return False                      # every word is ordinary: a sentence
    if len(words) > 1 and common * 2 >= len(words):
        return False                      # mostly ordinary words: a phrase, not a name
    return True


def _proper_run(title: str) -> str:
    """The leading proper-noun run of a title: 'Minimax H3 image is ...' -> 'Minimax H3'."""
    s = TRAILING_RE.sub("", str(title or "").strip())
    s = re.split(r"\s+[—|–]\s+", s)[0]
    run: list[str] = []
    for tok in s.split():
        core = tok.strip(".,!?:;\"'()")
        if not core:
            break
        if core.lower() in GENERIC_WORDS:
            if run:
                break
            continue
        proper = core[:1].isupper() or bool(re.search(r"[.\d]", core))
        if not proper:
            break
        run.append(core)
        if len(run) >= 4:
            break
    return " ".join(run).strip(" .,!?:;")


def topic_candidates(row, kind):
    """The tools/repos one post is about -> [(key, display)].

    Priority: an explicit repo link (one product per post), then the 'Name: description' lead,
    then a known tool from the lexicon, then the leading proper-noun run.
    """
    import idea_feed

    title = (row.get("title") or "").strip()
    url = (row.get("url") or "").strip()
    if kind == "web" and "/" in title and " " not in title:
        # gittrend lists "owner/repo": the repo IS the topic.
        return [(canonical_key(title), title)]

    out: list[tuple[str, str]] = []
    seen = set()

    def add(display: str):
        display = str(display or "").strip(" .,!?:;")
        if not display:
            return
        k = canonical_key(display)
        if not k or k in seen:
            return
        seen.add(k)
        out.append((k, display))

    # 1. the repo the post points at — the strongest topic signal there is
    for m in REPO_RE.finditer(title):
        owner, repo = m.group(1), m.group(2).rstrip(".,")
        if owner.lower() in ("sponsors", "topics", "orgs", "collections", "features", "about"):
            continue
        add(f"{owner}/{repo}")
    if out:
        return out[:2]

    # 1a. an owner/repo written without the github.com prefix ("acme/other-tool")
    for m in REPO_SLUG_RE.finditer(title):
        owner, repo = m.group(1), m.group(2).rstrip(".,")
        if owner.lower() in ("sponsors", "topics", "orgs", "collections", "features", "about", "r"):
            continue
        add(f"{owner}/{repo}")
    if out:
        return out[:1]

    # 1b. a Product Hunt feed item IS the product: its title is the product name. The URL slug
    #     carries a duplicate-name suffix ("codemesh-2"), so the title is the honest name.
    if PH_URL_RE.search(url):
        if title and len(title) <= 60:
            add(title)
            return out[:1]

    # 2. the leading proper-noun run. RSS feeds (release notes, launch posts) name the product
    #    in prose; video channels name it in a repo link, a lead or the lexicon, and a prose
    #    title from a business channel is not a topic at all.
    if kind == "rss":
        run = _proper_run(title)
        if run and _plausible(run):
            add(run)
            return out[:1]

    # 3. 'Name: description' — how the repo-picker channels announce a tool
    m = LEAD_NAME_RE.match(title)
    if m and _plausible(m.group(1)):
        add(m.group(1))
        return out[:1]

    # 4. a known tool from the lexicon (Claude Code, Qwen, ...)
    for rx, canon, _ in getattr(idea_feed, "LEXICON", []):
        if rx.search(title):
            add(canon)
            break
    return out[:1]


def _rel(path: Path) -> str:
    """Print a path relative to the studio when it is inside it, else absolute."""
    try:
        return str(path.relative_to(ROOT.parent))
    except ValueError:
        return str(path)


def main(argv=None, *, now=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hours", type=float, default=24.0, help="rolling window in hours (default 24)")
    ap.add_argument("--show-covered", action="store_true", help="list covered topics instead of hiding them")
    ap.add_argument("--limit", type=int, default=40, help="max topic rows in the sheet")
    a = ap.parse_args(argv)

    import sources
    import topics_covered

    registry = {s["handle"]: s for s in sources.load()}
    now = now or dt.datetime.now(dt.timezone.utc)
    window_s = a.hours * 3600

    rows = list(csv.DictReader(open(POSTS, newline="", encoding="utf-8"))) if POSTS.exists() else []

    # ---- staleness: the sheet must never look empty because nobody scanned
    touched = [t for t in (parse_ts(r.get("last_seen")) or parse_ts(r.get("first_seen")) for r in rows) if t]
    last_scan = max(touched) if touched else None
    scan_stale = last_scan is None or (now - last_scan).total_seconds() > STALE_AFTER_H * 3600

    # ---- per-channel medians (the outlier multiple: this channel's reach vs its own usual)
    view_rows = [r for r in rows if (r.get("views") or "").isdigit() and int(r["views"]) > 0]
    medians, counts = {}, {}
    for ch in {f"{source_kind(r, registry)}:{r['source']}" for r in view_rows}:
        vs = sorted(int(r["views"]) for r in view_rows if f"{source_kind(r, registry)}:{r['source']}" == ch)
        counts[ch] = len(vs)
        if len(vs) >= 4:
            medians[ch] = vs[len(vs) // 2]

    # ---- the rolling window
    fresh = []
    for r in rows:
        pub = parse_ts(r.get("published"))
        if not pub:
            continue
        age = (now - pub).total_seconds()
        if 0 <= age <= window_s:
            fresh.append((r, pub, age))

    # ---- consensus dedup: one row per topic, many sources
    agg = {}
    per_source = {}
    for r, pub, age in fresh:
        kind = source_kind(r, registry)
        handle = r.get("source") or "?"
        label = f"{kind}:{handle}"
        per_source.setdefault(label, []).append(r)
        views = int(r["views"]) if (r.get("views") or "").isdigit() else 0
        for k, disp in topic_candidates(r, kind):
            tp = agg.setdefault(k, {"key": k, "name": disp, "sources": set(), "views": 0, "posts": [],
                                    "best": None, "age_h": age, "kind": kind})
            tp["sources"].add(label)
            tp["views"] += views
            tp["age_h"] = min(tp["age_h"], age)
            tp["kind"] = kind if kind in ("tiktok", "youtube") else tp["kind"]
            if disp and ("/" in disp or not tp.get("name")):
                tp["name"] = disp
            title = (r.get("title") or "").strip()[:110]
            if title and title not in [p["title"] for p in tp["posts"]]:
                tp["posts"].append({"title": title, "url": r.get("url") or "", "source": label,
                                    "views": views, "age_h": age})
            if tp["best"] is None or views > tp["best"][0]:
                tp["best"] = (views, r.get("url") or "", label)

    covered_reg = topics_covered.rebuild()
    topics = []
    for tp in agg.values():
        hit = topics_covered.is_covered(tp["name"], covered_reg)
        if not hit:
            repo = tp["name"].split("/")[-1]
            hit = topics_covered.is_covered(repo, covered_reg)
        tp["covered"] = hit
        topics.append(tp)

    # First-party channel history actually contributes to the ranking (bounded,
    # transparent, and neutral when too sparse); external consensus still matters.
    import math
    import selection_analytics
    analytics_rows = selection_analytics.load_rows(now)
    for tp in topics:
        ch = tp["best"][2] if tp["best"] else ""
        m = medians.get(ch)
        # Compare the best individual source post with its own channel median;
        # never divide summed cross-channel views by one channel's median.
        mult = (tp["best"][0] / m) if m and tp["best"] else 0.0
        discovery = min(4.0, 1.5 * math.log2(1 + len(tp["sources"]))) + min(3.0, math.log2(1 + mult))
        tp["selection_score"] = selection_analytics.score_candidate(tp, analytics_rows, discovery)
    topics.sort(key=lambda t: (-t["selection_score"]["total_score"], t["age_h"], t["name"].lower()))
    fresh_topics = [t for t in topics if not t["covered"]]
    covered_topics = [t for t in topics if t["covered"]]

    # ---- the sheet
    today = now.date().isoformat()
    L = [f"# Today's topics: {today} — every registered source, last {a.hours:g} h", ""]
    from statistics import median
    usable_analytics = len(analytics_rows) >= 5 and median([r["views"] for r in analytics_rows]) > 0
    if not usable_analytics:
        L += ["> **Analytics unavailable, insufficient or too stale: ranking has no first-party adjustment; do not present it as analytics-informed.**", ""]
    else:
        L += [f"First-party YouTube baseline: {len(analytics_rows)} comparable 24–48-hour snapshots; median {median([r['views'] for r in analytics_rows]):g} views. Per-topic comparisons and exact snapshots are in the JSON. Small samples are directional, not forecasts.", ""]
    if scan_stale:
        L += ["> **SCAN STALE — re-run `python3 tools/sources.py scan --latest 15` before trusting this sheet.**", ""]
    L += [f"Registry: **{len(registry)} sources** ({sum(1 for s in registry.values() if s.get('type') == 'tiktok')} TikTok, "
          f"{sum(1 for s in registry.values() if s.get('type') == 'youtube')} YouTube, "
          f"{sum(1 for s in registry.values() if s.get('type') == 'rss')} RSS, "
          f"{sum(1 for s in registry.values() if s.get('type') == 'web')} web). "
          f"Items inside the rolling {a.hours:g} h window: **{len(fresh)}**. "
          f"Topics after consensus dedup: **{len(topics)}** ({len(fresh_topics)} fresh, {len(covered_topics)} already covered).", ""]

    L += ["## Source coverage in the window", "",
          "| Source | Type | Items in window | Newest item |", "|---|---|---|---|"]
    for handle, src in sorted(registry.items(), key=lambda kv: (kv[1].get("type", ""), kv[0])):
        label = f"{src.get('type')}:{handle}"
        items = per_source.get(label, [])
        newest = min((i[2] for i in fresh if f"{source_kind(i[0], registry)}:{i[0].get('source')}" == label), default=None)
        L.append(f"| {handle} | {src.get('type')} | {len(items)} | "
                 f"{(f'{newest / 3600:.1f} h ago' if newest is not None else '—')} |")
    L.append("")

    # ---- GitTrend freshness (upstream feature, kept): the site's own date, not fetch time.
    # A ranking that is undated, or dated with a gap, must say so: a stale "Today" list presented
    # as fresh is how a duplicate topic gets picked twice.
    try:
        import trend_radar
        snapshot = trend_radar.gittrend_snapshot(25)
        site_date = snapshot.get("date")
        site_items = snapshot.get("items") or []
    except Exception as exc:  # the lane is optional; a failure must be visible, not silent
        site_date, site_items = None, []
        L += ["## GitTrend lane", "", f"**Unavailable: {exc.__class__.__name__} — do not treat the "
              f"GitTrend list as fresh.**", ""]
    if site_date or site_items:
        if not site_date:
            L += ["## GitTrend lane", "", "**Undated snapshot — do not treat the list as fresh.**", ""]
        else:
            delta = (now.date() - dt.date.fromisoformat(site_date)).days
            fresh_note = ("current UTC date" if delta == 0
                          else f"NOT the current UTC date (difference {delta} days)")
            L += ["## GitTrend lane", "",
                  f"Site-reported date: **{site_date}** — {fresh_note}. "
                  f"Source: https://gittrend.io/ . Star velocity is not comparable to video views.", ""]
    covered_names = {t["name"].split("/")[-1].lower() for t in covered_topics}
    git_candidates = [i for i in site_items if i["name"].split("/", 1)[-1].lower() not in covered_names]
    if git_candidates:
        L += ["GitTrend candidates (separate signal — verify fit and claims before picking):", "",
              "| Rank | Repository | Covered? |", "|---|---|---|"]
        for item in git_candidates[:15]:
            repo = item["name"].split("/", 1)[-1]
            hit = repo.lower() in covered_names
            L.append(f"| {item.get('rank', '')} | [{item['name']}]({item.get('url', '')}) | "
                     f"{'already covered — exclude' if hit else 'candidate'} |")
        L.append("")

    L += [f"## Fresh topics ({len(fresh_topics)})", "",
          "**Consensus** = how many different sources mentioned it. One row per topic: the same tool "
          "seen by five channels is one idea, never five. Score = bounded discovery signal + first-party comparable-video analytics adjustment; missing data is neutral, not zero performance. Use as an editorial shortlist, not a prediction.", "",
          "| # | Topic | Type | Consensus | Sources | Views | Age (h) | Analytics adjustment | Score | Best link |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for i, t in enumerate(fresh_topics[:a.limit], 1):
        best = t["best"]
        ch = best[2] if best else ""
        m = medians.get(ch)
        v = t["views"]
        extra = f" (best post {best[0] / m:.1f}x its channel median)" if m and best else ""
        adj = t["selection_score"]["analytics"]["adjustment"]
        total = t["selection_score"]["total_score"]
        L.append(f"| {i} | **{t['name']}** | {t['kind']} | {len(t['sources'])} | "
                 f"{', '.join(sorted(t['sources']))} | {v:,}{extra} | {t['age_h'] / 3600:.1f} | {adj:+.2f} | {total:.2f} | "
                 f"{('[' + best[1][:46] + '](' + best[1] + ')') if best and best[1] else '—'} |")
    if not fresh_topics:
        L.append("| - | - | (no fresh topic in the window — the lane is genuinely empty) | - | - | - | - | - |")

    if covered_topics and a.show_covered:
        L += ["", f"## Already covered ({len(covered_topics)}) — excluded, never re-recommended", ""]
        for t in covered_topics:
            row = t["covered"] or {}
            L.append(f"- ~~{t['name']}~~ — {row.get('status', 'covered')} "
                     f"({', '.join((row.get('videos') or row.get('sources') or [])[:2])})")

    L += ["", "## What to do with this sheet", "",
          "1. Pick from the fresh table only. Consensus ≥ 2 is a confirmed niche trend.",
          "2. `python3 tools/topics_covered.py check <topic>` before you start — it exits 1 if the "
          "topic is already covered, so a duplicate short cannot begin.",
          "3. The sheet is a candidate list, not a script: every claim still needs a source.", ""]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"daily-{today}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---- machine-readable form for the selection/plan stages
    payload = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_hours": a.hours,
        "analytics_cohort": analytics_rows,
        "sources_registered": len(registry),
        "items_in_window": len(fresh),
        "scan_last_seen": last_scan.isoformat() if last_scan else None,
        "scan_stale": scan_stale,
        "topics": [
            {"key": t["key"], "name": t["name"], "kind": t["kind"], "consensus": len(t["sources"]),
             "sources": sorted(t["sources"]), "views": t["views"], "age_h": round(t["age_h"] / 3600, 2),
             "covered": bool(t["covered"]), "selection_score": t["selection_score"],
             "posts": t["posts"][:4],
             "best_url": t["best"][1] if t["best"] else ""}
            for t in topics if not t["covered"]
        ],
    }
    jout = OUT_DIR / f"daily-{today}.json"
    jout.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"daily topics -> {_rel(out)}")
    print(f"sources: {len(registry)} registered · {len(per_source)} with items in {a.hours:g} h · "
          f"items {len(fresh)} · topics {len(topics)} (fresh {len(fresh_topics)}, covered {len(covered_topics)})")
    print(f"json -> {_rel(jout)}")
    if scan_stale:
        print("warn: sources scan stale/missing — run tools/sources.py scan --latest 15", file=sys.stderr)
        return 2
    if not fresh:
        print("note: 0 items in the window — the lane is genuinely empty, nothing to pick", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
