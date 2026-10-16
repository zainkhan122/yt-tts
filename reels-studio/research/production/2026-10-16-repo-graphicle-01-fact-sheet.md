# Graphicle — fact sheet (checked 2026-10-16)
Sources: GitHub README + API (2026-10-16T08:20Z): 180 stars, 9 forks, created 2026-10-14, Apache-2.0.
- One Rust program: code graph + project memory (docs, decisions, past Claude Code/Codex sessions) + cited excerpts with file/line sources, via MCP; works with Claude Code, Codex, Cursor, any MCP client. Local-first: no account, no API key for the graph, no telemetry.
- Setup: brew install graphicle-ai/tap/graphicle, then graphicle setup (backs up files it changes; graphicle disconnect undoes).
- Vendor benchmarks (attribute, pre-release builds): 3.0-22.7x less time than Graphify 0.9.91 across 13 codebases; graphs differ slightly.
- Catches spoken: v0.1.x, days old; Windows build is an unsigned preview.
