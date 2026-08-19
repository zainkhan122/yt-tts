# Workspace — The Deeper Mind (build tools only)

Everything else lives in the GitHub repo `zainkhan122/yt-tts` under `vault/`.

| Path | Purpose |
|---|---|
| `tools/` | pipeline.py (video builder), bootstrap.py, stock_fetch.py, make_pad.py, verify.py, vault_push.py, git_push.py, repo_update.py, remix_test.py |
| `videos/video_NNN/` | current video's sources (script, voiceover, storyboard, images, final) — deleted after the user downloads |
| `reusable/` | locked voice (af_heart) config + reference sample |
| `secrets/` + `.pexels_key` | GitHub PAT + Pexels API key (local only, never pushed) |
| `MASTER_RULES.md` | R1–R20 — the authoritative build/quality rules |

## ⚠️ Session reset recovery (run this FIRST, every session)

The sandbox loses pip packages, `~/.cache/kokoro/` and `/tmp` on reset (NOT the
workspace files). Self-heal in one command:

```bash
python3 tools/bootstrap.py   # reinstalls deps, refetches kokoro model, checks secrets + disk
```

If it reports missing secrets, re-paste the GitHub PAT + Pexels key and re-run.

## Build commands (current video)

```bash
export PIPE_VIDEO=/home/user/videos/video_013
python3 tools/bootstrap.py          # once per session
python3 tools/pipeline.py assets    # (manual: generate images + fetch stock)
python3 tools/pipeline.py storyboard
python3 tools/pipeline.py tts
python3 tools/pipeline.py render    # chunked, first-chunk gate
python3 tools/pipeline.py assemble
python3 tools/pipeline.py finalize  # captions + music bed (R14/R20) + push
python3 tools/pipeline.py status    # check progress
```

## Repo vault layout

```text
vault/brand/          logo, banner, setup.md
vault/research/       pain points, prompts, strategy
vault/pipeline/       content pipeline docs + plans
vault/reusable/       kokoro voices.bin + voice_config.json (locked voice)
vault/docs/           market analysis
vault/tools/          current copies of the build tools (source of truth)
vault/MASTER_RULES.md R1–R20
vault/video_NNN/      final.mp4 + thumbnail + metadata + script + images
```
