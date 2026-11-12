#!/usr/bin/env python3
"""Trim a capture clip to its longest clean (non-blank) window, using the gate's own measurement.

Why: headless recordings open on white heroes / loading states and end on empty page background.
Re-recording does not fix that reliably — measuring and cutting does. Any clip that cannot yield
a clean window >= MIN_WINDOW seconds is deleted, so the renderer can never reach for it.

  python3 tools/clip_trim.py captures/<id>/*.mp4 [--min 3.0] [--dry-run]
"""
from __future__ import annotations

import subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui_proof_gate as gate  # noqa: E402  (reuses probe/stats/_is_blank/FF)

MIN_WINDOW = 3.0     # a scene needs at least this much usable screen time


def clean_windows(path: Path, fps: float = 2.5):
    dur = gate.probe(path).get("duration") or 0
    if dur <= 0:
        return [], 0.0
    flags, t = [], 0.0
    with tempfile.TemporaryDirectory() as tmp:
        i = 0
        while t < dur:
            f = Path(tmp) / f"c{i}.png"
            gate._run([gate.FF, "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(path),
                       "-frames:v", "1", "-vf", "scale=200:-2", str(f)])
            blank = True
            if f.exists():
                with gate.Image.open(f) as im:
                    blank = gate._is_blank(gate.stats(im.convert("RGB")))
            flags.append(not blank)
            t += 1.0 / fps
            i += 1
    # longest run of non-blank
    best, best_start, run, start = 0, 0.0, 0, 0.0
    for idx, ok in enumerate(flags):
        if ok:
            if run == 0:
                start = idx / fps
            run += 1
            if run > best:
                best, best_start = run, start
        else:
            run = 0
    return flags, best / fps, best_start


def trim(path: Path, dry: bool) -> bool:
    flags, length, start = clean_windows(path)
    if length < MIN_WINDOW:
        print(f"  DELETE {path.name}: longest clean window {length:.1f}s < {MIN_WINDOW}s")
        if not dry:
            path.unlink()
        return False
    total = len(flags) / 2.5
    if start <= 0.4 and length >= total - 0.8:
        print(f"  keep   {path.name}: clean {length:.1f}s / {total:.1f}s")
        return True
    print(f"  trim   {path.name}: keep {start:.1f}s..{start + length:.1f}s of {total:.1f}s")
    if dry:
        return True
    tmp = path.with_suffix(".trim.mp4")
    subprocess.run([gate.FF, "-y", "-loglevel", "error", "-ss", f"{start:.2f}",
                    "-i", str(path), "-t", f"{length:.2f}", "-c:v", "libx264",
                    "-preset", "fast", "-crf", "22", "-an", "-movflags", "+faststart",
                    str(tmp)], check=True)
    tmp.replace(path)
    _, after, _ = clean_windows(path)
    print(f"         -> {path.name} now {after:.1f}s clean")
    return after >= MIN_WINDOW


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    files = [Path(a) for a in sys.argv[1:] if not a.startswith("--")]
    for f in files:
        trim(f, dry)
