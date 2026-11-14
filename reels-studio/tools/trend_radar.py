#!/usr/bin/env python3
"""
Trend radar for the AI-tools niche: what is new and rising, from free public APIs (no scraping):
  * GitHub search API  - new AI repos (created in the last N days) ranked by stars/day
  * Hugging Face API   - trending models and trending Spaces (free "try it" apps)
Every item gets a RISK FLAG only for sexual or uncensored content (owner rule: no ToS, legal or licence exclusions).
Flagged items are never put into briefs.

  python3 tools/trend_radar.py --days 14            # writes research/radar/radar-YYYY-MM-DD.md
  python3 tools/trend_radar.py --days 14 --brief    # + briefs/draft-trending-repos-YYYY-MM-DD.json (placeholders only; a human writes the copy)
Uses GH_TOKEN or /var/tmp/gh/token if present (higher rate limit); works without.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Owner rule (30 Oct 2026): TOS, legal, licence and privacy are not a reason to exclude a topic.
# The only flag left is content the channel does not run (sexual content).
RISK = {
    "nsfw/uncensored": r"uncensor|nsfw|nude|porn|hentai|abliterat",
}
AI = re.compile(r"\b(ai|llm|llms|agent|agents|gpt|claude|gemini|mcp|diffusion|model|rag|voice|tts|video|image)\b", re.I)


def tok():
    import sys as _s; _s.path.insert(0, str(Path(__file__).resolve().parent.parent)); from lib.secrets import gh_token
    t = gh_token() or ""
    return t or None


def get(url, gh=False):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "reels-studio-radar"}
    if gh and tok():
        h["Authorization"] = f"Bearer {tok()}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
        return json.load(r)


def flags(*texts):
    blob = " ".join(t or "" for t in texts).lower()
    return [name for name, rx in RISK.items() if re.search(rx, blob)]


def non_english(text):
    return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", text or ""))


def github(days):
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    q = f"llm OR ai OR agent OR diffusion OR mcp OR tts created:>{since} stars:>150"  # GitHub allows max 5 OR operators
    d = get("https://api.github.com/search/repositories?" + urllib.parse.urlencode({"q": q, "sort": "stars", "order": "desc", "per_page": 50}), gh=True)
    out = []
    for r in d.get("items", []):
        age = max(1, (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))).days)
        desc = r.get("description") or ""
        out.append({"name": r["full_name"], "url": r["html_url"], "stars": r["stargazers_count"], "per_day": r["stargazers_count"] / age,
                    "license": (r.get("license") or {}).get("spdx_id") or "none", "desc": desc, "topics": r.get("topics", []),
                    "flags": flags(r["full_name"], desc, " ".join(r.get("topics", []))), "zh": non_english(desc)})
    return sorted(out, key=lambda x: -x["per_day"])


def hf(kind):
    d = get(f"https://huggingface.co/api/{kind}?sort=trendingScore&direction=-1&limit=25")
    return [{"name": m["id"], "url": f"https://huggingface.co/{'spaces/' if kind == 'spaces' else ''}{m['id']}", "score": m.get("trendingScore", 0),
             "likes": m.get("likes", 0), "tag": m.get("pipeline_tag") or m.get("sdk") or "", "flags": flags(m["id"], " ".join(m.get("tags", [])[:20]))}
            for m in d]


def parse_gittrend_snapshot(html, limit=25):
    """Parse the visible Today ranking and preserve the site's own date, not fetch time."""
    clean = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    match = re.search(r"Ranked by star velocity\s*[·-]\s*([A-Za-z]+\s+\d{1,2},\s*\d{4})", clean)
    try:
        date = dt.datetime.strptime(match.group(1), "%B %d, %Y").date().isoformat() if match else None
    except ValueError:
        date = None
    out, seen = [], set()
    for m in re.finditer(r'href="(?:https://gittrend\.io)?/repo/([^"/?#]+/[^"/?#]+)"', html):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        out.append({"name": name, "url": f"https://github.com/{name}", "source": "GitTrend", "rank": len(out) + 1})
        if len(out) >= limit:
            break
    return {"date": date, "items": out}


def gittrend_snapshot(limit=25):
    """Get the public Today page; a missing date or fetch failure must remain visible."""
    try:
        req = urllib.request.Request("https://gittrend.io/", headers={"User-Agent": "reels-studio-radar"})
        with urllib.request.urlopen(req, timeout=40) as r:
            return parse_gittrend_snapshot(r.read().decode("utf-8", "replace"), limit)
    except Exception:
        return {"date": None, "items": []}


def gittrend(limit=25):
    return gittrend_snapshot(limit)["items"]


def reference_posts(days=7, limit=30):
    """Recent posts from the source registry (research/sources.csv, history in research/sources/posts.csv):
    TikTok, YouTube (Shorts/long-form), RSS and web sources. Run `tools/sources.py scan` first."""
    import csv
    path = ROOT / "research/sources/posts.csv"
    if not path.exists():
        return []
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    out = []
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            pub = (r.get("published") or "")[:10]
            seen = (r.get("last_seen") or "")[:10]
            if max(pub, seen) < cutoff:
                continue
            try:
                views = int(float(r.get("views") or 0))
            except ValueError:
                views = 0
            out.append({"platform": r.get("platform", ""), "source": r.get("source", ""), "title": (r.get("title") or "")[:90],
                        "url": r.get("url", ""), "views": views, "published": pub})
    return sorted(out, key=lambda x: (-x["views"], x["published"]), reverse=False)[:limit]


