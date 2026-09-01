#!/usr/bin/env python3
"""verify.py — L4 artifacts, L5 shot cap, L3 thumb, disk.
Usage:
  python3 tools/verify.py preflight
  python3 tools/verify.py episode EP_DIR
  python3 tools/verify.py pack EP_DIR [keyword] [--shorts]
"""
import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def preflight():
    df = subprocess.check_output(["df", "-h", "/tmp"], text=True).strip().split("\n")[-1]
    du = subprocess.check_output(["du", "-sh", str(ROOT)], text=True).split()[0]
    print("/tmp :", df)
    print("proj :", du)
    print("PAT  :", "ok" if (ROOT / "secrets/github_pat.txt").exists() else "MISSING")


def episode(ep: Path):
    fails = []
    art = ep / "artifacts"
    files = list(art.glob("*")) if art.exists() else []
    files = [p for p in files if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".pdf"}]
    print(f"L4 artifacts: {len(files)} in {art}")
    if len(files) < 3:
        fails.append("L4 need ≥3 files in artifacts/ (headline, filing, photo)")
    if not (ep / "artifacts.md").exists() and not (art / "artifacts.md").exists():
        fails.append("L4 artifacts.md missing (must cite each file)")
    thumb = ep / "thumbnail.jpg"
    if thumb.exists():
        r = subprocess.run([sys.executable, str(ROOT / "tools/thumb_test.py"), str(thumb)])
        if r.returncode != 0:
            fails.append("L3 thumb_test failed")
    else:
        fails.append("no thumbnail.jpg")
    seq = Path("/tmp/e02live/seq.json")
    # generic seq next to episode
    for cand in [ep / "seq.json", Path("/tmp") / "cut_seq.json"]:
        if cand.exists():
            import json
            shots = json.loads(cand.read_text())
            long = [s for s in shots if float(s.get("len", 0)) > 7.01]
            print(f"L5 shots {len(shots)} over-7s {len(long)}")
            if long:
                fails.append(f"L5 {len(long)} shots longer than 7s (loop)")
            break
    if fails:
        for f in fails:
            print("  FAIL:", f)
        sys.exit(1)
    print("EPISODE VERIFY OK")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "preflight"
    if cmd == "preflight":
        preflight()
    elif cmd == "episode":
        episode(Path(sys.argv[2]))
    elif cmd == "pack":
        os.execv(sys.executable, [sys.executable, str(ROOT / "tools/qa_pack.py"), *sys.argv[2:]])
    else:
        sys.exit(f"unknown {cmd}")
