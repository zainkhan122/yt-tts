#!/usr/bin/env python3
"""Free TTS generator — Kokoro 82M, runs locally.
Usage: python3 tools/tts_generate.py <textfile> <output.mp3> [voice] [speed]

Example:
  python3 tools/tts_generate.py videos/video_002/voiceover.txt videos/video_002/voiceover.mp3 af_heart 1.0
"""
import os, sys, subprocess, time

CACHE = os.path.expanduser("~/.cache/kokoro")
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
MODEL = os.path.join(CACHE, "kokoro-v0_19.onnx")
VOICES = os.path.join(CACHE, "voices-v1.0.bin")

def ensure_model():
    os.makedirs(CACHE, exist_ok=True)
    if not os.path.exists(MODEL):
        print("downloading kokoro model (325MB)...")
        subprocess.run(["curl","-sL","--max-time","550","-o",MODEL,MODEL_URL], check=True)
    if not os.path.exists(VOICES):
        print("downloading voices (28MB)...")
        subprocess.run(["curl","-sL","--max-time","120","-o",VOICES,VOICES_URL], check=True)

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    textfile = sys.argv[1]; out = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "af_heart"
    speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0

    ensure_model()
    import soundfile as sf
    from kokoro_onnx import Kokoro
    kokoro = Kokoro(MODEL, VOICES)
    text = open(textfile, encoding="utf-8").read()
    t = time.time()
    samples, sr = kokoro.create(text, voice=voice, speed=speed, lang="en-us")
    print(f"generated {len(samples)/sr:.1f}s audio in {time.time()-t:.1f}s")
    tmp = out + ".wav"
    sf.write(tmp, samples, sr)
    # mp3 encode via ffmpeg (bundled binary)
    ff = subprocess.check_output(["python3","-c","import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()
    subprocess.run([ff,"-y","-i",tmp,"-codec:a","libmp3lame","-b:a","128k","-ac","1",out], check=True, capture_output=True)
    os.remove(tmp)
    print("saved:", out)

if __name__ == "__main__":
    main()
