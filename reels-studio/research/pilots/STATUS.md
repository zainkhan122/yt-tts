# Optional agent pilot — current state

**Decision: OFF / UNQUALIFIED.** Read `PILOT_REPORT.md` for the measured comparison and its limitations. Unit tests and capability smoke checks are not parity certification.

## Policy / model lock

- User-authorized, optional, non-publishing lab; no cron or automatic promotion.
- Free OpenRouter variants only; $0 paid inference, no model/provider fallback.
- Public sources/owned pilot drafts may be processed under the owner's explicit provider-training consent. No secrets/private account/workspace data in prompts.
- Selection revision 2: Nvidia Nemotron Ultra producer; Gemma 4 31B factual/visual critic; Nvidia Nemotron Omni audio specialist.
- Inkling rejected after approved-harness-only access restriction. No identity was spoofed; no runtime fallback was performed.

## Latest executed outcomes

| Run | Result |
|---|---|
| `38074907568` / free-p3 | Content/schema/evidence failures and a provider timeout; no accepted render. |
| `38076909677` / free-p4 | Controller research-loop budget exhausted; fixed by reserving final submission phase. No quality pass inferred. |
| `38077608119` / free-p5 | One Gemini revision passed structural/evidence gates; independent critic rate-rejected. Remaining cases held. |
| `38078521580` / first critic-only continuation | Critic still 429; no producer replay/render. |
| `38087301857` | Artifact-name mismatch blocked before inference. Fixed with an explicit, allowlisted artifact selector. |
| `38087458049` / latest critic-only continuation | Same immutable draft/config revalidated; three 429 responses honoring Retry-After. No render. |
| `38088167421`, `38088329564` / audio transport tests | Endpoint rejected tool-choice values despite catalog advertisement. No listening result. |
| `38088477850` / plain-JSON audio test | Pinned endpoint required at least $0.50 balance for audio. No funding or cap change; no listening result. |

Stale-config probe `38087078914` and earlier redundant probes were cancelled and are not quality evidence.

## What is and is not demonstrated

- Primary-source retrieval, registered captures/provenance, bounded drafting and evidence/schema rejection are exercised.
- One automatic quote repair reached structural gate acceptance; this is not semantic certification.
- **No candidate cleared all pre-render checks. No full candidate/baseline visual or voice comparison exists.**
- Bounded visual-only repair is implemented and unit-tested, but not live demonstrated.
- Local complete safety suite: **194 passed** at this checkpoint. Check the latest cloud safety run/report separately.
- Deduplicated content-trial cost: 47 successful $0 receipts, 9 explicit rejections, 1 incomplete/missing provider cost receipt across 57 attempts. Baseline Arena cost is unknown.

## Exact next safe action

Do not activate or blindly regenerate the producer. If the fixed critic becomes usable, resume only its explicitly rejected operation on the saved Gemini revision. Use the `source_artifact=resumed-pilot-evidence` selector when continuing run `38087458049`; preserve its prior receipt ledger. If the Actions artifact has expired, `free-p5/full-checkpoint-archive.json` points to a verified complete archive.

If model, provider, prompt/harness policy or inputs change, create a new explicit evaluation revision/pilot and disclose the change. Never call a weaker/paid substitute merely because a free endpoint is unavailable. Any later promotion still requires all five paired evaluations, owner review and unseen-topic canaries.

## Recovery verification
The complete latest blocked checkpoint was restored from its immutable Release archive and **all 156 files matched byte-for-byte**. Critic-resume validation passed without sending inference. Use `checkpoint_source=archived-free-p5` in `agent-resume-critic.yml` if the transient Actions artifact is gone. No producer call needs replaying.

Final cloud safety regression **38089170017** passed **194 tests**, with zero failures/errors, no model/social credentials, and production files unchanged.
