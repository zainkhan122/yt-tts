# Zipper mechanics — review render

**Status: review-only; not accepted as the requested autonomous quality milestone.** The complete 27-second video exists, but the visual direction and artwork are topic-specific and authored by the interactive agent in code. No live external planner was called, and this is not an autonomous planner selecting and executing treatments for arbitrary topics. The per-beat directions are explicitly coded, so the earlier instruction not to manually prescribe every beat remains unmet. No publishing or scheduling occurred.

## Deliverables

- `zipper-review.mp4`: 1080×1920, 24 fps, H.264/AAC, native-resolution vector frames and approved house narration.
- `contact-sheet.jpg`: 18 sampled frames at approximately 1.5-second intervals, shown at 270×480 per frame. This does not substitute for reviewing full motion and audio.
- `scheduled.json`, `visual-events.json`, `alignment-executed.json`, `technical-checks.json`: word-linked scheduled cues and technical diagnostics. Serialized alignment diagnostics are not an in-process verification receipt.

## Files created this turn

- `build_video.py`: agent-authored content-specific semantic beats, procedural visuals, strict alignment and scheduling, native Pillow drawing, and FFmpeg encoding/muxing.
- `inspect_video.py`: full decode, stream-duration measurements, frame timing calculations and sampled contact sheet.
- `test_build_video.py`: checks that actual rendered procedural object, diagram and typography frames vary during the relevant actions; checks the path interpolation helper.
- The rendered MP4, silent intermediate, contact sheet, sampled images and diagnostic JSON in this folder; this report. Existing house narration and script were reused. No general renderer or prior fixture was changed in this turn.

## Planning, execution and timing

The interactive agent selected a mechanism illustration, a Y-channel process diagram and kinetic statements because of the meanings of the three narration passages. The subject-specific `plan()` is manually authored in `build_video.py`, not returned by a live planning provider. The code uses the existing semantic schema and scheduler. It runs `FasterWhisperBackend('small.en')`, calls `require_verified`, then schedules and renders in the **same Python process**. All 81 words passed strict alignment against the real house narration.

Examples of narration-linked actions: slider emphasis at “slider” 1.86s; slider rises from “pull it upward” 4.68s toward “lock” 7.66s; the two diagram paths begin at “enter” 12.86s, meet at “merge” 14.14s, and the outgoing path begins at “leave” 15.44s; reversal begins at “pull” 18.06s, with the wedge highlighted at 19.92s; statement text enters on “no glue,” “no magnets,” “shape,” “pressure,” and “reversible connection.” Animated movement completion times are derived from other spoken events or the short emphasis interval. The two scene crossfades span 0.44 seconds around beat boundaries and therefore begin before the next beat.

At 24 fps, a mathematical first frame at/after each word timestamp is 3.3–38.3 ms later. This is frame quantization, not independent proof of perceptual audiovisual sync; subtle eased motion may not be visibly detectable on its first mathematical frame. Word timestamps are Whisper estimates, not sample-perfect ground truth.

## Technology and capabilities actually demonstrated

Native 1080×1920 frames are drawn with Pillow and piped to FFmpeg/libx264; the existing layer renderer's easing function is reused, but this demonstration uses a topic-specific procedural drawing loop, **not** the existing layer compositor or a general-purpose animation engine. The zipper consists of individually positioned illustrated teeth, tracks and slider; the positions respond to the moving slider. The diagram reveals two paths and a combined path; typography translates and fades into place; scenes crossfade. These are actual rendered actions, not merely interface declarations or mocks. The result is 2D schematic artwork, not 3D, photorealistic footage, physically validated zipper geometry, or a reusable general assembly engine.

## Inspection and tests

- Full FFmpeg video **and** audio decode: passed. Video stream: 649 frames, 27.0417s; AAC audio: 27.0300s. Difference: 11.7 ms, under one 24-fps frame.
- 18 contact-sheet samples were visually inspected. They show upward and downward slider movement, progressing channel lines and later text. The short crossfade creates a momentary double exposure of headings; the small wedge annotation and secondary labels are difficult at phone size. The first part is relatively static, the illustrated zipper is schematic and its overlapping teeth do not prove realistic interlocking, and the closing typography covers much of the mechanism. There are no full narration captions, dedicated realistic cover, or voiced house outro/CTA, so this is not a publishable finished short.
- **No full audiovisual human playback review has been performed.** A decode and sampled stills do not establish that narration sounds natural, all motion reads clearly, or the frame-level synchronization is perceptually correct. Independent review remains required.
- `python3 -m pytest -q -rs graphics/production/zipper_motion/test_build_video.py graphics/production/test_autonomous_modes.py graphics/production/test_production_modes.py graphics/production/test_automated_planner.py graphics/production/test_layer_renderer.py tests/test_production_alignment_semantic.py tests/test_visual_execution.py tests/test_beat_production.py graphics/tests tests/test_voice_handoff.py`: **114 passed, 1 skipped**. Skip: local Playwright absent in `graphics/tests/test_overflow_audit.py:32`. Tests do not prove visual quality.
- Existing battery fixture SHA-256 remains `088f77d8e8778d60382ad908e796cf1c26f46cc4a089e6c1b0dd950f3ffa9385`.
