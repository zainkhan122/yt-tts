#!/usr/bin/env python3
"""Run L1–L8 gates. Fail loud.
Usage: python3 tools/gate.py EPISODE_DIR [keyword] [--shorts]
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ep = Path(sys.argv[1])
rest = sys.argv[2:]
fails = 0


def run(label, args):
    global fails
    print(f"\n== {label} ==")
    r = subprocess.run([sys.executable, *args])
    if r.returncode != 0:
        print(f"GATE FAIL: {label}")
        fails += 1
    return r.returncode


run("L1/L2 script", [str(ROOT / "tools/check_script.py"), str(ep)])
run("L3/L6/L8 pack", [str(ROOT / "tools/qa_pack.py"), str(ep), *rest])
if "--shorts" not in rest:
    run("L3/L4 episode", [str(ROOT / "tools/verify.py"), "episode", str(ep)])
sys.exit(1 if fails else 0)
