# Free-p3 — failed pre-render comparison, not qualified

Run: https://github.com/zainkhan122/yt-tts/actions/runs/38074907568  
Source revision: `8c4e363`  
Scope: five matched existing topics; fresh source reads and registered capture pool; no publishing.

## Observed result

| Case | Outcome before rendering |
|---|---|
| Gemini agent | Three draft versions; final evidence quotation and metric binding still failed. |
| Haiku 5.5 | Three draft versions; non-matching quotations, metric binding and 143-word narration beyond the 140-word limit remained. |
| Whistle | Three draft versions; final quotation still failed. Earlier revision incorrectly attributed a source claim as recorded-test evidence. |
| Mosa | Initial schema error, then provider idle-timeout error inside HTTP 200 during repair. |
| Pomelli | Not meaningfully evaluated: the controller halted after the preceding uncertain/provider-invalid result. |

**Zero candidates cleared all pre-render gates.** Rendering and paired frame/audio comparison were therefore skipped. There are no new candidate videos from this run and no evidence of visual/voice parity.

## Cost accounting

17 attempted inference requests: 16 successful cost receipts reported $0; one HTTP-200/504 provider failure had no completed usage receipt in the artifact. The previous summary's `unknown_outcome_calls=0` was too narrow (it counted only the literal `uncertain` state). This is corrected in the harness: a policy-blocked HTTP-200 request with no usage is also an unknown/missing cost receipt. The OpenRouter key has a zero-dollar limit and route prices are restricted to zero, but missing usage is still not fabricated as a measured zero.

Baseline Arena monetary cost is unavailable. No paid route or model fallback was authorized.

## Independent inspection of the drafts

These are qualitative findings, not invented accuracy percentages:

- **Gemini:** the script adds a strong “org contract” access assertion and attempts to use Fortune-100 adoption as support. Adoption statistics do not establish the exact contract/eligibility requirements. This is less careful than the baseline's narrower enterprise/access caveat.
- **Haiku:** the output opens with the unnatural token `HAIKU55`, crowds in benchmark/security-policy details and remains over length after repair. This weakens the focused pricing story. Some quote mismatches are typographic rather than evidence of false facts; they must not all be labelled hallucinations.
- **Whistle:** the draft usefully acknowledges the recorded browser result, but foregrounds the author's M4 timing without equally clear attribution, omits the important seven-language/30-second constraints from narration, and ends with a “trade cloud accuracy” premise not established by the cited comparison. This is not accepted as matching the baseline.

## Harness issues separated from content quality

All initial drafts used string `"1"` rather than integer `1` for the protocol version. The schema declared `const: 1` without an explicit numeric type; free-p4 adds `type: integer` and `enum: [1]` while preserving strict validation. The evidence matcher also treated curly and straight apostrophes/dashes differently. Free-p4 normalizes typography only, not words, numbers or negation, and supplies a bounded exact-passage lookup tool.

These are transparent controller-interface improvements, not permission to ignore unsupported claims, change voices, loosen the word budget, skip critics or activate publishing.

## Decision

**Optional system remains OFF / unqualified.** The next trial must supply new evidence. Passing safety tests is not evidence that this failed content matched the human-guided work.
