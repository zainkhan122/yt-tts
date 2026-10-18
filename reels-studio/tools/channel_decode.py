#!/usr/bin/env python3
"""
Channel decode: pull apart how high-traffic short-form channels actually win —
Script + Voice (TTS) + Cover + Media + Heading + Description, per video.

For each account (TikTok handle or YouTube channel/ shorts URL):
  meta    latest N videos (views/likes/comments/shares/saves where the platform exposes them)
  decode  the top-K and bottom-1 by views:
            heading     title / caption first line, hook type, keyword position
            description first lines, where the link sits, hashtag count, CTA present
            script      auto-captions, else faster-whisper (tiny.en) on the audio
            voice       parselmouth prosody: pitch range (semitones), speech rate, pause share
            cover       thumbnail image saved for visual inspection
            media       frames at 0.5 s / 50% / 85% + contact sheet, cuts per 10 s (frame diffs)

  python3 tools/channel_decode.py --latest 10 --top 2 @github.signals https://www.youtube.com/channel/<id>/shorts

Raw media -> research/social/raw/decode/ (git-ignored; the repo is public).
Committed output: research/social/decode-<date>.md + decode-<date>.json (metrics + <=20-word excerpts only).
Prosody note: creators' mixes include music beds; pitch is measured on the mixed audio without
vocal separation, so read pitch ranges as relative, not absolute.
"""
import argparse
import datetime as dt
import json
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from channel_study import hook_type  # noqa: E402  (shared hook taxonomy)

RAW = ROOT / "research/social/raw/decode"
TODAY = dt.date.today().isoformat()


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ytdlp_json(args):
    r = run(["yt-dlp", "--no-warnings", "-q", "-J"] + args, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-400:])
    return json.loads(r.stdout)


def account_url(acc):
    if acc.startswith("http"):
        return acc
    return f"https://www.tiktok.com/@{acc.strip('@')}"


def account_name(acc, info):
    if "tiktok.com" in acc or not acc.startswith("http"):
        m = re.search(r"@([\w.]+)", acc)
        return "@" + (m.group(1) if m else acc.strip("@"))
    return "@" + (info.get("channel") or info.get("uploader") or "youtube")


def captions(url, out_base):
    """Auto-captions -> plain text, or '' (caller falls back to Whisper)."""
    run(["yt-dlp", "--no-warnings", "-q", "--skip-download", "--write-auto-subs",
         "--write-subs", "--sub-langs", "en.*", "--sub-format", "vtt", "-o", out_base, url],
        timeout=300)
    for vtt in sorted(Path(out_base).parent.glob(Path(out_base).name + "*.vtt")):
        lines, seen = [], set()
        for line in vtt.read_text(errors="ignore").splitlines():
            line = re.sub(r"<[^>]+>", "", line).strip()
            if not line or line == "WEBVTT" or "-->" in line or line.startswith(("Kind:", "Language:")):
                continue
            if line not in seen:
                seen.add(line)
                lines.append(line)
        if lines:
            return " ".join(lines)
    return ""


_fw = None


def whisper(wav):
    global _fw
    if _fw is None:
        from faster_whisper import WhisperModel
        _fw = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    segs, _ = _fw.transcribe(str(wav), language="en", vad_filter=True)
    return " ".join(s.text.strip() for s in segs)


def prosody(audio):
    """Pitch range (semitones), intensity range and voiced share via Praat."""
    import parselmouth
    snd = parselmouth.Sound(str(audio))
    dur = snd.get_total_duration()
    if dur < 3:
        return {}
    pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=60, pitch_ceiling=500)
    f0 = [f for f in pitch.selected_array["frequency"] if f > 0]
    inten = snd.to_intensity(time_step=0.01, minimum_pitch=70)
    ivals = [v for v in inten.values[0] if v > 0]
    out = {"duration": round(dur, 1), "voiced_share": round(len(f0) / max(1, len(pitch.selected_array["frequency"])), 2)}
    if len(f0) > 30:
        med = st.median(f0)
        lo, hi = st.quantiles(f0, n=100)[4], st.quantiles(f0, n=100)[94]
        out["pitch_median_hz"] = round(med)
        out["pitch_range_st"] = round(12 * __import__("math").log2(hi / lo), 1) if lo > 0 else None
    if ivals:
        out["intensity_range_db"] = round(max(ivals) - st.median(ivals), 1)
    return out


def frames_and_cuts(video, out_dir, vid):
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if n <= 0:
        return {}
    picks = {"cover_frame": 0.5, "mid_frame": 0.5 * n / fps, "late_frame": 0.85 * n / fps}
    saved = {}
    for name, t in picks.items():
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if ok:
            p = out_dir / f"{vid}-{name}.jpg"
            cv2.imwrite(str(p), fr, [cv2.IMWRITE_JPEG_QUALITY, 82])
            saved[name] = p.name
    # cuts: large mean-abs frame differences on a downscaled stream
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    prev, cuts, idx = None, 0, 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        idx += 1
        if idx % 3:
            continue
        small = cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (48, 85)).astype("float32")
        if prev is not None and float(np.mean(np.abs(small - prev))) > 18:
            cuts += 1
        prev = small
    cap.release()
    return {"frames": saved, "cuts_per_10s": round(cuts / (n / fps) * 10, 1) if n else None}


def first_lines(text, k=2):
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return lines[:k]


