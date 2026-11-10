#!/usr/bin/env python3
"""Reference teardown — after a topic is approved, dissect the SOURCE short before we make our own.

  python3 tools/reference_teardown.py <tiktok/youtube URL or post_id from posts.csv>

House rule (2026-11-10): we take LEAD from the reference, never copy it. The teardown therefore
extracts ANATOMY — hook formula, cut pacing, palette, beat structure, overlay grammar — as data,
and leaves clearly marked [AGENT] sections where the semantic analysis (what to take, what to
avoid) is written by the agent studying the extracted frames. The reference's footage and exact
words stay theirs.

Output: research/references/<platform>-<source>-<post_id>/
  manifest.json   — metrics: shots, cut rate, hook-window cuts, palette, luma/saturation, transcript
  teardown.md     — the analysis document (metrics auto-filled, [AGENT] sections to complete)
  frames/*.png    — keyframes at detected cuts + the 0-3s hook window (local only, git-ignored)

Downstream wiring:
  - brief JSON cites it via  "inspiration": {"platform","source","post_id"}  — ship.check then
    REQUIRES the completed teardown (no AGENT-TODO markers left) before approval.
  - preflight.check_reference_advisories flags phrase overlap between our copy and theirs (NOTE only).

Deps that survive sandbox resets: yt-dlp (vendored tools/bin/yt-dlp) + ffmpeg
(~/.config/reels-studio/bin/ffmpeg; resolver order: $FFMPEG > PATH > that path > imageio-ffmpeg).
"""
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "research" / "sources" / "posts.csv"
REFS = ROOT / "research" / "references"
YT_DLP = os.environ.get("YT_DLP") or shutil.which("yt-dlp") or str(ROOT / "tools" / "bin" / "yt-dlp")
FFMPEG = (os.environ.get("FFMPEG") or shutil.which("ffmpeg")
          or str(Path.home() / ".config/reels-studio/bin/ffmpeg"))
SCENE_THRESHOLD = 0.35
MAX_SHOT_FRAMES = 40
HOOK_WINDOW_S = 3.0
AGENT_TODO = "AGENT-TODO"


def run(cmd, timeout=300):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise SystemExit(f"teardown: command failed: {cmd[0]} …\n{p.stderr[-500:]}")
    return p


def resolve_post(token):
    """Find the post in posts.csv by URL substring, full URL, or bare post_id."""
    rows = list(csv.DictReader(open(POSTS, newline="", encoding="utf-8")))
    for r in rows:
        if r.get("platform") in ("tiktok", "youtube") and (token == r.get("url")
                                                           or token == r.get("post_id") or token in r.get("url", "")):
            if r.get("platform") in ("tiktok", "youtube"):
                return r
    raise SystemExit(f"teardown: '{token}' not found among tiktok/youtube rows in {POSTS.relative_to(ROOT)}")


def video_info(path):
    p = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0
    v = re.search(r"Stream .*Video:.*?(\d{3,4})x(\d{3,4}).*?([\d.]+) fps", p.stderr)
    return {"duration_s": round(dur, 2),
            "resolution": f"{v.group(1)}x{v.group(2)}" if v else "?",
            "fps": float(v.group(3)) if v else 0.0}


