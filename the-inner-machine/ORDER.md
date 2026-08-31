# THE INNER MACHINE — PRODUCTION SEQUENCE (auto-continue)

One task per session, in this exact order. **No "go ahead" is ever requested.**
`pipeline/run.py` reads `plan/<video>/run_state.json` and resumes at the next incomplete
step automatically, so every session just continues where the last left off.

## Sequence
| # | Task | Session | How |
|---|------|---------|-----|
| 1 | **Images** — generate the unique base images (batches ≤10) + Pexels b-roll | own | `run.py` reports `AGENT_ACTION: generate_images N`; agent generates; re-run |
| 2 | **Long video (16:9)** — rendered in CHUNKS | own | `run.py` (each call = one chunk, default 8 shots) until `LONG DONE` |
| 3 | **Thumbnail** | own | `run.py` (single call) → `cover.jpg` |
| 4 | **Metadata** | own | `run.py` (single call) → `metadata.md` |
| 5 | **Shorts (9:16)** — LAST | own | dedicated 9:16 builder from the finished long |

## Auto-continue contract
- State lives in `run_state.json` (`step`, `chunk`). Never deleted mid-video.
- At session start, run `run.py`; it does the next step/chunk and saves. It prints
  `[run] next step: X` — that is informational, NOT a question.
- The agent never asks "should I proceed?". It executes the next step and reports.
- One task per session: finish the current row, stop; the next session resumes at the next row.

## Visual bar (applies to the long video)
No sentence subtitles. Only KEY WORDS as kinetic text, TOP of screen, single line, synced
to the TTS. A visual change every 3–5s; every shot moves. See PRODUCTION_STANDARD.md.
