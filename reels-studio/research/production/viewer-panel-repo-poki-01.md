# Viewer panel: repo-poki-01 (round 1)

Video sha256: 72e3a71bf3914bf518a2e9982a619d5da789629ffde4e16e19e4b8d41b60a412
Release/artifact: Actions run `42260970838` (run 257), artifact `render-repo-poki-01` (13524909816), file
`repo-poki-01.mp4`, 40.37 s, 1080x1920, H.264/AAC, -13.9 LUFS, -2.0 dBFS peak.
Frames reviewed: 12 sampled frames at 1.0, 3.9, 4.6, 5.0, 5.3, 6.0, 9.5, 14.0, 17.6, 19.0, 26.5, 30.6,
31.4, 32.0, 38.5 s, plus the kit cover.

Rule in force (owner, 6 Nov 2026): generated graphics built from the tool's flow are the main media;
tool media is optional.

## Rule checks
- main media (generated graphic) in 12 of 12 sampled frames: PASS. Every frame is drawn graphics; no
  tool screenshot, no text-only card.
- hook names the tool on screen: PASS. Frame at 1.0 s reads "CAN POKI USE YOUR IPHONE?" with the karaoke
  caption "EVER WANTED AI TO"; `short_qa` `hook_anchor` passes on the tool name.
- hook and CTA are generated flow graphics: PASS (flow_link, then the CTA stack with COMMENT IPHONE).
- no label overflow or overlap: PASS. The terminal, the toggle steps, the chips and the CTA pills all sit
  inside the safe area; nothing crosses the bottom 330 px.
- sync: PASS. Terminal lines, toggle rows, flow nodes, chips and captions land on the words being spoken
  (checked frame by frame against the karaoke band); the caption band tracks the voice throughout.
- empty stages: NOT CLEAN. See finding 1 below.
- captions: PASS. Rolling three-word band, keyword highlighted, no line longer than two rows.

## Persona verdicts
- Cold scroller: PASS. The phone with a tap ripple and a ref tag is legible at phone size; the question
  in the headline does the work without sound.
- Niche dev/tinkerer: PASS. "MCP server", "Claude Code or Codex" and the real `./bin/setup` command are
  read as credible, not as marketing.
- Curious outsider: PASS with a note. The catch lands (it controls the real phone; the screen goes to
  your model service), but the Mac + Xcode requirement is the third chip and arrives late.
- Saver/searcher: PASS. The keyword is spoken in the hook, on screen in the first three seconds, and in
  the title, the description and one hashtag.
- Skeptic: PASS with a note. Nothing is invented: every claim is in the repo's README, `docs/tools.md`
  or `docs/verification.md`. The weak point is that the terminal is a drawn mock-up, which finding 1
  makes worse by sitting empty for a beat.

## Findings (not panel failures)
1. **Empty terminal, ~2.4 s.** The point1 terminal window appears at 3.79 s with no text and stays empty
   until the first command types after ~6.2 s, because the lines are bound to "run the setup script" and
   "start it", which are late in the sentence. It reads as a stalled frame. Fix: give the scene an earlier
   `cue_phrases` entry (e.g. "Poki") or a short prompt line that types at the scene start. Needs a
   graphics change and a new render (new input fingerprint).
2. **Node order in point3.** At 19.0 s "YOUR TASK" and "RESULT ON SCREEN" are on screen while the middle
   node is still to come, so the flow reads out of order for about a second. Fix: bind the middle node to
   an earlier phrase.
3. **Catch chips arrive late.** The third chip (Mac with Xcode) lands near the end of the line. It is the
   cost that most viewers care about, so it should arrive first or be the highlighted chip.
4. **Cover and hook differ by one word.** The pinned cover asks "CAN AI USE YOUR IPHONE?", the video's
   first frame asks "CAN POKI USE YOUR IPHONE?". Both are true and both pass COVER-RULES; the mismatch is
   cosmetic. Changing it means a new cover pack and therefore a new render (the cover hash is a render
   input), so it is not worth doing on its own.

Panel result: PASS. Findings 1-4 are quality notes; none of them breaks a rule, and none of them is a
false claim. Finding 1 is the one worth a follow-up render if the owner wants this Short polished.

---

# Viewer panel: repo-poki-01 (round 2 — after the sync + end-card fix)

Video sha256: `c8b9d5752924ffe8a8166d4186570a0175e7cc2c3cc0dd6360032173b0894912`
Artifact: Actions run `42341933288` (run 259) on `8b50d96`, artifact `render-repo-poki-01` (13562771433),
40.37 s, 1080x1920, 30 fps, H.264/AAC, 13.06 MB. Voice job re-synthesised the take
(`vo_sha256 04692c95…`), whisper char match 99.8%, `word_diffs=poki`.
Frames reviewed: 20 sampled frames at 0.8, 2.4, 3.6, 5.0, 8.3, 9.6, 10.4, 12.2, 16.3, 18.2, 21.2, 23.2,
27.5, 31.0, 33.6, 35.3, 37.0, 38.3, 38.8, 39.9 s.

