#!/usr/bin/env python3
"""verify.py — F17/F1/F9 helpers.
Usage:
  python3 tools/verify.py preflight
  python3 tools/verify.py pack VIDEO_DIR [keyword] [--shorts]
"""
import os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def preflight():
    df = subprocess.check_output(["df", "-h", "/tmp"], text=True).strip().split("\n")[-1]
    du = subprocess.check_output(["du", "-sh", ROOT], text=True).split()[0]
    print("F17 /tmp :", df)
    print("F17 proj :", du)
    pat = os.path.join(ROOT, "secrets/github_pat.txt")
    print("PAT      :", "ok" if os.path.exists(pat) else "MISSING")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "preflight"
    if cmd == "preflight":
        preflight()
    elif cmd == "pack":
        os.execv(sys.executable, [sys.executable, os.path.join(ROOT, "tools/qa_pack.py"), *sys.argv[2:]])
    else:
        sys.exit(f"unknown {cmd}")
