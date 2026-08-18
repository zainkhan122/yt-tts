# ⚖️ MASTER RULES — The Deeper Mind
### Must-follow for EVERY video. If a rule is violated, the video is NOT done.
*Last updated: 2026-08-16*

---

## R1. NEW ASSETS EVERY VIDEO (variety is non-negotiable)

1. Every video gets **its own NEW assets**: ≥10 AI images + ≥30 fresh stock clips/photos.
2. **NEVER reuse a previous video's assets.** No `oldNN`, no `v2img` pools. Zero exceptions.
3. AI images must be **visually distinct** — each a *different subject* (a face, an object,
   a place, an abstract, a scene, a symbol). NEVER 10 variants of one moody scene.
4. Stock must span ≥5 subject categories (people/faces, objects, nature, urban, abstract).
5. **CAP:** no single asset used more than **2×** per video.
6. **VERIFY** (storyboard step) and print: distinct-asset count + per-asset usage.
   FAIL the build if any asset >2× or if distinct < 80% of the pool.

## R2. CAPTION SYNC (kinetic text — exact, never estimated)

1. Every caption is anchored to a **keyword** in the script.
2. TTS **splits the sentence at the keyword**: `[pre] + 0.12s pause + [post]`.
   `cap_start = measured(pre duration) + 0.12s` → **exact**, not estimated.
3. Captions are applied at **FINALIZE** on the **absolute shared timeline** — video and
   audio both use per-beat `beat_dur`, so there is **zero cumulative drift**.
4. **Hold time = 2.6s** (2–3s for comprehension).
5. Each caption appears **exactly once** (dedup enforced at storyboard).
6. **VERIFY** at finalize: print every caption's absolute time. If a caption is missing
   or duplicated → fail loudly, do not ship.

## R3. ROBUSTNESS (never crash, never lose work)

1. **GitHub repo = source of truth. Workspace = scratch.**
2. Every step idempotent + resumable (`state.json` per video).
3. Chunked rendering (26 beats/chunk). Fail LOUD: verify assets exist at storyboard;
   verify chunk zips contain the right beat count before assemble; never mark a failed
   chunk done.
4. **Memory safety:** never use the concat FILTER with many concurrent video inputs (OOM)
   — use the concat DEMUXER + re-encode. Use `-threads 2`. Avoid `-shortest/+faststart`
   together (use `-t DUR`).
5. Push the final via `git_push.py`. On failure: `rm -rf /tmp/yt-tts-vault` and retry.

3. **Back up AI images to the repo immediately** after generating them
   (`vault/video_NNN/images/`). Generated images can't be re-fetched like stock —
   if the workspace snapshot drops them, they'd be lost. Push once, right after generation.

## R4. QUALITY BAR (the video must hold viewers)

1. Visual change every 3–5s (one beat = one sentence).
2. 8–10 min video = 100–140 beats, 20–28 captions.
3. Hook in the first 2 sentences; end with a comment-driving question.
4. Color grade + vignette + fades; audio loudnorm −16 LUFS.
5. Title + thumbnail create a curiosity gap (see vault/pipeline/03_thumbnail_prompts.md).

## R5. VOICE (locked forever)

- Voice = **Kokoro `af_heart`, speed 1.0** — pinned in `vault/reusable/voice_config.json`.
  Never change it. Same voice across all videos.

## R6. DELIVERY CHECKLIST (all ✅ before "done")

- [ ] final.mp4 built (1080p/30fps, ~6–10 min), decode spot-checked at 4 timestamps
- [ ] caption schedule printed + verified (R2.6)
- [ ] asset-variety verified (R1.6) — no reused assets from other videos
- [ ] final.mp4 pushed to repo; intermediates purged (workspace + repo tree)
- [ ] metadata.md (title / description / tags / pinned comment) written

## R7. BUILD ORDER (follow exactly)

```
storyboard → verify assets (R1) → tts (split timings) → render (no captions,
stores beat_dur) → assemble (per-beat pad) → finalize (absolute captions) → push
```

## R8. THUMBNAIL STYLE (locked — "C: the cryptic diagnosis")

1. **Title/Thumbnail Synergy (the core rule):**
   - The **TITLE** does *identification* — it names the viewer's pain / behavioral pattern.
   - The **THUMBNAIL** does the *cryptic diagnosis* — the ONE insight or mechanism they
     must click to discover. It is the knowledge gap, the promised cure.
   - **They must NEVER repeat each other.** If the title points at the viewer, the
     thumbnail names the hidden cause; if the title names the concept, the thumbnail
     hits the emotional gut. Complementary, not duplicate.
