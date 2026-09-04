# The Inner Machine — channel setup v2

## Identity

- **Name:** The Inner Machine
- **One-liner:** The hidden machinery of your mind.
- **Niche:** science-first animated explainers on psychology, behavior and consciousness.
- **Angle:** explain the mechanism behind what people think, feel and do; human takeaway last.
- **Audience:** curious adults who want understandable science, not a lecture or diagnosis.
- **Tone:** clear, warm and quietly wondrous; never preachy, jargon-dumped or sensational.

## Explicit separation

The Inner Machine is not The Deeper Mind. It does not use the reference channel’s Jungian rare-type positioning, title identity, voice lock, content pillars or visual identity. Only general production lessons such as resumable state, provenance tracking and fail-closed QA may be adapted.

## Brand

Graphite `#14181D`, steel `#2E4756`, copper `#E0A458`, cyan `#6FD3E0`, cream `#F4EFE6`. Flat 2D storybook forms, explanatory diagrams, restrained cinematic motion and subtle grain. The visual language varies by mechanism so the channel does not become a repeated AI template. Thumbnail text defaults to the top-left negative-space area with a dark scrim and must never cover the main subject, face, focal object or mechanism.

## Editorial strategy

`recognizable experience → mechanism → evidence and limits → visual model → human takeaway`

Pillars: Machinery, Behavior Explained, The Self and Glitches. The pilot cadence is one 6–9 minute long-form episode every 10–14 days and two 30–45 second native-vertical Shorts per episode. Reassess after four episodes.

## Toolchain

- `pipeline/produce.py` — config-driven renderer, with project validation before render.
- `pipeline/tts.py` — Kokoro wrapper; model downloads lazily, voice file is cached and checksum-recorded.
- `tools/validate_project.py` — fail-closed project/schema and asset checks.
- `tools/qa_video.py` — machine-readable ffprobe delivery QA.
- `brand/make_brand.py` — rebuilds brand finals from source art.
- `repo_push.py` — text/config/state push only; secrets and media remain outside normal sync.

## Workspace and repo

The repo folder `the-inner-machine/` is the SSOT. Workspace contains the active package, tools, reusable Kokoro data, temporary render work and secrets only. Every session begins by syncing from the repo and ends by updating `handoff/HANDOFF.md` and pushing text/config/state changes.

See `SYSTEM.md` for gates and `3_MONTH_CONTENT_PLAN.md` for the current slate.
