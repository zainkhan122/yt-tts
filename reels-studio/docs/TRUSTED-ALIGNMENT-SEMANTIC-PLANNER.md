# Alignment provenance and semantic planning (experimental)

These components are isolated from the existing production and publishing pipelines. They are not production-ready or security attestation.

## Responsibilities

- `graphics/production/alignment.py`: execute the built-in faster-whisper adapter; retain raw observations and expected transcript, word-by-word confidence, source index, provider and model; flag missing, unmatched, low/missing confidence, ambiguous tokens, overlap/out-of-order and invalid timestamps. Diagnostic `analyze` also marks explicitly estimated/interpolated methods. It never fabricates timestamps for unmatched words. An exact normalized match, valid nonoverlapping times, confidences at or above threshold (minimum 0.5), and no extra observations are required by the strict path. Case and punctuation are normalized; contractions and numbers are **not** semantically normalized. Human review remains essential.
- `graphics/production/semantic.py`: provider-neutral `Planner` protocol and strict plan structure, treatments, beat word partitions, asset references and event schema. It validates structure, not scientific truth or whether a suggested treatment is renderable.
- `graphics/production/openrouter_planner.py`: adapter for the existing `tools/agent/openrouter_client.py` policy-gated client. Instantiate only with an authorized, preflighted client and role. The existing pilot is owner-paused; do not change its config or bypass its gates. Requires an enabled external inference service and authorized account. No request was made in this implementation.
- `graphics/production/scheduler.py`: independently binds each event to a contiguous exact phrase and explicitly numbered occurrence inside its beat. It uses the first aligned word timestamp and rejects missing triggers or beat overrun. Times are absolute audio and beat-relative; it does not invent timing. Scheduling can still be perceptually wrong and requires audiovisual QC.

Existing script/narration and legacy alignment functions are untouched. The older `graphics/production/blueprint.py` `bind`/battery CLI still accepts method labels and is **prototype-only**, not the strict path. Existing `graphics/beats.py`, `graphics/timing.py`, `graphics/cues.py`, `graphics/stage.py` and the renderer remain unchanged. New semantic blueprints are a distinct data contract; no renderer or publisher consumes them yet.

## Run (requires a real model and authorization)

```
from graphics.production.alignment import FasterWhisperBackend, run_alignment
from graphics.production.semantic import create_plan
from graphics.production.scheduler import schedule
alignment = run_alignment('voice.wav', exact_script, FasterWhisperBackend('base.en'))
plan = create_plan(authorized_planner, exact_script, [w['text'] for w in alignment.report['words']])
blueprint = schedule('voice.wav', exact_script, alignment, plan)
```

`faster-whisper`, its compatible numpy/soundfile stack and model weights are required externally; they were not installed/available in this environment. First model download may require network and licenses must be reviewed. The adapter uses word timestamps from recognition, not a forced aligner; a recognizable match is not proof the word's time is correct, nor of speaker identity. Confidence threshold needs real-world calibration.

Strict scheduling only accepts the in-memory alignment result created by the registered built-in adapter in the same process; passing or relabeling a JSON timing file cannot create a trusted result. The receipt includes an internal content hash and rechecks audio and transcript. This prevents accidental edits or ordinary JSON substitution, but **is not cryptographic attestation**: Python memory, code and model/runtime are in the same trust boundary, and locally monkeypatched adapters can forge results. Serialized reports are useful diagnostics only. For cross-process trust, add authenticated, tamper-resistant receipts with secured keys and deployment identity; do not use an unsafely rehydrated report as proof.

## Tests and limitations

The acceptance-shaped smartphone test supplies a **controlled fake model response** and simulated raw aligner observations over silent WAV. It tests validation and mapping, not that a real AI independently planned the three scenes or that live alignment detected real speech. No real semantic planner call or audio alignment has been validated; the requested acceptance scenario remains unverified. The sample does not establish that all historical/scientific treatments are supported by any renderer. No asset generation, renderer compatibility adapter, actual clip generation, publishing integration, retry/resume, distributed security or UI was added. Repeated words are matched monotonically and exact phrase occurrence is explicit; ambiguous repeated word deletions remain a recognizer ambiguity and are rejected when transcript coverage fails. Additional adversarial, human-reviewed, real-audio and model-output tests are required.
