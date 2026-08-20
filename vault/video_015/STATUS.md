# STATUS — Video 015 "Why INFJs Push People Away When They Need Them Most"

## Step (a) assets + script — DONE (2026-08-20)

### Script (voiceover.txt)
- 169 beats (~8 min — R4 target). Hook in first 2 sentences; R12 midpoint
  interrupt at beat 76 (~45%): direct "pause" question; comment-driving question
  at the end.
- Jungian mechanism = Fe–Ti loop under stress (Fe feels own need as burden →
  pre-emptive withdrawal; Ti rationalizes "handle it alone"). Pain = the paradox
  of pushing people away when you need them most.
- Fence-checked (R22/R23): differentiated from v3 (go quiet when hurt, Fi) and
  v9 (door-slam/ghosting, Se-exit) — distinct pain (refusing help while hurting)
  + distinct mechanism (Fe–Ti loop). NOT a dup.

### Captions + config
- 27 captions (R4 20–28), all anchors verified unique across 169 sentences.
- 8 sections. max_uses 2. Title "Why…" (V15 — safe per R11: Why→Psych→Why).

### Assets
- 10 AI images (storm grey-blue monochrome, R13 — distinct from v13 dawn/cool-
  blue and v14 warm interior), repo-backed (commit 1fb8ed9b3d).
- 129 stock assets: 82 photos + 47 videos in /tmp/stock15 (NOT workspace).
  assets.json + stock_manifest.json built; fetch_assets.py idempotent + dedups
  by filename (fixes the v14 double-registration wart).

### Cleanup done this turn
- v13 + v14 shorts_ai images backed up to repo (R3.6).
- v14 parts .wav purged (shorts done; voice re-derivable via re-TTS).
- Local videos/video_013, videos/video_014, thumbnails/ wiped (all downloaded).
- Workspace 337KB before v15 step(a) files.

### Repo commits
- 1fb8ed9b3d — step(a) sources + 10 AI images.
- 35d4766aba — storyboard + state (step b PASS).

## Step (b) storyboard + verify — DONE (2026-08-20)
- 169 beats, 129 distinct assets (100% of pool used; 40 reuses at min distance
  118 beats — well above the 26-beat floor).
- verify.py storyboard: ✅ ALL CHECKS PASS.

### ⚠️ Next-turn note (session-reset self-heal, R19)
- stock15 lives in /tmp/stock15 → wiped on reset. Re-run
  `python3 videos/video_015/fetch_assets.py` (idempotent) before render if missing.
- bootstrap.py if imageio-ffmpeg/kokoro missing.

## Step (c) TTS — DONE (2026-08-20)
- 169 clips, voice af_heart @1.0 (R5). 7 audio chunks pushed to repo (00–06).
- verify.py tts: ✅ ALL CHECKS PASS (27/27 captions have cap_start; mid-sentence
  keywords cap_start > 0). Repo storyboard.json has all cap_start timings.

## Step (d) render — DONE (2026-08-20)
- 7 chunks rendered (169 beats). First-chunk gate PASSED (chunk 0), then 1–6.
- verify.py chunk 0–6: ✅ ALL PASS (30fps, SAR 1:1, duration≈beat_len).
- Repo: video_chunk_00..06.zip (36.5/36.4/36.8/40.9/31.6/33.0/14.8 MB).

### R10 fix shipped this step (push infra, never recur)
- **git_push.py v3**: two paths — (a) Git Data API for files ≤35MB (no clone),
  (b) shallow FULL clone (`--depth 1`, NO `--filter=blob:none`) for bigger files.
  Root cause of all the "No space left / could not fetch promisor" failures:
  partial clone (blob:none) + git 2.47 `write-tree` lazy-fetches a ~600MB
  promisor pack (triggered by root-level legacy blob ElevenLabs_v1.mp3 +
  index validation). Shallow full clone has all objects → normal add/commit/push.
- Deleted legacy root junk `ElevenLabs_v1.mp3` + `sync.bat` from the repo.

## Step (e) assemble — DONE (2026-08-20)
- 7 parts (part_00..06.mp4/.wav) assembled + pushed via git_push v3 (API path).
- A/V sync verified by re-pulling parts: video==audio on all 7 (diff 0.00s).
- ⚠️ Total runtime = 6:30 (169 beats × ~2.3s avg) — under R4's 8-min floor,
  same as v14 (6:38). Flag for user at finalize (ship vs expand).

## Step (f) finalize — DONE (2026-08-20)
- final.mp4 built: 6:29.8, 1080p/30fps, stereo AAC, 27 word-synced captions,
  R20 audio (pad 0.55 + sidechain), size-guard crf 26→28 → 72.7MB.
- Decode spot-check ×4 OK.
- Push failed first: repo tip was 970.7MB (chunks+parts still in tree) → the
  shallow full clone for the 72.7MB final overflowed /tmp. FIX: purged all
  video_015 intermediates (tip → 453MB), then pushed (commit 644148c).
- R21.6 updated: purge chunks+parts BEFORE final.mp4 push from now on.

## PENDING
- Thumbnail (R8) — next turn.
- 2 Shorts (hook + payoff) via make_short.py v2 (re-TTS, vertical).

## REPO (video_015)
- KEPT: images/ (10), final.mp4 (72.7MB), storyboard.json, assets.json,
  state.json, metadata.md, voiceover.txt, storyboard_config.json, fetch_assets.py.
- PURGED: video_chunk_00..06.zip, audio_chunk_00..06.zip, part_00..06.mp4/.wav.
