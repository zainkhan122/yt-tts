# Autonomous visual direction: implementation and acceptance report

Status: **NOT ACCEPTED — prototype planning integration only**. No unrelated-topic acceptance video was produced, and no live model inference was run.

## Changes

- `production_modes.py`: opt-in runtime/preflight interface, per-beat mode-intent selection, hybrid preflights, explicit policy-controlled fallback records, declared asset hashes, and lifecycle fields. `require_executed_and_verified` deliberately blocks because execution receipts are not integrated. The older `choose_mode` interface is retained for compatibility and still trusts its caller's `verified` flag; it must not be treated as the new evidence gate.
- `automated_planner.py`: optional model mode-intent payload and response, attached to existing semantic/alignment/scheduler/layer-planning pipeline. Legacy calls are unchanged. Timeline compilation occurs before mode selection; existing rendering routes do not call the blocking guard.
- `automated_openrouter.py`: opt-in mode-intent response instructions. This is only a prompt change: no API request was made, and the owner-paused OpenRouter pilot was not enabled.
- `test_production_modes.py`, `test_autonomous_modes.py`: synthetic adapters and planner exercise preflight, selection, explicit fallback, hybrid, lifecycle separation and declared asset hashes. These mocks are not evidence of operational providers or real capture.

## What is not implemented or proven

1. No operational mode adapters connect these preflights to actual screen capture, AI generation, or motion execution; the preflight callable is a trust boundary. Declarations and a passing mock probe do not establish operational availability.
2. No execution receipts, output verification integration, independent full audiovisual review, or enforced production rendering gate. `require_executed_and_verified` blocks only if a caller invokes it; the pre-existing renderer remains callable. Lifecycle fields and hashes are not independent proofs of source provenance or rendered output.
3. The model's intent and requested operations are not independently semantically checked against narration. It can misclassify a real application action or object-level animation as a simpler illustration or still-layer transformation. Explicit fallback disclosures do not repair a misleading final video. This prototype must not be used to make unattended acceptance decisions.
4. The planner still builds an existing layer-renderer layout for every beat before selecting a mode. Mode selections do not route work to distinct execution engines. The model prompt update has not been tested against a real model.
5. Source provenance is declared catalog data and a hash, not a verified chain of creation. Actual actions, visual fidelity, phone-size legibility, timing, and full audio/video playback remain unverified.
6. The requested unrelated-topic acceptance run needs an authorized live model path, approved house narration, strict alignment, working adapters, generated assets, execution evidence and independent human playback review. GitHub Actions has an OpenRouter secret, but that does not authorize activating the owner-paused pilot. No saved model response was replayed, no substitute voice was used, and no video, decode, duration comparison or contact sheet is claimed for this acceptance run.

## Local verification

Commands, run from the project root:

```sh
python3 -m py_compile graphics/production/{production_modes,automated_openrouter,automated_planner}.py
python3 -m pytest -q -rs graphics/production/test_autonomous_modes.py graphics/production/test_production_modes.py graphics/production/test_automated_planner.py graphics/production/test_layer_renderer.py tests/test_production_alignment_semantic.py tests/test_visual_execution.py tests/test_beat_production.py graphics/tests tests/test_voice_handoff.py
sha256sum graphics/production/demo_assets/battery-demo.mp4
```

Results: **109 passed, 1 skipped**. The skip was `graphics/tests/test_overflow_audit.py:32` because local Playwright was absent; the test's skip message mentions cloud rendering but no cloud render was performed for this work. `imageio-ffmpeg` was installed locally; `faster_whisper` and `playwright` were not installed in the current runtime. Battery fixture SHA-256 remained `088f77d8e8778d60382ad908e796cf1c26f46cc4a089e6c1b0dd950f3ffa9385`.

No publishing, scheduling, pilot activation, or existing smartphone fixture modification was performed. This is not a production-ready or accepted autonomous system.
