# Graphics pipeline — current handoff

This is the working graphics handoff; dated `HANDOFF-*.md` files are historical. Queue status remains `queue/publish.json` / generated `STATUS.md`. A successful render or technical gate is not owner approval or publishing permission.

## Current implementation

- `graphics/render.py` builds a deterministic 1080×1920, 30 fps browser stage from the selected template, injects bundled Inter / Anton / JetBrains Mono fonts, `templates/shared.css`, `templates/shared.js`, and `graphics/outro.js`, audits font loading, caption band and overflow, captures frames and muxes audio. The production encoder defaults to CRF 20 and x264 `medium`. The local preview explicitly defaults to `veryfast` and delivery CRF 25; no quality-equivalence comparison has been established.
- Shared caption: up to three words per fixed group, measured to fit one line, aligned on one baseline; the current spoken word is yellow. The endcard uses the earlier real-logo / Hypeless / handle / pink Follow button and cursor / COMMENT keyword chip / prompt layout. The outro stays stage-level and the template's card is suppressed.
- `tools/house_gate.py <stage.html>` checks one house card, visibility window, logo/name/follow/cursor/comment elements, sampled caption highlights, and scene text in the reserved band. `--house-gate` sets `HOUSE_GATE=1` for the local preview, which runs the gate before frame capture. **It is opt-in, not automatically enabled for all production renders.** It does not judge visual design, actual spoken alignment, or overall motion quality.
- `tools/local_preview_render.py` synthesizes per-scene Kokoro preview audio, concatenates silence at the same sample rate, aligns script words using `tools/align_words.py`, assigns words to the script scene by token order, builds the stage and encodes once. This is a CPU preview only; the approved production voice is the Chatterbox profile in `config/channel.json`. The local preview does not by itself satisfy production voice QA or the production receipt.
- Scene timings derived from speech are not a replacement for a human check: weak Whisper matches, interpolation, cue phrases and visual/audio semantics still need inspection. The aligner falls back to approximate length-weighted timings when unavailable or below its configured match threshold.

## Latest local review

`renders/tool-seedance-01/seedance-story-review.mp4` is the current local review preview, not tracked in Git and not approved for release. Its stage `renders/tool-seedance-01/story-work/stage.html` passed the house gate. It reuses the aligned Kokoro audio from `gfx-tool-seedance-01-pice11k_/vo.wav` after a fresh voice render was killed (exit 137). Latest motion sample: 168 consecutive 0.3 s intervals over the complete MP4, downscaled to 270×480 grayscale; 5 intervals had mean absolute pixel delta below 0.35, mean delta 1.82. This metric is an investigative proxy, **not a quality gate or evidence that the animation is good**. Subject, message, pacing, charts, transitions, legibility and sync need human review. The owner explicitly rejected the earlier outro, typography and animation; this revision has not been re-approved.

## Known blockers and limitations

- The larger selected test run had 2 failures: `test_outclass_briefs_pass_lint_and_rules` (workspace budget and a brief missing motion_standard) and `test_second_video_moves_off_taken_bracket` (planner returns no YouTube row in fixture). Result: 261 passed, 1 skipped, 2 failed. Re-run to establish current details. The plan-builder tests now use an isolated current-plan fixture and no longer write over a real brief. The focused suite `python3 -m pytest graphics/tests tests/test_preview_alignment.py tests/test_brief_lint.py -q` reported 46 passed, 1 skipped.
- `tools/maintenance/storage.py audit` is currently BLOCK: it includes persistent local model weights (approximately 338 MiB) in saved workspace and tracks the real source budget. Don't hide model weights from the audit or delete the voice model simply to force a PASS; decide separately where a reproducible model installation should live.
- House gate was exercised on the latest pulse stage. Template endcard guards exist in the default engine, negative, velocity-black, pulse, redline, musike, design-review and photo-to-3d; only the available pulse result was gate-checked against the current house code after cleanup. Validate each template with a fresh stage/render before claiming cross-template coverage. The negative engine also needs a fresh current-code visual review.
- `tools/brief_lint.py` BL140–143 currently treat missing format/duration/aspect as a vertical short; documented defaults are intentional code behavior, not explicit metadata. Check compatibility before changing.
- The user-requested cleanup removed `/home/user/uploads/`, including its original reference screenshots, and the separate `/home/user/skill/` and `/home/user/reelmimic-opencode/` folders. Derived `ref/` images were also removed in the subsequent old-data cleanup. References to `uploads/` in historical documents are not evidence that those files still exist. Only the current Seedance local cover/captures/render and its tracked plan remain in their respective folders. Older tracked plans and the old Claude preview metadata were deleted at the owner’s request; restoring a historical project requires retrieval from Git history or archives. The prior untracked cover/capture assets were deleted locally and may need reconstruction. No finished MP4s, browser cache, whisper models, or Kokoro weights are committed.

## Narration-led graphics pilot

The pulse Seedance beat plan now uses a proportionally accurate two-row leaderboard, cue-driven spec, cost and catch builds, explicit scene headings and a short scene entrance. See `docs/MOTION-GRAMMAR.md` and `tests/test_pulse_story_motion.py`. The figures come from the historical project research note and must be reverified before publication. Other templates are not upgraded. The local review render is complete but has not received owner approval; cue tests cover synthetic timestamps, not final production voice alignment.

## Quality work needed before release

1. Review the complete rendered MP4 and audio at phone size, including first frame, each claim/visual sync, transitions and the entire outro; compare the real previous approved endcard, not only a synthetic gate.
2. Design storyboards and chart data/labels from real sourced claims. Build a small reusable 2D motion grammar: meaningful chart builds, keyframe timing and easing, purposeful transitions and hierarchy; review scene-to-scene pacing and readability. GSAP is already vendored. Three.js is optional for genuine 3D (e.g. a product/model demonstration), not a prerequisite for clear 2D charts and typography. Any 3D renderer must remain deterministic under `setTime(t)` and perform reliably in the headless capture environment.
3. Add reproducible per-scene visual regression and endcard/word-baseline tests, plus post-encode sync and motion diagnostics. Pixel movement cannot measure narrative quality. Never make a metric the objective by adding meaningless drift.
4. Resolve the remaining test failures and workspace budget; re-render and review every affected template before a broad release. Keep requirements and documentation synchronized with actual behavior, not intended behavior.

## Safe commands

```sh
cd reels-studio
python3 -m pytest graphics/tests tests/test_preview_alignment.py tests/test_brief_lint.py -q
python3 tools/house_gate.py renders/tool-seedance-01/story-work/stage.html
python3 tools/local_preview_render.py tool-seedance-01 --delivery-crf 26 --house-gate
python3 tools/maintenance/storage.py audit
python3 tools/ship.py status
```

Local models are intentionally Git-ignored. The preview looks for `../models/kokoro/kokoro-v1.0.onnx` and `voices-v1.0.bin` (or `~/.cache/kokoro/`); a fresh machine must provision them separately. Playwright Chromium, ffmpeg, faster-whisper and their runtime dependencies must also be installed. Do not commit credentials or generated output.
