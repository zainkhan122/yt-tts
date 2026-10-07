#!/usr/bin/env python3
"""
Channel study: deep analysis of competitor accounts (TikTok / YouTube Shorts), 20-30 videos each.
Answers: which hooks work, how the tool's value is told, what keeps people watching (pace, cuts, on-screen text),
and what makes them comment, share and save.

  python3 tools/channel_study.py meta --latest 30 dr_cintas github.signals ...   # stats for all videos (1 request/account)
  python3 tools/channel_study.py visual --top 3 --bottom 1                       # cuts/10s, on-screen hook text (OCR), frame strips
  python3 tools/channel_study.py transcribe --per-account 22 --model base.en      # spoken scripts (audio only, deleted after)
  python3 tools/channel_study.py report                                          # per-account + top-vs-bottom findings

Accounts: TikTok handles (no @) or full URLs (YouTube: https://www.youtube.com/@x/shorts).
Raw data (full transcripts, frames) -> research/social/raw/ (workspace-only, git-ignored; the repo is public).
Committed: research/social/videos-<date>.csv (metrics, <=20-word hook excerpts, types) + study-<date>.md.
"""
import argparse
import concurrent.futures as cf
import csv
import datetime as dt
import json
import re
import shutil
import statistics as st
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import social_scan as ss  # noqa: E402  (fetch / transcribe / analyse / CTA rules)

RAW = ROOT / "research/social/raw"
META, VIDS, FRAMES = RAW / "meta", RAW / "videos", RAW / "frames"
TMP = Path("/var/tmp/social")
TODAY = dt.date.today().isoformat()

HOOKS = [  # first match wins; order = specificity
    ("list/countdown", r"^\W*(\d+|two|three|four|five|six|seven|eight|nine|ten|top)\b.{0,40}\b(tools?|repos?|ways|apps|sites|websites|prompts|projects|extensions|skills|agents|things|features)\b"),
    ("gold-mine/superlative", r"gold ?mine|insane|crazy|underrated|game.?changer|nobody (is )?talking|secret|hidden gem|mind.?blow|best .{0,20} (ever|i've)"),
    ("stop/problem", r"^\W*(stop|if you|you need|don't|never|tired of|struggl|still paying|you're (still )?(using|paying))"),
    ("question", r"^\W*(what|why|how|did you|have you|ever|do you|can you|is this)\b.*\?|\?\s*$"),
    ("news/just-dropped", r"\bjust (dropped|released|launched|open.?sourced)|\bannounced\b|\bnew\b.{0,30}\b(model|tool|repo|release|version)"),
    ("transformation", r"\b(turns?|transforms?|converts?|makes?) .{0,60}\binto\b|\blets you\b|\bwithout (needing|any|a)\b"),
    ("named-tool-first", r"^\W*[A-Z][\w.-]+(\s[A-Z][\w.-]+)? (is|lets|can|helps|turns|transforms|just)\b"),
    ("this-repo/this-tool", r"^\W*(this|these) (github |free |open.?source |new )?(repo|tool|project|app|website|extension|ai)"),
    ("how-to", r"^\W*(here'?s how|how to|watch (me|this))"),
]


def hook_type(text):
    t = (text or "").strip()
    for name, rx in HOOKS:
        if re.search(rx, t, re.I):
            return name
    return "other"


def handle_of(acc):
    m = re.search(r"@([\w.]+)", acc)
    return m.group(1) if m else acc.strip("@")


def url_of(acc):
    return acc if acc.startswith("http") else f"https://www.tiktok.com/@{acc.strip('@')}"


