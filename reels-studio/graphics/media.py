"""Media helpers for the graphics tier: cut still frames out of a captured screen recording.

WHY THIS EXISTS (owner rule, 2026-11-12): a short about a tool must SHOW the tool. The house
renderer draws its own pages, and a page of drawn type is not proof — the UI proof gate refuses
a short whose scenes reference no product evidence at all.

The capture packs hold real screen recordings (a phone-shaped capture of the tool's own page).
This module cuts deterministic JPEG stills out of one so a scene can paste the real product UI on
the page and advance through it. Nothing is fetched from the network: the frames come from the
capture pack that the production receipt pins by hash.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

_DUR_RE = re.compile(r"Duration:\s*(\d+):(\d{2}):(\d{2})\.(\d+)")
FRAME_COUNT = 5          # stills cut from one recording
FRAME_WIDTH = 1080       # the capture is 1080 wide; keep it (the page type has to stay readable)


def ffmpeg_exe() -> str:
    """The ffmpeg binary: the one on PATH, else the pip wheel (CI ships no system ffmpeg)."""
    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def clip_duration(path: Path) -> float:
    """Duration in seconds, read from the ffmpeg banner.

    The banner works on every ffmpeg build, including imageio-ffmpeg, which has no ffprobe.
    """
    r = subprocess.run([ffmpeg_exe(), "-i", str(path)], capture_output=True, text=True, timeout=180)
    m = _DUR_RE.search(r.stderr or "")
    if not m:
        return 0.0
    h, mi, s, frac = m.groups()
    return int(h) * 3600 + int(mi) * 60 + int(s) + float("0." + frac)


def clip_frames(path: Path, count: int = FRAME_COUNT, width: int = FRAME_WIDTH) -> list[bytes]:
    """`count` JPEG stills spread across the clip.

    The first 8% is skipped (that is the load-in, before the page has any content) and the frames
    are cut by decode-then-seek, so every still is the frame the recording really shows.
    """
    dur = clip_duration(path)
    if dur <= 0:
        return []
    out: list[bytes] = []
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(count):
            t = dur * (0.08 + 0.84 * (i + 0.5) / count)
            dst = Path(tmp) / f"f{i:02d}.jpg"
            subprocess.run(
                [ffmpeg_exe(), "-y", "-v", "error", "-i", str(path), "-ss", f"{t:.3f}",
                 "-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "4", str(dst)],
                capture_output=True, timeout=300)
            if dst.exists() and dst.stat().st_size > 0:
                out.append(dst.read_bytes())
    return out
