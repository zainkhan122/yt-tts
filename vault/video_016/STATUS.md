# STATUS — Video 016 "Why You're Exhausted as a Deep Thinker"

## Step (a) assets + script — DONE (2026-08-24)

### Session context
- FULL workspace wipe 2026-08-24 → recovered docs/tools/reusable from public
  repo (blobless sparse clone). Secrets re-pasted by user. HANDOFF.md rewritten
  (commit ddeb7dd2ce). bootstrap.py green.

### Script (voiceover.txt)
- 200 beats (~7.7–8 min at measured ~2.31s/beat — up from v15's 169/6:30).
- Hook in first 2 sentences; comment-driving question at the end
  ("replaying the past or rehearsing the future?").
- R12 midpoint interrupt at beat 95 (48%): MAYA vignette (story format — v15
  used a pause-question, so the format rotates).
- Mechanism = energy economics: Jung's psychic energy (finite budget) +
  directed thinking vs fantasy thinking + inferior function (sensation) as the
  unused rest-channel. "Five rules" practical section (externalize loops, cap
  rehearsal, feed the inferior, ration depth, build a shutdown).
- Fence-checked (R22/R23): NOT #6 (3AM rumination = anxiety loop; v16 centers
  drain/energy, not worry), NOT #19 (self-criticism), NOT #18 (rest guilt).
  Pain = cognitive drain; mechanism = Ni/Ti energy economics. Not a dup.
- R12.1: no v15 signposts reused (checked programmatically in check_step_a.py).

### Captions + config
- 27 captions (R2 20–28), all anchors verified: attach to intended FIRST
  occurrence, chronological, no dup displays. 15 gold / 12 caption.
- 8 sections, all start-phrases verified present + in order.
- Title formula: V14 Psych → V15 Why → V16 Why (2 in a row — allowed; V17 must
  NOT be "Why…").
- check_step_a.py = pre-storyboard self-checker (mirrors pipeline parsing).
  ALL CHECKS PASS.

### Assets
- 9 AI images so far (ember-dusk palette — R13 distinct from v13 dawn/cool-blue,
  v14 warm interior, v15 storm grey-blue; distinct subjects: face, candle,
  dusk road, desk thinker, hands, clockwork, insomnia bed, train car, burnt
  match). **img08 (underwater depth metaphor) BLOCKED: 1st attempt by the
  image-model safety filter, retry hit the 10-images-per-turn cap → GENERATE
  FIRST THING NEXT TURN, then re-run rebuild_assets.py.** All 9 verified
  1672×941 (16:9) + sane exposure via ImageMagick (no vision available this
  session).
- 160 stock assets in /tmp/stock16 (61 videos + 99 photos, 338MB): 16 video
  queries ×4 + 18 photo queries ×6, Pexels landscape. assets.json + 
  stock_manifest.json built; fetch_assets.py idempotent (API-based);
  rebuild_assets.py rebuilds from manifest with NO API calls (use this one
  after adding img08 — avoids search-result drift).
- Totals: 178 assets (89% of 200 beats); +img08 → 179 (90%, meets R18).

### Cleanup
- Old /tmp/ytrepo clone kept for reference this turn (28M); remove at step (b).
- Workspace: only video_016 sources (videos dir otherwise empty).

## Step (b) storyboard + verify — DONE (2026-08-24)
- img08 generated (softened prompt passed; 1672×941, brightness 10459) →
  rebuild_assets.py → 179 assets (90% of 200 beats, R18 ✓).
- storyboard: 200 beats, captioned 27, assets used 179/179 (100% of pool),
  over-cap none, min reuse distance 136 beats (floor 26), avg 175.
- verify.py storyboard: ✅ ALL CHECKS PASS.
- /tmp/ytrepo clone removed.

## Step (c) TTS — DONE (2026-08-24)
- 200 clips, voice af_heart @1.0 (R5). 8 audio chunks (00–07) pushed to repo.
- verify.py tts: ✅ ALL CHECKS PASS (27/27 captions have cap_start; mid-sentence
  keywords cap_start > 0).
