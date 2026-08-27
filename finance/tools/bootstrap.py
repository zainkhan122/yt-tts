#!/usr/bin/env python3
"""bootstrap.py — self-heal after a session reset. Run at the start of every BUILD session."""
import importlib, os, shutil, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DEPS = [
    ("numpy", "numpy"),
    ("matplotlib", "matplotlib"),
    ("PIL", "pillow"),
    ("imageio_ffmpeg", "imageio-ffmpeg"),
]

def sh(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode != 0:
        print("FAILED:", " ".join(args)[:120])
        print((r.stderr or "")[-800:])
        sys.exit(1)
    return r

print("== 1. pip ==")
for mod, pkg in DEPS:
    try:
        importlib.import_module(mod)
        print(f"  ok  {mod}")
    except ImportError:
        print(f"  installing {pkg} ...")
        sh([sys.executable, "-m", "pip", "install", "--quiet", pkg])

print("== 2. binaries ==")
try:
    ff = subprocess.check_output(
        [sys.executable, "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]
    ).decode().strip()
except Exception as e:
    ff = shutil.which("ffmpeg") or f"MISSING ({e})"
print("  ffmpeg:", ff)
print("  magick:", shutil.which("magick") or "MISSING")
print("  font:", "ok" if os.path.exists(FONT) else "MISSING")

print("== 3. secrets ==")
for p in [os.path.join(ROOT, "secrets/github_pat.txt"),
          os.path.expanduser("~/secrets/github_pat.txt")]:
    print(f"  {'ok' if os.path.exists(p) else 'MISSING — ASK USER':28s} {p}")

print("== 4. pre-flight ==")
for d in ["/tmp/finance-yt", "/tmp/yt-tts-vault"]:
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)
        print("  cleaned", d)
df = sh(["df", "-h", "/tmp"], check=False).stdout.strip().split("\n")[-1]
du = sh(["du", "-sh", ROOT], check=False).stdout.split()[0]
print("  /tmp     ->", df)
print("  project  ->", du)
print("\nbootstrap DONE")
