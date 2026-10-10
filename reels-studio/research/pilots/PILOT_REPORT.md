# Hypeless optional producer–critic pilot

## Decision: NOT QUALIFIED — remains OFF

The optional system has **not demonstrated the quality/reliability of our Arena-assisted production workflow**. It must not be activated. No candidate was permitted to bypass an evidence/critic gate, no pilot video entered the production queue, and no pilot content was posted to social platforms.

This is an honest **pre-render comparison and infrastructure assessment**, not a completed five-video visual/audio A/B trial. The failed earlier stages are meaningful results; the unexecuted later stages are not counted as passes.

## What is installed

- Versioned producer and independent critic prompts, closed schemas, a five-case baseline manifest, primary-source tools, immutable source/asset hashes and provenance records.
- Fixed free model/provider/version locks; zero-price request limits, zero-dollar key cap, no automatic fallback, bounded calls and persisted failure/cooldown receipts.
- Separate factual/script criticism, isolated Option-3 rendering, paired anonymous frame/audio comparison code, and a bounded visual-only repair tool that cannot rewrite narration, facts, metadata, voices or policy.
- Read-only pilot workflows: no cron, production queue writer, social credentials or auto-activation command.
- Recovery entry points: `RESUME.md`, `CURRENT_STATE.md`, versioned policies, provider journals and archived checkpoints. Secret handling is documented in `docs/SECURITY-BOUNDARIES.md`.

### Explicit model selections

| Role | Pinned free model | Observed limitation |
|---|---|---|
| Producer | `nvidia/nemotron-3-ultra-550b-a55b:free` | Can read sources and submit structured drafts; content and evidence-binding problems remain. |
| Factual/visual critic | `google/gemma-4-31b-it:free` | Repeated provider 429 responses, including after an hours-long gap. No independent acceptance was obtained for the pending candidate. |
| Audio specialist | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | Advertised tool-choice values were rejected. Plain JSON transport reached a separate **minimum $0.50 balance requirement for audio**. No funds/cap changes or paid fallback were made. |
| Rejected initial critic | `thinkingmachines/inkling:free` | Approved-harness-only 403; no application identity was spoofed. Replacement was an explicit selection revision, not a runtime downgrade. |

The owner's limited training/retention consent covers public sources and owned pilot drafts only. API keys, OAuth credentials and private account/workspace data are excluded from prompts.

## Measured content trials

