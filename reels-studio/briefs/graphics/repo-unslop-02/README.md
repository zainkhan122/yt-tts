# repo-unslop-02 — the rebuilt Short

The one unscheduled Short rebuilt against both audits (`AUDIT.md` P0-A, `SCRIPT-AUDIT.md` P0-S). Nothing else in the
batch was touched: `repo-unslop-01` and the other five stay as they are.

- Tool: **unslop** — a skill for Claude Code or Codex (`github.com/heydamir/unslop`, CC BY 4.0, @heydamir).
- Template: **`design-review`** (per-tool animation language, `graphics/templates/design-review/`).
- Length: 142 spoken words, ~42 s of speech; QA estimates 46.1 s at 186 wpm, the actual read lands near 208 wpm.
- CTA: comment keyword **UNSLOP** (kept) — "Comment UNSLOP and I'll pin the repo."
- Copyable action: **`/unslop this dashboard`** (spoken and typed on screen character by character).
- Pronunciation: the brief carries the channel lexicon, so the voice says "un-slop" (it used to read the word as
  "U N slop"); display text stays `UNSLOP` in headlines and captions.
- Captions: old-short scale (96px, 900, uppercase), the spoken word marked in the channel yellow `#FFD60A`.

## The script, scene by scene

| # | Eyebrow | On-screen headline | Spoken |
|---|---|---|---|
| 1 | AI-BUILT UI | UNSLOP: EVERY AI SCREEN | You've seen this screen. Why does every AI-built app look the same? |
| 2 | AUDIT | FIRST, IT NAMES THE SLOP | unslop is a skill for Claude Code or Codex, and it starts by naming the slop out loud, and where it lives. |
| 3 | DIRECTION | YOUR ANSWER IS THE DIRECTION | Then it asks what your product actually is. Your answer becomes the direction: the character, the one moment that carries the colour, the signature detail. |
| 4 | REDRAW | NINE PASSES, ONE SCREEN | Then it redraws the same screen in nine passes, so what you get back still looks like your product, just designed. |
| 5 | TYPE IT | TYPE SLASH UNSLOP | Type slash unslop, then your screen or a live link. It runs in Next.js, React, Vue, Svelte or plain CSS. |
| 6 | THE RESULT | SAME WORDS, DIFFERENT PRODUCT | Same layout, same words, different product. That is the whole point. |
| 7 | WHAT TO EXPECT | WHAT TO EXPECT | If your screen is already good it says so; it asks before any paid image; and it needs Claude Code or Codex to run. |
| 8 | — | COMMENT UNSLOP | Comment UNSLOP and I'll pin the repo. |

Scene 7 is the concession: it keeps its honest content and its own slot, but the eyebrow is *what to expect* and the lines
are flat statements — no section called "The catch", no warning framing (owner ruling 3).

## What each scene draws (archetypes in this template)

1. `ui_screen` — one fabricated product page, three pages hard-cut on the words (workflow → inbox → team), purple gradient
   and glow in every one. A stamp reads `SAME SCREEN × 3`.
2. `audit_marks` — the same screen, annotated: red callouts measured onto the real elements (`.cards` → purple gradient,
   `.cta` → soft glow, `.badges` → emoji label, `.hero h1` → shouty copy), each with a dot on the element and a leader.
   Verdict band `SLOP FOUND ×4` under the screen.
3. `direction_card` — a receipt that types itself in: `character: quiet, editorial`, `one moment: the invoice total`,
   `signature detail ...`.
4. `pass_stack` — the same screen redrawn in three hard cuts (slop → mid → clean), with `06 · LAYOUT`, nine pips and the
   nine pass names as a rail; the current pass is the only violet one.
5. `stack_chips` — a terminal that types `/unslop this dashboard` under a caret, over five stack tiles that are ghosted
   from frame one and light up as they are spoken.
6. `split_compare` — the slop screen wiped into the clean one, half to full, same layout and same words.
7. `boundary_rows` — three rules that draw themselves, one per honest limit.
8. `endcard` — brand mark, handle, tagline, follow pill and a cursor that presses on the pipeline's press time.
   The keyword chip that used to sit above the Follow button is gone (owner, 7 Nov): the headline *COMMENT UNSLOP*
   carries the keyword. The template keeps it as an option — an endcard renders the chip only when its payload sets
   `keyword_chip` (default on, off here).

## Gates

```
python3 research/production/batch-2026-11-09/build.py repo-unslop-02   -> PLAN PASS · features ok · beats ok · 8 scenes
python3 tools/short_qa.py plan repo-unslop-02                          -> PASS (11 PASS, 1 WARN: hook familiarity)
```

Rendered preview measurement (`preview-210wpm.mp4`, silent, timing faked at 210 wpm): 1283 frames, 42.8 s, mean
frame-to-frame change 2.85, longest run without a visible change 3.4 s, hard cuts only at scene boundaries.

## Files here

- `preview-210wpm.mp4` — silent local render of the real scene document (the approved voice only exists in the cloud render).
- The historical contact sheet was removed during approved old-output cleanup.
- `beats.json`, `features.json`, `words.estimate.json`, `source.md` — the brief's graphics side, written by the build.

Spec and plan: `research/production/batch-2026-11-09/specs/repo-unslop-02.py` (PLAN + FEATURES + BEATS);
brief: `briefs/repo-unslop-02.json`; covers: `covers/repo-unslop-02/cover-c{1,2,3}.png`;
preview driver: `research/production/batch-2026-11-09/preview.py`.

## What is left for a real publish

1. Cloud render with the approved voice (Chatterbox) — the only step that needs the GPU worker; the local preview cannot
   synthesise it.
2. `tools/short_qa.py video` on the finished MP4 against the render manifest (the measured post-render gates).
3. Cover pick from `cover-c1` (split before/after), `cover-c2` (half slop / half clean with audit labels), `cover-c3`
   (nine-pass rail + clean screen), then owner approval.

## Cloud render

Dispatched 2026-11-07: run [42395396578](https://github.com/zainkhan122/yt-tts/actions/runs/42395396578)
(`python3 reels-studio/reels.py cloud repo-unslop-02 --receipt research/production/receipts/2026-11-09-shorts-01.json`).
Artifact only — public publication off, nothing scheduled or posted.

Cover: owner picked **c1** (split before/after) — `covers/repo-unslop-02/selection.json`, sha `6d7845ac…`.
Capture pack: `captures/repo-unslop-02` is an **empty pack by design** (`{"files": {}}` with a note), the same shape as
`repo-autoloop-01` and `repo-dshgo-01`: this renderer fabricates every surface, so there is no tool media to capture.
