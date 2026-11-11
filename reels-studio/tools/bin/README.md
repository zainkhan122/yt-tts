# tools/bin — previously vendored executables

## yt-dlp — MOVED (2026-11-10, storage gate)

The vendored copy pushed tracked source over the 20 MB budget. It now lives at
`~/.config/reels-studio/bin/yt-dlp` (persists across sandbox resets, outside the tracked set).
Resolution order in tools/sources.py and tools/reference_teardown.py:
`$YT_DLP` env → `yt-dlp` on PATH → that file → curl re-fetch from
https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp (Unlicense).

ffmpeg for teardowns: `~/.cache/reels-studio/bin/ffmpeg`, auto-restored from the
imageio-ffmpeg pip wheel when the excluded cache is wiped. Override via `$FFMPEG`.