| Trial | Actual outcome |
|---|---|
| `free-p3` — [run 38074907568](https://github.com/zainkhan122/yt-tts/actions/runs/38074907568) | Several drafts/repairs across the five topics. Gemini, Haiku and Whistle did not clear all gates. Mosa hit an upstream HTTP-200/504 timeout during repair. Pomelli was not meaningfully evaluated after the controller halted. Zero accepted renders. |
| `free-p4` — [run 38076909677](https://github.com/zainkhan122/yt-tts/actions/runs/38076909677) | Research-tool loops exhausted the budget before submission. This exposed a **controller phase-design flaw**, not a valid judgment that every model-written fact was wrong. A final submission phase was then reserved. |
| `free-p5` — [run 38077608119](https://github.com/zainkhan122/yt-tts/actions/runs/38077608119) | Gemini reached structural/evidence gate acceptance after one repair. The independent critic was rate-rejected three times. Remaining cases were held under cooldown. Structural acceptance was NOT treated as factual certification. |
| Critic-only continuation — [run 38078521580](https://github.com/zainkhan122/yt-tts/actions/runs/38078521580) | Same unchanged draft; no producer replay. Critic still rate-rejected. |
| Later continuation — [run 38087458049](https://github.com/zainkhan122/yt-tts/actions/runs/38087458049) | Revalidated config, source/brief hashes, hard gates and explicit rejection receipts. Critic returned 429 at 21:24, 21:25 and 21:26 UTC, honoring 60-second Retry-After. No render/publication. |

A continuation attempt using the wrong artifact name failed **before inference** (`38087301857`). The artifact selector was corrected and regression-tested; this was not blamed on the model. The stale-config probe `38087078914` was cancelled, not counted as a quality result.

## Comparison findings

| Dimension | Finding versus the existing baseline |
|---|---|
| **Factual correctness** | Not at the required bar. The Gemini draft uses Fortune-100 adoption statistics to support an organization-only/personal-account exclusion; that evidence does not establish the asserted access requirements. Earlier Haiku/Whistle drafts also contained unsupported/poorly bound statements. |
| **Authenticity** | Provenance checks blocked invented hands-on attribution. The producer was told that supplied recordings were existing studio evidence, not a fresh experiment it had performed. End-to-end autonomous rights judgment and novel asset discovery are **not proven**. |
| **Script quality** | Manual audit found broader, less focused feature lists, awkward naming such as `HAIKU55`, overlength drafts and missing important caveats. A corrected schema/quotation interface is necessary but does not itself fix editorial taste. |
| **Visuals** | Candidate rendering was blocked before this stage. Existing templates and fresh screenshot tools are available, but **no candidate-versus-baseline visual parity result exists**. |
| **Voice** | Option 3 remains locked. No accepted candidate voice was rendered. The real-audio specialist test was blocked by provider capability/balance requirements, so **listening quality is not claimed assessed**. |
| **Repairs** | One bounded quotation repair demonstrably brought the Gemini draft through structural gates. Other repairs did not reach acceptance. Post-render visual repair is implemented/tested as a constrained tool, but **not live-demonstrated**; it must still be verified end to end. |
| **Reliability** | The free critic route did not provide reliable access during this test window. This alone prevents dependable unattended operation with this configuration. |

### Examples from the preserved drafts

- **Gemini:** “nearly 90% of the Fortune 100 use Gemini Enterprise” is not evidence that personal accounts are excluded or that a specific organization contract is universally required. The baseline used a narrower enterprise/access caveat.
- **Haiku:** the early draft crowded pricing, benchmarks and security-policy material into one short; an overlength draft persisted after repair. Some quote failures were typography/interface problems and are explicitly distinguished from fabricated facts.
- **Whistle:** the earlier candidate omitted important seven-language/30-second limitations from narration and introduced an ungrounded cloud-accuracy trade-off. That is less careful than the baseline's qualified account of the real recorded test.

## Tools and safety testing

The full local regression suite now passes **194 tests**. Coverage includes fake quotes, unread/tampered sources, fabricated testing, unbound metrics, illustration-as-evidence, missing/unsafe assets, HTML/path/SSRF targets, archive traversal, voice overrides, attempts to publish, secret-bearing prompts, model/provider drift, nonzero prices, unknown costs, quota limits, lost responses, corrupted candidates, constrained repairs and safe critic-only continuation.

Additional fixes stop all further model calls after ambiguous/persistent provider errors, reject a changed model/provider after preflight, and recheck the zero-price ceiling before each inference request.

**These tests validate mechanisms, not human-level content quality.** A model's own pass/score cannot waive a gate or activate the system.

## Cost: measured, unknown and rejected are separate

Deduplicated content-trial receipts across `free-p3`, `free-p4` and the latest `free-p5` chain:

- **57 attempted requests**.
- **47 successful cost receipts reported $0**.
- **9 explicit rate rejections**.
- **1 failed provider request lacks a completed cost receipt**; it is not fabricated as a measured zero.
- The key has a zero-dollar spending cap and requests restrict endpoint prices to zero.
- Baseline Arena monetary cost is **unknown**. Candidate rendering compute was not incurred because no candidate cleared all pre-render checks. Capturing/preparing sources and test runners still consumed compute time; free model inference is not a claim of zero infrastructure use.
- Earlier calls lack latency fields. The sum of recorded request seconds is only a partial measured total, not the total trial runtime.

Audio capability diagnostics are separate from these content-trial totals: two explicit tool-choice rejections, then the balance-gated request. They produced no completed listening assessment and no candidate video.

## Recovery and evidence

- `free-p3/ASSESSMENT.md` and `free-p4/ASSESSMENT.md` separate content weaknesses from controller defects.
- `free-p5/audit-evidence.tar.gz` preserves sanitized text/source/draft/receipt evidence and is byte-verified.
- `free-p5/full-checkpoint-archive.json` pins the complete working checkpoint by immutable Release asset ID/digest. It was archived by the trusted operator; **the model/pilot workflows have no Release-write permission**. It contains registered baseline media and checkpoint data, no secrets or candidate videos.
- Archive recovery was actually exercised: **all 156 restored files matched byte-for-byte**, and unchanged critic-resume validation passed without inference. The continuation workflow can restore this registered archive after transient Actions artifacts expire.
- A new session must inspect the current run/checkpoint before retrying. Resume only the explicitly rejected critic operation, never replay an uncertain producer call or overwrite a posted-video receipt.

## What would justify a later attempt?

1. Stable, permitted access to the selected free critic/audio capabilities, or an **explicitly approved new model configuration**—not an automatic fallback.
2. Accepted evidence-linked drafts across all five cases, followed by real renders and independent paired frame/audio reviews.
3. A live, bounded repair demonstration and non-regression checks.
4. Owner review, then unseen-topic non-publishing canaries. A small successful sample would still not prove universal parity.

Until then: **optional producer/critic OFF, existing deterministic publishing unchanged.**
