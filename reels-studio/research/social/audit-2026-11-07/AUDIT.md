# Reference audit · @buildwithai.club + @classified.ai vs our batch 2026-11-08

**Question from the owner:** all seven Shorts use the same template — same animation language, same colours, same layout —
while the reference accounts give every tool its own look. Audit both, at frame level, and say exactly what our pipeline
is missing. **No code changes in this pass.**

*Update 2026-11-07: the Instagram half is now in. Six files supplied by the owner were downloaded from the signed CDN links,
measured with the identical analyser, and folded into every section below (new §3b, §4.9, §5b; revised M2 / M3 / M8; new
M14–M17, R11–R12).*

---

## 1. What I could actually get (and what I could not)

| Source | Status | Detail |
|---|---|---|
| TikTok `@buildwithai.club` | **10 videos downloaded** | 29.0–60.4 s, 576×1024, 24.8–29.8 fps, 155–382 kb/s. Public timeline, no login. |
| Instagram `@classified.ai` | **6 files downloaded and analysed** | Owner-supplied signed `media.sssinstagram.com` links → 2 narrated 9:16 reels (36.1 s, 32.6 s), 1 silent 14.1 s AI-video clip, 3 cream 4:5 graphic slides (6.02 s each). 720×1280 / 720×900, 30 fps. The *profile* is still unreachable anonymously (login wall / 429), so this is 6 of the account's posts, not its last 10. |

Anonymous access stays a dead end — the working route is what happened here: signed URLs pasted by the owner, fetched with
a browser UA and an `instagram.com` referer (they expire within hours, so fetch the same day). Files are not committed
(third-party media); the metrics are.

**Method (identical for both groups):** every frame resampled to **20 fps**, 270×480 analysis canvas →
per-frame diff (cut / shot / motion), white-pixel share by five vertical bands (text + light-UI density), median-luma
regime per second (light vs dark background), Haar face detection every 5th frame, Canny edge density, k-means palette
(k=5) over the whole video; audio extracted to 16 kHz mono → RMS envelope, silence/pause statistics, energy onsets,
spectral centroid/flatness, autocorrelation F0; transcript + word timings from faster-whisper `tiny.en` for speech rate.
Reproducible: `python3 analyze.py <mp4…>` → `meta/*.json`, then `aggregate.py` (or
`aggregate.py "group name=/dir" …` to add a group without re-touching the TikTok rows). The six IG files form the two
`Instagram … 9:16 reels` / `… 4:5 posts` groups in `measurements.json`.

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

Instagram `@classified.ai` is more extreme in the same direction, and it shows something TikTok alone could not. Its two
narrated reels cut **46.5 and 82.7 times a minute** (mean shot 1.25 s and **0.71 s**), keep a **presenter tile in 34 % /
55 % of frames** at a fixed bottom-centre slot, and fill roughly **70 % of the runtime with full-bleed artifacts** — a real
GitHub repo page, a real PowerShell window, a `12,776 GITHUB STARS` stat card, a mock `₹0 / month` receipt, a mock inbox
at 7:00, a live Claude Code terminal, and a mock of Instagram's own comment box. Its three carousel slides are 100 % cream
`rgb(228,221,213)` paper and **share one palette while changing layout** — pairwise frame correlation **0.11**, against
**0.82** across our seven. Same brand, different pictures: the exact inverse of our problem. So the target is not "a
palette per video", it is **a fixed brand layer with a per-video composition**.

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

Frame sheets: `sheets/tt_highcuts.jpg`, `sheets/tt_lowcuts_face.jpg`, `sheets/tt_mid_60s.jpg`, `sheets/ours_unslop.jpg`,
plus `sheets/ig02_*.jpg`, `sheets/ig03_*.jpg`, `sheets/ig06_diwali_ai.jpg`, `sheets/ig01_*` / `ig04_*` / `ig05_*.jpg`.
Raw per-video data: `measurements.json`.

### 3b. Instagram `@classified.ai` next to both (median per group)

