# Shorts guidelines (v2, 2026-10-21)

This replaces PLAYBOOK §8A and the template system. There are no templates, no fixed scene
order, no fixed word counts, and no formula copy. The writer decides how each short is made.
The system checks only the hard rules in `studio/rules.py`, which protect facts, legal
safety, platform limits and the owner's rules.

## 1. Who the short is for

Write one sentence: **who is watching, and what situation are they in right now?**
A short that cannot name the viewer's situation in their own words is not ready.

## 2. The short's one idea

Write the idea in one sentence. If it needs two, make two shorts.
Ask: what does the viewer know after the short that they did not know before, and what
can they now do that they could not do before?

## 3. Proof, not description

Every claim in the short needs a proof plan:

- **capture:** a frame or clip from the capture pack (shown on screen);
- **source:** a dated, https source (read before it is spoken, if it can change);
- **owner_test:** something the owner ran and recorded.

A claim with no proof is cut or rewritten. A claim the viewer cannot see or verify is weaker
than one they can.

## 4. Shape follows the idea

Length, pacing, and scene count come from the idea. Some ideas land in 18 seconds, some need
50. Do not add a scene because a template has one; cut a scene if it does not earn its place.
There is no required opening type, middle type, or closing type.

Good openings put the viewer's situation on screen in the first second. Good payoffs deliver
the thing the opening promised. A "catch" (limits, cost, platform) belongs where the viewer
needs it to decide whether to try the tool, not in a fixed slot.

## 5. Copy, per platform

Write each platform's copy for that viewer on that platform:

- **YouTube:** a title that a searcher would type; a description that opens with the
  viewer's problem and gives the link; `#Shorts` plus 1–4 niche tags.
- **TikTok:** one line that makes the viewer stay; 2–5 niche tags.
- **Instagram:** a caption that reads like a note to a friend; 2–5 niche tags.
- **Facebook:** context for a reader who is not a developer; the AI-narration line is added
  by the system; 1–3 niche tags.
- **X:** one sharp line and the link; at most 2 tags.

Rules for all copy:

- Plain words, short sentences, the specific thing that broke or worked. No hype adjectives,
  no "game-changer", no "in this video", no "unlock".
- No credits, attribution, capture dates or "own captures" in visible copy. Credits live in
  the kit's credits file only.
- No generic tags (#AI, #Coding, #Video, #Tech, #viral, #fyp). Tags name the tool's audience
  or task (#ClaudeCode, #MacApps, #WebDev, #LandingPage).
- Every platform gets its own copy. Identical text on two platforms fails the check.
- Hashtags and the AI-narration line are not typed into the copy; the system adds them.
- Links are https only.

## 6. Learning from other creators (reference channels)

For each new short on a reference channel, record the delivery, not just the idea:

- title, hook (first 3 seconds and first spoken line), script in short form,
- description, hashtags, and the media used (what is shown, how long, what is on screen).

Write one row per short in `research/reference-study/YYYY-MM-DD.md`: what worked, what
the creator did in the first second, how the proof was shown, how the copy opened.

Use it to learn. Never copy a structure, a title, or a line. Take the principle
(for example, "the first frame already shows the problem") and apply it to our own idea
and our own footage.

## 7. Review before scheduling

A short is reviewed before it is scheduled. The review asks:

1. Does the first second make the viewer's situation obvious?
2. Is every claim covered by a proof plan that the viewer can see or check?
3. Does the copy sound like a person who used the tool?
4. Would I watch this to the end if I were the viewer?

If the answer to any is no, rewrite the part that fails. Do not patch it with a formula.
The review date and expiry go in the brief's `review` block. Facts are re-checked when the
review expires.

## 8. What the system enforces (hard rules only)

Run `python3 -m studio.check` (or `--show-final` to see the exact text per platform).

- Brief: no `template` field, no `credits_on_screen` field; required fields present;
  viewer's problem stated; scenes have a `type` and a spoken line (or a hold); spoken length
  fits the duration; a licence or legal term is not in the opening scene.
- Claims and proof: every claim has an https source and a proof plan entry; capture evidence
  exists in the capture pack; the review has not expired.
- Copy: final text (with hashtags and disclosure) within platform limits; no credits,
  promotional wording or placeholders; no generic tags; the YouTube title is 1–100 characters
  and the YouTube tags include `#Shorts`; https links only; the AI-narration line is on
  Facebook when the voice is synthetic; identical copy across platforms fails.
- Schedule: the day's random count (1–5) is recorded before the first post and matches the
  number of distinct videos scheduled that day (`studio/draw.py`).

Warnings (for example, promotional wording in a spoken line) are for the reviewer to decide.
Errors block the brief from being scheduled.

## 9. Measure, then adjust

After a short has run for a week, record the 3-second hold, average watch time, and the
comments that mention the problem in the viewer's words. Use these to choose the next idea.
Do not reuse a structure because it worked once; reuse only what the numbers show.

## 10. Not allowed

- Templates or scene orders stored in briefs, lint rules, or copy formulas.
- Editing a published post's copy to fix a rule after the fact; fix the next one and record
  the miss.
- Scheduling without a recorded draw, a passing check, and a passing production gate.
