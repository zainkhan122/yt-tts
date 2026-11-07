# Reference audit · @buildwithai.club vs our batch 2026-11-08

**Question from the owner:** all seven Shorts use the same template — same animation language, same colours, same layout —
while the reference accounts give every tool its own look. Audit both, at frame level, and say exactly what our pipeline
is missing. **No code changes in this pass.**

---

## 1. What I could actually get (and what I could not)

| Source | Status | Detail |
|---|---|---|
| TikTok `@buildwithai.club` | **10 videos downloaded** | 29.0–60.4 s, 576×1024, 24.8–29.8 fps, 155–382 kb/s. Public timeline, no login. |
| Instagram `@classified.ai` | **BLOCKED — not analysed** | `instagram:user` extractor is marked broken upstream; `web_profile_info` returns 404 without a session; the profile URL 302-redirects to the login wall; yt-dlp gets HTTP 429. Nothing from Instagram is in the numbers below. |

**To finish the Instagram half** I need one of: (a) the 10 reels dropped into the workspace as files, (b) a logged-in
`cookies.txt` for a throwaway account, or (c) screen-recorded exports. The analyser is already committed
(`research/social/audit-2026-11-07/analyze.py` + `aggregate.py`); the moment files land, the same numbers come out for IG.

**Method (identical for both groups):** every frame resampled to **20 fps**, 270×480 analysis canvas →
per-frame diff (cut / shot / motion), white-pixel share by five vertical bands (text + light-UI density), median-luma
regime per second (light vs dark background), Haar face detection every 5th frame, Canny edge density, k-means palette
(k=5) over the whole video; audio extracted to 16 kHz mono → RMS envelope, silence/pause statistics, energy onsets,
spectral centroid/flatness, autocorrelation F0; transcript + word timings from faster-whisper `tiny.en` for speech rate.
Reproducible: `python3 analyze.py <mp4…>` → `meta/*.json`, then `aggregate.py`.

---

## 2. Verdict in one paragraph

Our seven videos are technically clean and structurally identical: one dark plate (`#0C0E13`), one accent (`#FFD60A`),
one secondary blue (`#38BDF8`), one headline slot, one caption slot, six card archetypes, glide transitions, no cuts, no
human, no real product UI. Measured across the seven, the **median-frame brightness varies by 3.2 grey levels** — that is
not a style, it is a single frame repeated for 40 seconds. The reference account does the opposite: it cuts every **3.0 s
on average** (18.9 hard cuts/min, up to 44.7), alternates a **human presenter (face in 42 % of frames)** with **real
product UI and bespoke light "paper" graphics**, changes background regime constantly (**luma σ = 70.8**, 35 % of frames on
a light background), and speaks **217 wpm** with **half our pause count**. Their per-tool look changes because the artwork
*is* the tool — screenshots, its real colours, its real output. Ours changes only the words.

---

## 3. The numbers (median per group)

| Metric | @buildwithai.club (10) | ours (7) | Gap |
|---|---|---|---|
| duration | 43.7 s | 40.8 s | ok |
| **hard cuts / min** | **18.9** (7.6–44.7) | **0.0** | we have none — template `"cut": "glide"` |
| **mean shot length** | **3.0 s** (1.3–6.6) | **40.8 s** (7 scenes ≈ 5.7 s each, no cut) | 3–13× slower |
| **face on screen** | **42 %** of frames (14–62 %) | **0 %** | no presenter, no hands, no face |
| face size | 7–22 % of frame | — | mid-shot, not a talking-head sticker |
| **background luma σ** | **70.8** | **3.2** | one constant plate vs light↔dark alternation |
| frames on light bg (>190 luma) | **27 %** | **0 %** | no light/"paper" product UI |
| white-pixel share (text/UI) | **0.37** | 0.04 | our canvas is mostly empty dark space |
| white share by band (top→bottom) | .29 / .55 / .41 / .27 / .00 | .02 / .05 / .03 / .06 / .02 | their type + UI fill the middle; ours hugs the bottom edge |
| palette top colour | varies: 8× dark neutrals, **2× cream `#EAEADD`** | **identical `rgb(11,12,20)` in all 7** | no per-tool palette |
| median colour chroma | 0.08 | 0.22 | we are *more* saturated and less photographic |
| **mean pairwise frame correlation inside the set** | **0.59** (min 0.03) | **0.82** (min 0.75) | our videos are the same video; theirs are the same *brand* |
| speech rate | **217.6 wpm** (189.7–247.4) | 183.9 (177.1–190.8) | we are ~35 wpm slow |
| pauses > 250 ms / min | **15.6** | **35.0** | we stop twice as often |
| longest pause | 0.59 s | 0.64 s | ok |
| energy onsets / min (SFX, hits, cuts) | **161.6** | 92.8 | we are under-scored |
| median F0 / pitch spread | 160.8 Hz / 82.2 Hz IQR | 145.5 Hz / 70.2 Hz IQR | our read is deeper and flatter |
| loudness p90 | −15.6 dBFS | −12.2 dBFS | we are 3.4 dB hotter (no headroom for SFX) |

