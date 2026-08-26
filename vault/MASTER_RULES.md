# ⚖️ MASTER RULES — The Deeper Mind
### Must-follow for EVERY video. If a rule is violated, the video is NOT done.
*Last updated: 2026-08-19*
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
   audio both use per-beat `beat_len`, so there is **zero cumulative drift**.
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
5. Push the final via `git_push.py` (blobless clone + `read-tree HEAD`). On failure:
   `rm -rf /tmp/yt-tts-vault` and retry.
6. **Back up AI images to the repo immediately** after generating them
   (`vault/video_NNN/images/`). Generated images can't be re-fetched like stock —
   if the workspace snapshot drops them, they'd be lost.

## R4. QUALITY BAR (the video must hold viewers)

1. Visual change every 3–5s (one beat = one sentence).
2. 8–10 min video = 100–140 beats, 20–28 captions.
3. Hook in the first 2 sentences; end with a comment-driving question.
4. Color grade + vignette + fades; audio loudnorm −16 LUFS.

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
stores beat_len) → assemble (per-beat pad) → finalize (absolute captions) → push
```

## R8. THUMBNAIL STYLE (locked — "C: the cryptic diagnosis")

1. **Title/Thumbnail Synergy (the core rule):**
   - The **TITLE** does *identification* — it names the viewer's pain / behavioral pattern.
   - The **THUMBNAIL** does the *cryptic diagnosis* — the ONE insight or mechanism they
     must click to discover. It is the knowledge gap, the promised cure.
   - **They must NEVER repeat each other.**
2. **Thumbnail text:** 2-3 words. Bright **white #FFFFFF**, thick black stroke (~9px)
   + soft dark glow, over a dark scrim at the bottom-left. Readable at 120px.
   - NO questions. NO relatable quotes. NO full titles.
   - Give the diagnosis, not a mirror. ("IT'S YOUR SHADOW", not "TOO MUCH?".)
3. **Image:** full-bleed emotional close-up **FACE** (right side), eyes gazing toward
   the text, high contrast, bright midtones, dark negative space on the left.
4. Diagnosis-line bank kept per-video in VIDEO_QUEUE.md.
5. Every thumbnail presented for approval before it is pushed as final.
6. **UNIQUE CURIOSITY-GAP LINE PER VIDEO:** no thumbnail line may repeat another
   video's concept. Check VIDEO_QUEUE.md's used-lines list before every new thumbnail.
7. **VISUAL VARIETY ACROSS THE CHANNEL:** not every thumbnail may be "a face + text."
   Vary the composition by the video's own pain point — faces for *relational/emotional*
   pains; symbols, objects, silhouettes, split-scenes, or concept art for others.
   Check the last 3 thumbnails' compositions and pick a DIFFERENT treatment.
8. **MEASURE TEXT WIDTH BEFORE COMPOSITING:** render the label and measure its width
   (`magick -format %w`). If > ~1150px (frame 1280 minus margins), reduce font size
   until it fits. Never let text touch or exceed the frame edge.

## R9. DOUBLE-VERIFY EVERYTHING (check twice, ship zero mistakes)

1. **After storyboard** — verify ALL of: (a) every caption anchor exists in its sentence,
   (b) no duplicate captions, (c) no asset used > max_uses, (d) no two consecutive beats
   share an asset, (e) every asset file exists on disk, (f) no beat reuses an asset
   that already appeared ≥1× in the SAME chunk.
2. **After TTS** — verify ALL captioned beats have `cap_start`; mid-sentence keywords must
   have cap_start > 0; all audio chunks pushed + state updated.
3. **FIRST-CHUNK GATE (mandatory):** render chunk 0 ALONE, then verify EVERY beat in it —
   30fps, SAR 1:1, duration ≈ beat_len. Only if chunk 0 is PERFECT do you render 1..n.
4. **After assemble** — verify every part video==audio (±0.1s).
5. **After finalize** — decode spot-check ≥4 timestamps + print full caption schedule.
6. Any verification failure → STOP, fix, re-verify. Never proceed on a failed check.

## R10. CONTINUOUS IMPROVEMENT

Every build must be at least as correct as the last. When a mistake slips through, add a
new check so that class of mistake can never ship again.

## R11. TITLE FORMULA VARIETY

No 3 consecutive videos may share the same title formula. Rotate between:
"The Psychology of People Who…" / "Why…" / a claim-statement / a direct "You…" /
a curiosity statement. Track the last 2 formulas in VIDEO_QUEUE.md and check
before locking each new title.

## R12. SCRIPT VARIETY + MIDPOINT PATTERN-INTERRUPT

1. Vary the "furniture" of every script — never reuse the same signpost phrases
   ("Here's the truth nobody told you", "Here's what's actually happening",
   "I'll see you in the next one") verbatim two videos in a row.
2. Insert a MIDPOINT PATTERN-INTERRUPT at ~50%: a short story, a direct question
   to the viewer, a quote, or a "pause and sit with this" moment. The 50% mark is
   the 2nd-biggest retention drop; vary the format there on purpose.

## R13. AI IMAGE MOOD VARIETY

No two adjacent videos share a dominant AI-image mood. Rotate palettes/lighting:
warm-gold-dark, cool-blue, dawn/sunrise, warm interior, monochrome. Keep the
"high contrast + clean subject" quality, but vary the *mood* so the channel
doesn't read as one repeated aesthetic.

## R14. MUSIC BED + VOICE POLISH (ambient under voice, ducked)

Every video gets a SCORED ambient bed + polished voice via `finalize` PASS 3:
1. **Pad** = `tools/make_pad.py DUR out.wav` — chord progression Am→F→C→G
   (14s/chord, looping), slow breathing LFO, short room reverb, stereo, exact DUR.
2. **Voice polish** = `highpass=f=80` (de-rumble) → `equalizer=f=8000:g=2` (presence)
   → `acompressor=threshold=-18dB:ratio=2.5` (even out TTS spikes) → stereo.
3. **Sidechain ducking** = `sidechaincompress=threshold=0.05:ratio=3:attack=15:release=250`
   — pad dips gently (~6dB) while the voice speaks, swells in pauses. (Ducking verified.)
4. **REQUIRED:** `asplit` before the voice feeds both sidechain and mix (a filter
   output cannot feed two consumers in this ffmpeg build — verified 2026-08-18).
5. **Balance (v2, user-approved 2026-08-19):** pad volume **0.55** → music clearly
   audible in pauses, voice stays ~5–7dB on top in the speech band (measured).
   Final loudnorm −16 LUFS / TP −1.5, stereo AAC 160k.
6. NEVER raise the pad above 0.55 or drop duck ratio below 3 — the voice must stay
   dominant. (See R20.)

## R21. MONTH-2 CADENCE + SHORTS (locked 2026-08-19)

1. **2 long-form/week** (Tue + Fri), prime US/UK evening. Do NOT exceed 2 — the
   niche has finite topics and quality beats frequency.
2. **3 Shorts/week** (Mon/Wed/Sat), all **repurposed from existing long-forms**.
   Segments = the **HOOK (cold open) + the video's best SELF-CONTAINED payoff**
   — NEVER the R12 midpoint (it needs long-form context and dies without it;
   user-confirmed 2026-08-20). A Short must be a complete setup → tension →
   payoff in 30–45s. No original-topic Shorts.
3. **A Short uses NATIVE VERTICAL media (1080×1920)** — portrait stock clips +
   vertical AI images fetched FOR the Short (user-confirmed 2026-08-20). NOT
   blur-fill from landscape (reads amateur) and NOT a hard crop. We still reuse
   the long-form's expensive parts: the script segment, the already-generated
   voice (parts .wav — no re-TTS), the caption timings (storyboard.json), and
   the R20 audio balance. Build via `tools/make_short.py` (REWRITE needed for
   vertical; `stock_fetch.py` needs an orientation=portrait option).
4. The niche fence (R22) applies to Shorts too — same audience, same lane.
5. **Every Short gets an end-CTA, BOTH text AND spoken** (af_heart): a prominent
   text bar "▶ FULL VIDEO ON CHANNEL" + a spoken "Watch the full video on this
   channel." in the locked voice. A Short is independent — it must ask for the
   click itself. The CTA is **APPENDED after the narration ends** (the Short's
   total length extends to fit it) — the CTA voice must NEVER overlap the
   narration's last words. (`make_short.py` builds this in; `fix_short_cta.py`
   patches older Shorts.)
6. **Purge order for a video's intermediates (CRITICAL after video_015):**
   purge chunk zips + parts BEFORE pushing final.mp4. The repo tip must stay
   below ~700MB or the shallow full clone used by git_push.py for >35MB files
   (final.mp4) overflows the 993MB /tmp. Shorts re-TTS their voice
   (make_short.py v2), so parts .wav are NOT needed after assemble either.
   (Lesson: video_015 finalize — 970MB tip blew the push; purge → 453MB → OK.)

## R22. NICHE FENCE (what we are / are NOT)

We are: deep psychology for rare intuitive types (INFJ/INTJ/INFP/INTP) through a
Jungian lens. We are NOT: generic self-help (habits, motivation, dopamine,
productivity) or dark-psychology clickbait. Every topic must pass:
> "Does this name an experience a rare intuitive type secretly has, and explain
> it with a Jungian mechanism?" — if a generic motivation channel could publish
> it unchanged, REJECT it.

## R15. AUTO-CLEANUP BETWEEN VIDEOS (never make the user ask)

1. When the user says a video is downloaded (or before starting a NEW video), AUTOMATICALLY:
   - delete that video's workspace folder (`videos/video_NNN/`)
   - delete its thumbnail (`thumbnails/video_NNN_cover.jpg`)
   - delete its stock dir (`stockN/`), work dirs, beat/vbeat files, zips, parts
   - purge repo intermediates (chunks/parts/zips) but KEEP final.mp4 + text files in repo
2. Clean /tmp (clone dirs, verify temp, logs) at the START of every turn's build work.
3. The workspace should hold ONLY: tools/, reusable/, secrets/, MASTER_RULES.md,
   VIDEO_QUEUE.md, and the CURRENT video's source files + final.mp4 (until downloaded).
4. Do this WITHOUT being told.

## R16. SLOW ONE-STEP-AT-A-TIME WORKFLOW (mandatory pace)

1. **One step per turn.** Never chain a whole build in one turn.
2. **The fixed cadence, one turn each:**
   `(a) assets+script → (b) storyboard+verify → (c) tts → (d) render+verify chunks →
    (e) assemble+verify parts → (f) FINALIZE (concatenation) in its OWN turn.
