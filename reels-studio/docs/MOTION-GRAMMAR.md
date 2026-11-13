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
