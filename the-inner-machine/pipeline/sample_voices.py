#!/usr/bin/env python3
"""Generate 10-15s Kokoro samples for all English voices (resume-safe)."""
import os, subprocess, sys
from kokoro_onnx import Kokoro
import soundfile as sf
FF = subprocess.check_output([sys.executable, "-c",
      "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()
TEXT = "Ever wonder where your dreams actually come from? Not from some faraway place. From right here, your own brain. In REM sleep, the brainstem fires random sparks, and your cortex weaves them into a story."
k = Kokoro(".cache/kokoro/kokoro-v1.0.int8.onnx", ".cache/kokoro/voices-v1.0.bin")
en = [v for v in k.get_voices() if v[:2] in ("af", "am", "bf", "bm")]
print("total english:", len(en), flush=True)
for v in en:
    w = f"/tmp/{v}.wav"
    if not os.path.exists(w):
        lang = "en-gb" if v[0] == "b" else "en-us"
        audio, sr = k.create(TEXT, voice=v, speed=1.0, lang=lang)
        sf.write(w, audio, sr)
        print("synth", v, round(len(audio)/sr, 1), "s", flush=True)
    else:
        print("skip", v, flush=True)
# convert all to mp3
for v in en:
    out = f"voices/{v}.mp3"
    if not os.path.exists(out):
        subprocess.run([FF, "-y", "-i", f"/tmp/{v}.wav", "-q:a", "4", out],
                       capture_output=True)
        print("mp3", v, flush=True)
print("ALL DONE", flush=True)
