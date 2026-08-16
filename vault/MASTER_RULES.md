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
