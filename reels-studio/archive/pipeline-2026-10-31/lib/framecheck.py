#!/usr/bin/env python3
"""Frame-0 visibility check: a published short must show its hook in its very first frame.

Owner report 2026-10-12: every scheduled post showed a "plain frame 0 image which has Nothing on
it". The spotlight hook faded its heading in from 0.05 s, so frame 0 was the empty background. Any
platform that cannot take our uploaded cover (Buffer previews, Facebook Reels, YouTube Shorts until
the thumbnail lands) showed that empty frame.

This module is the measurable half of the guard. It decodes exactly one frame, as raw 8-bit gray,
and takes the brightest sample. Measured on the 2026-10-12 incident (13 published files):

  broken hook frames (4 videos, pre-fix releases)   max luma 73-76    (dark background only)
  fixed frames (9 videos, r3/r4 releases)           max luma 255      (headline + card visible)

The gap is the entire point: a hook shows a bright headline, a blanked hook has no bright pixel at
all. BRIGHT_YMAX = 160 sits in open space, so the check fails closed on the defect it was written
for without second-guessing ordinary dark scenes at t=0 (their headlines are still bright).

Uses raw pixel output rather than a filter, so it works with any ffmpeg build; stdlib only, so the
test suite imports it without ffmpeg or numpy.
"""
import subprocess

BRIGHT_YMAX = 160  # evidence above: broken <=76, fixed =255


def _raw_frame(source, t, ffmpeg):
    """One frame at t, as raw 8-bit gray bytes (b"" when ffmpeg cannot produce it)."""
    cmd = [ffmpeg, "-hide_banner", "-v", "error", "-ss", str(t), "-i", str(source),
           "-frames:v", "1", "-vf", "format=gray", "-f", "rawvideo", "-"]
    try:
        return subprocess.run(cmd, capture_output=True, timeout=120).stdout or b""
    except (OSError, subprocess.TimeoutExpired):
        return b""


def ymax_at(source, t=0, ffmpeg="ffmpeg"):
    """Brightest luma sample (0-255) of the frame at t seconds, or None if it cannot be measured."""
    frame = _raw_frame(source, t, ffmpeg)
    return float(max(frame)) if frame else None


def frame0(source, t=0, ffmpeg="ffmpeg"):
    """(ok, peak): ok is False when the measurement is missing (fail closed) or too dark."""
    peak = ymax_at(source, t, ffmpeg)
    return (peak is not None and peak >= BRIGHT_YMAX), peak


def describe(ok, peak):
    return (f"frame 0 bright content: {'visible' if ok else 'NOT VISIBLE'}"
            f" (max luma {peak if peak is not None else 'unmeasurable'}, need >= {BRIGHT_YMAX}). "
            "The hook must be on screen at 0.0 s - see templates/_spotlight/scene.js")
