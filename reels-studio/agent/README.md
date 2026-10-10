# Optional producer/critic lab — OFF for production

**Owner authorization:** build an optional producer + separate critic + hard-gate system, test it deeply against our existing work, and do not activate unattended publishing without demonstrated quality and explicit approval.

**Updated constraint:** use **free OpenRouter variants only**, $0 paid inference. `OPENROUTER_API_KEY` is an encrypted Actions secret. Do not ask for it again or copy it into the workspace/source. No paid fallback, no `openrouter/free` automatic router, no silent model substitution.

Pinned initial roles (subject to their actual measured performance, NOT an assertion of parity):
- Producer: `nvidia/nemotron-3-ultra-550b-a55b:free`, provider `nvidia`.
- Separate factual/visual critic (selection revision 2): `google/gemma-4-31b-it:free`, provider `google-ai-studio`.
- Audio specialist: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`, pinned Nvidia endpoint.
- Rejected initial critic: Inkling returned an approved-harness-only 403 and has additional data restrictions. No app identity was spoofed. This explicit selection revision is NOT an automatic runtime fallback, and does not establish parity.

Endpoint-version names, modalities and zero prices are rechecked before inference. Changed/unavailable providers or models block the pilot. Provider fallbacks are off; parameter support is required; provider data collection is allowed ONLY for public sources and owned pilot drafts, with explicit owner consent dated 2026-10-10. Secrets/private account data remain excluded from prompts. OpenRouter account-level free-model training settings can still block access.

## Trust boundaries

1. **Controller:** owns task limits, allowed tools, schemas and state. Model text is never executable code.
2. **Producer:** may read allowlisted public evidence, inspect asset manifests and propose a structured brief. It has no Buffer/Google publishing credentials or queue-write tool.
3. **Critic:** fresh context, independent model; reviews factual support, originality, asset authenticity and final frames/audio. Its score cannot override a hard gate.
4. **Deterministic renderer:** existing templates + pinned Option 3 narration. No model-selected voice or arbitrary render code.
5. **Existing publisher:** remains separate. Pilot outputs never enter `queue/publish.json`, YouTube queues, Pages hosting or social mutation endpoints automatically.
6. **Human/owner acceptance:** paired results and failure evidence must be reviewed. Passing model self-evaluations does not activate anything.

## Comparison contract

Use five matched baseline cases: Haiku pricing, Gemini enterprise agent, Mosa credits, Pomelli product images, and Whistle local speech. Producer does not receive our finished scripts. Record exactly which evidence/assets were supplied; curated asset use is not proof of autonomous asset discovery.

Assess factual correctness, unsupported/overstated claims, source recency, authenticity, script flow, visual clarity, narration, repair success, latency and cost. No invented accuracy percentages. Baseline Arena model cost is unknown and must not be reported as zero.

Inject defects: unsupported price, fabricated hands-on claim, missing asset, source-URL overflow, incorrect voice override, secret-bearing prompt, hostile source instruction and quota/provider drift. Failures must stop/repair or become visible holds—not silent downgrades.

**Promotion is deliberately unavailable in this pilot.** `production_enabled=false`, `publishing_enabled=false`, `qualification=unqualified`. Future activation would require complete comparative evidence, unseen-topic canaries, all hard gates and explicit owner approval.

## Current implementation status

The fixed/free API client and capability probe are being built/tested. A probe success is only proof that authentication, routing, tool output and image input work. It is NOT proof of equivalent research, writing or full video quality. Real comparison status is recorded in the pilot report, never inferred from unit tests.
