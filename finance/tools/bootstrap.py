#!/usr/bin/env python3
"""bootstrap.py — start of every BUILD session."""
import importlib, os, shutil, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DEPS = [
    ("PIL", "pillow"),
    ("imageio_ffmpeg", "imageio-ffmpeg"),
    ("soundfile", "soundfile"),
]

def sh(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode != 0:
        print("FAILED:", " ".join(args)[:120])
        print((r.stderr or "")[-800:])
        sys.exit(1)
    return r

print("== pip ==")
for mod, pkg in DEPS:
    try:
        importlib.import_module(mod)
        print(f"  ok  {mod}")
    except ImportError:
        print(f"  installing {pkg} ...")
        sh([sys.executable, "-m", "pip", "install", "--quiet", pkg])

print("== /tmp junk ==")
for d in ["/tmp/e01live", "/tmp/e02live", "/tmp/cut_long", "/tmp/e02caps",
          "/tmp/finance-yt", "/tmp/yt-tts-vault"]:
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)
        print("  cleaned", d)

print("== preflight ==")
df = sh(["df", "-h", "/tmp"], check=False).stdout.strip().split("\n")[-1]
du = sh(["du", "-sh", ROOT], check=False).stdout.split()[0]
print("  /tmp    ", df)
print("  project ", du)
print("bootstrap DONE — next: python3 tools/gate.py EP_DIR KEYWORD")
