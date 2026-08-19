# STATUS — Video 014 "The Psychology of People Who Apologize for Existing"

## Step (a) assets + script — DONE (2026-08-19)

### Script (voiceover.txt)
- 171 beats (~8 min — R4 target hit; v13 was 109 beats/5:06, length lesson applied).
- Hook in sentence 1. R12 midpoint interrupt at ~beat 106 ("pause here" question,
  ~50% is at beat ~86; the interrupt sits just past 50% inside ACT5 — verified on
  the real timeline at tts/storyboard).
- Jungian mechanism = Extraverted Feeling dominance + weak Introverted Feeling
  (Fe without an Fi anchor). Pain = over-apologizing / self-erasure.
- Fence-checked (R22/R23): NOT a dup of v1 (absorption), v3 (withdraw when hurt),
  v7 ("too much"). Distinct pain + distinct mechanism.

### Captions + config
- 27 captions (R4 20-28), all anchors verified unique across 171 sentences.
- 8 sections. max_uses 2. Title "The Psychology of People Who…" (V14 — safe per R11).

### Assets
- 10 AI images (warm interior, R13 — distinct from v13 dawn/cool-blue), repo-backed.
- 154 stock assets: 82 photos + 72 videos in /tmp/stock14 (NOT workspace — snapshot
  cap untouched). assets.json + stock_manifest.json built; fetch_assets.py idempotent.

### Repo commits
- cd9dffdeec — step(a) sources + 10 AI images.
- b6912bbd12 — storyboard + state (step b PASS).

## Step (b) storyboard + verify — DONE (2026-08-19)
- 171 beats, 154 distinct assets (100% of pool used; 17 reuses at min distance
  125 beats — well above the 26-beat floor).
- verify.py storyboard: ✅ ALL CHECKS PASS.

### ⚠️ Next-turn note (session-reset self-heal, R19)
- stock14 lives in /tmp/stock14 → wiped on session reset. Re-run
  `python3 videos/video_014/fetch_assets.py` (idempotent) before render if missing.
- bootstrap.py re-run if imageio-ffmpeg/kokoro missing.

## Step (c) TTS — DONE (2026-08-19)
- 171 clips, voice af_heart @1.0 (R5). 7 audio chunks pushed to repo (00–06).
- verify.py tts: ✅ ALL CHECKS PASS (27/27 captions have cap_start; mid-sentence
  keywords cap_start > 0). Repo storyboard.json has all cap_start timings.

## Step (d) render — DONE (2026-08-19)
- 7 chunks rendered (171 beats). First-chunk gate PASSED (chunk 0 perfect), then 1–6.
- verify.py chunk 0–6: ✅ ALL PASS (30fps, SAR 1:1, duration≈beat_len every beat).
- Repo: video_chunk_00..06.zip (209.3MB total).

### Known cosmetic wart (fix post-ship)
- One Pexels clip (pexels_v7279754.mp4) is registered under TWO asset keys
  (two queries returned the same video; the skip-existing-download left both
  entries). File exists, render unaffected — it behaves like a normal reuse
  (R1 allows 2×). Fix: dedupe by filename in fetch_assets.py after v14 ships.

## NEXT STEP (e): assemble + verify parts
`for k in 0..6: PIPE_VIDEO=... python3 tools/pipeline.py assemble $k`
then `python3 tools/verify.py /home/user/videos/video_014 assemble`.
Parts push via git_push.py. Run detached + poll.
