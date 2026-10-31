#!/usr/bin/env python3
"""
Social scan: learn from TikTok / YouTube Shorts / Instagram explainer videos.
Pulls each video's SPOKEN SCRIPT (whisper.cpp), timing and stats, then measures what top videos do:
hook (first 3 s), words per minute, structure, CTA type, and comments per 1k views.

  python3 tools/social_scan.py --account https://www.tiktok.com/@sabrina_ramonov --latest 12 --top 3
  python3 tools/social_scan.py --account https://www.youtube.com/@mreflow/shorts --latest 10 --top 3
  python3 tools/social_scan.py --url https://www.tiktok.com/@user/video/123 --url https://youtube.com/shorts/abc
  python3 tools/social_scan.py --url <instagram reel> --cookies /var/tmp/ig-cookies.txt   # IG usually needs a login

Research-only by design (the repo is public):
  * only AUDIO is downloaded, transcribed, then deleted. Videos are never stored or reused
  * full transcripts stay workspace-only in research/social/raw/ (git-ignored)
  * git gets the digest: metrics, a <=20-word hook excerpt, and our lessons (commentary/analysis)
Access (tested 2026-10-07 from this sandbox): TikTok ✅ without login, YouTube Shorts ✅, Instagram ❌ needs cookies.
"""
import argparse
import csv
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib import pipeline  # noqa: E402

TMP = Path("/var/tmp/social")
RAW = ROOT / "research/social/raw"
OUT = ROOT / "research/social"
WHISPER = pipeline.HF_CACHE / "whisper/whisper.cpp/build/bin/whisper-cli"
MODELS = pipeline.HF_CACHE / "whisper/models"
CTA = {
    "comment-keyword": r"\bcomment\b[^.?!]{0,40}\b(word|keyword|below|[\"'“][A-Za-z]+[\"'”]|[A-Z]{3,})",
    "comment": r"\b(comment|let me know|tell me|drop (a|your))\b",
    "follow": r"\b(follow|subscribe)\b",
    "save/share": r"\b(save this|share this|send this|bookmark)\b",
    "link": r"\b(link in (my )?bio|link below|in the description|pinned comments?|link.{0,40}\b(comments?|description|desc|bio)\b)",
    "dm": r"\b(dm me|send me a message|message me)\b",
}
STRUCT = {
    "list/countdown": r"\b(number (one|two|three|four|five)|first(ly)?|second(ly)?|third|top \d+|\d+ (tools|apps|repos|sites|ways|prompts|things))\b",
    "tutorial": r"\b(step|here's how|how to|click|go to|install|type|paste|open)\b",
    "comparison": r"\b(vs\.?|versus|better than|instead of|replace[sd]?|alternative)\b",
    "news/claim": r"\b(just (released|dropped|launched)|new|announced|breaking)\b",
}


def ytdlp(*args, cookies=None):
    cmd = ["yt-dlp", "--no-warnings", "-q"] + (["--cookies", cookies] if cookies else []) + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


def list_account(url, latest, cookies):
    p = ytdlp("--flat-playlist", "--playlist-end", str(latest), "-J", url, cookies=cookies)
    if p.returncode != 0 or not p.stdout.strip():
        raise SystemExit(f"cannot list {url}: {(p.stderr or 'empty').strip()[-200:]} (Instagram needs --cookies)")
    d = json.loads(p.stdout)
    return [{"url": e.get("url") or e.get("webpage_url"), "views": e.get("view_count") or 0, "title": e.get("title") or ""}
            for e in d.get("entries") or [] if e.get("url") or e.get("webpage_url")]


def fetch(url, cookies):
    """Audio only (16 kHz mono WAV for whisper) + metadata. Returns (wav, info)."""
    TMP.mkdir(parents=True, exist_ok=True)
    p = ytdlp("-f", "ba/b", "-x", "--audio-format", "wav", "--postprocessor-args", "ffmpeg:-ar 16000 -ac 1",
              "--write-info-json", "-o", str(TMP / "%(extractor_key)s-%(id)s.%(ext)s"), "--print", "after_move:filepath", url, cookies=cookies)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or "download failed").strip()[-300:])
    wav = Path(p.stdout.strip().splitlines()[-1])
    info_path = wav.with_suffix(".info.json")
    info = json.loads(info_path.read_text())
    info_path.unlink(missing_ok=True)  # YouTube info.json can be 10+ MB; keep only what we need
    return wav, info


def transcribe(wav, lang, model_name=None):
    """model_name: small.en (default, most accurate), base.en (~3x faster, bulk studies), base (multilingual)."""
    model = MODELS / (f"ggml-{model_name}.bin" if model_name else ("ggml-small.en.bin" if lang == "en" else "ggml-base.bin"))
    if not model.exists():
        url = f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{model.name}"
        subprocess.run(["curl", "-fsSL", "-o", str(model), url], check=True)
    prefix = wav.with_suffix("")
    fast = ["-bs", "1", "-bo", "1", "-nf"] if model_name in ("base.en", "tiny.en", "base") else []  # greedy decode for bulk studies (~3-5x faster)
    subprocess.run([str(WHISPER), "-m", str(model), "-f", str(wav), "-t", "2", "-l", "en" if lang == "en" else "auto",
                    "-oj", "-of", str(prefix), "-np", *fast], check=True, capture_output=True, timeout=600)
    data = json.loads(prefix.with_suffix(".json").read_text())
    prefix.with_suffix(".json").unlink(missing_ok=True)
    segs = [{"start": s["offsets"]["from"] / 1000, "end": s["offsets"]["to"] / 1000, "text": s["text"].strip()}
            for s in data.get("transcription", []) if s["text"].strip()]
    return segs, data.get("result", {}).get("language", lang)


