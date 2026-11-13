> **Current implementation note:** The later owner correction restored the earlier logo/name/Follow/cursor/COMMENT endcard and single-line, word-synced yellow captions. The v3 description below is historical and does not describe the current outro, caption grouping or gate coverage. See `../HANDOFF-GRAPHICS-CURRENT.md` for present behavior and unresolved visual-quality work. The motion number below is an experiment, not a production gate. Reference screenshots under `uploads/` and `ref/` may be local-only.

# Cloning a reference short — the measured method

Why this file exists: for days the reference was copied by *describing* it — dark, bold, clean,
minimal — and the render came back that described the reference without being it. Adjectives do not
survive contact with a frame. This file replaces the adjectives with numbers, and it is the method
`negative` (2026-11-13) was built with.

The short that proved it: `explainer-negative-01`, from a phone capture at
`uploads/image-3.png` / `image-4.png`, template `graphics/templates/negative/`.

---

## 0. The five mistakes that were being made

| what was done | why the result was wrong |
|---|---|
| measured the whole screenshot | the screenshot is a **phone player**: letterbox bars + a play button + a scrubber. Measuring it copies the phone. |
| matched the look | the look is a *consequence* of the layout numbers (where type sits, how big, how much void). Matching colour without matching geometry is what "same vibe, wrong video" means. |
| described the typeface | no reference is set in the box default. Ours was: see §1. |
| decorated beats with cards/grids | the reference's beats are **instruments floating in a void**. Cards and grids are a different genre. |
| invented a number to fill a beat | "1x" on screen is not a fact. If there is no measurement, show words. |

## 1. First, prove the fonts load

`graphics/render.py` never injected `@font-face`, so every template fell through to DejaVu Sans
for 27 shorts. `document.fonts.check()` returns **true for a fallback**, so nothing caught it.
The gate now loads each face, waits for `fonts.ready`, and compares widths against a
never-defined family. Measured after the fix at 100px: Inter 1660 · Anton 1192 · JetBrains Mono
1680 · fallback 1919.

If you add a font, add it to `_FONT_FACES` in `graphics/render.py` and re-run any render — the gate
fails loudly rather than shipping the wrong typeface.

## 2. Isolate the video from the player

```bash
python3 tools/ref_crop.py uploads/image-3.png --out ref/A3.viewport.png
```

Prints the viewport bbox and what was cut. On `image-3`: 472×756 screenshot → 421×748 viewport
(aspect 0.5628 = 9:16), cutting 12px left, 4px top, 39px right. That is the real frame.

## 3. Measure it

```bash
python3 tools/ref_measure.py ref/A3.viewport.png ref/A4.viewport.png \
  --ignore-bottom 100 --out ref/ref-A.fingerprint.json
```

`--ignore-bottom` masks the player chrome drawn **over** the video (play button, scrubber), which
otherwise becomes a fake "text band". Output is a `contract` block: the values every frame agrees on.

Measured for the reference used here, normalised to 1080 wide (scale 2.565 from 421):

| element | y % | size | x span | note |
|---|---|---|---|---|
| ground | – | **#000000**, 89.8% empty | – | true black, not #0A0B12 |
| handle | 3.6–5.1 | 26px mono, tracking .22em | 41–58% | centred, ghost grey |
| headline | 11.0–13.8 | ≈96px, 800 weight | 9–91% | sentence case, white |
| telemetry | 24.2–25.4 | 34px mono | 25–75% | label ghost, **live value #F05080** |
| instrument | 39.0–51.1 | hairline trace | 4.5–56% | sits on a 1px baseline |
| annotation | 56.8–57.8 | 34px mono | 6–58% | ghost |
| caption | 80.3–84.7 | 76px, 800 weight | 13–87% | one word in the accent |

**The accent is one hue used once per beat** — `#F05080`, on the live value only.

## 4. Write the style file from the table

Not from memory. Each band becomes a CSS rule; each measured value gets a comment in `stage.css`
saying which band it came from, so the next agent can check the derivation instead of trusting it.

Reproduce the *system* (void ground, one instrument, mono telemetry, one accent), never the
artwork, the words, or the subject framing. `negative` keeps the grammar and changes the subject.

## 5. Gates that actually look at pixels

All three run on frames pulled out of the finished MP4, at each scene's midpoint
(`(t0+t1)/2` — sampling at `0.62` shows the *next* scene):

1. **font gate** (in `render.py`, pre-encode) — faces are loaded and distinct.
2. **overflow audit** (in `render.py`, pre-encode) — nothing past the frame edge.
3. **ground gate** (post-render) — the modal colour of every frame must be the ground we asked for.

The ground gate is the one that caught a real bug: `#postfx .grain` uses `mix-blend-mode: overlay`,
and overlay maths is `2*b*s`, so over pure black any noise above zero **lifts** it. Measured
`[9,8,8]` instead of `#000000`. The halftone and vignette lifted it the same way. `negative`
disables all three — a clean digital black is itself the style.

## 6. Re-measure the render against the reference

```bash
python3 tools/ref_measure.py ref/final/*.png --out ref/render.fingerprint.json
```

Then compare the `contract` blocks. If the ground differs, the style is not copied yet. If the
headline band sits outside the reference's range, the type is not copied yet.

## 7. The caption is not a subtitle

The reference shows 3–5 words, sentence case, with the claim-carrying word in the accent. Our
caption band already does this; the failure mode to avoid is a full sentence or a second line
colliding with the beat's own type.

---

## Reusable checklist