def decode_video(entry, acc_dir):
    url = entry.get("webpage_url") or entry.get("url")
    vid = entry.get("id")
    try:
        info = ytdlp_json([url])
    except Exception as exc:
        # YouTube full fetch can be bot-gated without cookies; keep the flat-listing facts
        # (heading/views/duration) and mark the deep decode as unavailable for this row.
        print(f"  full fetch failed {vid}: {str(exc)[:120]}", file=sys.stderr)
        info = {"id": vid, "webpage_url": url, "title": entry.get("title"),
                "view_count": entry.get("views"), "duration": entry.get("duration"),
                "description": "", "tags": [], "thumbnail": None}
        row = {"id": vid, "url": url, "views": info["view_count"], "likes": None,
               "comments": None, "duration": info["duration"] or 0,
               "heading": (info["title"] or "")[:160], "hook_type": hook_type(info["title"] or ""),
               "script_words": 0, "wpm": None, "script_source": "unavailable (bot-gated)",
               "script_hook_excerpt": "", "cta_in_script": False,
               "description_first_lines": [], "description_has_link": False,
               "hashtags": [], "tags": [], "cover": ""}
        return row
    dur = info.get("duration") or 0
    desc = info.get("description") or ""
    work = acc_dir / vid
    work.mkdir(parents=True, exist_ok=True)
    # audio for voice + script fallback; small video for frames
    run(["yt-dlp", "--no-warnings", "-q", "-f", "ba/b", "-o", str(work / "audio.%(ext)s"), url], timeout=600)
    audio = next(iter(sorted(work.glob("audio.*"))), None)
    script, script_src = captions(url, str(work / "cap")), "captions"
    if len(script.split()) < 8 and audio:
        try:
            script, script_src = whisper(audio), "whisper-tiny"
        except Exception as exc:  # keep decoding the rest
            print(f"  whisper failed {vid}: {exc}", file=sys.stderr)
    voice = {}
    if audio:
        try:
            voice = prosody(audio)
        except Exception as exc:
            print(f"  prosody failed {vid}: {exc}", file=sys.stderr)
    media = {}
    run(["yt-dlp", "--no-warnings", "-q", "-f", "bv*[height<=480]/b[height<=480]/b",
         "-o", str(work / "video.%(ext)s"), url], timeout=600)
    video = next(iter(sorted(work.glob("video.*"))), None)
    if video:
        try:
            media = frames_and_cuts(video, work, vid)
        except Exception as exc:
            print(f"  frames failed {vid}: {exc}", file=sys.stderr)
    thumb = info.get("thumbnail")
    cover = ""
    if thumb:
        r = run(["curl", "-sL", "-o", str(work / "cover.jpg"), thumb], timeout=120)
        if r.returncode == 0 and (work / "cover.jpg").exists():
            cover = "cover.jpg"
    words = script.split()
    row = {
        "id": vid, "url": url, "views": info.get("view_count"),
        "likes": info.get("like_count"), "comments": info.get("comment_count"),
        "duration": dur,
        "heading": (info.get("title") or "")[:160],
        "hook_type": hook_type(script or info.get("title") or ""),
        "script_words": len(words),
        "wpm": round(len(words) / (dur / 60)) if dur else None,
        "script_source": script_src,
        "script_hook_excerpt": " ".join(words[:20]),
        "cta_in_script": bool(re.search(r"comment|follow|save|subscribe|link in", script, re.I)),
        "description_first_lines": first_lines(desc),
        "description_has_link": bool(re.search(r"https?://|www\.|github\.com/", desc)),
        "hashtags": re.findall(r"#\w+", desc)[:10],
        "tags": (info.get("tags") or [])[:8],
        "cover": cover, **voice, **media,
    }
    (work / "decode.json").write_text(json.dumps(row, indent=1))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accounts", nargs="+", help="TikTok handles (@x or x) or YouTube channel/shorts URLs")
    ap.add_argument("--latest", type=int, default=10)
    ap.add_argument("--top", type=int, default=2, help="top-K by views to decode, plus the bottom one")
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for acc in args.accounts:
        url = account_url(acc)
        print(f"== {url}")
        listing = ytdlp_json(["--flat-playlist", "--playlist-end", str(args.latest), url])
        entries = [e for e in (listing.get("entries") or []) if e.get("id")]
        name = account_name(url, listing)
        acc_dir = RAW / name.strip("@")
        acc_dir.mkdir(parents=True, exist_ok=True)
        brief = []
        for e in entries:
            full = e if e.get("view_count") is not None else None
            brief.append({"id": e.get("id"), "url": e.get("webpage_url") or e.get("url") or f"{url}",
                          "views": e.get("view_count"), "title": (e.get("title") or "")[:120],
                          "duration": e.get("duration")})
        ranked = sorted([b for b in brief if b["views"] is not None], key=lambda b: -b["views"])
        picks = ranked[:args.top] + (ranked[-1:] if len(ranked) > args.top else [])
        print(f"  {len(entries)} listed; decoding {[p['id'] for p in picks]}")
        rows = []
        for p in picks:
            try:
                row = decode_video(p, acc_dir)
            except Exception as exc:
                print(f"  decode failed {p['id']}: {exc}", file=sys.stderr)
                continue
            row["account"] = name
            row["tier"] = "bottom" if p is ranked[-1] and len(ranked) > args.top else "top"
            rows.append(row)
            all_rows.append(row)
        (acc_dir / "latest.json").write_text(json.dumps({"account": name, "url": url,
                                                         "listed": brief, "decoded": rows}, indent=1))
    out_json = ROOT / f"research/social/decode-{TODAY}.json"
    if out_json.exists():  # merge repeat runs by (account, id) instead of clobbering
        old = json.loads(out_json.read_text())
        seen = {(r.get("account"), r.get("id")) for r in all_rows}
        all_rows = all_rows + [r for r in old if (r.get("account"), r.get("id")) not in seen]
    out_json.write_text(json.dumps(all_rows, indent=1))
    print(f"wrote {out_json} ({len(all_rows)} videos)")


if __name__ == "__main__":
    main()