Frame sheets: `sheets/tt_highcuts.jpg`, `sheets/tt_lowcuts_face.jpg`, `sheets/tt_mid_60s.jpg`, `sheets/ours_unslop.jpg`.
Raw per-video data: `measurements.json`.

---

## 4. How the reference actually builds a Short

### 4.1 Four recurring structures (not one)

1. **Presenter ⇄ screen-capture** (`7697701717076364564`, 23.9 cuts/min): talking head delivers the claim, hard cut to a
   full-screen browser doing the thing (real Chrome window, real cursor, real ChatGPT reply streaming), cut back to the face
   for the verdict. Roughly 50 % face / 45 % screen / 5 % transitions, sampled.
2. **Light "paper" product mock** (`7699861233939381388`, 7.6 cuts/min, face 62 %): a cream `#EAEADD` UI is *drawn* — pill
   buttons, chips, a real price chart, an isometric stack of 10 000 simulated trades, "29.4 % up" in green — intercut with
   the presenter against a dark bookshelf. Zero screenshots; every panel is bespoke.
3. **Diagram-led explainer** (`7704525765915774229`, 16.9 cuts/min): cream canvas, an icon-row "Claude ⟶ 🧩 ⟶ 🌐 ⟶ 🗂 ⟶ 📧"
   pipeline, a real setup-guide page with redaction, a server rack illustration, then a 2-3-5 card fan. One idea per frame.
4. **Pure screen-record demo** (`7700231606509866260`, 44.7 cuts/min, face 31 %): mostly the tool's own UI with punch-ins,
   the presenter used as a punctuation cut.

Transitions are **hard cuts**, occasionally a whip-pan or an object wipe (a hand, a card fan) — never a crossfade. Nothing
in the ten videos is "a graphic card with a headline and a caption".

### 4.2 Cutting rhythm

- Mean shot **3.0 s**; 18.9 cuts/min median, 44.7 at the top end. Our cadence is one cut per video.
- Cuts land **on the word** that changes the idea, not on scene boundaries.
- Every video keeps a *visual change* inside the shot too: cursor travel, a value counting, a highlight sliding, a zoom-in
  on the region being described (their `static_share` 0.6 is real held UI, ours 0.0 is constant low-level shimmer — the
  opposite of what the metric means for us).

### 4.3 Layout & typography

- **Two caption systems in the same video**: (a) one-word emphasis under the graphic — `just`, `one`, `charts`, `signal`,
  `takes`, `using`, `money` — set in a bold lowercase sans with a soft shadow; (b) a handwritten/script accent for the
  emotional word (`something hard` in red script over a cartoon; `easy`; `remember`) that replaces part of the caption line.
- Headlines are **not** repeated as a static top-left block. The top-of-frame is used for *tool chrome* (real menu bars,
  the Claude pill with its 🧩 icon) — the layout is a **product surface, not a slide**.
- Safe areas: the graphic occupies the middle 55–60 % of the frame; captions sit inside the artwork, not under it; the top
  12 % and bottom 10 % stay clean for TikTok/IG furniture.

### 4.4 Colour

- **Per-tool palettes.** Claude content → the orange/tan of Claude's own brand plus cream paper; ChatGPT content → its grey
  UI plus a red script accent; Cloudflare → its orange; the trading tool → green/red data on cream.
- **Light↔dark alternation** is the main "colour" device: a cream UI next to a dark presenter is what makes each cut read as
  a cut at thumbnail size. 27 % of frames are near-white; ours are 0 %.
- Saturation is spent on **one artifact** per shot (a yellow study sheet, a green P&L bar), not on the frame furniture.
  Our batch is the inverse: a saturated yellow accent on every card, no artifact.

### 4.5 Graphics language

