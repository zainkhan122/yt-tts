# Beat-level visual production prototype (opt-in, not production-ready)

This is an experimental stage under `graphics/production`, not wired into `lib/pipeline.py` or publishing. Existing workflows and publishing gates are unchanged. It is a narrow proof of concept, not the complete requested production engine.

## Existing architecture assessment

- Scripts/briefs: `tools/video_plan.py`, `tools/brief_from_plan.py`, `reels.py` and `briefs/`; pilot agent's configured OpenRouter text/vision client in `tools/agent/openrouter_client.py` is explicitly paused in its config, free/pinned, and should not be assumed available.
- Narration: `lib/pipeline.py` implements approved Chatterbox plus other local options; `lib/voice_handoff.py` hashes audio and persists timings; `tools/draft_voice.py` and GitHub Actions support handoff. Synthesizer timestamps are not assumed.
- Alignment: `tools/align_words.py` uses faster-whisper word timestamps; it can interpolate unmatched words or fall back to length-weighted estimates. `lib/pipeline.py` also has Whisper QA and legacy estimated timing fallbacks. The prototype rejects a declared length-weighted method, but method metadata alone **cannot prove** timestamps or individual words were really aligned. Manually check alignment; interpolated Whisper words are not separately flagged by the current aligner. A production gate must address this.
- Visual decisions: `graphics/beats.py` has a validated archetype plan, `graphics/timing.py` segments phrases, `graphics/cues.py` maps words to visual events, `graphics/stage.py` bridges voice timings to the existing house engine. Existing fallbacks include equal word partitions and cue spreading; those are not authoritative audio alignment.
- Visual production: `graphics/render.py` uses deterministic Playwright frames and FFmpeg, `graphics/templates/` has charts, object and typography graphics. Other one-off `tools/render_*.py` use PIL and FFmpeg. Image-generation was previously invoked through the host's interactive tool; that does not establish an available repository API. No configured general-purpose video-generation or 3D provider was verified in this local audit. The registry here advertises nothing automatically.
- Publishing: `tools/ship.py`, `tools/post/`, and `tools/youtube/direct_short_production.py`, `cover_ctl.py`; cover rules in `docs/DEDICATED-COVER-PRODUCTION.md`, outro rules in `docs/HOUSE-OUTRO-PRODUCTION.md`. Nothing here schedules, certifies, or bypasses those gates.
- Performance: existing per-frame browser screenshots and CPU Chatterbox are expensive; memory and concurrency must be bounded. Existing repository includes multiple historical render scripts; this prototype intentionally does not replace them.

## What works

`blueprint.bind` requires measured PCM WAV duration, a supplied word timestamp list, an explicitly declared non-estimated alignment method, and an explicit partition; it rejects out-of-range timing. Narration digest binds the blueprint to the exact audio. Rebuild after changing audio or word timestamps. `auto_groups()` reuses the existing phrase segmenter; the battery proof uses three manually chosen groups. JSON is editable and validated on render. Assets and animation requirements are explicitly associated with each beat. `providers.Registry` exposes a minimal explicit capability registry but does not automatically connect real external adapters.

The battery renderer uses Pillow shapes and moving objects: casing separation and a push-in, changing charge indicator, and animated ions. It is a schematic illustration, **not photorealism or validated scientific simulation**. Frame 0 can be generated from the opening composition; a different external cover is rejected. Rendered clips cache independently by beat data, timing, rendering version and relevant cover. `--force-beat beat-002` rebuilds that clip only; final mux is redone. Outputs are 540x960 at 24 fps, not the standard publish-ready 1080x1920. Each clip is rendered frame-by-frame rather than holding all frames in memory; a small state JSON records per-beat success/failure and permits rerun using completed clip files. Existing cover verifier requires 1080x1920 and is therefore not applicable to this prototype.

## Usage

Requires existing Pillow and imageio-ffmpeg (or system FFmpeg). No new package is introduced. Prepare a PCM WAV narration and actual word timing JSON from a trusted alignment stage. Supported JSON: `{"method":"whisper-word", "words":[["Your", 0.1, 0.3], ...]}`. Be aware of interpolated word timing caveat above.

```
python -m graphics.production.cli plan --audio voice.wav --alignment words.json --groups 3,6,6 --out blueprint.json
python -m graphics.production.cli render --audio voice.wav --blueprint blueprint.json --work job --out result.mp4
python -m graphics.production.cli render --audio voice.wav --blueprint blueprint.json --work job --out result.mp4 --force-beat beat-002
```

Counts must exactly partition your alignment. To make an opening-frame cover, use `graphics.production.render.frame(blueprint['beats'][0], 0).save('cover.png')` and pass `--cover cover.png`. A cover is optional in this proof of concept; this is **not** an approved publication workflow.

## Material limitations / remaining work

- No real spoken-audio end-to-end battery acceptance run was performed; tests use synthetic silence and supplied synthetic timestamps. Actual alignment quality, audiovisual review, and scientific correctness require independent assessment.
- No AI semantic planner, generic visual-treatment selector, storyboard UI/HTML visual previews, continuity manager, image/video provider adapters, or actual AI-generated photorealistic smartphone. `battery_specs` is a hardcoded demonstration; camera labels other than first push are cuts, not 3D motion.
- Blueprint validation is incomplete for arbitrary nested overlay and sound-effect data; prototype renderer rejects nonempty overlays/effects, non-cut transitions and multiple animation events rather than silently ignoring them. It does not support music, other clips/layers, SFX, model retries, async jobs, asset download/dimension validation, live progress, cache garbage collection, locking/concurrent jobs, durable orchestration, crashed-process reconciliation, or cancellation. Clip cache corruption validation is absent; use fresh job directories for critical tests.
- PCM WAV only; user-provided method metadata is not a trusted alignment receipt. The sample does not verify exact narration text. Do not use it for publishing.
- There is no integration with existing production/publishing paths, house outro or dedicated cover certification. This is intentional until feature coverage, safety gates, tests, and audiovisual quality are complete. The current implementation is **not the requested production-grade system** and must not be represented as such.