| Metric | TikTok (10) | **IG reels (3)** | IG 4:5 posts (3) | ours (7) |
|---|---|---|---|---|
| duration | 43.7 s | **36.1 s** (16.6–36.2) | 6.0 s | 40.8 s |
| **hard cuts / min** | 18.9 | **46.5** (0.0–82.7) | 0.0 | **0.0** |
| **mean shot** | 3.0 s | **1.25 s** (0.71–14.1) | 6.0 s (a held still) | 40.8 s |
| soft scene changes / min | — | **91.5** (89.1–114.2) | 0.0–129.6 | — |
| **presenter on screen** | 42 % | **34.3 %** (7.1–55.1) | 0 % | **0 %** |
| **background luma σ** | 70.8 | **19.5** (11.7–50.3) | 0.0–0.5 | **3.2** |
| near-white bg share | 0.27 | **0.00** | **1.00** | 0.00 |
| median luma | 104 | **21** | **222** | 16 |
| white share (type + UI) | 0.37 | 0.04–0.07 | **0.18–0.38** | 0.04 |
| white by band, top→bottom | .29/.55/.41/.27/.00 | .05/.13/.10/.01/.00 | .04/**.52**/.18/.05/.02 | .02/.05/.03/.06/.02 |
| edge density | 0.04 | 0.05 | **0.11** | 0.04 |
| palette max chroma | 0.08 | 0.16 | 0.13 | **0.22** |
| **pairwise frame correlation** | 0.59 | **0.46** (0.24–0.70) | **0.11** (0.00–0.30) | **0.82** |
| speech rate (wpm) | 217.6 | 125.8–168.6\* | — (music only) | 183.9 |
| pauses > 250 ms / min | 15.6 | **7.4** | — | **35.0** |
| energy onsets / min | 161.6 | 132.6–148.0 | 0–10 | 92.8 |
| loudness p90 | −15.6 dBFS | −12.9 dBFS | −12.1 dBFS | −12.2 dBFS |

\* The IG reels are spoken in **Roman-Urdu with English tool nouns**; `tiny.en` transcribes that poorly, so the wpm figures
are a lower bound and word-level timing is unreliable. Everything visual is unaffected.

Three things this table changes:

1. **Cuts are far more aggressive than TikTok.** The floor for "reads as social-native" is not 12 cuts/min — it is
   **≥ 25, with 0.7–1.3 s shots at the dense moments**. Our 40 s single shot is off the measured scale of both accounts.
2. **Light↔dark alternation is one device, not the law.** IG's reels stay dark (near-white 0.00, σ 19.5) and still read
   as cutting, because the *surface* changes every second (artifact card ↔ presenter tile). Its light treatment lives in a
   different format entirely (the cream 4:5 posts, luma 222). So the invariant across both accounts is **"a different
   visual surface every 1–3 s"**, of which light/dark is one flavour.
3. **The pause count, not the wpm, is our pace defect.** TikTok is fast *and* pauses 15.6×/min; IG is slower (~150 wpm
   speech) yet pauses only 7.4×/min. We pause **35×/min** — we stop for breath twice as often as either reference. M8 is
   re-specified below accordingly.

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

### 4.9 Instagram `@classified.ai`: the same job, a different grammar

The account runs **three formats**, and only one of them is a reel:

| Format | What is on screen | Measured |
|---|---|---|
| **Dark narrated reel** (ig02, ig03) | artifact cards + presenter tile, hard cuts, Roman-Urdu VO | 33–36 s, 46.5–82.7 cuts/min, face 34–55 % |
| **Silent AI-video clip** (ig06, Diwali) | one continuous AI-generated scene, slow push, gold serif "Happy Diwali" | 14.1 s, 0 cuts, no speech, chroma 0.33 |
| **Cream 4:5 graphic slide** (ig01, ig04, ig05) | a *poster* — headline, chips, mock cards, comment CTA, handle footer | 6.02 s, static, music only, luma 222 |

The two reels share one production grammar, and it is not ours:

1. **Every shot is a full-bleed artifact,** not a headline over a plate: the actual GitHub repo page with its stars and
   licence pill; a real PowerShell window with a `winget` line; a `12,776 GITHUB STARS` number card; a mock receipt
   (`MONTHLY COST · ₹0`); a mock inbox (`DAILY ROUTINE · 7:00` with real Gmail/Calendar/Drive rows); a `1:53` ring timer
   for "set up in 3 minutes"; a live Claude Code terminal; a real Blender viewport with `Characters / Props /
   Environment / Lighting / Textures` export rows; a real docs page ("Blender Director — 1 Domain · 3 Pages · …").
2. **The headline lives inside the artifact**, at the top of it, in two registers: a heavy uppercase white sans
   (`SAVE IT`, `ONE LINE`, `WRITES CODE`, `12,776`) plus **one italic/handwritten accent word in amber or yellow**
   (`#EEC364` in ig02, `#DECF29` in ig03), with a tiny mono eyebrow above (`STEP 1`, `THE ONLY COST`, `JUST TYPE`).
   There is **no bottom subtitle track** — the spoken line is rendered as a small Roman-Urdu line *inside* the card.
