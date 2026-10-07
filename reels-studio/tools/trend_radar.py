#!/usr/bin/env python3
"""
Trend radar for the AI-tools niche: what is new and rising, from free public APIs (no scraping):
  * GitHub search API  - new AI repos (created in the last N days) ranked by stars/day
  * Hugging Face API   - trending models and trending Spaces (free "try it" apps)
Every item gets RISK FLAGS (uncensored/NSFW, ToS bypass, "free API key" abuse, bot evasion, crack/leak).
Flagged items are never put into briefs: promoting them can cost the channel (and its viewers).

  python3 tools/trend_radar.py --days 14            # writes research/radar/radar-YYYY-MM-DD.md
  python3 tools/trend_radar.py --days 14 --brief    # + briefs/draft-trending-repos-YYYY-MM-DD.json (ranked-list)
Uses GH_TOKEN or /var/tmp/gh/token if present (higher rate limit); works without.
"""
import argparse
import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RISK = {
    "nsfw/uncensored": r"uncensor|nsfw|nude|porn|hentai|abliterat",
    "ToS bypass / free-key abuse": r"no api key|without (an? )?api key|free (unlimited )?(gpt|claude|api)|reverse[- ]?proxy|api[- ]?key (leak|free)|keygen|crack|jailbreak|bypass",
    "bot / detection evasion": r"undetect|anti[- ]?bot|captcha|stealth|evad",
    "scraping personal data": r"scrape (instagram|linkedin|tiktok|facebook)|osint|doxx",
}
AI = re.compile(r"\b(ai|llm|llms|agent|agents|gpt|claude|gemini|mcp|diffusion|model|rag|voice|tts|video|image)\b", re.I)


def tok():
    t = os.environ.get("GH_TOKEN") or (Path("/var/tmp/gh/token").read_text().strip() if Path("/var/tmp/gh/token").exists() else "")
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


def angle(item):
    d = (item.get("desc") or "").lower()
    if "mcp" in d or "claude code" in d or "plugin" in d:
        return "tool-spotlight: 'Claude/Cursor just got a superpower' + 3-step setup"
    if any(k in d for k in ("video", "image", "voice", "tts", "music")):
        return "tool-spotlight with a real before/after you generate yourself"
    if "agent" in d:
        return "ranked-list: 'AI agents you can run free this week'"
    return "ranked-list entry (trending repos of the week)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--brief", action="store_true")
    a = ap.parse_args()
    today = dt.date.today().isoformat()
    gh = github(a.days)
    models, spaces = hf("models"), hf("spaces")
    L = [f"# Trend radar: {today} (last {a.days} days)", "",
         "Sources: GitHub search API (new repos, ranked by stars/day), Hugging Face trending models and Spaces.",
         "⚠ = risk flag. Never promote flagged items. ZH = description not in English (translate and verify before covering).", "",
         "## New AI repos on GitHub", "", "| # | Repo | ★ | ★/day | Licence | What it is | Flags | Video angle |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(gh[:20], 1):
        fl = ("⚠ " + ", ".join(r["flags"])) if r["flags"] else ("ZH" if r["zh"] else "")
        L.append(f"| {i} | [{r['name']}]({r['url']}) | {r['stars']:,} | {r['per_day']:.0f} | {r['license']} | {r['desc'][:90].replace('|', '/')} | {fl} | {'-' if r['flags'] else angle(r)} |")
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
        brief = {"id": f"trending-repos-{today}", "template": "ranked-list", "draft": True,
                 "needs_review": ["rewrite each 'line' as a spoken sentence you verified by running the tool",
                                  "check the licence and that the repo does what it claims", "add a real takeaway in the CTA"],
                 "title": f"{len(top)} AI repos blowing up on GitHub this week", "lang": "en-us", "voice": "af_heart", "speed": 1.05, "style": "midnight",
                 "brand": {"handle": "@yourhandle", "name": "Your Channel", "tagline": "Trending AI tools, tested"},
                 "content": {"kicker": "📈 TRENDING ON GITHUB", "hook": f"These {len(top)} AI repos exploded on GitHub this week.",
                             "hook_display": f"{len(top)} AI repos exploding this week", "sub": "ranked by GitHub stars",
                             "metric_label": "GitHub stars", "metric_icon": "⭐", "items": items,
                             "cta": "Which one should I test next? Comment below and follow for the weekly list."},
                 "sources": [f"GitHub API, fetched {today}: " + ", ".join(f"{r['name']} {r['stars']}★" for r in top)]}
        bp = ROOT / "briefs" / f"draft-trending-repos-{today}.json"
        bp.write_text(json.dumps(brief, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"draft brief -> {bp.relative_to(ROOT.parent)} (review the 'needs_review' list before rendering)")


if __name__ == "__main__":
    main()
