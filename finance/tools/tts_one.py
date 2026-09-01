#!/usr/bin/env python3
"""One paragraph, one process, then exit (frees RAM)."""
import os, sys
CACHE = os.environ.get("KOKORO_CACHE", "/home/user/.cache/kokoro")
MODEL = os.path.join(CACHE, "kokoro-v0_19.onnx")
VOICES = os.path.join(CACHE, "voices-v1.0.bin")
text = open(sys.argv[1], encoding="utf-8").read().strip()
out, voice = sys.argv[2], sys.argv[3]
import soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro(MODEL, VOICES)
samples, sr = k.create(text, voice=voice, speed=1.0, lang="en-us")
sf.write(out, samples, sr)
print(f"ok {len(samples)/sr:.1f}s", flush=True)