3. **The presenter is a fixed tile, not a talking head.** Detected face boxes: centre x **0.507 / 0.501**, centre y
   **0.845 / 0.840**, width **30 % / 28 %**, height **16.9 % / 15.8 %** of frame — i.e. a rounded bottom-centre window,
   ~0.28 × 0.17 of the frame, over a *constant set* (green hex/binary wall; orange-purple gradient). It is cut in for the
   claim and the payoff and out for the demo. Nothing is ever captioned over it.
4. **The CTA is a mock of the platform.** ig03 ends on a drawn Instagram comment box with `JARVIS` typed and a "Post"
   button; ig02 ends on the same box with `BLENDER`. Both open on a **save-CTA card** ("Save this reel / I'll show you",
   "SAVE IT" with a 3.3K-saves proof strip).
5. **Proof numbers are borrowed from outside the tool**: 12,776 GitHub stars, 4.2 M subscribers, 3.3 K saves, ₹26K saved
   per year. Every one of them is a number the audience can verify, shown on its own card.
6. **Colour comes from the subject, not a house style.** ig02 is Blender's own viewport greys on a dark green circuit set
   with amber accents; ig03 is Iron-Man navy/gold with the film stills as the hook; the carousel is cream paper with a
   charcoal + `#D77350` red-orange accent and white chips. What stays constant is the *grammar* (full-bleed artifact,
   two-register headline, eyebrow, presenter tile, comment-box CTA), not the palette.

**The carousel is the cheapest lesson.** Three slides, one palette (`rgb(228,221,213)`), three completely different
compositions — a support-ticket style infographic with app chips and connector arrows and a `₹2,202 vs ₹0` price strip; a
newspaper collage of 6 thumbnails with a YouTube channel card; a product mock with a prompt chip and a video preview.
Pairwise correlation between them is **0.11**: recognisably one brand, three different pictures. That is the number our
0.82 has to fall to, and it does not require a presenter, a camera, or a single cut.

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

### 5b. The six Instagram files, measured the same way

| File | What it is | dur | cuts/min | mean shot | face | white | luma | luma σ | top palette |
|---|---|---|---|---|---|---|---|---|---|
| ig02 | reel · "Claude runs Blender" | 36.1 s | **46.5** | 1.25 s | 34.3 % | 0.038 | 10.5 | 50.3 | `11,7,6` |
| ig03 | reel · "OpenJarvis" | 32.6 s | **82.7** | **0.71 s** | 55.1 % | 0.068 | 21.0 | 19.5 | `9,13,24` |
| ig06 | AI-video clip · Diwali | 14.1 s | 0.0 | 14.1 s | 7.1 % | 0.002 | 30.0 | 11.7 | `8,14,46` |
| ig01 | 4:5 slide · Adobe alternatives | 6.0 s | 0.0 | held | 0 % | 0.375 | 223.0 | 0.0 | `228,221,213` |
| ig04 | 4:5 slide · history channels | 6.0 s | 0.0 | held | 0 % | 0.183 | 222.0 | 0.0 | `227,220,210` |
| ig05 | 4:5 slide · Claude documentary | 6.0 s | 0.0 | held | 0 % | 0.209 | 221.5 | 0.5 | `228,221,210` |

