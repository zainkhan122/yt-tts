# Zipper benchmark: reusable motion milestone — NOT ACCEPTED

The approved `graphics/production/zipper_motion/zipper-review.mp4` is the visual benchmark. Its SHA-256 remains `02decba05764e15e929c1933c6a0745ec7fba573995edc46027134fe469542ca`; it was not modified. No video was published or scheduled.

## What was built

- `graphics/production/vector_motion.py` is a topic-neutral Pillow vector renderer. It draws independent shape groups and supports word-anchored translation, scale, rotation, opacity and progressive path reveals, easing, native 1080×1920 output and a short fade through a neutral background at scene boundaries. Vector text below 18 design pixels, no-op events, beats with only opacity/scale, malformed values and overlapping animations on a single property are rejected. These checks catch limited mechanical defects; they **cannot** determine whether a beat is meaningful, visually polished, legible in context or equal to the zipper benchmark.
- `graphics/production/render_vector_story.py` accepts narration, house voice and director-supplied vector direction, runs the existing strict faster-whisper service and `require_verified`, uses the existing semantic schema and scheduler in the same process, then renders a review-only video with FFmpeg. Animation start and end are derived from spoken phrase timestamps. It does not infer a visual direction from narration.
- `graphics/production/test_vector_motion.py` exercises actual path masking and vector pixels, eased timing and text overflow. An additional in-process smoke check used the *existing zipper audio* and real strict `small.en` alignment, semantic scheduler and two different vector frames. It did not modify the benchmark and is not a new unrelated-topic acceptance video.
- `graphics/production/water_cycle_review/narration.json` and `direction.json` contain an unrelated water-cycle script and this interactive agent's hand-authored visual direction. `request_house_voice.py` uses the existing review-only house-voice workflow. `preview-0.png`, `preview-1.png`, and `preview-2.png` are static layout previews generated with synthetic preview times, **not video frames** and not a demonstration of narration synchronization.

## Why the requested milestone is not complete

1. The approved-house-voice workflow run **45902342526** was dispatched and was still in progress in its voice dependency restoration step at the time of this report. The workspace does not yet contain its finished narration. No substitute voice or interpolated word timing was used. As a result, no completed water-cycle video, actual word alignment, rendered contact sheet, full decode or audiovisual review is claimed. The local request helper is waiting for the same run; it does not publish.
2. The water-cycle vector direction was written by the interactive agent as scene data. The renderer does **not** independently understand the narration or create those scene specifications. Therefore this does not satisfy the requirement that the system independently produce a new topic without scene-by-scene direction. An authorized actual planning/execution route would be needed; the owner-paused OpenRouter pilot was not activated.
3. The preview artwork is schematic and simpler than the approved zipper's object treatment. Static preview frames cannot demonstrate motion quality. Do not treat this as a passed benchmark comparison. Every completed beat would still need a real visual and audiovisual comparison against the approved reference, revisions for weak beats, and human acceptance; the limited automatic checks must not silently accept it.

## Verification

Command run from the project root:

```sh
python3 -m pytest -q -rs graphics/production/test_vector_motion.py graphics/production/zipper_motion/test_build_video.py graphics/production/test_autonomous_modes.py graphics/production/test_production_modes.py graphics/production/test_automated_planner.py graphics/production/test_layer_renderer.py tests/test_production_alignment_semantic.py tests/test_visual_execution.py tests/test_beat_production.py graphics/tests tests/test_voice_handoff.py
sha256sum graphics/production/zipper_motion/zipper-review.mp4
```

Result: **118 passed, 1 skipped**. The skipped test is the local Playwright overflow audit; no cloud render was performed to replace it. The test result does not establish the visual benchmark or independent semantic direction.

When the approved voice run resolves, the generic command is `python3 -m graphics.production.render_vector_story --directory graphics/production/water_cycle_review`. It must pass strict alignment and then be inspected; do not claim the requested independent, benchmark-quality result solely because it renders.