def load_meta():
    out = {}
    for f in sorted(META.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        es = [e for e in d.get("entries") or [] if e.get("view_count") is not None]
        out[f.stem] = sorted(es, key=lambda e: -(e.get("timestamp") or 0))
    return out


# ------------------------------------------------------------------ stages
def cmd_meta(a):
    META.mkdir(parents=True, exist_ok=True)
    for acc in a.accounts:
        h = handle_of(acc)
        p = subprocess.run(["yt-dlp", "--flat-playlist", "--playlist-end", str(a.latest), "-J", "--no-warnings", url_of(acc)],
                           capture_output=True, text=True, timeout=300)
        if p.returncode or not p.stdout.strip():
            print(f"  ✗ {h}: {(p.stderr or 'no data').strip()[-160:]}")
            continue
        (META / f"{h}.json").write_text(p.stdout)
        print(f"  ✓ {h}: {len(json.loads(p.stdout).get('entries') or [])} videos")


def cmd_transcribe(a):
    VIDS.mkdir(parents=True, exist_ok=True)
    per = {}
    for h, es in load_meta().items():
        if a.only and h not in a.only:
            continue
        # most informative first: top performers + bottom quartile (the contrast), then the rest by recency
        by_views = sorted(es, key=lambda e: -e["view_count"])
        q = max(1, a.per_account // 4)
        order = by_views[:a.per_account - q] + by_views[-q:]
        order += [e for e in es if e not in order]
        per[h] = [(h, e, VIDS / f"{h}-{e['id']}.json") for e in order[:a.per_account]]
    jobs = []  # ROUND-ROBIN across accounts: a partial run still covers every account's top videos
    for i in range(a.per_account):
        for h in per:
            if i < len(per[h]) and not per[h][i][2].exists():
                jobs.append(per[h][i])
    print(f"{len(jobs)} videos to transcribe with {a.model} (audio prefetch x3)")

    def dl(job):
        h, e, out = job
        try:
            return job, ss.fetch(e.get("url") or e.get("webpage_url"), None), None
        except Exception as ex:  # photo posts / removed videos
            return job, None, str(ex)[:160]
    done = 0
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        for job, got, err in pool.map(dl, jobs):  # map keeps order; downloads run ahead of whisper
            h, e, out = job
            if err or not got:
                out.write_text(json.dumps({"id": e["id"], "account": h, "error": err or "no audio"}))
                continue
            wav, info = got
            try:
                model = "base" if h in (a.multilingual or []) else a.model  # Hindi/Urdu creators -> multilingual model
                segs, lang = ss.transcribe(wav, "auto" if model == "base" else "en", model)
            except Exception as ex:
                segs, lang = [], f"error: {str(ex)[:80]}"
            wav.unlink(missing_ok=True)
            m = ss.analyse(info, segs)
            out.write_text(json.dumps({"id": e["id"], "account": h, "url": e.get("url"), "metrics": m, "transcript": segs,
                                       "language": lang, "model": "base" if h in (a.multilingual or []) else a.model}, ensure_ascii=False))
            done += 1
            if done % 10 == 0:
                print(f"  {done}/{len(jobs)} transcribed", flush=True)
    print(f"transcribed {done}/{len(jobs)}")


def cuts_per_10s(mp4, dur):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4), "-vf", "select='gt(scene,0.30)',metadata=print", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=300)
    n = len(re.findall(r"pts_time", p.stderr))
    return round(n / max(dur, 1) * 10, 1), n


def ocr(img):
    if not shutil.which("tesseract"):
        return ""
    p = subprocess.run(["tesseract", str(img), "-", "--psm", "11"], capture_output=True, text=True, timeout=60)
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9'’.+-]{1,}", p.stdout) if len(w) > 1]
    return " ".join(words[:25])


def cmd_visual(a):
    FRAMES.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for h, es in load_meta().items():
        if a.only and h not in a.only:
            continue
        ranked = sorted(es, key=lambda e: -e["view_count"])
        pick = ranked[:a.top] + (ranked[-a.bottom:] if a.bottom else [])
        for e in pick:
            out = FRAMES / f"{h}-{e['id']}.json"
            if out.exists():
                continue
            mp4 = TMP / f"v-{e['id']}.mp4"
            p = subprocess.run(["yt-dlp", "-q", "--no-warnings", "-f", "worst[vcodec!=none]/worst", "-o", str(mp4), e["url"]],
                               capture_output=True, text=True, timeout=240)
            if p.returncode or not mp4.exists():
                out.write_text(json.dumps({"id": e["id"], "error": (p.stderr or "download failed")[-160:]}))
                continue
            dur = e.get("duration") or 30
            cps, n = cuts_per_10s(mp4, dur)
            times = [0.3, 1.0, 2.0, 3.5, dur * 0.25, dur * 0.5, dur * 0.75, max(dur - 1.5, 4)]
            frames = []
            for i, t in enumerate(times):
                f = TMP / f"f-{e['id']}-{i}.jpg"
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf", "scale=360:-2", str(f)])
                if f.exists():
                    frames.append(f)
            hook_txt = " | ".join(x for x in (ocr(frames[0]) if frames else "", ocr(frames[1]) if len(frames) > 1 else "") if x)
            strip = FRAMES / f"{h}-{e['id']}.jpg"
            if frames:
                subprocess.run(["ffmpeg", "-y", "-v", "error", *sum([["-i", str(f)] for f in frames], []), "-filter_complex",
                                f"{''.join(f'[{i}:v]' for i in range(len(frames)))}hstack=inputs={len(frames)},scale=1600:-2", str(strip)])
            out.write_text(json.dumps({"id": e["id"], "account": h, "views": e["view_count"], "duration": dur, "cuts": n,
                                       "cuts_per_10s": cps, "onscreen_hook": hook_txt, "strip": strip.name}, ensure_ascii=False))
            for f in frames:
                f.unlink(missing_ok=True)
            mp4.unlink(missing_ok=True)
            print(f"  {h:15s} {e['view_count']:>9,} views · {cps:>4} cuts/10s · text: {hook_txt[:70]}", flush=True)