- **Runtime projection: ~10.9 min** (sampled 70 wavs across chunks 00/04/07:
  avg 3.06s/beat speech + 0.2s gaps). LONGEST video yet — slightly over R4's
  8–10 window after chronic under-length (v14 6:38, v15 6:30). Decision for
  user: ship as-is (recommended — midroll-eligible, fixes the under-length
  flag) or trim ~15–20 beats (would invalidate TTS chunks — expensive).
  If shipping as-is, no action needed; render proceeds on the full 200.

## Step (d) render — DONE (2026-08-24)
- /tmp wiped between turns (tmpfs reset): bootstrap re-run + stock refetched.
  NOTE: search results did NOT drift (all 179 storyboard keys resolved).
- First-chunk gate: chunk 0 rendered alone → verify PASS → then 1–7 sequential.
- 8 chunks (00–07) rendered + pushed. verify.py chunk 0–7: ✅ ALL PASS
  (30fps, SAR 1:1, duration≈beat_len).
- **New tool `tools/refetch_stock.py`** (R10 lesson): git_push's big-file path
  frees /tmp/stockN on every >35MB chunk push → plain fetch_assets.py re-runs
  would blow Pexels' 200/hr limit. refetch_stock.py harvests direct CDN URLs
  ONCE (stock_urls.json in video dir) then re-downloads by URL with ZERO API
  calls. Render loop = refetch → render per chunk (~3 min/chunk, all 8 in
  ~25 min wall).

## Step (e) assemble — DONE (2026-08-24)
- **R21.6 pressure hit at ASSEMBLE time** (not just finalize): part_01 push
  failed — shallow clone of main tip (~840MB, bloated by 300MB video chunk
  zips) + part copy + loose object > 993MB tmpfs. Real error surfaced by new
  git_push stderr print (R10): "unable to write loose object: No space left".
- **Structural fix (now permanent in tools):**
  1. `git_push.py --branch X` — clone main once, push to refs/heads/X (side
     branch) so main's tip never grows during intermediate pushes.
  2. `pipeline.py` assemble pushes parts to `parts/{NAME}-{k:02d}` branches;
     finalize pulls branch-first, main-fallback.
  3. Purged video_chunk_00..07.zip from main tip (served their purpose);
     audio chunks KEPT (re-TTS insurance, 32MB).
- Parts: part_00 on MAIN; parts 01–07 on branches parts/video_016-01..07.
- verify.py assemble (re-pulled all 8): ✅ ALL PASS (A/V diff ±0.1s each).
- **Total runtime: 656.8s = 10.95 min** (matches TTS projection).
- Local intermediates cleaned (workspace 29MB).

## NEXT TURN — step (f) FINALIZE (its OWN turn, R16.2)
1. Pre-flight: /tmp >300MB free ✓ (936MB).
2. PIPE_VIDEO=/home/user/videos/video_016 python3 tools/pipeline.py finalize
   (~12 min: pulls 8 parts branch-first, concat + captions on absolute
   timeline, R20 audio chain, loudnorm; size-guard crf 26→28→30→32 <95MB).
3. **R21.6 purge BEFORE final.mp4 push**: delete audio_chunk_00..07.zip from
   main + part_00 from main + refs/heads/parts/video_016-0* (API) → tip ~460MB.
4. Push final.mp4 (75-95MB → shallow path OK at slim tip). Decode spot-check
   ×4 + caption schedule print. metadata.md.
5. THEN (separate turns): thumbnail (R8 — vary composition; last 3: bowed
   figure / padlocked door / child's face) → 2 vertical Shorts.

## Repo (video_016) — after this push
- voiceover.txt, storyboard_config.json, images/img01-07+09+10, fetch_assets.py,
  rebuild_assets.py, check_step_a.py, assets.json, stock_manifest.json, STATUS.md.
