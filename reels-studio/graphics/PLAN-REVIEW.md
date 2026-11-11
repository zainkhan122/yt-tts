# Review of HYPELESS STUDIO master plan (PLAN.md v1.0) and revised plan (v1.1)

Reviewer role: senior app developer. Scope of review: architecture, sequencing, correctness of the
rules, testability, and fit with what already exists in `shorts-pipeline/reels-studio`.

## 1. Verdict

The plan is a strong product spec. The core idea (every spoken phrase owns a generated visual that
depicts its claim, grounded in the tool's own README) is right, and §14 is the part to build first.
The plan as written is not buildable as one unit: it describes a new FastAPI application, a
dashboard, a topic radar, analytics, and a VPS deployment, all before the core visual loop is proven.
It also duplicates a pipeline that already exists in `reels-studio`.

Recommendation: ship a vertical slice first (feature sheet → beat plan → generated scenes → render →
QA), prove it on real output, then wire it into the existing pipeline. Control-plane work comes after.

## 2. Findings, ranked by impact

| # | Finding | Impact | Revision |
|---|---|---|---|
| 1 | Scope: four phases, a new app, 15 archetypes, radar, analytics, dashboard in one document. No slice can be verified alone. | High | Vertical slice first (§4 below). Control plane deferred to Phase D. |
| 2 | Duplication: `reels-studio` already has batch orchestration, QA gates, cloud render and receipts. The plan "ports" them into a second app. Two pipelines will drift. | High | One pipeline. The graphics engine is a module called by the existing brief builder. Decide this before Phase B. |
| 3 | Voice is the time budget. In the last render, the TTS stage took 470 s of 660 s total (CPU Chatterbox). The plan's "3–9 videos/day on 8 vCPU" is unmeasured. | High | Add a measured per-video budget (TTS, render, QA) and a benchmark gate before scaling. |
| 4 | Non-determinism sits in the critical path. The LLM beat planner decides every visual. A flaky planner means a flaky video. | Medium | The LLM only proposes the beat plan as JSON. Deterministic lint decides. One retry with violations, then owner review. Archetype rendering is already deterministic. |
| 5 | Rule S4 (keyword overlap between phrase and `depicts`) is fragile: stopwords, synonyms, and inflection make it noisy. | Medium | Keep a weak check (B4: `depicts` shares a word with the phrase). The strong checks are structural: `feature_id` binding (B3) and metric equality (B7). Implemented in `graphics/beats.py`. |
| 6 | §16 says "frame change min 2 Hz sampled at 4 fps". Units are unclear. The code uses a mean pixel difference of at least 2.0 per 0.25 s bin. | Medium | Document the exact measure in §16. Keep the threshold in config only. |
| 7 | §14.3 `media_policy: generated_first` allows up to 2 real-media `proof_zoom` scenes by default. This contradicts the owner's directive (no tool screenshots as the main visual). | High | Default must be `generated_only`. `proof_zoom` is opt-in per video and off in the channel config. Implemented: the engine has no media archetype at all in v1. |
| 8 | The archetype palette is said to be "verified frame by frame" from the reference channel. No reference folder exists on this machine, and the channel page returns errors, so this could not be re-verified. | Medium | Mark the palette as the studio's own brand tokens. Do not claim a verified match. |
| 9 | Visual quality has no regression test. Cloud QA checks 9 structural items and does not measure what is drawn. | High | Golden-frame tests per archetype: fixed scene JSON at fixed t gives a fixed frame hash. Plus the pixel QA gates on real output. |
| 10 | The GitHub token sits in plain text in `uploads/`. The plan's own secret doctrine says vault-only. | Medium | Read the token from an environment variable or the vault only. Never a plain file in the workspace. |
| 11 | Idle motion is not specified. §14.1(5) requires every scene to move. Entrance-only motion leaves holds still, and the pixel gate fails on them. | High | Every archetype has a continuous idle motion, and the ambient grid drifts on the clock. Verified with the pixel QA (see the results in §5). |
| 12 | Browser runtime dependencies are undocumented. Chromium needs system libraries (`libnspr4`, `libnss3`, and others). The first render failed on this. | Low | Add a `setup` step that installs and checks them. Document the Linux package list. |
| 13 | Job model: a single process with worker threads plus subprocesses. A crashed subprocess needs a lease and heartbeat, or a job is stuck forever. | Medium | Each stage run gets a lease with a timeout. An expired lease goes to dead-letter, never a silent retry. |
| 14 | §13.1 state machine has about 20 states. Most transitions are not tested. | Low | Keep the states that the pipeline needs, and test every transition. |
| 15 | The cover stage (§18.4) has no archetype definition, although `cover-lab` already exists. | Low | Reuse `cover-lab`. Do not define a second cover system. |

## 3. What the code now does (Phase A, this session)

Location: `shorts-pipeline/graphics/`

- `features.py`: feature-sheet lint. Every `evidence_quote` must appear verbatim in the fetched README (markdown-normalised). Metrics must be numeric. A risk is required.
- `timing.py`: deterministic phrase chunker from word timings (no LLM). Breaks on punctuation after a minimum duration, on pauses of 0.40 s or more, and at a 4.0 s maximum. `close_gaps` makes the timeline contiguous from 0 to the audio end.
- `beats.py`: beat-plan lint. B1 coverage (one scene per phrase, in order), B2 no identical archetypes back to back, B3 grounding (fact archetypes need a `feature_id`; script-only archetypes must not have one), B4 `depicts` overlap, B5 payload safety (no URL, markdown or emoji; length caps), B6 payload schema, B7 stat values equal the feature's metric.
- `templates/engine.js`, `templates/stage.css`: deterministic renderer. `setTime(t)` draws frame `t` from scratch. Seven archetypes: `concept_card`, `stat_pop`, `chip_grid`, `flow_link`, `terminal_type`, `toggle_steps`, `cta_stack`. Word-synced captions with the active word highlighted.
- `render.py`: Playwright frame capture at 30 fps piped into ffmpeg (libx264), then the TTS track is muxed in. Output is reproducible for the same inputs.
- `cli.py`: `lint` and `build` commands. Lint runs before any render. Exit codes: 2 feature lint, 3 beat lint, 4 render error.
- `tests/test_graphics.py`: 18 tests, all passing (`python3 -m pytest graphics/tests`).

## 4. Revised plan (v1.1)

**Phase A: vertical slice (done in this session, to be proven on real output)**
- Acceptance: lint passes on a real README; the render has no scene without a visual; every scene
  moves; the audio is the approved voice; the pixel QA gates pass on the output.

**Phase B: integrate with the existing pipeline (`reels-studio`)**
- Brief builder reads the feature sheet and the beat plan. `media_policy` defaults to `generated_only`.
- The beat planner is an LLM call that returns JSON. The deterministic lint decides. One retry with
  violations. Then the owner sees the diff.
- Measured budget per video (TTS, render, QA), recorded in the receipt.
- Acceptance: one Short from `storytold/craft-anything` passes the existing batch gates end to end
  (with the owner's approvals still required for topic and cover).

**Phase C: quality gates on real output**
- Golden-frame tests for each archetype.
- Pixel QA gates (visual change share, graphic-only share, motion gap) on every render.
- Vision panel stays advisory only.

**Phase D: control plane (the original plan's §4–§12, §19–§21)**
- Only after Phases A–C are proven on at least three real Shorts. Then the dashboard, radar and analytics.

## 5. Results of the Phase A proof (craft-anything, owner's approved script and voice)

Measured with `tools/short_qa.py video` on the rendered MP4, using the same word timings as the
approved voice.

| Run | Visual change on speech (≥75%) | Graphic-only share (≤25%) | Longest still stretch (≤3 s) | Hook first phrase (≤3.5 s) | Result |
|---|---|---|---|---|---|
| v1 (entrance-only motion) | 59.4% | 44.4% | 1.75 s | 2.09 s | BLOCK on 2 gates |
| v2 (idle motion added) | 77.4% | 25.7% | 1.00 s | 2.09 s | BLOCK on 1 gate (25.7% > 25%) |
| v3 (idle motion + stronger ambient grid + larger terminal text) | 90.2% | 9.7% | 0.50 s | 2.09 s | PASS on all pixel gates |

Lint: 13 phrases, 13 scenes, feature sheet and beat plan pass with zero violations. 18 unit tests pass.
Frames were checked by eye at 13 points and at 4 more in v3. Each phrase shows a visual that
depicts its claim, and the CTA stack lands on the last phrase.

**Caveat on the pixel result:** the ambient grid drifts on every frame. It helps the motion
gates, but the gates cannot tell content motion from background motion. The phrase-level animations
carry the meaning; the grid carries the "never still" requirement. Measuring the gates without the
grid is the next check, before Phase B.


## 6. Open items for the owner

- Reference channel: the folder named in the request does not exist on this machine, and the channel
  page returns errors. Send screenshots or a folder, or describe the styles. The archetype set is
  built from the plan's §14 description, not from the channel itself.
- Cover: still needs `--approve-cover` for the existing batch. The new engine does not produce a cover.
- Publishing: stays off. No publish, queue or schedule.
