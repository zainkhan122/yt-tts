# 🔄 HANDOFF — The Deeper Mind (resume here)
*Written 2026-08-20. Read this FIRST if you are a new chat session.*

## How to use this file
1. Read this whole file. It compresses everything learned so far.
2. Run `python3 tools/bootstrap.py` (session resets wipe pip/ffmpeg/kokoro — see OPERATIONAL FACTS).
3. Continue from NEXT ACTIONS (bottom).

## The project in one paragraph
"The Deeper Mind" — a faceless YouTube psychology channel for rare intuitive
types (INFJ / INTJ / INFP / INTP) through a Jungian lens. USA/UK audience.
14 long-form videos shipped + 2 Shorts (v13). The system is a Python pipeline
(`tools/pipeline.py`) that turns script + stock/AI assets into a captioned 1080p
video with a music bed, everything backed up to GitHub repo
`zainkhan122/yt-tts` (branch main — **the repo is PUBLIC**).

## CURRENT STATE (exact)
- **v1–v12** shipped (Month 1, ~3/wk).
- **v13 "Why You Feel Like an Old Soul"** — SHIPPED: final.mp4 (5:06), thumbnail
  "ARRIVED EARLY", 2 Shorts (LEGACY blur-fill). Downloaded by user.
- **v14 "The Psychology of People Who Apologize for Existing"** — final.mp4
  (6:38) built, verified, pushed (repo commit 7f76af325b8f). User DOWNLOADED it
  (local copy removed). **Thumbnail candidate "SORRY IS SURRENDER" built but NOT
  approved yet** (user moved to a Shorts discussion before saying go). **Shorts
  NOT built.**
- **Decisions the user JUST made (2026-08-20 — apply these):**
  1. **Shorts must NOT use the R12 midpoint** — those clips lack context and die
     in the first seconds. Use **HOOK + the video's best SELF-CONTAINED payoff**.
  2. **Shorts must use NATIVE VERTICAL (portrait) media**, not blur-fill from the
     landscape video ("it seems small on screen").

## LOCKED RULES (quick reference — full text in MASTER_RULES.md, R1–R23)
- **Voice (R5):** Kokoro `af_heart`, speed 1.0. Never change.
- **Audio mix (R20):** pad `volume=0.55` + sidechain
  `threshold=0.05:ratio=3:attack=15:release=250`, final loudnorm I=-16 TP=-1.5
  LRA=11, stereo AAC 160k. NEVER raise pad above 0.55 or drop ratio below 3.
