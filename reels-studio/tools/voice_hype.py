#!/usr/bin/env python3
"""Enthusiasm audition for af_heart: energetic (B) vs hype (D) vs hype+bright (E), line by line exactly like the pipeline
(per-line accents for 'hype', then the preset chain).  -> research/voice-audition/enthusiastic/"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib import pipeline  # noqa: E402

LINES = ["Okay, this AI just put Minecraft inside GTA Five!",
         "And no, it's not a mod pack.",
         "An AI coding agent built the whole thing!",
         "The best part?",
         "It's free, it's open source, and it hit almost five thousand GitHub stars in one week!"]
SAMPLES = [("B-energetic", 1.28, None, "energetic", "last version: faster + creator-mic chain"),
           ("D-hype", 1.33, None, "hype", "more enthusiastic: per-line melody accents, +0.8 st lift, stronger punch"),
           ("E-hype-bright", 1.33, {"af_bella": 0.3}, "hype", "D + 30% af_bella brightness")]


def main():
    out = ROOT / "research/voice-audition/enthusiastic"
    out.mkdir(parents=True, exist_ok=True)
    rows, parts = [], []
    words = sum(len(l.split()) for l in LINES)
    for name, speed, blend, fx, note in SAMPLES:
        spk = pipeline.KokoroVoice("af_heart", speed, "en-us", blend=blend)
        acc = pipeline.hype_accents(LINES) if fx == "hype" else [0] * len(LINES)
        chunks = []
        for line, semis in zip(LINES, acc):
            a, sr = spk(line)
            chunks += [pipeline.pitch_accent(np.asarray(a, dtype=np.float32), sr, semis), np.zeros(int(0.12 * sr), dtype=np.float32)]
        vo = pipeline.apply_voice_fx(np.concatenate(chunks), sr, fx)
        wav = Path(f"/var/tmp/{name}.wav")
        sf.write(wav, vo, sr)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", "loudnorm=I=-15:TP=-1.5", "-ac", "1", "-b:a", "80k", str(out / f"{name}.mp3")], check=True)
        dur = len(vo) / sr
        rows.append(f"| {name} | ×{speed}{' + ' + str(blend) if blend else ''} | {fx} | {words / dur * 60:.0f} wpm | {note} |")
        parts.append(wav)
        print(f"  {name}: {dur:.1f}s, {words / dur * 60:.0f} wpm")
    pipeline.release_tts()
    sil = Path("/var/tmp/sil.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "1.0", str(sil)], check=True)
    lst = Path("/var/tmp/hype-list.txt")
    lst.write_text("".join(f"file '{p}'\nfile '{sil}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-af", "loudnorm=I=-15:TP=-1.5",
                    "-ac", "1", "-b:a", "80k", str(out / "00-B-D-E-in-order.mp3")], check=True)
    (out / "index.md").write_text("# More enthusiastic af_heart: B vs D vs E\n\nListen to `00-B-D-E-in-order.mp3` (B, then D, then E).\n\n"
                                  "Script lines:\n" + "\n".join(f"- {l}" for l in LINES) +
                                  "\n\n| Sample | Speed / blend | Preset | Pace | Note |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    print("-> research/voice-audition/enthusiastic/")


if __name__ == "__main__":
    main()
