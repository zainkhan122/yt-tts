# Automated semantic-to-layer planning — isolated development stage

## Audit / reuse

`semantic.py` defines the existing beat/event contract and checks complete ordered word ranges and asset links. `alignment.py` rejects estimated timing for the strict in-process path; `scheduler.py` anchors phrase events to actual accepted word timestamps and rejects beat overruns. `execution.py` selects configured generation providers but has no verified real image/video provider. `layer_renderer.py` composes local image/video layers with position, scale, rotation, opacity, camera scale/vertical movement, and cut/fade. `build_battery_demo.py` is an authored reference, not a generic planner. The existing OpenRouter pilot client is `paused_by_owner`; this phase does not enable it, change policy, or make requests.

## New route

`automated_planner.generate_and_compile` takes a caller-provided planner, exact narration, `Alignment` result from the existing in-process service, a local asset catalog, optional context and explicit fallback pairs. It:

1. Runs the existing strict audio/transcript alignment check before invoking the planner.
2. Sends word timestamps, semantic context, catalog descriptions (not local paths), and the layer renderer's actual supported operations/easing/transitions in a provider-neutral payload.
3. Validates the model response against the existing semantic contract and its additional layer, rationale, asset, animation and explicit-fallback contracts. It applies basic specificity checks, rejects missing assets, unknown operations, no-op motions, invalid targets, unsupported transitions, unapproved fallbacks and same-property chains the renderer cannot express.
4. Calls the existing strict scheduler, then `layer_renderer.compile_timeline`. Those components validate actual timing boundaries, audio/asset hashes and executable numeric values. A caller may then invoke `layer_renderer.render` for review.

`automated_openrouter.OpenRouterVisualPlanner` is a thin adapter around an **already authorized and preflighted** existing `OpenRouter` client. It does not initialize or authorize the client, activate the paused pilot, or use a new API. No inference request was made. No external model, service, or capability has been verified in this phase.

Catalog input maps safe IDs to `{path, sha256, type, description}` for existing local files. The provider sees only ID, type and description. The model response has `semantic_plan`, `layout`, `rationale`, and `fallbacks`. Each layout layer also links to its semantic asset; every event maps to a renderer operation and a specific layer. Fallback pairs must be authorized by the caller, and the response must explain each deviation. The resulting plan, scheduled timeline and renderer instructions are returned separately; there is no publishing integration.

## Tests

From the repository root:

```
python3 -m pytest -q graphics/production/test_automated_planner.py graphics/production/test_layer_renderer.py tests/test_visual_execution.py tests/test_production_alignment_semantic.py tests/test_beat_production.py graphics/tests tests/test_voice_handoff.py
```

The unrelated weather-shaped test uses a **hand-authored fake provider response**, synthetic word observations and silent audio to exercise the contract; it is NOT the requested independent AI acceptance test. It does render an MP4 to exercise the bridge. The battery video is preserved as a hash-checked regression fixture and was not re-rendered or modified.

## Limitations and acceptance status

The requested real AI acceptance test **has not run**: no authorized unpaused semantic planner or real local faster-whisper alignment was available. There is no independently planned unrelated-topic video to inspect. A permitted real provider, model, actual house-voice narration, valid per-word alignment and matching real assets are required before running that test.

The specificity check is a heuristic: it can reject short generic language but cannot prove physical accuracy, truthful representation, audience relevance, visual quality or that a suggested static image contains the described object. Human audiovisual review is required. The output cannot create assets; it selects from the supplied catalog. A semantic plan may request a treatment that cannot be visually achieved with those assets, even if a basic transform technically validates. No segmentation, fluid simulation, real 3D, general chart renderer, advanced camera motion or automatic SFX is added. The caller must not use transform-only fallback as evidence of a physical process. Model prompt injection remains a risk; input is untrusted data, but prompt text is not a security sandbox. The in-process alignment receipt is not cryptographic attestation, and code/model trust and per-word confidence require separate assessment. No owner approval, dedicated cover, house outro or publishing gates are changed.
