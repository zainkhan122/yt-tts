# Optional agent pilot — current status

The repository is the authority. Inspect current Actions runs before restarting work.

## Scope / permanent switches

- Owner-approved **optional, non-publishing** comparison.
- Free OpenRouter variants only, **$0 paid inference**; encrypted Actions key is present.
- Limited provider training/retention approved for public sources and owned pilot drafts, not secrets/private data.
- No automatic activation or silent model/provider fallback.

## Explicit model-selection revision 2

- Producer: pinned free Nvidia Nemotron Ultra endpoint.
- Factual/visual critic: pinned free Google Gemma 4 31B endpoint.
- Audio critic: pinned free Nvidia Nemotron Omni endpoint.
- Inkling was rejected after a harness-only 403; no identity was spoofed. The revision is an explicit new evaluation choice, not a runtime fallback or a claim of equal quality.

## Executed evidence so far

- Initial data-policy-denied probes: `38070240895`, `38070412627`.
- Subsequent capability probes: `38072005635`, `38072331007`, `38072739967`; inspect their artifacts for individual failures. Producer structured evidence smoke passed; complete multimodal capability is not implied by that.
- Prior authoring attempt `38074358798`: Haiku case blocked by an upstream idle timeout inside an HTTP-200 response. Three attempted calls; no accepted candidate/render from that attempt. No publishing.
- Current inspected canary: **`38074907568`**, commit **`8c4e363`**, authoring was in progress at last check. Do not start another copy blindly.
- Stale-config probe `38076022733` was cancelled; no result should be claimed from it.
- Local full suite at `8c4e363`: **170 tests passed**. These are safety/contract tests, not proof of content parity.

## Still required before any qualification claim

Complete the live canary, inspect draft/critic/repair artifacts, render only accepted candidates, perform actual paired visual/audio assessment, and compare several baseline cases. Persist an honest report, including missing stages, quota/provider failures and unknown costs. Owner review plus unseen-topic validation remains necessary even if model comparisons look favorable.

The initial implementation includes source/evidence checks, bounded draft repairs and quarantined render/comparison jobs. Do not claim every proposed repair scenario has been exercised end-to-end merely because a unit test exists.

## Further measured trials
- `free-p3` / run 38074907568: 3 quality-blocked cases, 1 provider timeout and 1 cascade-held case. No render accepted. Detailed evidence and independent inspection are in `free-p3/ASSESSMENT.md`.
- `free-p4` / run 38076909677: controller research-loop budget ended before submission; this was a harness issue, not a content-quality measurement. Fixed by reserving the final tool round for a draft after sources were read.
- `free-p5` / run 38077608119: Gemini reached a hard-gate-passed revision after one draft repair; the independent critic returned 429 three times, honoring 60-second Retry-After. Remaining cases were held under the persisted cooldown. No render/publication. Cost receipts: 6 successful calls reported $0, 3 explicit rate rejections.
- An explicit critic-only resume path is now available for that unchanged, already gate-passed draft, after cooldown. It refuses unknown/uncertain outcomes, changed configs and failed gates. It does not replay the producer.
- A bounded visual-only repair tool is implemented and unit-tested; live post-render repair is NOT claimed demonstrated.