3. **Verify before moving on:**
   - after render: every vbeat must be **30fps + SAR 1:1 + duration≈beat_dur**;
   - after assemble: every part **video duration == audio duration (±0.1s)**;
   - if any check fails, STOP and fix — do not proceed.
4. End every turn with a one-line status + the exact next step (also write `STATUS.md`).

## R17. PRE-FLIGHT CHECK BEFORE EVERY STEP (avoid crashes)

Before ANY heavy step (tts / render / assemble / finalize), check:
1. `/tmp` free space (df) — need >300MB; clean if <300MB.
2. Workspace size (du) — snapshot cap ~128MB; clean old videos/stock if over.
3. Time budget — heavy steps can take 5-15 min; if a step risks the 30-min cap,
   SPLIT it (do fewer chunks per turn).
Never start a step without this check. Print the numbers so the user sees them.

## R18. ASSET VARIETY — NO PATTERNS, NO UNNECESSARY REPEATS

1. **Fetch enough assets:** stock + AI count should be ≥ 90% of the beat count, so a
   5-6 min video (~110-130 beats) carries ~100+ assets and reuses are rare.
2. **Global pool:** asset selection spans ALL assets — never locked to a small
   section list.
3. **Use everything before reusing:** prefer never-used assets strongly.
4. **Maximize reuse distance:** 2nd use ≥ 40 beats from the 1st.
5. **Randomize:** seeded-random asset order + motion per beat (never the same motion
   twice in a row, never a fixed cycle). Deterministic per video.