def analyse(info, segs):
    text = " ".join(s["text"] for s in segs)
    words = re.findall(r"[\w'’.-]+", text)
    speech = sum(s["end"] - s["start"] for s in segs) or 1
    hook = " ".join(s["text"] for s in segs if s["start"] < 3.0)
    first_sentence = re.split(r"(?<=[.?!])\s", text.strip(), maxsplit=1)[0] if text else ""
    tail = " ".join(s["text"] for s in segs if s["end"] > (segs[-1]["end"] - 8)) if segs else ""
    views = info.get("view_count") or 0
    likes, comments, shares = info.get("like_count") or 0, info.get("comment_count") or 0, info.get("repost_count") or 0
    return {
        "duration": info.get("duration"), "words": len(words), "wpm": round(len(words) / speech * 60),
        "hook_3s": hook, "first_sentence": first_sentence,
        "hook_has_number": bool(re.search(r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million)\b", hook, re.I)),
        "hook_has_you": bool(re.search(r"\byou(r)?\b", hook, re.I)), "hook_is_question": "?" in hook,
        "cta": [k for k, rx in CTA.items() if re.search(rx, tail, re.I)],
        "structure": [k for k, rx in STRUCT.items() if len(re.findall(rx, text, re.I)) >= 2],
        "engagement_rate": round((likes + comments + shares) / views * 100, 2) if views else None,
        "comments_per_1k_views": round(comments / views * 1000, 1) if views else None,
        "likes_per_1k_views": round(likes / views * 1000, 1) if views else None,
    }


def excerpt(s, n=20):
    w = s.split()
    return " ".join(w[:n]) + (" …" if len(w) > n else "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", action="append", default=[], help="video URL (repeatable)")
    ap.add_argument("--account", action="append", default=[], help="profile/channel URL (repeatable)")
    ap.add_argument("--latest", type=int, default=12, help="how many recent videos to list per account")
    ap.add_argument("--top", type=int, default=3, help="transcribe the N most-viewed of those")
    ap.add_argument("--lang", default="en", choices=["en", "auto"], help="auto = multilingual model (Hindi/Urdu…)")
    ap.add_argument("--cookies", help="Netscape cookies.txt (keep it in /var/tmp; never in the workspace)")
    a = ap.parse_args()

    targets = [(u, None) for u in a.url]
    for acc in a.account:
        vids = sorted(list_account(acc, a.latest, a.cookies), key=lambda v: -v["views"])
        print(f"{acc}: {len(vids)} recent videos; transcribing top {a.top} by views")
        targets += [(v["url"], acc) for v in vids[:a.top]]

    RAW.mkdir(parents=True, exist_ok=True)
    idx_path = OUT / "index.csv"
    seen = set(r["url"] for r in csv.DictReader(idx_path.open())) if idx_path.exists() else set()
    rows = []
    for url, acc in targets:
        if url in seen:
            print(f"  = already scanned: {url}")
            continue
        try:
            wav, info = fetch(url, a.cookies)
            segs, lang = transcribe(wav, a.lang)
            wav.unlink(missing_ok=True)  # research only: no media kept
        except Exception as e:  # keep going; report at the end
            print(f"  ✗ {url}: {e}")
            rows.append({"url": url, "error": str(e)[:200]})
            continue
        m = analyse(info, segs)
        item = {"url": url, "platform": info.get("extractor_key"), "id": info.get("id"),
                "account": info.get("uploader") or info.get("channel") or acc, "upload_date": info.get("upload_date"),
                "title": info.get("title"), "description": (info.get("description") or "")[:1000],
                "hashtags": re.findall(r"#\w+", info.get("description") or ""), "views": info.get("view_count"),
                "likes": info.get("like_count"), "comments": info.get("comment_count"), "shares": info.get("repost_count"),
                "language": lang, "metrics": m, "transcript": segs, "scanned": dt.date.today().isoformat()}
        (RAW / f"{item['platform']}-{item['id']}.json").write_text(json.dumps(item, indent=1, ensure_ascii=False))
        rows.append(item)
        print(f"  ✓ {item['platform']} @{item['account']} {item['views']:,} views · {m['duration']}s · {m['wpm']} wpm · CTA {m['cta']} · hook: {excerpt(m['hook_3s'], 12)}")

    ok = [r for r in rows if "error" not in r]
    idx = OUT / "index.csv"
    new = not idx.exists()
    with idx.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["scanned", "platform", "account", "url", "upload_date", "views", "likes", "comments", "duration_s", "wpm",
                        "hook_has_number", "hook_is_question", "cta", "structure", "comments_per_1k", "hook_excerpt"])
        for r in ok:
            m = r["metrics"]
            w.writerow([r["scanned"], r["platform"], r["account"], r["url"], r["upload_date"], r["views"], r["likes"], r["comments"],
                        m["duration"], m["wpm"], m["hook_has_number"], m["hook_is_question"], "|".join(m["cta"]), "|".join(m["structure"]),
                        m["comments_per_1k_views"], excerpt(m["hook_3s"])])
    print(f"{len(ok)}/{len(rows)} videos scanned -> research/social/index.csv (+ raw transcripts, workspace-only)")


if __name__ == "__main__":
    main()
