# tools/bin — vendored executables

## yt-dlp (2026.10.26, zipapp, requires python3 on PATH as `python3`)

- Source: https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp (fetched 2026-11-10)
- License: Unlicense (public domain) — https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE
- Used by: the topics sources lane — `tools/sources.py scan` (TikTok + YouTube Shorts)
  and therefore `tools/todays_topics.py`.
- Why vendored: topics tooling must keep working after a fresh checkout or a wiped
  Python environment. `tools/sources.py` resolves the binary in this order:
  `$YT_DLP` env var → `yt-dlp` on PATH → this file. Override via `YT_DLP=/path/to/yt-dlp`.
- Update: `curl -L -o tools/bin/yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp && chmod +x tools/bin/yt-dlp`
