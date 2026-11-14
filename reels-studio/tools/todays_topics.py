#!/usr/bin/env python3
"""Today's topics — source-channel shorts and GitTrend Today candidates.

Owner update: include GitTrend Today alongside source-channel Shorts. Keep their
metrics separate: channel views are not comparable to repository star velocity.
Show the date GitTrend actually displays and label unavailable or stale snapshots.

  python3 tools/sources.py scan --latest 15   # refresh research/sources/posts.csv first
  python3 tools/todays_topics.py              # writes research/topics/daily-<today>.md

Ranking: views ÷ the channel's OWN median views (outlier multiple, same idea as
tools/topic_rank.py) computed over every post we have for that channel. Medians are
only shown when we hold >= 4 viewed samples, otherwise the column says n/a.

Exit codes: 0 = sheet written (possibly an announced silent day); 2 = the sources
scan looks stale or never ran, so an empty lane cannot pass silently.
"""
import csv
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "research" / "sources" / "posts.csv"
OUT_DIR = ROOT / "research" / "topics"
STALE_AFTER_H = 26  # no tiktok/youtube row touched in the last 26 h => scan missing/stale


def parse_ts(raw):
    if not raw:
        return None
    try:
        t = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def main():
    now = dt.datetime.now(dt.timezone.utc)
    rows = list(csv.DictReader(open(POSTS, newline="", encoding="utf-8")))
    video = [r for r in rows if r.get("platform") in ("tiktok", "youtube")]

    medians, counts = {}, {}
    for ch in {f"{r['platform']}:{r['source']}" for r in video}:
        views = sorted(int(r["views"]) for r in video
                       if f"{r['platform']}:{r['source']}" == ch and (r.get("views") or "").isdigit()
                       and int(r["views"]) > 0)
        counts[ch] = len(views)
        if len(views) >= 4:
            medians[ch] = views[len(views) // 2]

    fresh = []
    for r in video:
        pub = parse_ts(r.get("published"))
        if pub and 0 <= (now - pub).total_seconds() <= 86400:
            fresh.append(r)

    touched = [t for t in (parse_ts(r.get("last_seen")) or parse_ts(r.get("first_seen")) for r in video) if t]
    last_scan = max(touched) if touched else None
    scan_stale = last_scan is None or (now - last_scan).total_seconds() > STALE_AFTER_H * 3600

    def multiple(r):
        ch = f"{r['platform']}:{r['source']}"
        m = medians.get(ch)
        v = int(r["views"]) if (r.get("views") or "").isdigit() else 0
        return (v / m) if m else None

    fresh.sort(key=lambda r: (multiple(r) is None, -(multiple(r) or 0)))

    today = now.date().isoformat()
    L = [f"# Today's topics: {today} — source channels and GitTrend", ""]
    if scan_stale:
        L += ["> **SCAN STALE — re-run `python3 tools/sources.py scan --latest 15` before trusting this sheet.**", ""]
    L += ["Inputs: SHORTS published in the last 24 h by the source channels in research/sources.csv "
          "(TikTok + YouTube Shorts). GitTrend Today is a separate source lane below; its "
          "star-velocity ranking is not comparable to video views.", ""]
    L += [f"## Source-channel shorts — last 24 h ({len(fresh)})", "",
          "| Platform | Source | Short | Views | Chan. median | ×median | Age (h) |",
          "|---|---|---|---|---|---|---|"]
    for r in fresh:
        ch = f"{r['platform']}:{r['source']}"
        m = medians.get(ch)
        mult = multiple(r)
        views = int(r["views"]) if (r.get("views") or "").isdigit() else 0
        age_h = (now - parse_ts(r["published"])).total_seconds() / 3600
        L.append(f"| {r['platform']} | {r['source']} | [{(r.get('title') or r['url'])[:80]}]({r['url']}) "
                 f"| {views:,} | {f'{m:,}' if m else 'n/a'} | {f'{mult:.1f}x' if mult else 'n/a'} | {age_h:.1f} |")
    if not fresh:
        L.append("| - | - | (no source-channel shorts in the last 24 h) | - | - | - | - |")

    sys.path.insert(0, str(ROOT / "tools"))
    import trend_radar, topics_covered
    snapshot = trend_radar.gittrend_snapshot(25)
    covered = topics_covered.collect()
    date = snapshot["date"]
    L += ["", "## GitTrend Today — star velocity (separate signal)", ""]
    if not date or not snapshot["items"]:
        L.append("**Unavailable or undated:** do not treat the list as fresh.")
    else:
        delta = (now.date() - dt.date.fromisoformat(date)).days
        freshness = "current UTC date" if delta == 0 else f"NOT current UTC date (difference {delta} days)"
        L.append(f"Site-reported date: {date} — {freshness}. Source: https://gittrend.io/ .")
        L += ["", "| Source rank | Repository | Selection status |", "|---|---|---|"]
        for item in snapshot["items"]:
            name = item["name"]
            hit = topics_covered.is_covered(name.split("/", 1)[-1], covered)
            status = "Already covered/selected — exclude" if hit else "Candidate — verify fit and claims"
            L.append(f"| {item['rank']} | [{name}]({item['url']}) | {status} |")

    L += ["", f"**Summary:** {len(fresh)} shorts in the last 24 h "
              f"(scan last touched {last_scan.isoformat(timespec='minutes') if last_scan else 'never'}). "
              "Shorts are ranked by outlier multiple; GitTrend candidates use the site's separate ranking."]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"daily-{today}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"daily topics -> {out.relative_to(ROOT.parent)}")
    print(f"shorts 24h: {len(fresh)} · source channels: {len(counts)} · medians computed: {len(medians)}")
    if scan_stale:
        print("warn: sources scan stale/missing — run tools/sources.py scan --latest 15", file=sys.stderr)
        return 2
    if not fresh:
        print("note: 0 source-channel shorts in the last 24 h; check the separate GitTrend lane", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
