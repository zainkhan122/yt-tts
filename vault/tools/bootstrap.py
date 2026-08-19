#!/usr/bin/env python3
"""bootstrap.py — one-shot SELF-HEAL after a session reset.

Run this FIRST at the start of every build session. The sandbox loses pip
packages, ~/.cache/kokoro and /tmp on reset — but NOT workspace files
(tools/, reusable/, secrets/, MASTER_RULES.md, VIDEO_QUEUE.md).

It:
  1. reinstalls pip deps (kokoro-onnx, soundfile, imageio-ffmpeg)
  2. re-downloads the Kokoro voice model + voices (only if missing)
  3. verifies ffmpeg + fonts + ImageMagick exist
  4. checks secrets (github_pat.txt, .pexels_key) — warns if missing
  5. cleans /tmp clone dirs + prints pre-flight (df /tmp, du /home/user)

Usage: python3 tools/bootstrap.py
"""
import importlib, os, shutil, subprocess, sys

CACHE = os.path.expanduser("~/.cache/kokoro")
MODEL = os.path.join(CACHE, "kokoro-v0_19.onnx")
VOICES = os.path.join(CACHE, "voices-v1.0.bin")
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def sh(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode != 0:
        print("FAILED:", " ".join(args)[:120])
        print(r.stderr[-800:])
        sys.exit(1)
    return r

print("== 1. pip deps ==")
for mod, pkg in [("kokoro_onnx", "kokoro-onnx"), ("soundfile", "soundfile"),
                 ("imageio_ffmpeg", "imageio-ffmpeg")]:
    try:
        importlib.import_module(mod)
        print(f"  ok  {mod}")
    except ImportError:
        print(f"  installing {pkg} ...")
        sh([sys.executable, "-m", "pip", "install", "--quiet", pkg])

print("== 2. kokoro model + voices ==")
os.makedirs(CACHE, exist_ok=True)
for path, url, tmo in [(MODEL, MODEL_URL, 550), (VOICES, VOICES_URL, 120)]:
    if os.path.exists(path) and os.path.getsize(path) > 0:
        print(f"  ok  {os.path.basename(path)} ({os.path.getsize(path)//1024} KB)")
    else:
        print(f"  downloading {os.path.basename(path)} ...")
        sh(["curl", "-sL", "--retry", "5", "--max-time", str(tmo), "-o", path, url])
        if os.path.getsize(path) == 0:
            print(f"  ⚠ empty download: {path}"); sys.exit(1)

print("== 3. binaries ==")
ff = subprocess.check_output(
    ["python3", "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]
).decode().strip()
print("  ffmpeg:", ff)
print("  font:", "ok" if os.path.exists(FONT) else "⚠ MISSING", FONT)
print("  magick:", shutil.which("magick") or "⚠ MISSING")

print("== 4. secrets ==")
for p in ["~/secrets/github_pat.txt", "~/.pexels_key"]:
    full = os.path.expanduser(p)
    state = "ok" if os.path.exists(full) else "⚠ MISSING — ASK USER"
    print(f"  {state:30s} {p}")

print("== 5. /tmp cleanup + pre-flight ==")
for d in ["/tmp/yt-tts-vault"]:
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)
        print("  cleaned", d)
df = sh(["df", "-h", "/tmp"], check=False).stdout.strip().split("\n")[-1]
du = sh(["du", "-sh", "/home/user"], check=False).stdout.split()[0]
print("  /tmp      ->", df)
print("  workspace ->", du, "(snapshot cap ~128MB)")

print("\nbootstrap DONE — ready to build.")
