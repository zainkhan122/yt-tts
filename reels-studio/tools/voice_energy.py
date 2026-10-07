#!/usr/bin/env python3
"""Energetic-voice audition for the channel voice (af_heart): neutral vs energetic vs energetic+bright.
Uses the pipeline's own KokoroVoice (+blend) and apply_voice_fx, so what you hear is what renders get.
  python3 tools/voice_energy.py   -> research/voice-audition/energetic/"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib import pipeline  # noqa: E402

PLAIN = ("This AI just put Minecraft inside GTA Five. It's free, it's open source, "
         "and it hit almost five thousand GitHub stars in one week. Here's how it works.")
ENERGY = ("This AI just put Minecraft inside GTA Five! It's free, it's open source, "
          "and it hit almost five thousand GitHub stars in one week! Here's how it works.")
SAMPLES = [("A-neutral", "af_heart", 1.15, None, None, PLAIN, "current neutral read"),
           ("B-energetic", "af_heart", 1.28, None, "energetic", ENERGY, "faster, punchy punctuation, creator-mic chain"),
           ("C-energetic-bright", "af_heart", 1.28, {"af_bella": 0.25}, "energetic", ENERGY, "B + 25% af_bella brightness")]


def main():
    out = ROOT / "research/voice-audition/energetic"
    out.mkdir(parents=True, exist_ok=True)
    rows, parts = [], []
    for name, voice, speed, blend, fx, text, note in SAMPLES:
        audio, sr = pipeline.KokoroVoice(voice, speed, "en-us", blend=blend)(text)
        audio = pipeline.apply_voice_fx(np.asarray(audio, dtype=np.float32), sr, fx)
        wav = Path(f"/var/tmp/{name}.wav")
        sf.write(wav, audio, sr)
        mp3 = out / f"{name}.mp3"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", "loudnorm=I=-15:TP=-1.5", "-ac", "1", "-b:a", "80k", str(mp3)], check=True)
        dur = len(audio) / sr
        rows.append(f"| {name} | `{voice}` ×{speed}{' + ' + str(blend) if blend else ''} | {fx or 'none'} | {len(text.split()) / dur * 60:.0f} wpm | {note} |")
        parts.append(wav)
        print(f"  {name}: {dur:.1f}s, {len(text.split()) / dur * 60:.0f} wpm")
    pipeline.release_tts()
    sil = Path("/var/tmp/sil.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.9", str(sil)], check=True)
    lst = Path("/var/tmp/energy-list.txt")
    lst.write_text("".join(f"file '{p}'\nfile '{sil}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-af", "loudnorm=I=-15:TP=-1.5",
                    "-ac", "1", "-b:a", "80k", str(out / "00-A-B-C-in-order.mp3")], check=True)
    (out / "index.md").write_text("# Energetic af_heart: A/B/C\n\nListen to `00-A-B-C-in-order.mp3` (A, then B, then C).\n\n"
                                  "| Sample | Voice | Chain | Pace | Note |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    print("-> research/voice-audition/energetic/")


if __name__ == "__main__":
    main()