6. `verify.py storyboard` must report distinct assets, unused assets, min reuse
   distance — and FAIL if (a) assets unused while pool ≤ beats, or (b) min reuse
   distance < 26 beats.

## R19. SESSION-RESET RESILIENCE (self-heal, never rebuild from memory)

1. A session reset wipes pip packages, `~/.cache/kokoro/`, and `/tmp` — but **NOT**
   workspace files (`tools/`, `reusable/`, `secrets/`, `MASTER_RULES.md`, `VIDEO_QUEUE.md`).
2. **At the start of EVERY build session run `python3 tools/bootstrap.py`.** It
   reinstalls deps, re-downloads the Kokoro model/voices if missing, verifies
   ffmpeg + fonts + ImageMagick, checks secrets, cleans `/tmp`, and prints the
   R17 pre-flight numbers (df /tmp, du /home/user).
3. `pipeline.py` also self-heals on every subcommand (its internal `bootstrap()`
   installs missing pip packages + re-fetches the Kokoro model before TTS).
4. **If secrets are missing** after a snapshot reset (`secrets/github_pat.txt`,
   `~/.pexels_key`) → STOP and ASK THE USER to re-paste them. Never guess or skip.
5. Repo = source of truth (R3). After every session reset, re-sync the latest
   `pipeline.py` / `MASTER_RULES.md` from the repo if the workspace copies are
   older than the repo's.

## R20. AUDIO MIX V2 (locked — user-approved 2026-08-19)

1. Pad volume **0.55**, sidechain **`threshold=0.05:ratio=3`** (replaces the old
   0.26 / 0.02:12 which buried the music bed under the voice).
