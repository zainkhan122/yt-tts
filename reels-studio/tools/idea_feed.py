#!/usr/bin/env python3
"""
Idea feed: "don't reinvent the wheel". Scan the watchlist channels' latest posts, extract the tools/repos they
cover, and rank topics by CONSENSUS (how many channels covered it), recency and views. Topics covered by
>= 2 channels in the window are confirmed niche trends; we cover them (with our own research + angle) to stay
in search and relevance.

  python3 tools/idea_feed.py --days 7 --per-channel 12          # -> research/ideas/feed-<date>.md + backlog rows
Cheap: one listing request per channel (titles, captions, stats). No downloads.
"""
import argparse
import csv
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = set("""this these that the a an and or for with your you our new free open source github repo repos tool tools ai app apps
here how why what when stop best top just now meet introducing it its it's is are was get use using try
claude code chatgpt gpt gemini cursor codex openai google meta llm agent agents skill skills mcp model models
video videos image images api apis day week today 2026 part follow comment link bio save share
youtube tiktok instagram facebook twitter reddit discord linkedin javascript typescript python rust golang java linux windows
macos mac iphone android apple microsoft nvidia amazon aws chrome browser software developer developers coding programming
webdev pcgaming gaming opensource aitools aiagents claudecode machinelearning tech technology tutorial productivity
china india usa europe japan korea pakistan america gpu gpus cpu ram laptop phone startup startups business ceo""".split())
CAMEL = re.compile(r"\b([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+"            # MeshAvatarStudio, GoLive
                   r"|[A-Z][a-z0-9]+(?:[-.][A-Z0-9][A-Za-z0-9]*)+"     # Qwen3-VL, Open-Sora (filtered unless digit/CAPS)
                   r"|[A-Z]{2,}[-.]?\d[\w.]*(?:\s[A-Z][a-z]+)?"        # GPT-6 Astra, SD3.5, GLM-5.2
                   r"|[A-Z]{2,}[a-z]+[A-Za-z]*)\b")                  # ComfyUI-like
LEAD = re.compile(r"^\W*(?:meet |introducing |this is |it's called )?([A-Z][\w.+-]{2,}(?:\s[A-Z][\w.+-]{2,})?)\s*(?::|is|lets|turns|transforms|just|can|helps|makes|—|-)\s", re.I)


def topics(text):
    found = {}
    text = re.sub(r"#\w+", " ", text)  # hashtags are categories (#AIAgents), not products
    for m in re.finditer(r"github\.com/([\w.-]+)/([\w.-]+)", text):
        found[m.group(2).lower().rstrip(".")] = f"{m.group(1)}/{m.group(2).rstrip('.')}"
    m = LEAD.match(text)
    if m and m.group(1).lower().split()[0] not in STOP:
        found.setdefault(m.group(1).lower(), m.group(1))
    for m in CAMEL.finditer(text):
        w = m.group(1)
        if "-" in w and not re.search(r"\d|[A-Z]{2,}", w):  # "Self-Educated", "Real-Time" = words; keep "GPT-6", "Qwen3-VL"
            continue
        if w.lower() not in STOP and len(w) > 3:
            found.setdefault(w.lower(), w)
    return found  # key -> display (or owner/repo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--per-channel", type=int, default=12)
    a = ap.parse_args()
    since = time.time() - a.days * 86400
    sys.path.insert(0, str(ROOT / "tools"))
    import sources  # registry + persistence: every scan is also saved to research/sources/posts.csv
    got = sources.scan_all(latest=a.per_channel)
    reg = {s["handle"]: s for s in sources.load()}
    agg = {}
    for handle, posts in got.items():
        typ = reg.get(handle, {}).get("type", "web")
        label = f"{ {'tiktok': 'tt', 'youtube': 'yt', 'rss': 'web'}.get(typ, typ) }:{handle}"
        for e in posts:
            ts = e.get("timestamp") or 0
            if ts and ts < since:
                continue
            text = " ".join(x for x in (e.get("title"), e.get("description")) if x)
            for key, disp in topics(text).items():
                tp = agg.setdefault(key, {"name": disp, "channels": set(), "views": 0, "best": None, "first": ts or time.time()})
                tp["channels"].add(label)
                tp["views"] += e.get("views") or 0
                if "/" in disp:
                    tp["name"] = disp
                if not tp["best"] or (e.get("views") or 0) > tp["best"][0]:
                    tp["best"] = ((e.get("views") or 0), e.get("url"))
                tp["first"] = min(tp["first"], ts or tp["first"])
    chans = list(got)
    ranked = sorted(agg.values(), key=lambda t: (-len(t["channels"]), -t["views"]))
    today = dt.date.today().isoformat()
    L = [f"# Idea feed: {today} (last {a.days} days, {len(chans)} watchlist channels)", "",
         "**Consensus** = number of watchlist channels that posted about it. ≥ 2 = confirmed niche trend: cover it with our own research and angle.",
         "Topics are auto-extracted, so verify each before scoring (rubric: PIPELINE.md §2).", "",
         "| # | Topic | Consensus | Channels | Views (sum) | Best video | Repo |", "|---|---|---|---|---|---|---|"]
    for i, t in enumerate(ranked[:40], 1):
        repo = t["name"] if "/" in t["name"] else ""
        L.append(f"| {i} | **{t['name'].split('/')[-1]}** | {len(t['channels'])} | {', '.join(sorted(t['channels']))} | {t['views']:,} | "
                 f"[{t['best'][0]:,} views]({t['best'][1]}) | {('github.com/' + repo) if repo else ''} |")
    out = ROOT / "research/ideas" / f"feed-{today}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    # consensus topics -> backlog (status idea), deduped by topic key
    bl = ROOT / "topics/backlog.csv"
    have = bl.read_text().lower() if bl.exists() else ""
    added = 0
    with bl.open("a", newline="") as f:
        w = csv.writer(f)
        for t in ranked:
            key = t["name"].split("/")[-1]
            generic = key.lower() in STOP
            if len(t["channels"]) >= 2 and key.lower() not in have and not generic:
                w.writerow([today, key, "from idea feed", ("https://github.com/" + t["name"]) if "/" in t["name"] else t["best"][1],
                            f"{len(t['channels'])} watchlist channels, {t['views']:,} views", "", "", ";".join(sorted(t["channels"])), "", "", "", "idea", "", "auto: verify + score"])
                added += 1
    print(f"-> {out.relative_to(ROOT)} ({len(ranked)} topics; {sum(1 for t in ranked if len(t['channels']) >= 2)} with consensus ≥ 2; {added} added to backlog)")


if __name__ == "__main__":
    main()
