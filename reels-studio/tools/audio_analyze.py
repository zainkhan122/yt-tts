#!/usr/bin/env python3
"""Audio delivery analysis: extract voice-delivery metrics from a video.

Uses only tools already in the pipeline: ffmpeg (audio extraction) +
whisper.cpp (transcription with word timings). No new dependencies.

Metrics extracted:
  * wpm          — words per minute (delivery pace)
  * pause_density — pauses per second of speech (rhythm)
  * emphasis     — words spoken with >1.5x median duration (stressed words)
  * silence_pct  — percentage of total audio that is silence

This is a ONE-TIME analysis to set our delivery pattern baseline. Run it on
our own published videos and on reference videos to learn what delivery
patterns correlate with retention.

  python3 tools/audio_analyze.py /path/to/video.mp4
  python3 tools/audio_analyze.py https://youtube.com/shorts/XXXXX  # yt-dlp download
  python3 tools/audio_analyze.py video.mp4 --json
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _ffmpeg_exe() -> str:
    """Resolve ffmpeg binary: system first, then imageio-ffmpeg fallback."""
    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise FileNotFoundError("ffmpeg not available (install imageio-ffmpeg or system ffmpeg)")


def _ffprobe_exe() -> str:
    """ffprobe may not ship with imageio-ffmpeg; derive from ffmpeg path."""
    ff = _ffmpeg_exe()
    probe = ff.replace("ffmpeg", "ffprobe")
    if Path(probe).exists():
        return probe
    # imageio-ffmpeg ships only ffmpeg; use ffmpeg to probe duration
    return None


def extract_audio(video_path: str, out_path: str) -> str:
    """Extract 16kHz mono WAV using ffmpeg."""
    ff = _ffmpeg_exe()
    subprocess.run(
        [ff, "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000",
         "-f", "wav", out_path],
        capture_output=True, check=True, timeout=120,
    )
    return out_path


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds via ffmpeg stderr parsing (no ffprobe needed)."""
    ff = _ffmpeg_exe()
    p = subprocess.run(
        [ff, "-i", audio_path], capture_output=True, text=True, timeout=30,
    )
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", p.stderr)
    if m:
        h, mn, s = m.groups()
        return int(h) * 3600 + int(mn) * 60 + float(s)
    return 0.0


def whisper_transcribe(audio_path: str) -> dict:
    """Run whisper to get word-level timings. Returns {words:[...], text}.

    Uses whisper.cpp (setup/whisper) if available, falls back to openai-whisper
    pip package, or returns empty if neither is installed (audio-only metrics still work).
    """
    # Try whisper.cpp binary first
    whisper_dir = ROOT / "setup" / "whisper"
    if whisper_dir.exists():
        import os
        whisper_bin = whisper_dir / "main" / "whisper-cli"
        if not whisper_bin.exists():
            for p in whisper_dir.rglob("whisper*"):
                if p.is_file() and os.access(p, os.X_OK):
                    whisper_bin = p
                    break
        if whisper_bin.exists():
            model = whisper_dir / "models" / "ggml-small.en.bin"
            if model.exists():
                subprocess.run(
                    [str(whisper_bin), "-f", audio_path, "-m", str(model), "-l", "en",
                     "-o", "json", "-of", str(Path(audio_path).with_suffix("")),
                     "--output-json"],
                    capture_output=True, text=True, timeout=180,
                )
                json_path = Path(audio_path).with_suffix(".json")
                if json_path.exists():
                    data = json.loads(json_path.read_text())
                    segments = data.get("transcription", []) if isinstance(data, dict) else []
                    words, text_parts = [], []
                    for seg in segments:
                        text = seg.get("text", "").strip()
                        text_parts.append(text)
                        for w in seg.get("words", []):
                            words.append({"word": w.get("word",""), "start": w.get("start",0), "end": w.get("end",0)})
                    return {"words": words, "text": " ".join(text_parts), "source": "whisper.cpp"}

    # Fallback: openai-whisper pip package
    try:
        import whisper
        model = whisper.load_model("small.en")
        result = model.transcribe(audio_path, fp16=False)
        words = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                words.append({"word": w.get("word",""), "start": w.get("start",0), "end": w.get("end",0)})
        return {"words": words, "text": result.get("text","").strip(), "source": "openai-whisper"}
    except ImportError:
        return {"words": [], "text": "", "source": "none",
                "note": "whisper not installed; word-level timing unavailable (audio-only metrics still computed)"}