- Real product surfaces: browser chrome, cursor, streaming text, a settings page, a terminal.
- Bespoke data graphics drawn with the tool's own numbers (10 000 simulations → a stacked isometric column; "29.4 % up").
- Illustrated objects with personality (a red cartoon book stack, a server rack, a Post-it study sheet, a 2-3-5 card fan).
- Stickers/emoji as *labels on real things* (🧩 on the Claude pill, 🗂 on a folder row) — never a decorative icon on a card.

### 4.6 Human presence

Face in 42 % of frames median, as a **mid-shot at desk distance** (7–22 % of frame area), cut in for the claim and the
payoff, out for the demo. Eye contact, glasses catch-light, no captions over the face.

### 4.7 Audio

- 217 wpm median, 15.6 pauses/min (ours 184 / 35.0) — the read is continuous and confident.
- Pitch sits higher and moves more (F0 IQR 82 Hz vs our 70 Hz).
- **161 energy onsets/min**: every cut gets a whoosh/click, numbers get ticks, reveals get a soft impact. Ours: 92.8, mostly
  music beats.
- Mix peaks at −15.6 dBFS p90 — headroom so the SFX can punch. Ours peaks at −12.2, so hits have nowhere to go.

### 4.8 Script

From the transcripts (verbatim excerpts, `measurements.json`):

> "Everyone gives Claude prompts, but **the top 1 % give it playbooks**. Here's the trick. It's called the AI delegation loop,
> and you can set this up in **three simple steps**."

> "…**But here is the clever part.** Before an issue gets confirmed, **another agent tries to prove the first one wrong.**"

> "Here are **top three ways** to use it **that no one's talking about**."

Pattern: a status-gap hook ("top 1 %", "no one's talking about") → an *enumerated* demo (three ways / three steps) →
a twist or proof beat → a direct instruction ("ask Claude, build me a mod…"). Second person throughout, contractions,
concrete commands the viewer can copy. Median 190–247 wpm allows ~240 words in 45 s; our scripts carry 113–125 words.

---

## 5. Our seven, measured the same way

| Short | cuts/min | bg luma σ | face | white (text/UI) | wpm | top palette |
|---|---|---|---|---|---|---|
| unslop | 0 | 3.3 | 0 % | 0.036 | 184.1 | 11,12,20 |
| superagent | 0 | 3.0 | 0 % | 0.037 | 190.8 | 11,12,20 |
| reavideo | 0 | 3.2 | 0 % | 0.035 | 181.4 | 11,12,19 |
| dshgo | 0 | 3.1 | 0 % | 0.039 | 177.1 | 11,12,20 |
| autoloop | 0 | 3.2 | 0 % | 0.038 | 183.9 | 11,12,20 |
| vork | 0 | 3.1 | 0 % | 0.036 | 178.5 | 11,12,20 |
| sand3d | 0 | 3.0 | 0 % | 0.041 | 184.3 | 11,12,20 |

Mean pairwise frame correlation **0.823** (min 0.752) — every one of the 21 pairs is more similar than the most similar
pair in the reference set's average. The seven are one video with seven scripts.

---

## 6. Root causes in *our* pipeline (why it cannot look different yet)

| # | Cause | Where | Effect |
|---|---|---|---|
| R1 | **One skin by design.** `DEFAULT_SKIN = "tool-spotlight"  # the one visual skin` | `lib/pipeline.py:375`, `:1232` | every brief renders through the same template; `manifest.skin` is always `tool-spotlight` |
| R2 | **Palette is hard-coded hex in one CSS.** `#0C0E13` plate, `#FFD60A` accent, `#38BDF8` secondary, fixed grid/glow | `graphics/templates/stage.css:2-8` | no theme variables, no per-brief colour system, no light theme |
| R3 | **Fixed composition slots.** headline 190–420, visual 470–1400, captions 1480–1640; `.headline` top-left, `.sub` centred, captions bottom | `stage.css:1,9-14` + `graphics/engine.js` | the layout *is* the template; nothing can be full-bleed or edge-to-edge like a screenshot |
| R4 | **Fixed archetype enum** (`flow_link`, `chip_grid`, `toggle_steps`, `terminal_type`, `concept_card`, `stat_pop`, `endcard`) | `graphics/beats.py`, `engine.js` | every topic is forced into the same six drawings; a real UI screenshot or a data chart is not expressible |
| R5 | **No cuts.** Template CFG `"cut": "glide"` | `templates/repo-spotlight/template.py:16` | 0 hard cuts; two-layer presenter/UI alternation is impossible |
| R6 | **No capture path in graphics mode.** `renderer: "graphics"` ignores capture packs; the packs we ship are stubs (`files:{}`) | `captures/<id>/manifest.json`, `lib/pipeline.py:1572` | no real screenshots, cursors, product surfaces — only drawn cards |
| R7 | **No human.** Faceless-only is encoded in QA (`faceless only` doc note) and there is no presenter asset path | `config/qa-thresholds.json:_doc`, `brand/voice/*` | face share 0 %; the reference's single strongest attention device is unavailable |
| R8 | **One voice, one pace.** Channel voice fixed at Chatterbox `speed 1.15` (ignored by the engine — see `voice_tempo` workaround) | `config/channel.json`, `lib/pipeline.py:614` | 184 wpm and flat pitch; the engine gives no pace knob, so we added `voice_tempo` (1.03–1.10) as a workaround |
| R9 | **Covers and in-video palette are the same kit.** `covers/_kit.py` plate/accent/grey | `covers/_kit.py` | the cover reinforces the sameness instead of the tool's identity |
| R10 | **Script budget tuned for the old format** (100–125 words ≈ 35–42 s at 175 wpm) | `research/production/batch-2026-11-08/specs/*`, plan lint | we cannot carry a 3-step demo in the time the reference fills |