- [ ] crop to viewport, check the printed aspect is 0.5625
- [ ] `--ignore-bottom` past the player chrome
- [ ] fonts proven loaded (widths differ from fallback)
- [ ] ground colour + empty fraction measured, not assumed
- [ ] one accent hue, appearing once per beat, tied to a spoken cue
- [ ] every beat has an instrument in the middle third
- [ ] no invented numbers — words when there is no measurement
- [ ] render, pull midpoints from the MP4, re-measure, diff the contract
- [ ] proof sheet: reference frame beside rendered frame, values printed under each

---

# Motion is a separate system from style (v2, owner verdict 2026-11-13)

The owner's question on v1: *"WILL a user even watch for 3 sec?"* — no. The style was copied and
the result was still unwatchable, because **layout is not motion**. v1 had six static slides; frames
at 0.8 s and 3.2 s were pixel-identical.

Measured, before and after, on the delivered MP4:

| | mean frame-to-frame delta | frozen frames |
|---|---|---|
| v1 (copy the look, fades only) | 1.32 | **6 / 29 (21%)** |
| v2 (motion grammar below) | 2.54 | **0 / 33** |

## The five motion layers, all of them per-frame

1. **camera** — the whole beat scales/parallaxes continuously (`camera()` in the engine). Never
   static; never more than ~10%, or the type clips the frame edge.
2. **ambient** — a hairline grid drifts forever under every beat (`ambientTick()`). This is what
   guarantees no two frames are identical even when the content holds.
3. **trace** — instruments travel: the waveform scrolls, the needle rides it, counters never freeze.
4. **stagger** — type lands word by word, never as a block.
5. **impact** — the hook punches in and settles, and **frame 0 is already full** (`stagger` starts
   at negative time). An empty first frame is the same mistake as a frozen one.

## The gate

```python
# pull N frames, measure mean |frame_n - frame_{n-1}|
frozen = sum(1 for d in deltas if d < 0.35)
```

Run it on the finished MP4, not on the page. v1 passed every existing gate while being visually
frozen, because every existing gate measured geometry, never change-over-time. Also check
`frame 0` ink coverage is non-trivial — a hook that fades up from empty loses the first second.

## Brand layer is not part of the style

The style file may define the *system* (ground, instrument, accent). It may not touch:

- **voice** — house voice is Kokoro `am_michael` at speed 1.15 (`voice-lab/lab.py`). A preview
  narrated in piper is judging a different video.
- **type** — headlines are **Anton**, body **Inter**, telemetry a mono. `brand/profiles.json`
  `brand.fonts` is the source of truth, and `graphics/render.py` must prove the faces loaded.
- **outro** — the house endcard: real brand logo (`brand/logo/avatar-1080.png` via
  `stage.brand_block()`), the handle, the keyword, the follow line. Not a bespoke sign-off.

---

# The house layer (v3, owner directive 2026-11-13)

> "Each short to have our own Voice, Outro and kinetic text font with Yellow highlight."

Three things are now **pipeline**, not per-video choices. They live in one place, are injected into
every template, and a template cannot override them.

| house element | where it lives | what breaks if a template owns it |
|---|---|---|
| **Voice** | `config/channel.json` → Chatterbox, `brand/voice/michael-ref.wav`, exh 0.7 / cfg 0.4. Kokoro `am_michael` 1.15 is the *CPU preview* path only. | Pacing judged against a different timbre is judging a different video. |
| **Caption** | `graphics/templates/shared.css` + `shared.js`, injected by `render.py` | Seven engines each growing their own caption is how the yellow highlight disappeared. |
| **Outro** | `graphics/outro.js`, drawn by `shared.js`; brand block from `stage.brand_block()` | A bespoke sign-off per video means the channel is never recognised. |

## Caption contract

- Anton, ALL CAPS, **88px**, 2–4 words per chunk (`DATA.caption_words`).
- Band `y 1250–1450`. **No scene element may enter `y >= 1210`** — enforced by the caption-band gate.
- Exactly **one word per chunk is `#FFD60A`**: the scene's `cue_word` when it is on screen,
  otherwise the chunk's strongest content word. Never a stopword.
- If a beat plan does not name a `cue_word`, `beats.scene_list` derives one from the headline, so
  no short can ship with zero highlight.

## Word sync

`tools/align_words.py` runs faster-whisper on the finished voice and matches the recognised words
back onto our own script tokens (difflib, monotonic). Measured on the last render: **match 0.99,
98/98 words**. Below `min_match` it says so and falls back to a length-weighted split rather than
shipping timings it does not trust.

Two traps paid for once each:
- **No word may be dropped** when assigning words to scenes. Dropping a boundary word changes the
  script fingerprint and the beat plan is then rejected as belonging to another script (B0).
- **faster-whisper's own decoder** passes `metadata_errors=` to PyAV; decode with `soundfile` and
  hand it an array instead.

## Gates added this round

| gate | catches |
|---|---|
| caption-band (`render.py`, pre-encode) | any scene element entering the caption band |
| font gate (`render.py`, pre-encode) | a webfont that silently falls back to DejaVu |
| motion gate (post-render) | frozen frames — v1 of the void template had 21% |
| ground gate (post-render) | a template that asks for `#000000` and measures `#080808` |
| BL140–143 (`brief_lint.py`) | script length 100–125, hook ≤ 12 words, tool named ≤ ~7 s, comment-keyword CTA |

BL140–143 immediately rejected the script this file was written against (98 words, 16-word hook).
That is the rules doing their job.
