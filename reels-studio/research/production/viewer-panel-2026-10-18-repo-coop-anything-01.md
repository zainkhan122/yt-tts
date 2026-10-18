# Viewer panel: repo-coop-anything-01 — **FAIL**

Video: `repo-coop-anything-01.mp4` · 48.8 s · reviewed 2026-10-18 by opening all 7
extracted frames (3.5 s / 10.5 s / 17.4 s / 24.4 s / 31.4 s / 38.3 s / 45.3 s) and
scoring as a viewer, not as the producer. This is the first panel run under the
2026-10-18 media standard; it was run *after* the video had already been scheduled
in Buffer for 2026-10-19 — which is exactly the process failure the panel exists to
prevent. Panels run before queueing from now on.

## What the frames actually show

| t | Frame | Verdict |
|---|------|---------|
| 3.5 s | "NEVER MEANT FOR FRIENDS" text hook on empty gradient | Strong words, zero product. Nothing to stop a thumb except the claim itself. |
| 10.5 s | Fake terminal mock (generated graphic, "R" typed into an empty black box) | A *drawing* of a terminal, not a real capture. Reads as stock filler. |
| 17.4 s | Narrow PIL list card ("ALREADY PLAYABLE TOGETHER") floating in a mostly-empty stage; credit line clipped mid-sentence ("visual made for this…") | Card-only scene + a visible text-overflow defect the 8/8 QA passed. |
| 24.4 s | "BEFORE YOU GET EXCITED" catch/good text cards | Honest content, but still typography on gradient. No proof anywhere. |
| 31.4 s | **Empty stage** — heading + "THE HONEST CATCH:" with a giant blank middle | The placeholder-stage failure, shipped. A viewer sees a broken video. |
| 38.3 s | "MEET CO-OP ANYTHING" intro card near the end of the video | Card-only again; the actual GitHub repo page never appears in the whole video. |
| 45.3 s | "HOW IT WORKS" steps card + caption | Three numbered lines on a card where a real agent/terminal run should be. |

**Real product media: 0 of 7 frames (0%).** No repo page, no real terminal run, no
gameplay, no UI. The entire video is generated text cards over an empty gradient —
precisely what the channel decode says losers do, and what the owner flagged.

## Persona verdicts

- **Cold scroller**: SWIPE — "Big text, nothing happening. Next."
- **Niche dev/gamer**: SWIPE — "You claim an agent builds co-op mods and show me a fake terminal with one letter typed. Show me the repo or it didn't happen."
- **Curious outsider**: SWIPE — "I get 'old games with friends' from the words, but there's nothing to look at, and at 31 s the screen is just… empty."
- **Saver/searcher**: SWIPE — "Nothing to save. No demo, no steps I can follow, no link moment worth coming back for."
- **Skeptic**: SWIPE — "Zero proof in 49 seconds. This is AI-slop formatting: gradient, yellow highlights, empty stage. The clipped credit line confirms nobody watched it."

## Scene-by-scene media check

- [ ] every scene has real media or a justified graphic — **NO** (empty stage at ~31 s; card-only scenes throughout)
- [ ] real product media covers >= 60% of scenes — **NO (0%)**
- [x] first frame sells the benefit muted, in the first 3 s — words yes ("NEVER MEANT FOR FRIENDS"), product no
- [x] one-sentence takeaway: "An AI agent turns your old solo games into co-op you can play with friends." (The *script* is fine — the visuals never prove it.)

## Panel result: FAIL

Triggers hit: majority swipe in 3 s · empty/placeholder stage present · real-media
coverage 0% (< 60%). Under the media standard this video returns to production:
rebuild with `capture.py` on the real repo (README, mod directory, per-game pages),
the project's own demo media if published, and cards only as support graphics.
The 8/8 automatic QA score measured technical validity only and is not a ship
decision — see PLAYBOOK §8.

Note: Blender MCP and Earshot (2026-10-18 batch) were built the same card-based way
and went out before this standard existed; treat their numbers as the card-only
baseline, not as a format to repeat.
