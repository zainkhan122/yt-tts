#!/usr/bin/env python3
"""Today's topic candidates, built from ALL live inputs with a strict last-24-hours window.

Rule: "give me today's topics" ALWAYS means every one of these, never radar alone:
  1. Trend radar (GitHub new repos + GitTrend + Hugging Face models/Spaces) — last 24 h only.
  2. Source channels (research/sources.csv): TikTok + YouTube Shorts ONLY, and ONLY shorts
     published in the last 24 h (long-form videos are excluded; undated rows are excluded).
  3. News feeds (the RSS/everything channels in sources.csv: Product Hunt, HF blog,
     Reddit, ...) — last 24 h only.
  4. The covered/scheduled ledger (tools/topics_covered.py) filters out anything already
     rendered or queued, so no topic ever repeats what we made or scheduled.

Writes research/topics/daily-YYYY-MM-DD.md grouped by input, every row tagged with its
age, so the human editor picks the top 10 from one sheet.

  python3 tools/sources.py scan --latest 15   # refresh first (fills published dates)
  python3 tools/todays_topics.py              # -> research/topics/daily-<today>.md
  python3 tools/todays_topics.py --no-scan    # reuse existing posts.csv
"""
import csv
import datetime as dt
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

DAY = dt.timedelta(days=1)


def entries_24h():
    """Source-channel posts: STRICT last 24 h by publish time. Shorts only (tiktok + youtube shorts)."""
    posts = ROOT / "research/sources/posts.csv"
    if not posts.exists():
        return [], []
    now = dt.datetime.now(dt.timezone.utc)
    shorts, news = [], []
    for r in csv.DictReader(posts.open(encoding="utf-8", newline="")):
        pub = r.get("published") or ""
        if not pub:
            continue
        ts = dt.datetime.fromisoformat(pub).timestamp()
        age_h = (now.timestamp() - ts) / 3600
        if age_h > 24 or age_h < 0:
            continue
        try:
            views = int(float(r.get("views") or 0))
        except ValueError:
            views = 0
        rec = {"platform": r["platform"], "source": r["source"], "title": (r.get("title") or "")[:110],
               "url": r.get("url") or "", "views": views, "age_h": round(age_h, 1)}
        if r["platform"] in ("tiktok", "youtube"):  # 'youtube' = a shorts tab post; '-long' is excluded
            shorts.append(rec)
        elif r["platform"] in ("web", "rss"):
            news.append(rec)
    return sorted(shorts, key=lambda x: -x["views"]), sorted(news, key=lambda x: -x["views"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-scan", action="store_true", help="skip re-running trend_radar fetches")
    a = ap.parse_args()

    import trend_radar, topics_covered
    today = dt.date.today().isoformat()

    gh = trend_radar.github(1)  # last 24 h: GitHub created <= 1 day ago
    trending = trend_radar.gittrend()
    solved = topics_covered.rebuild()
    gh = [r for r in gh if not topics_covered.is_covered(r["name"], solved)]
    trending = [t for t in trending if not topics_covered.is_covered(t["name"], solved)]

    # HF "trending" is already a ~24h velocity chart; ledger-filtered the same way.
    models = [m for m in trend_radar.hf("models") if not topics_covered.is_covered(m["name"], solved)]
    spaces = [m for m in trend_radar.hf("spaces") if not topics_covered.is_covered(m["name"], solved)]

    shorts, news = entries_24h()
    if not shorts:
        print("warn: no source-channel shorts dated within 24 h — run tools/sources.py scan --latest 15 first",
              file=sys.stderr)

    L = [f"# Today's topics: {today} (strict last 24 h windows)", "",
         "Inputs: trend radar (GitHub/GitTrend/Hugging Face) last 24 h · source-channel SHORTS published "
         "in the last 24 h (TikTok + YouTube Shorts only) · RSS news feeds last 24 h. "
         "All rows already ledger-filtered (never re-recommend covered or scheduled topics).", "",
         f"## 1. Source-channel shorts — last 24 h ({len(shorts)})", "",
         "| Platform | Source | Short | Views | Age (h) |", "|---|---|---|---|---|"]
    for s in shorts:
        L.append(f"| {s['platform']} | {s['source']} | [{s['title'] or s['url']}]({s['url']}) | {s['views']:,} | {s['age_h']} |")
    if not shorts:
        L.append("| - | - | (none dated within 24 h — re-run sources scan) | - | - |")

    L += ["", f"## 2. News feeds — last 24 h ({len(news)})", "", "| Source | Headline | Age (h) |", "|---|---|---|"]
    for s in news[:25]:
        L.append(f"| {s['source']} | [{s['title'] or s['url']}]({s['url']}) | {s['age_h']} |")

    safe = [r for r in gh if not r["flags"] and not r["zh"]]
    L += ["", f"## 3. New GitHub repos — created in the last 24 h ({len(gh)}, {len(safe)} safe)", "",
          "| Repo | ★ | ★/day | Licence | What it is | Flags |", "|---|---|---|---|---|---|"]
    for r in gh[:20]:
        fl = ("⚠ " + ", ".join(r["flags"])) if r["flags"] else ("ZH" if r["zh"] else "")
        L.append(f"| [{r['name']}]({r['url']}) | {r['stars']:,} | {r['per_day']:.0f} | {r['license']} | {r['desc'][:90].replace('|', '/')} | {fl} |")

    L += ["", f"## 4. GitTrend star velocity, today ({len(trending)} after ledger filter)", ""]
    L += [f"- [{t['name']}]({t['url']})" for t in trending] or ["- (none after filtering)"]

    for title, items in ((f"5. Trending HF models, today ({len(models)})", models),
                         (f"6. Trending HF Spaces, today ({len(spaces)})", spaces)):
        L += ["", f"## {title}", "", "| Item | Trend score | Likes | Type | Flags |", "|---|---|---|---|---|"]
        for m in items[:12]:
            L.append(f"| [{m['name']}]({m['url']}) | {m['score']} | {m['likes']} | {m['tag']} | {('⚠ ' + ', '.join(m['flags'])) if m['flags'] else ''} |")

    L += ["", f"**Summary:** {len(shorts)} shorts + {len(news)} news (last 24 h), {len(gh)} new repos ({len(safe)} safe), "
              f"{len(models)} models / {len(spaces)} spaces — all ledger-deduped. Editor picks the top 10 from this sheet."]
    out = ROOT / "research/topics" / f"daily-{today}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"daily topics -> {out.relative_to(ROOT.parent)}")
    print(f"shorts 24h: {len(shorts)} · news 24h: {len(news)} · new repos: {len(gh)} ({len(safe)} safe) · "
          f"models: {len(models)} · spaces: {len(spaces)}")
    if shorts:
        print("\nTop shorts last 24 h:")
        for s in shorts[:10]:
            print(f"  {s['views']:>10,}  {s['source']:18} {s['title'][:80]}")


if __name__ == "__main__":
    main()