2. **Thumbnail text:** 2-3 words. Bright **white #FFFFFF**, thick black stroke (~9px)
   + soft dark glow, over a dark scrim at the bottom-left. Readable at 120px.
   - NO questions. NO relatable quotes. NO full titles.
   - Give the diagnosis, not a mirror. ("IT'S YOUR SHADOW", not "TOO MUCH?".)
3. **Image:** full-bleed emotional close-up **FACE** (right side), eyes gazing toward
   the text, high contrast, bright midtones, dark negative space on the left.
4. **Diagnosis-line bank** (title → thumbnail line) is kept per-video in VIDEO_QUEUE.md.
5. Every thumbnail is generated against this formula and presented for approval before
   it is pushed as final.
6. **UNIQUE CURIOSITY-GAP LINE PER VIDEO:** no thumbnail line may repeat another
   video's concept (e.g. if "SHADOW" is used once, no other video may use "SHADOW").
   Each video gets a distinct, fresh curiosity-gap line. Keep a running list of used
   lines in VIDEO_QUEUE.md and check it before every new thumbnail.
7. **VISUAL VARIETY ACROSS THE CHANNEL:** not every thumbnail may be "a face + text."
   Vary the composition by the video's own pain point — use faces for *relational/emotional*
   pains, but symbols, objects, silhouettes, split-scenes, or concept art for others
   (e.g. an empty chair, a closed door, a shadow, a spiral). Before building any new
   thumbnail, list the last 3 thumbnails' compositions and pick a DIFFERENT treatment,
   so no two adjacent thumbnails look alike. The goal: each thumbnail is instantly
   recognizable as ITS video, not as "another one from that channel."
8. **MEASURE TEXT WIDTH BEFORE COMPOSITING:** before placing thumbnail text, render the
   label and measure its width (ImageMagick `-format %w`). If width > ~1150px (frame
   1280 minus margins), reduce the font size until it fits. Never let text touch or
   exceed the frame edge. This rule exists because oversized text clips and ruins
   thumbnails.

## R9. DOUBLE-VERIFY EVERYTHING (check twice, ship zero mistakes)

1. **After storyboard** — verify ALL of: (a) every caption anchor exists in its sentence,
   (b) no duplicate captions, (c) no asset used > max_uses, (d) no two consecutive beats
   share an asset, (e) every asset file exists on disk, (f) no beat reuses an asset
   that already appeared ≥1× in the SAME chunk.
2. **After TTS** — verify ALL captioned beats have `cap_start`; mid-sentence keywords must
   have cap_start > 0; all audio chunks pushed + state updated.
3. **FIRST-CHUNK GATE (mandatory):** render chunk 0 ALONE, then verify EVERY beat in it —
   30fps, SAR 1:1, duration ≈ beat_len, caption present on captioned beats. Only if
   chunk 0 is PERFECT do you render chunks 1..n.
4. **After assemble** — verify every part video==audio (±0.1s).
5. **After finalize** — decode spot-check ≥4 timestamps + print full caption schedule.
6. Any verification failure → STOP, fix, re-verify. Never proceed on a failed check.

## R10. CONTINUOUS IMPROVEMENT

Every build must be at least as correct as the last. When a mistake slips through, add a
new check to R10 so that class of mistake can never ship again.

## ## R11. TITLE FORMULA VARIETY

No 3 consecutive videos may share the same title formula. Rotate between:
"The Psychology of People Who…" / "Why…" / a claim-statement / a direct "You…" /
a curiosity statement. Track the last 2 formulas in VIDEO_QUEUE.md and check
before locking each new title.

## ## R12. SCRIPT VARIETY + MIDPOINT PATTERN-INTERRUPT

1. Vary the "furniture" of every script — never reuse the same signpost phrases
   ("Here's the truth nobody told you", "Here's what's actually happening",
   "I'll see you in the next one") verbatim two videos in a row.
2. Insert a MIDPOINT PATTERN-INTERRUPT at ~50%: a short story, a direct question
   to the viewer, a quote, or a "pause and sit with this" moment. The 50% mark is
   the 2nd-biggest retention drop; vary the format there on purpose.

