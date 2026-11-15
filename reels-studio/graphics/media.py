"""Media helpers for the graphics tier: cut still frames out of a captured screen recording.

WHY THIS EXISTS (owner rule, 2026-11-12): a short about a tool must SHOW the tool. The house
renderer draws its own pages, and a page of drawn type is not proof — the UI proof gate refuses
a short whose scenes reference no product evidence at all.

The capture packs hold real screen recordings (a capture of the tool's own page). This module
cuts deterministic JPEG stills out of one so a scene can play the real product UI on the page.
Nothing is fetched from the network: the frames come from the capture pack that the production
receipt pins by hash, and they are written next to the stage file, so the stage HTML stays small
and the render never carries megabytes of base64.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

_DUR_RE = re.compile(r"Duration:\s*(\d+):(\d{2}):(\d{2})\.(\d+)")
FRAME_COUNT = 5          # stills cut from one recording when no rate is asked for
FRAME_WIDTH = 1080       # the capture is 1080 wide; keep it (the page type has to stay readable)
FRAME_FPS = 4.0          # frames per second of the recording that a scene plays back


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


def cut_clip_frames(path: Path, out_dir: Path, fps: float = FRAME_FPS, width: int = FRAME_WIDTH,
                    height: int | None = None) -> list[Path]:
    """Write the recording's frames to `out_dir` as JPEG stills and return their paths.

    The frames are cut at `fps` and keep the recording's own order, so a scene can play the
    product the way a person recorded it. `height` crops the frame to the box it is shown in
    (the shot is a wide crop of a tall phone capture), so the frames fill the frame exactly.
    """
    dur = clip_duration(path)
    if dur <= 0:
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    scale = f"scale={width}:-2" + (f",crop={width}:{height}:0:0" if height else "")
    written: list[Path] = []
    count = max(1, int(round(dur * fps)))
    for i in range(count):
        t = dur * (i + 0.5) / count
        dst = out_dir / f"f{i:03d}.jpg"
        subprocess.run(
            [ffmpeg_exe(), "-y", "-v", "error", "-i", str(path), "-ss", f"{t:.3f}",
             "-frames:v", "1", "-vf", scale, "-q:v", "5", str(dst)],
            capture_output=True, timeout=300)
        if dst.exists() and dst.stat().st_size > 0:
            written.append(dst)
        else:
            dst.unlink(missing_ok=True)
    return written


def clip_frames(path: Path, count: int = FRAME_COUNT, width: int = FRAME_WIDTH) -> list[bytes]:
    """`count` JPEG stills spread across the clip, as bytes (the in-memory path).

    The first 8% is skipped (that is the load-in, before the page has any content) and the frames
    are cut by decode-then-seek, so every still is the frame the recording really shows.
    """
    dur = clip_duration(path)
    if dur <= 0:
        return []
    out: list[bytes] = []
    import tempfile
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
