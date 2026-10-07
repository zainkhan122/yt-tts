#!/usr/bin/env python3
"""
Voice audition: the same hook read by several Kokoro voices (+ a speed comparison) so the channel voice is
chosen by ear, once, then fixed in config/channel.json.  Output: research/voice-audition/ (MP3 + index.md).

  python3 tools/voice_audition.py
"""
import subprocess
import sys
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib import pipeline  # noqa: E402

TEXT = ("An AI coding agent built this: real Minecraft, running inside GTA Five. "
        "It's free, open source, and it got almost five thousand GitHub stars in its first week.")
# (voice, speed, note). Kokoro's own quality grades: af_heart A, af_bella A-, bf_emma B-, am_michael C+, am_puck C+
CANDIDATES = [("af_heart", 1.15, "US female, Kokoro grade A (current default)"),
              ("af_bella", 1.15, "US female, grade A-, brighter"),
              ("bf_emma", 1.15, "UK female, grade B-"),
              ("am_michael", 1.15, "US male, grade C+, calm"),
              ("am_puck", 1.15, "US male, grade C+, energetic"),
              ("af_heart", 1.05, "speed test: our old pace"),
              ("af_heart", 1.30, "speed test: TikTok-creator pace")]


def main():
    out = ROOT / "research/voice-audition"
    out.mkdir(parents=True, exist_ok=True)
    rows, parts = [], []
    words = len(TEXT.split())
    for i, (voice, speed, note) in enumerate(CANDIDATES, 1):
        audio, sr = pipeline.KokoroVoice(voice, speed, "en-us")(pipeline.spoken_clean(TEXT) if hasattr(pipeline, "spoken_clean") else TEXT)
        wav = Path("/var/tmp") / f"aud-{i}.wav"
        sf.write(wav, audio, sr)
        dur = len(audio) / sr
        name = f"{i:02d}-{voice}-x{speed:.2f}.mp3"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5", "-ac", "1", "-b:a", "64k", str(out / name)], check=True)
        parts.append(wav)
        rows.append(f"| {i} | `{voice}` | ×{speed:.2f} | {dur:.1f} s | {words / dur * 60:.0f} | {note} | [{name}]({name}) |")
        print(f"  {i}. {voice} x{speed}: {dur:.1f}s, {words / dur * 60:.0f} wpm")
    pipeline.release_tts()
    # one file to listen to everything in order (0.8 s gaps)
    lst = Path("/var/tmp/aud-list.txt")
    sil = Path("/var/tmp/aud-sil.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.8", str(sil)], check=True)
    lst.write_text("".join(f"file '{p}'\nfile '{sil}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-af", "loudnorm=I=-16:TP=-1.5",
                    "-ac", "1", "-b:a", "64k", str(out / "00-all-voices-in-order.mp3")], check=True)
    (out / "index.md").write_text(
        "# Voice audition: pick the channel voice\n\n"
        f"Line: \"{TEXT}\"\n\n"
        "Listen to `00-all-voices-in-order.mp3`, which plays the samples in the table's order with short gaps.\n\n"
        "| # | Voice | Speed | Length | Words/min | Note | File |\n|---|---|---|---|---|---|---|\n" + "\n".join(rows) +
        "\n\nBenchmark from the social scan: top TikTok AI-tool creators speak at **~170–230 wpm** (`research/social/index.csv`).\n")
    print("-> research/voice-audition/")


if __name__ == "__main__":
    main()
