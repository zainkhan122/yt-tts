# Viewer-first Short scripts

Apply to every new script; do not change already approved or scheduled videos. Start with the viewer's concrete result or problem—not an announcement, product release or project biography. A question is optional, not a requirement. Vary the hook to fit the actual viewer job; never force a sensational formula or add an invented date, number, cost saving or guarantee.

## Write and review
1. In research, identify who the video helps, what they can do after watching, the best available evidence, and the one caveat that matters to them.
2. Draft at least three truthful first-sentence options: outcome, problem-to-result and a curiosity gap. Select the clearest and strongest, not automatically the highest heuristic score. Do not imply novelty with “now” unless timing is verified.
3. Put that outcome in the first sentence. Name the tool naturally soon afterward; show a real or honestly labelled illustrative result early, then connect input → process → output. Each line should answer “what does this do for me?” and lead to the next result. Use ordinary spoken language, short sentences, and transitions tied to the relevant action. No generic news framing or spec dump.
4. Pay off the hook within the Short; don't hold the useful result hostage until the CTA. Explain meaningful limits and costs in plain language; distinguish video draft generation from automatic publishing or a guaranteed usable result. Check accuracy, output and media rights.
5. Close with a viewer value recap and a single specific action when appropriate. Do not promise services we cannot provide.
6. Read the whole script aloud and record a short editorial judgment: viewer outcome, why the chosen hook matters, how the promised result is demonstrated, when the hook pays off, meaningful caveat, and reviewer. Human/agent review is mandatory; presence of these fields is not proof of quality. Compare against the viewer job and source, not word count alone.

## Pipeline contract
New plan-authoring uses `hook` (a statement or question) and `script_review` with nonempty `viewer_outcome`, `hook_reason`, `demonstration`, `payoff`, `caveat`, and `reviewer`. `tools/video_plan.py` blocks missing review fields for plans using the new hook form; `tools/brief_from_plan.py` preserves both the exact hook and review in the resulting brief. Old question-only plans are still readable and are not retroactively modified. `production_gate.py` verifies that a brief marked `viewer-first-v1` retains the review before rendering. Directly authored briefs must opt into this standard and carry the same review before their script is considered complete; omission on an unmarked direct brief is not automatically detected. The existing hook scoring tool is advisory: keyword/formula scores do not establish viewer value or predict retention.

For the next scripts, review results against first-party, age-matched retention and views when available; use small-sample analytics directionally, not as a promise. Specify the hypothesis before testing, change one major creative variable at a time, and do not infer causal lift from unequal-age or sparse samples.