The three cream slides are 100 % light-background, 0 % face, 0 cuts, music-only — and still carry the account's whole
identity. They are the proof that the sameness problem is a *composition* problem before it is a motion problem.

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
| R11 | **No artifact frame.** The six archetypes are drawings inside fixed slots — there is no container that is *a window/receipt/timer/comment-box* with its own chrome, and no text model for eyebrow + two-register headline + accent word. Type is one font stack, one weight, one colour. | `graphics/beats.py`, `graphics/engine.js`, `stage.css` | we cannot show a repo page, a terminal, a receipt or the platform's own CTA — the three devices Instagram uses in ~70 % of its runtime |
| R12 | **One output format.** The renderer emits a 9:16 narrated MP4 and nothing else; covers are 1920×1080/1080×1920 stills outside the video path. There is no 4:5, no still-motion slide, no carousel export. | `lib/pipeline.py` (`renderer: "graphics"`), `covers/_kit.py` | the account's light/cream regime lives in a format we cannot produce, and one of our biggest gaps (`share_near_white_bg 0.00`) is only cheaply fixable there |
| R13 | **No proof or platform-CTA slot.** Briefs carry the README's claims only; there is no field for a third-party number (stars, saves, subscribers, price saved) and no beat type for "save this" / "comment WORD" drawn as the platform's own UI. | `briefs/*` schema, `graphics/cues.py` (`chat` cue is a keyword map, not a drawn CTA) | our end card is a brand plate; theirs is a screenshot of Instagram asking for a comment |

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
| M2 | **Surface alternation every 1–3 s** *(revised after Instagram)*: the device is not light↔dark, it is *different visual surface* — artifact ⇄ presenter/host tile ⇄ paper canvas. Light↔dark is one flavour of it; IG's reels stay dark (near-white 0.00, σ 19.5) and still read as fast cutting. | primary: mean shot ≤ 2 s and ≥ 2 distinct surfaces per 5 s (viewer panel counts them); secondary (for at least the light-format video of each pair): `share_near_white_bg` ≥ 0.20, `luma_std` ≥ 35 |
| M3 | **Hard cuts as the default** *(revised after Instagram)*, with glide only inside a beat. Scene change = cut on a word boundary. Measured floor across both accounts: TikTok 18.9, IG reels 46.5 / 82.7. | `cuts_per_min` ≥ **25** (≥ 12 absolute minimum), mean shot ≤ **2.0 s**, no shot longer than 4 s except the deliberate single "burn" shot |
| M4 | **Real product surface in ≥ 40 % of scenes**: a drawn-but-faithful replica of the tool's own UI (its chrome, its colours, its output), or a real capture where a pack exists. | white-pixel share ≥ **0.22**; `edge_density` up 1.5×; viewer panel bar "product/result visible in N of 7 scenes" ≥ 3 |
| M5 | **New archetypes**: `screen_ui` (full-bleed app window), `data_chart` (the tool's own numbers), `artifact` (the object the tool produces), `split_before_after`, `quote_repost`. Keep the current six as secondary. | archetype histogram across a batch: no archetype > 40 % |

### P1 — the liveliness

| # | Fix | Acceptance test |
|---|---|---|
| M6 | **Presenter track** (owner decision needed): a reusable host clip set or an AI-presenter licence. Until then, emulate the alternation with hands/avatars? See §9. | `face_frame_share` ≥ 0.25 in at least the hook + CTA |
| M7 | **Caption system per format**: one-word emphasis inside the artwork + a script/display accent font for the emotional word; captions must not sit in a fixed bottom slot for the whole video. | white share by band: middle bands ≥ top/bottom bands; ≤ 40 % of frames share one band profile |
| M8 | **Script length + pace** *(revised after Instagram)*: the defect is pauses, not speed — TikTok runs 217 wpm with 15.6 pauses/min, IG runs ~150 wpm with 7.4, we run 184 wpm with **35.0**. Target: continuous read, no breath before every clause; 180–230 words per 45 s; keep the verbatim-claim rule. | `pauses_over_250ms_per_min` ≤ **12** (hard fail > 20); `wpm` 175–220; `silence_share` ≤ 0.40 |
| M9 | **SFX layer at the cut** (whoosh on cut, tick on numbers, soft impact on reveals) and **4 dB more headroom** for the mix. | `energy_onsets_per_min` ≥ 140; `loud_p90_dbfs` ≤ −14 |
| M10 | **Hook before frame 3**: number/claim on screen at 0.0 s, first spoken word at 0.0 s (we are at 0.0–0.18 s — fine, keep). | `first_word_at` ≤ 0.15 s |
| M14 | **Host-tile contract** (works with or without a presenter): a rounded bottom-centre tile, **28–30 % wide × 16–17 % tall, centre at (0.50, 0.84)**, over a *constant* set, cut in for the claim and the payoff, never captioned over. If we stay faceless, the tile holds the tool's own "host artifact" (its logo-in-situ, a real cursor capture, a hand holding the phone) so the cut rhythm keeps its anchor. | face share ≥ 0.25 in hook + CTA once a presenter exists; otherwise tile present in ≥ 30 % of frames at that geometry (measured by the same face/tile detector in `analyze.py`) |
| M15 | **Artifact card system**: full-bleed cards with their own chrome — `window` (real app frame), `receipt`, `timer`, `inbox`, `stat`, `repo_page`, `comment_box` — each with eyebrow (mono, 11 px), two-register headline (white caps + one amber italic accent word), body artifact, and the spoken line inside the card, not in a subtitle track. | archetype histogram: ≥ 5 distinct artifacts per video; `edge_density` ≥ 0.08; white share by band peaks in bands 2–3 |
| M16 | **Save-CTA + proof beat**: open on a save-CTA card (a drawn bookmark + our own save count once we have one), close on a drawn comment-box CTA ("comment WORD"), and put **one verifiable third-party number** on its own card (GitHub stars, downloads, subscribers). | viewer panel: save-CTA in first 3 s = yes, comment-box CTA in last 4 s = yes, one external proof number present = yes |
| M17 | **Format portfolio**: add a still-motion **4:5 cream slide** export (6 s, music only, one composition per tool) next to the reel. Cheapest way to get a light-paper regime, and it shares the theme layer with the video. | batch of 7 also emits 7 slides at 1080×1350; slide `median_luma` ≥ 200, `share_near_white_bg` ≥ 0.9; reel+slide palette ΔE < 10 |

### P2 — polish

| # | Fix | Acceptance test |
|---|---|---|
| M11 | Palette spend rule: saturation only on the one artifact that carries the claim; frame furniture neutral. | `palette_max_chroma` ≤ 0.15 with one accent cluster ≥ 60 % of the accent pixels |
| M12 | Zoom/punch-in inside a shot (their screenshots breathe) — 3 % scale drift per shot. | `static_share` between 0.25 and 0.55 (real holds, not shimmer) |
| M13 | Cover is generated *from* the video's hero artifact (not from a separate cover kit), so the thumbnail matches the first 2 s. | cover palette == video palette top-2 by ΔE < 10 |
| M18 | **One brand layer, many compositions** (the carousel lesson): the palette/type/tile geometry are brand constants; the composition, artifact type and layout must change per video. | pairwise frame correlation inside a batch **< 0.30** for slides and **< 0.60** for reels, with palette top-1 identical across the batch (that is what "brand" means here) |

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

**Instagram confirms the per-tool table and adds one instruction:** give each tool the *artifact* its own README produces
(a real PR thread, a real `report.html`, a real phone screen, a real GLB row) and let the artifact carry the palette — the
theme block then only has to pick a paper/dark base and one accent. Two of the seven are already artifact-first in
spirit (dsh-superagent's PR thread, rea-video's `report.html`); those are the cheapest to bring up to the reference
standard, and unslop's before/after split is the closest thing we have to an IG-style full-bleed card.

**Colour policy if we cannot shoot/present people:** use *tool-native* palettes and real UI as the identity layer; the
alternation device becomes "product surface (light) ↔ diagram canvas (dark)" instead of "UI ↔ face". That is measurable by
M2/M4 and gets us most of the way without a presenter.

---

## 9. What I need from you before any code changes

1. ~~Instagram files.~~ **Done** — the 6 signed links you pasted are analysed (§3b, §4.9, §5b). If you want the account's
   *last 10* posts covered, paste that set the same way; the analyser and the group merge take about a minute per video.
   Two follow-ups only you can answer: **(a) language** — the account speaks Roman-Urdu with English tool nouns, our channel
   speaks English TTS; do we stay English (and lose that audience's register) or add an Urdu track? **(b) formats** — do we
   want the 4:5 cream slide and the occasional silent AI-video clip as part of the schedule, or reels only?
2. **Presenter policy.** The reference's biggest lever is a human face. Options: (a) stay faceless and lean on tool-native
   UI/artifacts (my recommendation for the current batch, since 3 of 7 are already scheduled), (b) a licensed AI presenter,
   (c) your own recorded host clips — which changes the capture pipeline (new stage, new consent/licensing record).
3. **Capture packs.** M4 wants real product surfaces. Today `capture_store` ships stub packs (`files:{}`). To do this properly
   we need a capture step per repo (browser/CLI screenshots at 1080×1920, cursor path, 6–10 frames per tool).
4. **Host tile without a presenter (M14).** If the answer to (2) is "stay faceless", confirm the substitute anchor I should
   put in the bottom-centre tile — a real cursor capture, a hand prop, or the tool's logo-in-situ. The cut rhythm depends on
   that slot existing; the face is optional, the slot is not.
5. **Scope of the rebuild.** Re-cutting all seven into the new language is a re-render + re-QA + re-schedule cycle; the three
   already on Buffer for 8 Nov (reavideo, dshgo, autoloop) would have to be pulled and re-slotted. Tell me whether to (i)
   rebuild only the four not yet scheduled (9–10 Nov), (ii) pull and rebuild all seven, or (iii) ship this batch as-is and
   apply the new language from the next batch.

---

*Files: this document, `measurements.json` (all per-video metrics + transcripts, plus `rows_ig` / `ig_extras` — presenter
tile geometry and per-video accent colours), `analyze.py` (20 fps analyser), `aggregate.py` (group statistics; accepts
`"name=/dir"` groups), `sheets/*.jpg` (12–18-frame strips — TikTok, ours, and the six IG files).*
*Reference clips are deliberately not committed (third-party media); re-fetch them with the owner's signed links.*
