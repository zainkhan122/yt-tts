# the-inner-machine/ — The Inner Machine

Standalone animated explainers about how the mind works: psychology, behavior and consciousness.

The Inner Machine has its own name, brand, voice, strategy and SOP. It is not a personality-typing or Jungian channel, and its identity must not be merged with another project.

## Layout

- `SYSTEM.md` — source-of-truth rules and production gates.
- `STRATEGY.md` — original channel strategy.
- `PRODUCTION_STANDARD.md` — enforceable output bar.
- `brand/` — channel identity, metadata and brand tool.
- `pipeline/` — TTS, rendering and repository sync tools.
- `tools/` — project, storyboard and final-video validators.
- `plan/` — content plan and per-video source packages.
- `reusable/` — Kokoro voice file/configuration.
- `handoff/` — operational resume state.

## Produce a video

A project must first pass validation and have its required assets. The current three-month slate is in `plan/3_MONTH_CONTENT_PLAN.md`.

```bash
python3 tools/validate_project.py plan/video-01-where-do-dreams-come-from/project.json
python3 pipeline/produce.py plan/video-01-where-do-dreams-come-from/project.json
```

Do not bypass gates or render the current demo until its landscape assets and claim-level source package are complete.