- **Cadence (R21):** 2 long-form/week (Tue+Fri), 3 Shorts/week (Mon/Wed/Sat).
- **Thumbnails (R8):** title identifies; thumbnail = cryptic 2–3 word diagnosis
  (white #FFFFFF, ~9px black stroke, soft glow, dark scrim bottom-left). Never
  repeat a concept — used-lines list lives in VIDEO_QUEUE.md. Vary composition.
- **Titles (R11):** rotate formulas, no 3 consecutive same.
- **Scripts (R4/R12):** hook in first 2 sentences; midpoint pattern-interrupt at
  ~50%; end with a comment-driving question; target 8–10 min (~170 beats,
  ~4s/beat — current average is ~2.3s, too short, keep calibrating).
- **Captions (R2):** 20–28 per video, word-synced (split sentence at keyword +
  0.12s gap), hold 2.6s.
- **Niche fence (R22):** rare intuitive types + Jungian mechanisms. Reject
  anything a generic motivation channel could publish unchanged.
- **Dedup register (R23):** every shipped video/short's title + pain point +
  mechanism is recorded in VIDEO_QUEUE.md. A new topic must not reuse a
  registered pain point OR mechanism (reworded titles = duplicates).

## BUILD PIPELINE (R16 — ONE step per user turn)
Cadence: (a) assets+script → (b) storyboard+verify → (c) tts → (d) render+verify
chunks (first-chunk gate) → (e) assemble+verify parts → (f) finalize.
```bash
PIPE_VIDEO=/home/user/videos/video_015 python3 tools/pipeline.py storyboard
PIPE_VIDEO=/home/user/videos/video_015 python3 tools/pipeline.py tts
PIPE_VIDEO=/home/user/videos/video_015 python3 tools/pipeline.py render 0
PIPE_VIDEO=/home/user/videos/video_015 python3 tools/pipeline.py assemble 0
PIPE_VIDEO=/home/user/videos/video_015 python3 tools/pipeline.py finalize
python3 tools/verify.py /home/user/videos/video_015 storyboard|tts|chunk 0|assemble
```
Each step: pre-flight (df /tmp >300MB free, du /home/user <128MB) per R17.

## OPERATIONAL FACTS (hard-won — do NOT relearn these)
- **Session resets** wipe pip packages, `~/.cache/kokoro`, and `/tmp` — but NOT
  `/home/user` workspace files. Run `python3 tools/bootstrap.py` FIRST every
  session. `pipeline.py` self-heals too.
- ffmpeg: `python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"`.
  ImageMagick = `magick`. Font `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`.
- `/tmp` is tmpfs 993MB. Stock assets live in `/tmp/stockN` (NOT the workspace,
  to respect the ~128MB workspace snapshot cap). `fetch_assets.py` is idempotent
  — re-run it after any reset to refetch missing stock.
- **`git_push.py` uses the PLUMBING path** (write-tree + commit-tree + update-ref
  + explicit-ref push). DO NOT reintroduce `git commit`: in a partial clone it
  lazy-fetches a ~600MB promisor pack (repo is ~5.8GB) and fills /tmp. Cleanup
  is in a `finally`.
- Git Data API blob ceiling ~40MB → use `git_push.py` for big files. GitHub hard
  file limit 100MB → pipeline's size guard escalates crf 26→28→30→32 to stay
  <95MB.
- `repo_update.py` (Git Data API) = small files + deletes. `git_push.py` = big
  files (final.mp4, parts, chunk zips).
- RAM is 2GB → run heavy steps detached (`nohup bash -c '...' >log 2>&1 < /dev/null
  & disown`) and poll flag files. The sandbox kills a foreground shell at ~50s
  under load but orphans the child (which keeps running). Run chunks one process
  at a time to avoid push races.
- Rough runtimes: tts ~6min, render ~13min, assemble ~8min, finalize ~12min.
  Poll every 30s.

## SHORTS — THE NEW SYSTEM (build next)
1. **Segments:** HOOK (cold open) + the video's best SELF-CONTAINED payoff
   (pick per-video; a standalone setup → tension → payoff in 30–45s). Never the
   midpoint.
2. **Visuals:** NATIVE VERTICAL. Fetch ~25 portrait stock clips (Pexels videos
   `orientation=portrait` — `stock_fetch.py` needs a portrait option added) +
   ~5 vertical AI images per Short. Render true 1080×1920. No blur-fill.
3. **Reuse from the long-form:** script segment, voice (from parts .wav — no
   re-TTS), caption timings (storyboard.json), R20 audio chain.
4. **Every Short:** word-synced captions + end-CTA (text bar "▶ FULL VIDEO ON
   CHANNEL" + spoken "Watch the full video on this channel." in af_heart,
   APPENDED after narration — never overlapping, R21.5).
5. `tools/make_short.py` currently does blur-fill + hook/midpoint → **REWRITE for
   vertical**. `tools/fix_short_cta.py` patches CTAs on existing Shorts.
6. v13's 2 Shorts are LEGACY blur-fill (downloaded). Leave them unless the user
   asks to redo.

## NEXT ACTIONS (in order)
1. **v14 thumbnail:** candidate "SORRY IS SURRENDER" is at
   `/home/user/thumbnails/video_014_cover.jpg` (workspace) and
   `vault/video_014/thumbnail_candidate.jpg` (repo). Show the user → on "go",
   push as `vault/video_014/thumbnail.jpg` and register the line in
   VIDEO_QUEUE.md's used-lines list.
2. **Build the VERTICAL Shorts system** (rewrite `tools/make_short.py` + add a
   portrait option to `tools/stock_fetch.py`). One dedicated turn.
3. **Build v14's 2 Shorts** (hook + best self-contained payoff) with it.
4. Purge v14 parts .wav after Shorts are approved (parts .mp4 already purged).
5. **Video 15 "Why INFJs Push People Away When They Need Them Most"**
   (pain: self-sabotaged closeness · mechanism: Fe–Ti loop under stress) —
   step (a). Check VIDEO_QUEUE.md slate + dedup register first.

## SECRETS (do NOT push into the PUBLIC repo)
- `/home/user/secrets/github_pat.txt` (read/write on zainkhan122/yt-tts)
- `/home/user/.pexels_key`
- If either is missing after a reset → STOP and ask the user to re-paste. Never
  guess or skip.

## REPO FLAGS
- The repo is **PUBLIC** and ~5.8GB (video binaries; GitHub never GCs old
  blobs). Purge intermediates promptly after each video ships. Old blobs stay in
  history forever — consider LFS or a fresh repo if size becomes a problem.
- Repo layout: `vault/{MASTER_RULES.md, VIDEO_QUEUE.md, MONTH2_PLAN.md,
  HANDOFF.md, README.md, tools/, reusable/, video_001..014/}`.

## KEY FILES
- Workspace: `/home/user/{MASTER_RULES.md, VIDEO_QUEUE.md, MONTH2_PLAN.md,
  HANDOFF.md, README.md, AUDIT_2026-08-18.md, tools/, reusable/, secrets/,
  thumbnails/, videos/video_014/}`
- Repo: `vault/{...same docs..., tools/, reusable/, video_001..014/}`
