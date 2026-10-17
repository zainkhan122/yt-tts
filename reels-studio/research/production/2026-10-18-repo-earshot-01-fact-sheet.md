# Fact sheet — Earshot (repo-earshot-01)
Checked 2026-10-18 (Karachi) against primary sources.
- Repo: github.com/Leonxlnx/earshot — "Ears for coding agents: let AI hear, review and make sound. CPU-only, open source."
- GitHub API 2026-10-18: 651 stars, 39 forks, created 2026-10-15, MIT, Python.
- README: turns sound into evidence an agent can reason about — describe (what a file sounds like in words), match/rank/find (best moments in long recordings), critique (launch-film scorecard vs professional references), forge (make sounds in code, improved by listening), fit (recording -> code recipe). CLI, Python API and MCP server; annotated listening sheet PNG.
- Runs locally on CPU. Install: git clone, Python 3.10+ venv, CPU torch, pip install -e; ffmpeg/ffprobe needed. First model use downloads ~1.4 GB (CLAP + AudioSet tagger).
- Catches (spoken): ~1.4 GB model download on first use; each CLI call loads models (~20-40 s; MCP server keeps them loaded); brand new v0.1 (launch film released with v0.1.0).