def detect_cuts(video, dur):
    p = subprocess.run([FFMPEG, "-i", str(video), "-vf",
                        f"select='gt(scene,{SCENE_THRESHOLD})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=300)
    cuts = sorted(round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", p.stderr))
    return [t for t in cuts if 0.2 < t < dur - 0.2]


def grab_frames(video, times, frames_dir):
    out = []
    for i, t in enumerate(times):
        png = frames_dir / f"{i:02d}-{t:06.2f}s.png"
        p = subprocess.run([FFMPEG, "-y", "-ss", f"{t:.2f}", "-i", str(video),
                            "-frames:v", "1", "-q:v", "2", str(png)],
                           capture_output=True, text=True, timeout=60)
        if p.returncode == 0 and png.exists() and png.stat().st_size > 0:
            out.append({"t": t, "path": f"frames/{png.name}"})
    return out


def avg_colors(video, fps, dur):
    """One average RGB per sampled frame over the whole video — a few KB of raw bytes."""
    step = max(1, int(fps / 2)) if fps else 15  # ~2 samples per second
    p = subprocess.run([FFMPEG, "-i", str(video), "-vf", f"select='not(mod(n,{step}))',scale=1:1:flags=area",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=300)
    data = p.stdout
    return [tuple(data[i:i + 3]) for i in range(0, len(data) - 2, 3)]


def palette_summary(colors):
    def luma(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    def sat(c):
        hi, lo = max(c), min(c)
        return (hi - lo) / hi if hi else 0.0
    buckets = {}
    for c in colors:
        key = tuple(min(255, round(v / 32) * 32) for v in c)
        buckets[key] = buckets.get(key, 0) + 1
    top = sorted(buckets.items(), key=lambda kv: -kv[1])[:6]
    total = len(colors) or 1
    return {
        "dominant_hex": ["#%02x%02x%02x" % k for k, _ in top],
        "dominant_share": [round(n / total, 2) for _, n in top],
        "dark_frame_ratio": round(sum(1 for c in colors if luma(c) < 60) / total, 2),
        "avg_saturation": round(sum(sat(c) for c in colors) / total, 2),
    }


def vtt_text(vtt):
    lines, seen = [], set()
    for raw in vtt.read_text(encoding="utf-8", errors="replace").splitlines():
        t = re.sub(r"<[^>]+>", "", raw).strip()
        if not t or "-->" in t or t.startswith(("WEBVTT", "Kind:", "Language:")) or t in seen:
            continue
        seen.add(t)
        lines.append(t)
    return "\n".join(lines)


def transcribe(video, ref_dir):
    """Script via platform captions first; faster-whisper if none; None if neither."""
    subs = sorted(ref_dir.glob("subs*.vtt"))
    if subs:
        return vtt_text(subs[0]), "platform-captions"
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None, "unavailable (no platform captions; faster-whisper not installed)"
    audio = ref_dir / "audio.wav"
    run([FFMPEG, "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
    model = WhisperModel("small", device="cpu", compute_type="int8")
    text = " ".join(seg.text.strip() for seg, _ in model.transcribe(str(audio), beam_size=5))
    audio.unlink(missing_ok=True)
    return text, "faster-whisper small"


# ---------- pure helpers reused by preflight advisories ----------

def ngrams(text, n=5):
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def shared_ngrams(a, b, n=5):
    return sorted(ngrams(a, n) & ngrams(b, n))


def reference_dir(platform, source, post_id):
    return REFS / f"{platform}-{source}-{post_id}"


def load_manifest(ref_dir):
    p = Path(ref_dir) / "manifest.json"
    return json.loads(p.read_text()) if p.exists() else None


DEF_TEARDOWN_MD = """# Reference teardown: {title}

- Source: {platform} · @{source} · {url}
- Teardown dir: `research/references/{dirname}/` · video downloaded {date} (frames local-only, git-ignored)
- Outlier at teardown: {views:,} views vs channel median {median:,} → **{multiple}x**
- Taken as LEAD only. Copying their footage, script sentences, or first-frame layout is a shipping block.

## Verified metrics (auto)

| Metric | Value |
|---|---|
| Duration | {duration_s}s |
| Resolution / fps | {resolution} · {fps} |
| Detected cuts | {cut_count} ({cut_rate}s avg shot length) |
| Cuts inside 0-{hook}s hook window | {hook_cuts} |
| Dark-frame ratio (luma<60) | {dark} |
| Avg colour saturation | {sat} |
| Dominant palette | {palette} |
| Script source | {script_source} |

Shot timeline (s): {timeline}
Frames: see `frames/` (keyframe per detected cut, capped {max_frames}, plus 0-3s hook window).

## Hook anatomy — {todo}
_(their first spoken line / first on-screen text; which hook_panel formula it matches and its score;
seconds until the first concrete proof appears)_

## Script beats — {todo}
_(beat map: what each ~5s block is doing — setup / mechanism / demo / payoff; BEATS not sentences)_

## Media & animation grammar — {todo}
_(what moves and why: layout skeleton, motion type, diagram vs screen-capture, overlay text style)_

## Colour & typography — {todo}
_(mood read vs the palette above; type scale/weight; contrast choices)_

## What we take — {todo}
_(mechanics worth borrowing for OUR short, stated as principles)_

## What we avoid — {todo}
_(anything too close to their execution; how our version must visibly differ)_

---
## Their transcript (for overlap checking — never quoted verbatim in our script)

{transcript}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("token", help="tiktok/youtube URL or post_id from posts.csv")
    ap.add_argument("--force", action="store_true", help="re-download even if the teardown dir exists")
    a = ap.parse_args()

    post = resolve_post(a.token)
    platform, source, pid = post["platform"], post["source"], post["post_id"]
    url, title = post["url"], post.get("title") or ""
    views = int(post["views"]) if (post.get("views") or "").isdigit() else 0
    ref_dir = reference_dir(platform, source, pid)
    if ref_dir.exists() and not a.force:
        raise SystemExit(f"teardown exists: {ref_dir.relative_to(ROOT)} (use --force to redo)")
    ref_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = ref_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    if not Path(YT_DLP).exists() and not shutil.which("yt-dlp"):
        raise SystemExit("teardown: yt-dlp missing (expected vendored tools/bin/yt-dlp)")
    if not Path(FFMPEG).exists() and not shutil.which("ffmpeg"):
        raise SystemExit("teardown: ffmpeg missing (set $FFMPEG or install to ~/.config/reels-studio/bin/ffmpeg)")

    print(f"downloading {url}", flush=True)
    run([YT_DLP, "--no-playlist", "-f", "best[ext=mp4]/best",
         "--write-subs", "--write-auto-subs", "--sub-langs", "en.*,en",
         "--sub-format", "vtt", "-o", str(ref_dir / "video.%(ext)s"), url], timeout=600)
    for s in ref_dir.glob("video.*.vtt"):
        s.rename(ref_dir / ("subs" + s.suffix if not (ref_dir / "subs.vtt").exists() else s.name))
    videos = [v for v in ref_dir.glob("video.*") if v.suffix in (".mp4", ".webm", ".mkv", ".mov")]
    if not videos:
        raise SystemExit("teardown: download produced no video file")
    video = videos[0]

    info = video_info(video)
    print(f"video {info['duration_s']}s {info['resolution']} — detecting cuts", flush=True)
    cuts = detect_cuts(video, info["duration_s"])
    if len(cuts) < 3 and info["duration_s"]:
        # screen-record style edits use scrolls/crossfades, not hard cuts — fall back to a time grid
        step = max(2.0, info["duration_s"] / 20)
        grid_n = int((info["duration_s"] - 0.5) / step)
        cuts = [round((i + 1) * step, 2) for i in range(grid_n)]
        print(f"few hard cuts ({len(detect_cuts(video, info['duration_s']))}) — grid-sampling every {step:.1f}s", flush=True)
    shot_len = round(info["duration_s"] / (len(cuts) + 1), 2) if info["duration_s"] else 0
    hook_cuts = sum(1 for t in cuts if t <= HOOK_WINDOW_S)
    times = sorted(set([0.0, 0.5, 1.0, 1.5, 2.5] + [t + 0.05 for t in cuts[:MAX_SHOT_FRAMES]]))
    frames = grab_frames(video, [t for t in times if t < info["duration_s"]], frames_dir)
    print(f"{len(cuts)} cuts, {len(frames)} frames — colours + script", flush=True)
    pal = palette_summary(avg_colors(video, info["fps"], info["duration_s"]))
    transcript, script_src = transcribe(video, ref_dir)

    rows = list(csv.DictReader(open(POSTS, newline="", encoding="utf-8")))
    ch_views = sorted(int(r["views"]) for r in rows
                      if r["platform"] == platform and r["source"] == source
                      and (r.get("views") or "").isdigit() and int(r["views"]) > 0)
    median = ch_views[len(ch_views) // 2] if len(ch_views) >= 4 else 0
    manifest = {
        "platform": platform, "source": source, "post_id": pid, "url": url, "title": title,
        "views_at_teardown": views, "channel_median_views": median,
        "outlier_multiple": round(views / median, 1) if median else None,
        **info, "cuts": cuts, "avg_shot_s": shot_len, "hook_window_s": HOOK_WINDOW_S,
        "hook_window_cuts": hook_cuts, "palette": pal, "frames": frames,
        "script_source": script_src, "transcript": transcript,
    }
    (ref_dir / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    md = DEF_TEARDOWN_MD.format(
        title=title or url, platform=platform, source=source, url=url,
        dirname=ref_dir.name, date=__import__("datetime").date.today().isoformat(),
        views=views, median=median, multiple=manifest["outlier_multiple"] or "n/a",
        duration_s=info["duration_s"], resolution=info["resolution"], fps=info["fps"],
        cut_count=len(cuts), cut_rate=shot_len, hook=int(HOOK_WINDOW_S), hook_cuts=hook_cuts,
        dark=pal["dark_frame_ratio"], sat=pal["avg_saturation"],
        palette=", ".join(pal["dominant_hex"]), script_source=script_src,
        timeline=", ".join(str(t) for t in cuts[:60]) or "(none detected)",
        max_frames=MAX_SHOT_FRAMES, todo=f"[{AGENT_TODO}]",
        transcript=transcript or "(no transcript — analyse spoken content from frames/audio review)")
    (ref_dir / "teardown.md").write_text(md, encoding="utf-8")
    print(f"teardown -> {ref_dir.relative_to(ROOT)}")
    print(f"next: study frames/ + transcript, replace every [{AGENT_TODO}] in teardown.md,")
    print(f"then cite it from the brief: \"inspiration\": "
          f"{{\"platform\": \"{platform}\", \"source\": \"{source}\", \"post_id\": \"{pid}\"}}")


if __name__ == "__main__":
    main()
