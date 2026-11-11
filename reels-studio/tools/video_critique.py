#!/usr/bin/env python3
"""Video critique: send the FULL video (not sampled frames) to a video-capable NIM model
(cosmos-reason1-7b and friends accept `video_url` with a base64 data URI) and write a forensic
delivery teardown to research/critiques/video-<subject>-<date>.md.

Reference = lead, never copy: we extract anatomy (pacing, caption sizes, beats), never assets.
Runs in the frame-critique workflow (mode=video) — NVIDIA_KEY is a GitHub Actions secret only.

  python3 tools/video_critique.py --subject instagram-malva-veo --video-urls "https://..."
  python3 tools/video_critique.py --subject tiktok-vanta-plugins --video-file /tmp/a.mp4
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

from frame_critique import API, ROOT, CascadeSkip, call, call_vision, key, models as vlm_models

VIDEO_PREFERRED = [  # known video-capable NIM models first; then anything the catalog hints at
    "nvidia/cosmos-reason3-30b-a16b-think", "nvidia/cosmos-reason3-7b",
    "nvidia/cosmos-reason2-8b", "nvidia/cosmos-reason1-7b", "microsoft/cosmos-reason1-7b",
    "nvidia/vila",
]
VIDEO_MAX_BYTES = 10 * 1024 * 1024  # NIM free tier rejects larger payloads; keep shorts small

TEARDOWN_PROMPT = """You are a forensic reviewer of short-form vertical videos, briefing a senior video editor.
Watch the WHOLE video (motion over time matters). Report ONLY what is on screen:

1. STRUCTURE: list every beat with its on-screen time range (0-3s, 3-8s...), the dominant visual, and the exact on-screen text of each beat (quote it).
2. DELIVERY: caption placement (where on frame, size relative to frame), caption style (word-by-word chunks? sentence? karaoke highlight?), colors and casing, font weight.
3. MOTION: what MOVES per beat (zoom, pan, element slides, pops, cursor presses, state changes in UI); describe the transitions between beats (cut/fade/slide/wipe); note anything striking.
4. MEDIA GRAMMAR: is media a product UI, screen recording, generated art, stock footage, or talking head? How much of the frame does it occupy?
5. HOOK & PAYOFF: quote the first visual + first caption; what promise is made and what the payoff frame shows.
6. TAKEAWAYS: 5 concrete techniques worth imitating IN OUR OWN STYLE (vector UI, house captions), and 3 mistakes to avoid.

Be specific with timings and text. This is for study, not copying."""


def video_models(tok):
    live = vlm_models(tok)  # catalog query; returns preferred-first vision hints
    video = [m for m in VIDEO_PREFERRED if m in live]
    hinted = [m for m in live if m not in video and "cosmos" in m.lower()]
    return video + hinted + [m for m in VIDEO_PREFERRED if m not in live and m not in hinted]


def fetch(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return dest


def b64video(path):
    data = Path(path).read_bytes()
    if len(data) > VIDEO_MAX_BYTES:
        raise SystemExit(f"video too large for NIM payload: {path} ({len(data)//1024} KB) — keep clips short")
    return f"data:video/mp4;base64," + base64.b64encode(data).decode()


def call_video(model, data_url, tok, prompt=TEARDOWN_PROMPT, max_tokens=3500):
    content = [{"type": "video_url", "video_url": {"url": data_url}},
               {"type": "text", "text": prompt}]
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": content}],
                       "max_tokens": max_tokens, "temperature": 0.2, "top_p": 0.9, "stream": False,
                       "media_io_kwargs": {"video": {"fps": 4}}}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception as e:  # cascade decision belongs to the caller
        raise CascadeSkip(f"{model}: {type(e).__name__} {e}") from e


def teardown(video_path, tok, model_list):
    data_url = b64video(video_path)
    last = None
    for m in model_list:
        try:
            print(f"video critique: {Path(video_path).name} -> {m}", file=sys.stderr)
            return m, call_video(m, data_url, tok)
        except CascadeSkip as e:
            last = e
            print(f"cascade: {e}, trying next", file=sys.stderr)
    raise SystemExit(f"video_critique: no video model accepted the request ({last})")


TEXT_FALLBACK = ["meta/llama-3.3-70b-instruct", "google/gemma-3-27b-it", "google/gemma-3-12b-it"]

FRAME_BEAT_PROMPT = ("You are logging one frame of a short vertical video for a forensic teardown. "
                     "Report tersely: (1) ALL on-screen text, quoted; (2) the dominant visual "
                     "(UI mockup? footage? face?); (3) one word for the motion feel (pop/zoom/pan/slide/static).")

SYNTH_PROMPT = """Below are per-frame logs (t = seconds into the video) from a short-form reference video, \
logged by a vision model. Reconstruct the delivery anatomy into these sections:
1. STRUCTURE: beats with time ranges, dominant visual, exact on-screen text per beat.
2. DELIVERY: caption placement, size, style (word chunks/sentence/karaoke), colors, casing.
3. MOTION: what moves per beat; transitions between beats.
4. MEDIA GRAMMAR: what the media IS (product UI, footage, face) and how much of the frame it occupies.
5. HOOK & PAYOFF: first visual + first caption quoted; promise made; payoff frame.
6. TAKEAWAYS: 5 techniques worth imitating IN OUR OWN STYLE; 3 mistakes to avoid.

