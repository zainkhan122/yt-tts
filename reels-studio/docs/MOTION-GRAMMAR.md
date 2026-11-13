# Narration-led chart and scene motion

This is the implemented `pulse` pilot, not a claim that every template has been upgraded or that a short is publish-ready. Every animation must be a deterministic function of `setTime(t)`, including backwards seeking for frame capture.

## Narration to visual

1. Beat plans specify meaningful `cue_phrases`. The pulse engine matches consecutive normalized narration tokens to the aligned word timestamps. Missing cues use a timed stagger, so a fallback is not evidence of precise sync; inspect the rendered audio/video.
2. Give each scene one clear headline, then place the evidence below it and reserve the caption band. Do not use chart decoration merely to make frames move.
3. Reveal chart elements when the narrated entity or claim is spoken. In the Seedance pilot, the independent leaderboard rows build at “Seedance” and “Veo”; specs build at “two K,” “fifteen” and “lip sync”; cost choices build at “free” and “fourteen”; the catch rows build at “China,” “self reported,” “independent,” and “prompts.”
4. The scene entrance is a deterministic 0.28 s ease/16 px slide from 70% opacity, without a blank or overlapping prior scene. This is not a generic claim that fades or shifts alone are high-quality transitions. Design a transition around the story and check it at full speed.
5. The captured leaderboard is drawn on a zero-based proportional scale using only the two numbers in the existing source note. A historical snapshot is not live data: verify values, scope, ranking, availability and price from authoritative dated sources before publication. Never label the independent value as a vendor score or infer the runner-up's rank from these two rows.

## Quality checks

- `python3 -m pytest tests/test_pulse_story_motion.py -q`: exercises multi-word cue matching, visual reveal timing, bar proportions, comparison ordering and catch sequencing in a real browser.
- `python3 tools/house_gate.py <built-stage.html>`: basic house layer and band checks, not an editorial, sync or motion-quality review.
- Review the full MP4 at phone size with audio: hook readability at frame zero, that each claim is shown when spoken, no meaningful content appearing prematurely or too late, clear data labels, natural scene rhythm, sound/artwork quality and the established house outro. A montage of stills is not a motion review; pixel delta is not an engagement metric.
- Current pilot uses existing locally aligned Kokoro preview audio; production remains Chatterbox with its own word timings and QA. Retest cue accuracy using the actual final voice. No media is approved merely because a test passes.

## Extending it

Build a small palette of chart grammars (comparison, before/after, process, timeline), each driven by actual sourced data and word cues. Provide fallback behavior and tests for missing words, text overflow, scene boundary timing, rewinding and narrow-phone legibility. GSAP is vendored; use it only if the timeline is explicitly seekable. Three.js is appropriate for genuinely spatial scenes, not required for 2D data graphics.

## Cross-template rollout (in progress)

`graphics/templates/motion.js` resolves exact, normalized contiguous spoken-word cues and records `window.__motionCueReports` with fallback status. Cue timing is deterministic and bounded; a fallback is a warning for editorial review, not proof of synchronization. Pulse, redline, design-review, photo-to-3d, musike (selected beats), and velocity-black (lane chart) use the shared resolver. The remaining legacy archetypes, including negative and the base engine, retain their existing choreography: this is not yet a complete cue-by-cue conversion. The house gate checks caption bands, single visible caption/handle, and the established outro, not aesthetic quality or factual accuracy.

Seven real storyboard plans have passed synthetic-timing house checks; synthetic speech timings do not establish real voice sync. A redline test was also rendered against word-aligned Kokoro preview narration (not production Chatterbox). Review found and corrected a mismatch between its spoken TOKENS CTA and the on-screen LIMIT keyword, with a cross-template CTA regression test. The redline numerical stamp now begins when its narrated number is spoken; Sherlock lanes and Musike selected interface changes use spoken cues. Remove unsupported benchmark comparisons rather than drawing arbitrary bars. The IDOL SSIM graphic displays the cited 0.726, not invented competitor values; the wider narration and all historical/current factual claims still need source verification before publication. Visual scale/legibility on design-review and photo-to-3d and full playback of every template remain outstanding. Regenerate with final Chatterbox voice and review timing, fallback reports, legibility, source provenance and transitions end-to-end.

## Latest wiring and remaining coverage

The negative template now binds its category rows, comparison plates, trace start and loss callout to narration; its illustrative categories no longer have unequal pseudo-data bars and its unsourced timing number has been removed. `render()` writes `motion-cues.json`, reports unmatched shared-JS phrases, and supports `MOTION_CUES_STRICT=1` to refuse encoding when one is unmatched. This strict mode covers only cues that actually use `HouseMotion`, not all visual events and not the separate Python cue fallbacks. The pipeline already returns Python `cue_fallbacks` via `graphics.stage.render_for_pipeline`; review both reports. An empty report is not evidence of full coverage.

A browser regression checks seven real storyboard fixtures for page errors, house layers, deterministic visible DOM on backwards seek, matching CTA keywords, and a negative list's word-cued reveal. Synthetic timings and a one-second renderer smoke test are not a production voice review. Important remaining work: inventory every archetype, add explicit cue contracts and meaningful choreography for those that still use scene-relative staggers (including many legacy velocity-black and Musike beats and default engine's separate Python binding), reconcile the Python and JS semantics, ensure reports include every event and cover missing words in strict mode, source and label all actual charts, inspect transitions and phone-scale layouts, and render/review every template with final Chatterbox narration. Do not mark the entire narration-led system fully wired before those checks.