def angle(item):
    """A prompt for the human editor, not a format. Picking the angle is a judgment call."""
    d = (item.get("desc") or "").strip()
    return f"Editor to decide: what can a viewer see this do on screen? ({d[:60]})" if d else "Editor to decide"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--brief", action="store_true")
    a = ap.parse_args()
    today = dt.date.today().isoformat()
    gh = github(a.days)
    # Owner rule: the radar never re-surfaces a tool we already covered. One registry, tools/topics_covered.py.
    sys.path.insert(0, str(ROOT / "tools"))
    import topics_covered
    solved = topics_covered.rebuild()
    before = len(gh)
    covered_hits = [r["name"] for r in gh if topics_covered.is_covered(r["name"], solved)]
    gh = [r for r in gh if not topics_covered.is_covered(r["name"], solved)]
    if covered_hits:
        print(f"radar: {before - len(gh)} repo(s) already covered, ignored: " + ", ".join(covered_hits[:8]))
    models, spaces = hf("models"), hf("spaces")
    trending = gittrend()
    refs = reference_posts()
    L = [f"# Trend radar: {today} (last {a.days} days)", "",
         "Sources: GitHub search API (new repos, ranked by stars/day), Hugging Face trending models and Spaces, GitTrend trending today (https://gittrend.io/).",
         "⚠ = risk flag. Never promote flagged items. ZH = description not in English (translate and verify before covering).", "",
         "## New AI repos on GitHub", "", "| # | Repo | ★ | ★/day | Licence | What it is | Flags | Video angle |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(gh[:20], 1):
        fl = ("⚠ " + ", ".join(r["flags"])) if r["flags"] else ("ZH" if r["zh"] else "")
        L.append(f"| {i} | [{r['name']}]({r['url']}) | {r['stars']:,} | {r['per_day']:.0f} | {r['license']} | {r['desc'][:90].replace('|', '/')} | {fl} | {'-' if r['flags'] else angle(r)} |")
    L += ["", "## Reference channels (research/sources.csv, last 7 days, by views)", ""]
    L += ["| Platform | Source | Post | Views | Published |", "|---|---|---|---|---|"]
    L += [f"| {x['platform']} | {x['source']} | [{x['title'] or x['url']}]({x['url']}) | {x['views']:,} | {x['published']} |" for x in refs] or ["- (no recent posts; run tools/sources.py scan)"]
    L += ["", "## GitTrend: trending repos today (star velocity)", ""]
    L += [f"- [{t['name']}]({t['url']})" for t in trending] or ["- (GitTrend unavailable today)"]
    for title, items in (("Trending models on Hugging Face", models), ("Trending Spaces (free apps to try)", spaces)):
        L += ["", f"## {title}", "", "| # | Item | Trend score | Likes | Type | Flags |", "|---|---|---|---|---|---|"]
        for i, m in enumerate(items[:12], 1):
            L.append(f"| {i} | [{m['name']}]({m['url']}) | {m['score']} | {m['likes']} | {m['tag']} | {('⚠ ' + ', '.join(m['flags'])) if m['flags'] else ''} |")
    safe = [r for r in gh if not r["flags"] and not r["zh"] and AI.search(r["desc"])]
    flagged = sum(1 for r in gh if r["flags"]) + sum(1 for m in models + spaces if m["flags"])
    L += ["", f"**Summary:** {len(gh)} new repos, {len(safe)} safe English candidates, {flagged} items flagged as risky across all sources."]
    out = ROOT / "research" / "radar" / f"radar-{today}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"radar -> {out.relative_to(ROOT.parent)}  ({len(safe)} safe candidates, {flagged} flagged)")
    if a.brief and len(safe) >= 3:
        top = sorted(safe[:5], key=lambda r: r["stars"])  # countdown: smallest first
        items = [{"rank": len(top) - k, "name": r["name"].split("/")[1][:22], "line": re.sub(r"\s+", " ", r["desc"]).strip()[:90],
                  "value": r["stars"], "tag": f"{r['license']} · {r['per_day']:.0f}★/day", "mono": r["name"].split("/")[1][:2].upper()} for k, r in enumerate(top)]
        brief = {"id": f"trending-repos-{today}", "draft": True,
                 "needs_review": ["write the hook, sub and CTA yourself from what you verified by running each tool (no formula copy)",
                                  "rewrite each 'line' as a spoken sentence you verified by running the tool",
                                  "check the licence and that the repo does what it claims", "add a real takeaway in the CTA"],
                 "title": f"{len(top)} AI repos blowing up on GitHub this week", "lang": "en-us", "voice": "af_heart", "speed": 1.05, "style": "midnight",
                 "brand": {"handle": "@yourhandle", "name": "Your Channel", "tagline": "Trending AI tools, tested"},
                 "content": {"kicker": "", "hook": "TODO: write the viewer-problem hook", "hook_display": "TODO",
                             "sub": "TODO",
                             "metric_label": "GitHub stars", "metric_icon": "⭐", "items": items,
                             "cta": "TODO: one concrete next step for the viewer"},
                 "sources": [f"GitHub API, fetched {today}: " + ", ".join(f"{r['name']} {r['stars']}★" for r in top)]}
        bp = ROOT / "briefs" / f"draft-trending-repos-{today}.json"
        bp.write_text(json.dumps(brief, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"draft brief -> {bp.relative_to(ROOT.parent)} (review the 'needs_review' list before rendering)")


if __name__ == "__main__":
    main()