## ## R13. AI IMAGE MOOD VARIETY

No two adjacent videos share a dominant AI-image mood. Rotate palettes/lighting:
warm-gold-dark, cool-blue, dawn/sunrise, warm interior, monochrome. Keep the
"high contrast + clean subject" quality, but vary the *mood* so the channel
doesn't read as one repeated aesthetic.

## ## R14. MUSIC BED (ambient under voice)

Every video gets a subtle ambient pad mixed under the voice:
- generated by `tools/make_pad.py DUR out.wav` (no external asset, deterministic)
- mixed at volume 0.30 under the voice (~-27 LUFS), stereo, fade in/out
- final audio loudness-normalized to -16 LUFS / TP -1.5
This fixes the "dry AI voice" feel. NEVER mix the pad louder than 0.35.

## ## R15. AUTO-CLEANUP BETWEEN VIDEOS (never make the user ask) (never make the user ask)

1. When the user says a video is downloaded (or before starting a NEW video), AUTOMATICALLY:
   - delete that video's workspace folder (`videos/video_NNN/`) EXCEPT keep nothing — it's in the repo
   - delete its thumbnail (`thumbnails/video_NNN_cover.jpg`) — user has it
   - delete its stock dir (`stockN/`), work dirs, beat/vbeat files, zips, parts
   - purge repo intermediates (chunks/parts/zips) but KEEP final.mp4 + text files in repo
2. Clean /tmp (clone dirs, verify temp, logs) at the START of every turn's build work.
3. The workspace should hold ONLY: tools/, reusable/, secrets/, MASTER_RULES.md,
   VIDEO_QUEUE.md, and the CURRENT video's source files + final.mp4 (until downloaded).
4. Do this WITHOUT being told. This rule exists so the user never has to ask again.

## ## R16. SLOW ONE-STEP-AT-A-TIME WORKFLOW (mandatory pace) (mandatory pace)

1. **One step per turn.** Never chain a whole build in one turn — long turns get
   terminated mid-step and lose work.
2. **The fixed cadence, one turn each:**
   `(a) assets+script → (b) storyboard+verify → (c) tts → (d) render+verify chunks →
    (e) assemble+verify parts → (f) FINALIZE (concatenation) in its OWN turn.
3. **Verify before moving on** (never trust, always measure):
   - after render: every vbeat must be **30fps + SAR 1:1 + duration≈beat_dur**;
   - after assemble: every part **video duration == audio duration (±0.1s)**;
   - if any check fails, STOP and fix — do not proceed.
4. End every turn with a one-line status + the exact next step, so a fresh session
   can pick up with zero context loss (also write `STATUS.md` in the video folder).

## ## R17. PRE-FLIGHT CHECK BEFORE EVERY STEP (avoid crashes) (avoid crashes)

Before ANY heavy step (tts / render / assemble / finalize), check:
1. `/tmp` free space (df) — need >300MB for git clones / zips; clean if <300MB.
2. Workspace size (du) — snapshot cap ~128MB; clean old videos/stock if over.
3. Time budget — heavy steps can take 5-15 min; if a step risks the 30-min cap,
   SPLIT it (do fewer chunks per turn).
Never start a step without this check. Print the numbers so the user sees them.

## ## R18. ASSET VARIETY — NO PATTERNS, NO UNNECESSARY REPEATS

1. **Fetch enough assets:** stock + AI count should be ≥ 90% of the beat count, so a
   5-6 min video (~110-130 beats) carries ~100+ assets and reuses are rare.
2. **Global pool:** asset selection spans ALL assets — never locked to a small
   section list (that caused a fixed rotation pattern).
3. **Use everything before reusing:** prefer never-used assets strongly, so no asset
   gets a 2nd use while another is untouched.
4. **Maximize reuse distance:** when an asset must repeat, its 2nd use must be as far
   as possible from the 1st (≥ 40 beats). Reusing an asset 17 beats later reads as
   "the same sequence twice" — banned.
5. **Randomize:** seeded-random asset order + motion per beat (never the same motion
   twice in a row, never a fixed cycle). Deterministic per video (same seed = same
   storyboard) so builds stay reproducible.
6. `verify.py storyboard` must report: distinct assets, unused assets, min reuse
   distance — and FAIL if (a) assets unused while pool ≤ beats, or (b) min reuse
   distance < 26 beats.