Frame logs:
"""


def frame_teardown(video_path, tok):
    """Fallback: dense per-frame vision calls (1 fps) + text synthesis — real motion evidence."""
    import shutil
    import subprocess
    ff = shutil.which("ffmpeg")
    if not ff:  # imageio vendored binary (vendored-tooling rule: survives runner resets)
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    frames_dir = Path(tempfile.mkdtemp())
    fps = 1.0  # shorts are ~20-70 s; cap at 90 calls regardless of length
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(video_path),
                    "-vf", f"fps={fps},scale=512:-1", "-frames:v", "90", "-q:v", "4",
                    str(frames_dir / "f%03d.jpg")], check=True)
    logs = []
    for i, f in enumerate(sorted(frames_dir.glob("f*.jpg"))):
        t = float(i)  # fps is 1.0 (90-frame cap): frame index == seconds
        try:
            m, note = call_vision(f, FRAME_BEAT_PROMPT, tok, max_tokens=220)
            logs.append(f"t={t:04.1f}s: {note.strip()}")
            print(f"  frame {i+1} t={t:.0f}s ok ({m})", file=sys.stderr)
        except SystemExit as e:
            logs.append(f"t={t:04.1f}s: (unreadable)")
            print(f"  frame {i} skipped: {e}", file=sys.stderr)
    last = None
    for m in TEXT_FALLBACK:
        try:
            text = call(m, [{"role": "user", "content": SYNTH_PROMPT + "\n".join(logs)}], tok, max_tokens=3500)
            return m, f"_Dense-frame fallback ({fps:.2f} fps, {len(logs)} frames; video catalog empty)_\n\n{text}"
        except CascadeSkip as e:
            last = e
    raise SystemExit(f"video_critique: no text model for synthesis ({last})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True, help="slug for the output doc")
    ap.add_argument("--video-urls", default="", help="space-separated mp4 URLs (max 5)")
    ap.add_argument("--video-file", default="", help="one local mp4 instead of URLs")
    args = ap.parse_args()

    tok = key()
    mdl_list = video_models(tok)
    live = vlm_models(tok)
    print("video models:", ", ".join(mdl_list[:8]), file=sys.stderr)
    print("live catalog (vision hints):", ", ".join(live[:20]), file=sys.stderr)

    out = ROOT / "research" / "critiques" / f"video-{args.subject}-{dt.date.today():%Y-%m-%d}.md"
    parts = [f"# Video teardown: {args.subject} — {dt.date.today():%Y-%m-%d}",
             "\nMethod: FULL video sent to a video-capable NVIDIA NIM model (not frame sampling), "
             "4 fps decode server-side. Reference = lead, never copy.\n"]

    vids = []
    if args.video_file:
        vids.append(Path(args.video_file))
    for i, url in enumerate([u for u in args.video_urls.split() if u][:5]):
        dest = Path(tempfile.mkdtemp()) / f"ref-{i}.mp4"
        print(f"download {url}", file=sys.stderr)
        vids.append(fetch(url, dest))

    for v in vids:
        try:
            model, text = teardown(v, tok, mdl_list)
        except SystemExit as e:
            if "no video model" not in str(e):
                raise
            print("video catalog empty — dense-frame fallback", file=sys.stderr)
            model, text = frame_teardown(v, tok)
        parts.append(f"\n## {v.name}\n\n_Model: {model}; clip: {len(v.read_bytes())//1024} KB_\n\n{text}\n")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
