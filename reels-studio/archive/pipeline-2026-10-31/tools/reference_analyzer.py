#!/usr/bin/env python3
"""Reference video analyzer: extract lessons from a reference channel's video.

Combines:
  * yt-dlp metadata (title, description, hashtags, views, likes, comments, duration)
  * audio delivery analysis (wpm, pause density, emphasis, silence — via audio_analyze.py)
  * frame extraction (key frames at scene boundaries — via ffmpeg)
  * scene-change detection (via ffmpeg)

Output: a structured "lessons report" saved to research/reference-study/.

This is a ONE-TIME analysis to set our delivery pattern baseline. Run it on
our own published videos and on reference videos to learn what delivery
patterns correlate with retention.

  python3 tools/reference_analyzer.py https://www.youtube.com/shorts/XXXXX
  python3 tools/reference_analyzer.py --channel @github.awesome --latest 3
  python3 tools/reference_analyzer.py --json <url>
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDY_DIR = ROOT / "research" / "reference-study"


def _ffmpeg_exe() -> str:
    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def yt_dlp_metadata(url: str) -> dict:
    """Extract full metadata from a YouTube video via yt-dlp."""
    p = subprocess.run(
        ["yt-dlp", "--skip-download", "-J", "--no-warnings", url],
        capture_output=True, text=True, timeout=120,
    )
    if p.returncode or not p.stdout.strip():
        return {"error": (p.stderr or "no data").strip()[-200:]}
    d = json.loads(p.stdout)
    return {
        "title": d.get("title", ""),
        "description": (d.get("description") or "")[:2000],
        "uploader": d.get("uploader", d.get("channel", "")),
        "duration_s": d.get("duration", 0),
        "view_count": d.get("view_count", 0),
        "like_count": d.get("like_count", 0),
        "comment_count": d.get("comment_count", 0),
        "repost_count": d.get("repost_count", 0),
        "tags": d.get("tags", []),
        "categories": d.get("categories", []),
        "url": d.get("webpage_url", url),
        "id": d.get("id", ""),
        "upload_date": d.get("upload_date", ""),
        "ext": d.get("ext", ""),
    }


def download_audio(url: str, out_path: str) -> str:
    """Download just the audio track from a YouTube video."""
    subprocess.run(
        ["yt-dlp", "-x", "--audio-format", "wav", "--audio-quality", "5",
         "-o", out_path, "--no-playlist", url],
        capture_output=True, check=True, timeout=180,
    )
    return out_path


def extract_key_frames(video_path: str, out_dir: str, n: int = 8) -> list[str]:
    """Extract evenly-spaced key frames from a video."""
    ff = _ffmpeg_exe()
    frames = []
    for i in range(n):
        out = f"{out_dir}/frame_{i:02d}.jpg"
        subprocess.run(
            [ff, "-ss", str(i * 4), "-i", video_path, "-frames:v", "1",
             "-q:v", "3", out],
            capture_output=True, timeout=60,
        )
        if Path(out).exists():
            frames.append(out)
    return frames


def detect_scene_changes(video_path: str) -> list[float]:
    """Detect scene change timestamps using ffmpeg's select filter."""
    ff = _ffmpeg_exe()
    p = subprocess.run(
        [ff, "-i", video_path, "-vf", "select='gt(scene,0.3)',showinfo",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=60,
    )
    times = re.findall(r"pts_time:([\d.]+)", p.stderr)
    return [float(t) for t in times]


def analyze(url: str, with_audio: bool = True) -> dict:
    """Full analysis of a reference video."""
    meta = yt_dlp_metadata(url)
    if "error" in meta:
        return {"error": meta["error"]}

    result = {"metadata": meta}

    # Audio delivery analysis
    if with_audio:
        with tempfile.TemporaryDirectory() as td:
            audio_path = td + "/audio.wav"
            try:
                download_audio(url, audio_path)
                sys.path.insert(0, str(ROOT / "tools"))
                import audio_analyze as aa
                result["audio"] = aa.compute_metrics([], 0, "", audio_path)
            except Exception as e:
                result["audio"] = {"error": str(e)[:200]}

    # Scene changes
    with tempfile.TemporaryDirectory() as td:
        video_path = td + "/video.mp4"
        try:
            subprocess.run(
                ["yt-dlp", "-f", "worst[ext=mp4]/worst", "-o", video_path,
                 "--no-playlist", url],
                capture_output=True, check=True, timeout=180,
            )
            scenes = detect_scene_changes(video_path)
            result["scene_changes"] = scenes
            result["scene_count"] = len(scenes)
        except Exception as e:
            result["scene_changes"] = []
            result["scene_count"] = 0

    return result


def lessons_report(data: dict) -> str:
    """Generate a human-readable lessons report from analysis data."""
    meta = data.get("metadata", {})
    audio = data.get("audio", {})
    scenes = data.get("scene_changes", [])

    L = []
    L.append(f"# Reference analysis: {meta.get('title', '?')}")
    L.append(f"URL: {meta.get('url', '?')}")
    L.append(f"Channel: {meta.get('uploader', '?')}")
    L.append(f"Duration: {meta.get('duration_s', 0)}s | Views: {meta.get('view_count', 0):,} | "
             f"Likes: {meta.get('like_count') or 0:,} | Comments: {meta.get('comment_count') or 0:,}")
    L.append("")

    # Description analysis
    desc = meta.get("description", "")
    if desc:
        lines = desc.strip().split("\n")
        L.append(f"## Description ({len(lines)} lines, {len(desc)} chars)")
        for line in lines[:5]:
            L.append(f"  - {line[:100]}")
        hashtags = re.findall(r"#(\w+)", desc)
        if hashtags:
            L.append(f"  Hashtags: {', '.join('#'+h for h in hashtags[:8])}")
        L.append("")

    # Tags
    tags = meta.get("tags", [])
    if tags:
        L.append(f"## Tags: {', '.join(tags[:10])}")
        L.append("")

    # Audio delivery
    if audio and "error" not in audio:
        L.append("## Audio delivery")
        if audio.get("wpm"):
            L.append(f"  WPM: {audio['wpm']}")
            L.append(f"  Pause density: {audio.get('pause_density_per_min', '?')}/min")
            L.append(f"  Emphasis words: {audio.get('emphasis_words', [])}")
        if audio.get("silence_pct") is not None:
            L.append(f"  Silence: {audio['silence_pct']}%")
        if audio.get("rms_level_db"):
            L.append(f"  RMS level: {audio['rms_level_db']} dB")
        L.append("")

    # Scene structure
    if scenes:
        L.append(f"## Scene changes: {len(scenes)} across {meta.get('duration_s', 0)}s")
        for t in scenes:
            L.append(f"  - {t:.1f}s")
        L.append("")

    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?", help="YouTube video URL")
    ap.add_argument("--channel", help="Channel handle (e.g., @github.awesome)")
    ap.add_argument("--latest", type=int, default=3, help="Latest N videos from channel")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-audio", action="store_true", help="Skip audio download")
    a = ap.parse_args()

    if a.channel:
        # List recent videos from channel
        urls = []
        p = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--playlist-end", str(a.latest),
             "-J", "--no-warnings", f"https://www.youtube.com/{a.channel}/shorts"],
            capture_output=True, text=True, timeout=120,
        )
        if p.returncode:
            print(f"Failed to list channel: {p.stderr[:200]}", file=sys.stderr)
            return 1
        d = json.loads(p.stdout)
        for e in d.get("entries", []):
            if e:
                urls.append(f"https://www.youtube.com/shorts/{e['id']}")
    else:
        urls = [a.url] if a.url else []

    if not urls:
        print("No URLs to analyze", file=sys.stderr)
        return 1

    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    for url in urls:
        data = analyze(url, with_audio=not a.no_audio)
        if "error" in data:
            print(f"  ✗ {url}: {data['error']}")
            continue
        report = lessons_report(data)
        fname = STUDY_DIR / f"{data['metadata'].get('id', 'unknown')}.md"
        fname.write_text(report + "\n")
        reports.append(str(fname))
        print(f"  ✓ {data['metadata'].get('title', '?')[:60]} -> {fname.name}")

    if a.json:
        print(json.dumps({"reports": reports}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