Owner's review of round 1 (the reason for this render): *"animations, TTS, kinetic text is out of sync.
Outro is shit"* + *"this pipeline already using an outro with channel logo and click on follow animation,
where is that???"*

## What changed
- **The outro is now the pipeline's own end-card.** Real Hypeless logo (`brand/logo/avatar-1080.png`),
  name + verified badge, `@hypeless`, the tagline, the spoken keyword `COMMENT IPHONE`, a FOLLOW button
  and a cursor that arrives and presses it (scale dip, white ring, label flips to "✓ Following").
  The press is the pipeline's `ev["press"]` = 38.65 s, the exact number the click SFX fires on.
- **Cues land on the spoken phrase** instead of a later word inside it, and the first element of a
  scene is on screen from the scene's first word.
- **Captions lead with the word being said**; the concept title is fully up 0.34 s after its cue.
- **The terminal is never a blank box**: `$` prompt + "● waiting" from the first frame, `● running`
  while typing, `✓ done` only when every line has typed.

## Rule checks (round 2)
- main media (generated graphic) in 20 of 20 sampled frames: PASS.
- outro = brand end-card with the real logo + click-to-follow animation: **PASS** (35.3 s card up,
  37.0 s keyword chip, 38.3 s cursor, 38.8 s pressed + ring + "Following", holds to the last frame).
- sync: **PASS**. Terminal prompt at 3.6 s while the voice says "it's called Poki", commands typed on
  "setup script"/"start it"; ticks 10.4/12.2; flow nodes 16.3/18.2/21.2 in sentence order; chips
  27.5/31.0/33.6 in spoken order; keyword chip 37.0 on "IPHONE"; press 38.65 on the click.
- empty stages: **CLEAN** (round 1 finding 1 fixed; the terminal shows its prompt from frame 1).
- cue fallbacks: **none** (`graphics` render stage reported 7 phrases / 7 scenes, no fallbacks).
- `short_qa video`: **PASS** — visual change 0.868, graphic-only 0.168, motion gap 0.75 s, WPM 178.9,
  longest pause 0.56 s, duration 40.25 s.

## Round-1 findings, status
1. Empty terminal for ~2.4 s — **fixed** (prompt + status from the first frame).
2. point3 nodes out of order — **fixed** (nodes renamed to the sentence's order and bound to their words).
3. Catch's Mac/Xcode chip last — **kept on purpose**: the voice says it last, and firing it earlier
   would put the picture ahead of the sentence. It is the third chip, in spoken order.
4. Cover "CAN AI…" vs frame "CAN POKI…" — unchanged (cover hash is a render input; still cosmetic).

Panel result: **PASS**. Nothing is queued, scheduled or published.

---

# Viewer panel: repo-poki-01 (round 3 = the shipped file)

Video sha256: 41691322713d21827afc691dc47a07c8da9d0b39af867ab31e910cfbdd3b8b7f
Release: `renders-2026-11-07`, asset `repo-poki-01.mp4` (719816618, 13,060,284 bytes), kit
`repo-poki-01-kit.zip` (719816702), produced by Actions run `42344973851` (`cc20055`), which also
published the release through `publish_verified_batch.py`.
Frames re-checked in THIS file: 3.6, 10.4, 18.2, 27.5, 35.3, 37.0, 38.8, 39.9 s.

Why this render exists: the queue refused the round-2 file because a render that reuses the voice
job's handoff recorded only `engine: "chatterbox"` in `manifest.json`, and `tools/post/common.py`
requires the full Option-3 audit string. Fixed in `cc20055` (the handoff now carries
`engine_detail`); this run records `chatterbox exag0.7 cfg0.4 ref michael-ref.wav, flow (3 chunks,
worst match 99%, melody [16.7, 18.0, 17.3] st, retries 0)`. The voice job reused the original
approved take (`vo_sha256 8adab7da…`), so the narration is the take the owner has already heard.

## Rule checks (round 3)
- `short_qa video`: **PASS** — duration 40.25, WPM 178.9, longest pause 0.56, visual change 0.868,
  graphic-only 0.168, motion gap 0.75 s. Identical to round 2 (same take, same graphics).
- Kit QA: 9/9 checks true (`1080x1920`, `30fps`, `h264+aac`, `duration_matches`, `loudness_-14±1`,
  `peak<=-1dBFS`, `frame0_visible`, `approved_voice`, `designed_cover`).
- End-card in this file: card 35.3 s, `COMMENT IPHONE` 37.0 s, cursor 38.3 s, pressed + ring +
  "✓ Following" 38.8 s, holds to the last frame.
- Terminal prompt + "● waiting" 3.6 s; ticks 10.4 s; flow nodes 18.2 s; chips 27.5 s — all in
  spoken order, no cue fallbacks (`stages.render.cue_fallbacks` is `{}`).
- Cover for YouTube: `cover.jpg` = the approved c1 (`sha256:aa6277d5…`), 1080×1920 PNG/JPEG
  container, passes `validate_short_cover`.

Panel result: PASS. Nothing is queued or published by this document itself.