2. Result: music bed clearly audible in pauses (pad 60–100Hz band ≈ −30dB in the
   mix), voice stays ~5–7dB on top in the speech band. Final loudnorm −16 LUFS / TP −1.5.
3. These values are hard-coded in `pipeline.py` finalize PASS 3. `tools/remix_test.py`
   can rebuild the test mix at any pad volume for A/B review.

## R23. TOPIC DEDUP REGISTER (no duplicate pain points or mechanisms)

1. VIDEO_QUEUE.md keeps the master register: every shipped video/short's TITLE +
   PAIN POINT + JUNGIAN MECHANISM + thumbnail line + Short hook.
2. Before approving ANY new topic (or Short hook), check the register. A new topic
   is a DUPLICATE (reject) if it gives the viewer the same "this is about me" hit
   OR reuses a registered pain point / mechanism — even if the title is reworded.
3. Cosmetic rewording of an old title = duplicate. A genuinely different pain +
   mechanism = acceptable.
4. When a topic is retired for duplication, add it to the RETIRED list in
   VIDEO_QUEUE.md so it is never resurrected.
5. Every shipped video/short is registered the same day it is finalized.

## R24. SHORTS MEDIA INDEPENDENCE (user-mandated 2026-08-26, non-negotiable)
1. **EVERY Short gets its OWN media pool** — fresh portrait stock fetched with
   queries unique to THAT Short (`queries_hook.txt` / `queries_payoff.txt`)
   plus its OWN newly generated vertical AI images. Never share AI images
   between the two Shorts of a video, never reuse another video's assets (R1).
2. **Queries must be themed to the segment's actual content** — the hook's
   cold-open imagery vs the payoff arc's imagery — not generic video-level
   queries.
3. **Layout:** `videos/NNN/shorts_ai/hook/` and `videos/NNN/shorts_ai/payoff/`
   (disjoint). `make_short.py` reads ONLY its own kind's dir, fetches stock
   into a per-kind /tmp dir, and seeds its RNG with (video, kind) — so two
   Shorts of the same video can never show the same assets in the same order.
4. **Verify before ship:** the build log's `media pool [kind]` line must show
   the per-kind AI dir; if it ever falls back to the flat shared dir, STOP.

## R25. HANDOFF FRESHNESS (user-mandated 2026-08-26)
1. **Update HANDOFF.md at the START of every session** (and after any
   milestone) so a new chat can resume instantly if this one dies: current
   state, next actions, any new operational facts. Push it to the repo the
   same turn.
2. **All tools live in `tools/`** (workspace) and `vault/tools/` (repo) —
   generalized, CLI-parameterized. Per-video dirs keep only per-video CONFIG
   (fetch_assets.py queries, queries_hook/payoff.txt, stock_urls.json,
   storyboards) — never generic code.
3. Repo > HANDOFF > memory: if they disagree, the repo is the truth.

## R26. TRAFFIC QUALITY GATE (2026-08-26 — every video passes before publish)
The pack (title+thumbnail+description+tags+hashtags+script hook) decides CTR;
CTR + retention decide distribution. Hard criteria, checked by
`tools/qa_pack.py VIDEO_DIR` before ANY upload:
1. **TITLE:** ≤60 chars (mobile truncation). Primary search keyword in the
   first 5 words. Formula rotation per R11 still applies. Must pair keyword
   with curiosity/benefit — identification AND intrigue.
2. **DESCRIPTION:** primary keyword in the FIRST sentence (first 150 chars =
   the search snippet — never waste them on pure hook prose). ≥200 words.
   Chapters included (Google video snippets). Comment CTA. Disclaimer.
3. **HASHTAGS: 3–5 TOTAL, no more.** First 3 appear above the title — order
   by strength: niche audience first (#infj etc.), then topic (#psychology),
   then optional channel brand tag. NEVER 6–15 (diluted) and NEVER >15
   (YouTube ignores ALL). #Shorts mandatory in every Short description.
4. **TAGS (backend):** exact primary keyword FIRST, then 5–10 variations,
   within the 500-char budget. Low weight but free.
5. **THUMBNAIL (R8 +):** 2–3 word cryptic diagnosis, ≤1150px text width,
   readable at 120px, composition varies from last 3. Title and thumbnail
   must NEVER repeat each other (curiosity gap, not redundancy).
6. **SCRIPT:** primary keyword SPOKEN naturally in the first 60 seconds
   (transcript indexing); hook = first 2 sentences; comment-driving closer.
   First visual asset must MIRROR the first spoken line (beat-match).
7. **ENGAGEMENT:** pinned comment ready at publish (first-24h comments are
   the strongest engagement signal); community post for major videos.
