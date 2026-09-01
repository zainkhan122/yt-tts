#!/usr/bin/env python3
"""Kokoro TTS like yt-tts: ONE model, paragraph wavs on disk, ffmpeg concat.
Never keep the full show in RAM (2GB box).
"""
import gc, os, sys, time, subprocess
from pathlib import Path

CACHE = os.environ.get("KOKORO_CACHE", "/home/user/.cache/kokoro")
MODEL = os.path.join(CACHE, "kokoro-v0_19.onnx")
VOICES = os.path.join(CACHE, "voices-v1.0.bin")
WORK = Path("/tmp/kokoro_parts")

def ff():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def main():
    textfile, out = sys.argv[1], sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "am_michael"
    speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    text = open(textfile, encoding="utf-8").read().strip()
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    print("paras", len(paras), "voice", voice, flush=True)
    import soundfile as sf
    from kokoro_onnx import Kokoro
    print("loading...", flush=True)
    kokoro = Kokoro(MODEL, VOICES)
    print("loaded", flush=True)
    WORK.mkdir(exist_ok=True)
    for p in WORK.glob("*.wav"):
        p.unlink()
    t0 = time.time()
    files = []
    for i, para in enumerate(paras):
        samples, sr = kokoro.create(para, voice=voice, speed=speed, lang="en-us")
        path = WORK / f"p{i:02d}.wav"
        sf.write(str(path), samples, sr)
        files.append(path)
        print(f"p{i:02d} {len(samples)/sr:.1f}s", flush=True)
        del samples
        gc.collect()
    lst = WORK / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in files))
    subprocess.run([ff(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:a", "pcm_s16le", out], check=True, capture_output=True)
    print(f"wrote {out} in {time.time()-t0:.1f}s", flush=True)
    for p in files:
        p.unlink()

if __name__ == "__main__":
    main()