Note: nothing above is a bug. The pipeline was built as *one* faceless explainer skin with hard technical gates, and it
delivers that exactly — the gates (`short_qa.py`, viewer panel, covers) all pass because they measure motion, contrast,
speech rate and copy, not visual distinctiveness.

---

## 7. Mismatch list, in fix order

Severity: **P0** = the reason all seven look the same; **P1** = what makes the reference feel alive; **P2** = polish.
Each has an acceptance test that the analyser in this folder can measure, so the fix is verifiable, not a matter of taste.

### P0 — the sameness itself

| # | Fix | Acceptance test (analyser) |
|---|---|---|
| M1 | **Per-tool theme layer**: a `theme` block in the brief (`plate`, `ink`, `accent`, `accent2`, `surface`, `font_pair`, `grid_on/off`) that `stage.css` consumes as CSS variables; default from the repo/site brand, override per brief. | palette top-1 colour **differs** across the batch; pairwise frame correlation inside a batch **< 0.60** |
| M2 | **Two-regime alternation**: every video must alternate a *light* and a *dark* treatment (or product-surface vs presenter/canvas). | `share_near_white_bg` ≥ **0.20**; `luma_std` ≥ **35**; no video with σ < 10 |
| M3 | **Hard cuts as the default**, with glide only inside a beat. Scene change = cut on a word boundary. | `cuts_per_min` ≥ **12**, mean shot ≤ **4 s** |
| M4 | **Real product surface in ≥ 40 % of scenes**: a drawn-but-faithful replica of the tool's own UI (its chrome, its colours, its output), or a real capture where a pack exists. | white-pixel share ≥ **0.22**; `edge_density` up 1.5×; viewer panel bar "product/result visible in N of 7 scenes" ≥ 3 |
| M5 | **New archetypes**: `screen_ui` (full-bleed app window), `data_chart` (the tool's own numbers), `artifact` (the object the tool produces), `split_before_after`, `quote_repost`. Keep the current six as secondary. | archetype histogram across a batch: no archetype > 40 % |

### P1 — the liveliness

| # | Fix | Acceptance test |
|---|---|---|
| M6 | **Presenter track** (owner decision needed): a reusable host clip set or an AI-presenter licence. Until then, emulate the alternation with hands/avatars? See §9. | `face_frame_share` ≥ 0.25 in at least the hook + CTA |
| M7 | **Caption system per format**: one-word emphasis inside the artwork + a script/display accent font for the emotional word; captions must not sit in a fixed bottom slot for the whole video. | white share by band: middle bands ≥ top/bottom bands; ≤ 40 % of frames share one band profile |
| M8 | **Script length + pace**: 190–215 wpm, 180–230 words for 45 s, ≤ 20 pauses/min, no phrase longer than 12 words. Keep the verbatim-claim rule. | `wpm` 190–215; `pauses_over_250ms_per_min` ≤ 20 |
| M9 | **SFX layer at the cut** (whoosh on cut, tick on numbers, soft impact on reveals) and **4 dB more headroom** for the mix. | `energy_onsets_per_min` ≥ 140; `loud_p90_dbfs` ≤ −14 |
| M10 | **Hook before frame 3**: number/claim on screen at 0.0 s, first spoken word at 0.0 s (we are at 0.0–0.18 s — fine, keep). | `first_word_at` ≤ 0.15 s |

### P2 — polish

| # | Fix | Acceptance test |
|---|---|---|
| M11 | Palette spend rule: saturation only on the one artifact that carries the claim; frame furniture neutral. | `palette_max_chroma` ≤ 0.15 with one accent cluster ≥ 60 % of the accent pixels |
| M12 | Zoom/punch-in inside a shot (their screenshots breathe) — 3 % scale drift per shot. | `static_share` between 0.25 and 0.55 (real holds, not shimmer) |
| M13 | Cover is generated *from* the video's hero artifact (not from a separate cover kit), so the thumbnail matches the first 2 s. | cover palette == video palette top-2 by ΔE < 10 |

---

## 8. Art direction per tool (for the seven already scheduled)

These are the concrete treatments the mismatch list implies for this exact batch — the reference-account pattern applied
per tool, so a rebuild can be scoped one video at a time (`render.yml` supports single-scene rebuilds):

| Short | Palette / theme | Hero artifact (real) | Structure |
|---|---|---|---|
| **unslop** | warm off-white paper `#F2EDE3` + charcoal, one violet accent (design-tool feel) | before/after split of the *same* AI app: purple-gradient version ⟶ the fixed one; the skill's own audit list as sticky notes | 4 cuts in the hook (before/after flicker), 3-pass reveal |
| **dsh-superagent** | GitHub dark `#0D1117` + its blue link colour, mono type | a real PR thread: issue → agent comment → merge, with the web panel beside it | presenter-less but UI-led: 6–8 cuts between thread and panel |
| **rea-video** | film-slate black + amber, storyboard storyboarding | the tool's own `report.html` and an SRT overlay on a real clip, BPM/timing ruler | shot-by-shot scrub: 10 cuts, one per shot analysed |
| **DSH Go** | Android material light + its accent, device frame | the phone UI: chat with steps folding, the "send now" pill, the approval card | device-in-hand framing, 5 cuts, one zoom on the tap |
| **agent-autoloop** | terminal green-on-black *plus* a light notification card | the desktop card that arrives, and `agent-autoloop answer 1` typed live | calm first half, cut-cut-cut on the decision |
| **vork** | cinematic stills (real footage plate) + wireframe cyan | the million-bird murmuration still and the VFX-tracked desk shot, wireframe↔render **inside one frame** | slow burn: 3 long shots, one hard cut at "no generative video" |
| **sand3d** | Blender-ish viewport grey + cream, its own export file names | the 38-line washing-machine program next to the rotating assembly and the GLB/STL export row | 3 cuts, each landing on an export format |

**Colour policy if we cannot shoot/present people:** use *tool-native* palettes and real UI as the identity layer; the
alternation device becomes "product surface (light) ↔ diagram canvas (dark)" instead of "UI ↔ face". That is measurable by
M2/M4 and gets us most of the way without a presenter.

---

## 9. What I need from you before any code changes

1. **Instagram files.** The account is unreachable from here (details in §1). Drop the 10 reels in the workspace and I will
   run the same analyser and extend this audit with the IG column.
2. **Presenter policy.** The reference's biggest lever is a human face. Options: (a) stay faceless and lean on tool-native
   UI/artifacts (my recommendation for the current batch, since 3 of 7 are already scheduled), (b) a licensed AI presenter,
   (c) your own recorded host clips — which changes the capture pipeline (new stage, new consent/licensing record).
3. **Capture packs.** M4 wants real product surfaces. Today `capture_store` ships stub packs (`files:{}`). To do this properly
   we need a capture step per repo (browser/CLI screenshots at 1080×1920, cursor path, 6–10 frames per tool).
4. **Scope of the rebuild.** Re-cutting all seven into the new language is a re-render + re-QA + re-schedule cycle; the three
   already on Buffer for 8 Nov (reavideo, dshgo, autoloop) would have to be pulled and re-slotted. Tell me whether to (i)
   rebuild only the four not yet scheduled (9–10 Nov), (ii) pull and rebuild all seven, or (iii) ship this batch as-is and
   apply the new language from the next batch.

---

*Files: this document, `measurements.json` (all per-video metrics + transcripts), `analyze.py` (20 fps analyser),
`aggregate.py` (group statistics), `sheets/*.jpg` (12-frame strips at ~1.6 fps).*