def topic_names(text, desc):
    names = set(re.findall(r"github\.com/([\w.-]+/[\w.-]+)", (desc or "") + " " + (text or "")))
    for m in re.finditer(r"\b(?:called|named|meet|introducing|it's|try|use|install)\s+([A-Z][\w.+-]{2,}(?:\s[A-Z][\w.+-]{2,})?)", text or ""):
        names.add(m.group(1).strip(" .,"))
    return sorted(names)[:6]


def cmd_report(a):
    meta = load_meta()
    rows = []
    for h, es in meta.items():
        views = sorted(e["view_count"] for e in es)
        q75 = views[int(len(views) * 0.75)] if views else 0
        q25 = views[int(len(views) * 0.25)] if views else 0
        for e in es:
            v = max(e["view_count"], 1)
            tj = VIDS / f"{h}-{e['id']}.json"
            fj = FRAMES / f"{h}-{e['id']}.json"
            t = json.loads(tj.read_text()) if tj.exists() else {}
            fr = json.loads(fj.read_text()) if fj.exists() else {}
            m = t.get("metrics") or {}
            text = " ".join(s["text"] for s in t.get("transcript") or [])
            desc = e.get("description") or e.get("title") or ""
            first = m.get("first_sentence") or ""
            rows.append({
                "account": h, "id": e["id"], "url": e.get("url"), "date": dt.datetime.fromtimestamp(e.get("timestamp") or 0).date().isoformat(),
                "views": e["view_count"], "tier": "top25" if e["view_count"] >= q75 else ("bottom25" if e["view_count"] <= q25 else "mid"),
                "likes_1k": round((e.get("like_count") or 0) / v * 1000, 1), "comments_1k": round((e.get("comment_count") or 0) / v * 1000, 2),
                "shares_1k": round((e.get("repost_count") or 0) / v * 1000, 1), "saves_1k": round((e.get("save_count") or 0) / v * 1000, 1),
                "duration": e.get("duration"), "wpm": m.get("wpm"), "words": m.get("words"),
                "hook_type": hook_type(first) if first else "", "hook_excerpt": ss.excerpt(first, 20) if first else "",
                "cta_spoken": "|".join(k for k, rx in ss.CTA.items() if re.search(rx, " ".join(s["text"] for s in (t.get("transcript") or []) if s["end"] > ((t.get("transcript") or [{"end": 0}])[-1]["end"] - 8)), re.I)),  # recomputed with current rules
                "cta_caption": "|".join(k for k, rx in ss.CTA.items() if re.search(rx, desc, re.I)),
                "hashtags": len(re.findall(r"#\w+", desc)), "caption_len": len(desc), "github_link_in_caption": "github.com" in desc.lower(),
                "music": "original" if re.search(r"original sound|son original|sonido original", (e.get("track") or "original sound"), re.I) else (e.get("track") or "")[:40],
                "cuts_per_10s": fr.get("cuts_per_10s"), "onscreen_hook": (fr.get("onscreen_hook") or "")[:120],
                "topics": "|".join(topic_names(text, desc)), "transcribed": bool(text),
            })
    out_csv = ROOT / f"research/social/videos-{TODAY}.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def med(xs):
        xs = [x for x in xs if isinstance(x, (int, float))]
        return st.median(xs) if xs else None

    def share(xs, cond):
        xs = list(xs)
        return round(100 * sum(1 for x in xs if cond(x)) / len(xs)) if xs else 0
    L = [f"# Channel study: {TODAY}", "", f"{len(rows)} videos from {len(meta)} accounts. "
         f"Transcribed: {sum(r['transcribed'] for r in rows)}. Visual sample: {sum(1 for r in rows if r['cuts_per_10s'] is not None)}.", "",
         "## Per account (medians)", "", "| Account | n | Views | Likes/1k | Comments/1k | Shares/1k | Saves/1k | Length | wpm | Cuts/10s | Top hook types | Spoken CTA |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for h in meta:
        R = [r for r in rows if r["account"] == h]
        hooks = {}
        for r in R:
            if r["hook_type"]:
                hooks[r["hook_type"]] = hooks.get(r["hook_type"], 0) + 1
        top_hooks = ", ".join(f"{k} {v}" for k, v in sorted(hooks.items(), key=lambda x: -x[1])[:3])
        L.append(f"| @{h} | {len(R)} | {med(r['views'] for r in R):,.0f} | {med(r['likes_1k'] for r in R)} | {med(r['comments_1k'] for r in R)} | "
                 f"{med(r['shares_1k'] for r in R)} | {med(r['saves_1k'] for r in R)} | {med(r['duration'] for r in R)} s | {med(r['wpm'] for r in R) or '–'} | "
                 f"{med(r['cuts_per_10s'] for r in R) or '–'} | {top_hooks or '–'} | {share((r for r in R if r['transcribed']), lambda r: bool(r['cta_spoken']))}% |")
    T = [r for r in rows if r["tier"] == "top25"]
    B = [r for r in rows if r["tier"] == "bottom25"]
    L += ["", "## Top-25% vs bottom-25% videos (each account's own quartiles, pooled)", "", "| Signal | Top 25% | Bottom 25% |", "|---|---|---|"]
    for label, f in [("median length (s)", lambda R: med(r["duration"] for r in R)), ("median wpm", lambda R: med(r["wpm"] for r in R)),
                     ("saves/1k", lambda R: med(r["saves_1k"] for r in R)), ("shares/1k", lambda R: med(r["shares_1k"] for r in R)),
                     ("comments/1k", lambda R: med(r["comments_1k"] for r in R)), ("cuts/10s (visual sample)", lambda R: med(r["cuts_per_10s"] for r in R)),
                     ("spoken CTA %", lambda R: share((r for r in R if r["transcribed"]), lambda r: bool(r["cta_spoken"]))),
                     ("GitHub link in caption %", lambda R: share(R, lambda r: r["github_link_in_caption"])),
                     ("median hashtags", lambda R: med(r["hashtags"] for r in R))]:
        L.append(f"| {label} | {f(T)} | {f(B)} |")
    L += ["", "| Hook type | share of top-25% | share of bottom-25% |", "|---|---|---|"]
    types = sorted({r["hook_type"] for r in rows if r["hook_type"]})
    tt = [r for r in T if r["hook_type"]]
    bb = [r for r in B if r["hook_type"]]
    for ty in types:
        L.append(f"| {ty} | {share(tt, lambda r: r['hook_type'] == ty)}% | {share(bb, lambda r: r['hook_type'] == ty)}% |")
    L += ["", "## Top 3 videos per account", ""]
    for h in meta:
        R = sorted([r for r in rows if r["account"] == h], key=lambda r: -r["views"])[:3]
        for r in R:
            L.append(f"- **@{h}** {r['views']:,} views · {r['duration']} s · saves/1k {r['saves_1k']} · hook *{r['hook_type'] or '?'}*: "
                     f"\"{r['hook_excerpt'] or r['onscreen_hook'][:80]}\"")
    (ROOT / f"research/social/study-{TODAY}.md").write_text("\n".join(L) + "\n")
    print(f"-> research/social/videos-{TODAY}.csv ({len(rows)} rows) + study-{TODAY}.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("meta"); p.add_argument("accounts", nargs="+"); p.add_argument("--latest", type=int, default=30)
    p = sub.add_parser("transcribe"); p.add_argument("--per-account", type=int, default=22); p.add_argument("--model", default="base.en"); p.add_argument("--only", nargs="*"); p.add_argument("--multilingual", nargs="*", default=[])
    p = sub.add_parser("visual"); p.add_argument("--top", type=int, default=3); p.add_argument("--bottom", type=int, default=1); p.add_argument("--only", nargs="*")
    sub.add_parser("report")
    a = ap.parse_args()
    {"meta": cmd_meta, "transcribe": cmd_transcribe, "visual": cmd_visual, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