def compute_metrics(words: list[dict], total_audio_duration: float, text: str, audio_path: str | None = None) -> dict:
    """Compute delivery metrics from whisper word timings + audio waveform analysis."""
    # Waveform-only metrics (work without whisper)
    waveform = {}
    if audio_path and Path(audio_path).exists():
        waveform = _audio_waveform_stats(audio_path)

    if not words and not waveform:
        return {"error": "no data available (whisper not installed and no waveform stats)"}

    # Word-level metrics (need whisper)
    word_metrics = {}
    if words:
        word_count = len(words)
        speech_start = words[0].get("start", 0)
        speech_end = words[-1].get("end", speech_start)
        speech_duration = speech_end - speech_start
        wpm = round(word_count / (speech_duration / 60)) if speech_duration > 0 else 0

        pauses = []
        for i in range(1, len(words)):
            gap = words[i].get("start", 0) - words[i-1].get("end", 0)
            if gap > 0.3:
                pauses.append(round(gap, 2))
        pause_density = round(len(pauses) / (speech_duration / 60)) if speech_duration > 0 else 0

        durations = [w.get("end",0) - w.get("start",0) for w in words if w.get("end",0) > w.get("start",0)]
        if durations:
            median_dur = statistics.median(durations)
            emphasis_words = [w["word"] for w in words if (w.get("end",0)-w.get("start",0)) > median_dur * 1.5]
        else:
            emphasis_words = []

        sentences = len(re.findall(r'[.!?]+', text)) if text else 0

        word_metrics = {
            "word_count": word_count,
            "speech_duration_s": round(speech_duration, 2),
            "wpm": wpm,
            "pause_count": len(pauses),
            "pause_density_per_min": pause_density,
            "avg_pause_duration_s": round(statistics.mean(pauses), 2) if pauses else 0,
            "emphasis_words": emphasis_words[:20],
            "emphasis_word_count": len(emphasis_words),
            "sentence_count": sentences,
            "avg_words_per_sentence": round(word_count / sentences, 1) if sentences > 0 else 0,
        }

    result = {**word_metrics, **waveform}
    if not word_metrics:
        result["note"] = "whisper not available; word-level metrics unavailable (waveform stats only)"
    return result


def _audio_waveform_stats(audio_path: str) -> dict:
    """Extract audio statistics from waveform using ffmpeg astats. No whisper needed."""
    ff = _ffmpeg_exe()
    # Use ffmpeg astats to get RMS levels, silence detection
    p = subprocess.run(
        [ff, "-i", audio_path, "-af",
         "silencedetect=noise=-30dB:d=0.3,astats=metadata=1:reset=1",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=60,
    )
    out = p.stderr
    # Parse silence detection
    silence_starts = re.findall(r"silence_start:\s*([\d.]+)", out)
    silence_ends = re.findall(r"silence_end:\s*([\d.]+)", out)
    silence_durations = []
    for start, end in zip(silence_starts, silence_ends):
        silence_durations.append(float(end) - float(start))

    # Parse RMS level
    rms_match = re.findall(r"RMS level dB:\s*([\-\d.]+)", out)
    rms_avg = round(statistics.mean([float(x) for x in rms_match]), 2) if rms_match else -99

    # Parse peak level
    peak_match = re.findall(r"Peak level dB:\s*([\-\d.]+)", out)
    peak = round(max([float(x) for x in peak_match]), 2) if peak_match else -99

    # Get total duration
    dur = get_audio_duration(audio_path)

    silence_total = sum(silence_durations)
    silence_pct = round((silence_total / dur) * 100, 1) if dur > 0 else 0

    return {
        "total_audio_duration_s": round(dur, 2),
        "silence_count": len(silence_durations),
        "silence_total_s": round(silence_total, 2),
        "silence_pct": silence_pct,
        "rms_level_db": rms_avg,
        "peak_level_db": peak,
        "source": "ffmpeg-astats",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", help="video file path or YouTube URL")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--download", action="store_true", help="download YouTube URL via yt-dlp")
    a = ap.parse_args()

    # Handle YouTube URL
    video_path = a.video
    if a.video.startswith("http") and not Path(a.video).exists():
        if not a.download:
            print("Use --download to fetch YouTube URLs", file=sys.stderr)
            return 1
        with tempfile.TemporaryDirectory() as td:
            video_path = td + "/video.mp4"
            subprocess.run(
                ["yt-dlp", "-f", "worst[ext=mp4]/worst", "-o", video_path,
                 "--no-playlist", a.video],
                capture_output=True, check=True, timeout=180,
            )

    if not Path(video_path).exists():
        print(f"Video not found: {video_path}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as td:
        audio_path = td + "/audio.wav"
        extract_audio(video_path, audio_path)
        duration = get_audio_duration(audio_path)
        result = whisper_transcribe(audio_path)
        metrics = compute_metrics(result["words"], duration, result["text"], audio_path)

    if a.json:
        print(json.dumps({"metrics": metrics, "text": result["text"]}, indent=2))
    else:
        print(f"Audio delivery analysis: {video_path}")
        print(f"  word count:          {metrics.get('word_count', '?')}")
        print(f"  speech duration:     {metrics.get('speech_duration_s', '?')}s")
        print(f"  WPM:                 {metrics.get('wpm', '?')}")
        print(f"  pause count:         {metrics.get('pause_count', '?')}")
        print(f"  pause density:       {metrics.get('pause_density_per_min', '?')}/min")
        print(f"  avg pause duration:  {metrics.get('avg_pause_duration_s', '?')}s")
        print(f"  emphasis words:      {metrics.get('emphasis_words', [])}")
        print(f"  silence %:           {metrics.get('silence_pct', '?')}")
        print(f"  sentences:           {metrics.get('sentence_count', '?')}")
        print(f"  avg words/sentence:  {metrics.get('avg_words_per_sentence', '?')}")
        if result["text"]:
            print(f"\n  transcript: {result['text'][:200]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())