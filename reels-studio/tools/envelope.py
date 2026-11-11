#!/usr/bin/env python3
"""Amplitude envelope of an audio file, for animated waveforms in split scenes.

  python3 tools/envelope.py <audio.wav|mp3> <out.json> [--bars 48]

Decodes with the ffmpeg binary from imageio-ffmpeg (or $FFMPEG), computes RMS per
1/30 s frame, and writes {"fps": 30, "duration": s, "levels": [0..1, ...]}.
Levels are normalised to the file's own peak so quiet and loud clips both fill the
panel. Only the audio's own samples are used: nothing is synthesised.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

FPS = 30
SR = 16000


def ffmpeg_exe():
    if os.environ.get("FFMPEG"):
        return os.environ["FFMPEG"]
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def decode(path):
    cmd = [ffmpeg_exe(), "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
           "-f", "s16le", "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def envelope(x):
    hop = SR // FPS
    n = len(x) // hop
    if n == 0:
        return []
    frames = x[: n * hop].reshape(n, hop)
    rms = np.sqrt((frames ** 2).mean(axis=1))
    # light smoothing so bars move like speech, not like noise
    k = np.array([0.25, 0.5, 0.25])
    rms = np.convolve(rms, k, mode="same")
    peak = float(rms.max()) or 1.0
    return [round(float(v) / peak, 3) for v in rms]


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    src, out = Path(argv[0]), Path(argv[1])
    levels = envelope(decode(src))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"fps": FPS, "duration": round(len(levels) / FPS, 3),
                               "source": src.name, "levels": levels}), encoding="utf-8")
    print(f"{out}: {len(levels)} frames ({len(levels) / FPS:.2f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
