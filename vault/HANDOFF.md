# 🔄 HANDOFF — The Deeper Mind (resume here)
*Rewritten 2026-08-24 after a FULL workspace wipe (the 08-20 copy was stale).
Read this FIRST if you are a new chat session. Repo > this file if they disagree.*

## How to use this file
1. Read this whole file.
2. Run `python3 tools/bootstrap.py` (resets wipe pip/ffmpeg/kokoro — see OPERATIONAL FACTS).
3. If the workspace is EMPTY (full wipe): recover docs/tools/reusable from the
   PUBLIC repo — blobless sparse clone (see OPERATIONAL FACTS). Then re-ask the
   user for BOTH secrets (they cannot be recovered any other way).
4. Continue from NEXT ACTIONS (bottom). Cross-check VIDEO_QUEUE.md — it is the
   live progress tracker; this file compresses context only.

## The project in one paragraph
"The Deeper Mind" — a faceless YouTube psychology channel for rare intuitive
types (INFJ / INTJ / INFP / INTP) through a Jungian lens. USA/UK audience.
**15 long-form videos shipped + 6 Shorts (all NATIVE VERTICAL)**. The system is
a Python pipeline (`tools/pipeline.py`) that turns script + stock/AI assets into
a captioned 1080p video with a music bed, everything backed up to GitHub repo
`zainkhan122/yt-tts` (branch main — **the repo is PUBLIC**, ~5.8GB).

## CURRENT STATE (verified against repo 2026-08-24, tip ba360d6)
- **v1–v15 SHIPPED.** v14 "Apologize for Existing" 6:38 thumb SORRY IS
  SURRENDER; v15 "INFJs Push People Away" 6:30 thumb THE LOCKED DOOR (tip
  commit ba360d6 = v15 shorts complete).
- **Shorts system v2 (vertical) BUILT and PROVEN** — `make_short.py` v2 +
  portrait option in `stock_fetch.py`. 6 Shorts shipped: hook+payoff for v13,
  v14, v15 (all registered in VIDEO_QUEUE.md Shorts register).
- **R21.6 purge order:** purge chunk zips + parts BEFORE pushing final.mp4
  (repo tip must stay <~700MB or the shallow clone for big pushes overflows
  /tmp). Applied on v15. Parts .wav not needed after assemble (Shorts re-TTS).
- **Length calibration:** beats land ~2.3s each → ~170 beats ≈ 6:30 (v14 6:38,
  v15 6:30, both under the 8-min R4 floor; user shipped both anyway). For ~8
  min target ~205–210 beats.
- Workspace was FULLY WIPED on 2026-08-24 (docs/tools/secrets included) —
  everything except repo contents was lost. Fully recovered from the repo.

## LOCKED RULES (quick reference — full text in MASTER_RULES.md, R1–R23)
- **Voice (R5):** Kokoro `af_heart`, speed 1.0. Never change.
- **Audio mix (R20):** pad `volume=0.55` + sidechain
  `threshold=0.05:ratio=3:attack=15:release=250`, final loudnorm I=-16 TP=-1.5
  LRA=11, stereo AAC 160k. NEVER raise pad above 0.55 or drop ratio below 3.
- **Cadence (R21):** 2 long-form/week (Tue+Fri), 3 Shorts/week (Mon/Wed/Sat).
- **Shorts (R21.3):** hook + best SELF-CONTAINED payoff (never the midpoint),
  NATIVE VERTICAL 1080×1920 media, reuse long-form script/CTA rules; end-CTA
  text+spoken appended after narration.
- **Thumbnails (R8):** title identifies; thumbnail = cryptic 2–3 word diagnosis
  (white #FFFFFF, ~9px black stroke, soft glow, dark scrim bottom-left). Never
  repeat a concept — used-lines list in VIDEO_QUEUE.md. Vary composition.
- **Titles (R11):** rotate formulas, no 3 consecutive same. V14 Psych → V15 Why
  → V16 Why (2 in a row, OK) → **V17 must NOT be "Why…"**.
- **Scripts (R4/R12):** hook in first 2 sentences; midpoint pattern-interrupt at
  ~50% (VARY the format — v15 used a pause-question); end with a
  comment-driving question; target 8–10 min (~205 beats at measured 2.3s).
- **Captions (R2):** 20–28 per video, word-synced (split at keyword + 0.12s),
  hold 2.6s. Caption anchor attaches to the FIRST sentence containing it.
- **Niche fence (R22):** rare intuitive types + Jungian mechanisms.
- **Dedup (R23):** check VIDEO_QUEUE.md register BEFORE approving any topic.
  Used thumb lines / retired topics / Short hooks all live there too.

## BUILD PIPELINE (R16 — ONE step per user turn)
Cadence: (a) assets+script → (b) storyboard+verify → (c) tts → (d) render+verify
chunks (first-chunk gate) → (e) assemble+verify parts → (f) finalize (purge
chunks+parts BEFORE final push per R21.6) → thumbnail (approval) → 2 Shorts.
```bash
PIPE_VIDEO=/home/user/videos/video_016 python3 tools/pipeline.py storyboard
PIPE_VIDEO=/home/user/videos/video_016 python3 tools/pipeline.py tts
PIPE_VIDEO=/home/user/videos/video_016 python3 tools/pipeline.py render 0
PIPE_VIDEO=/home/user/videos/video_016 python3 tools/pipeline.py assemble 0
PIPE_VIDEO=/home/user/videos/video_016 python3 tools/pipeline.py finalize
python3 tools/verify.py /home/user/videos/video_016 storyboard|tts|chunk 0|assemble
```
Each step: pre-flight (df /tmp >300MB free, du /home/user sane) per R17.

## OPERATIONAL FACTS (hard-won — do NOT relearn these)
- **Resets come in two flavors:** (1) normal: pip + ~/.cache/kokoro + /tmp
  wiped, workspace survives → just run bootstrap; (2) FULL wipe (2026-08-24):
  everything gone. Recovery: blobless sparse clone —
  `git clone --filter=blob:none --no-checkout --depth 1
  https://github.com/zainkhan122/yt-tts.git /tmp/ytrepo && cd /tmp/ytrepo &&
  git sparse-checkout init --cone && git sparse-checkout set vault/tools
  vault/reusable && git checkout main` → copy docs+tools+reusable to
  /home/user. NEVER clone with blobs (repo ~5.8GB; partial-clone+commit
  lazy-fetches a ~600MB promisor pack and fills /tmp).
- **Secrets cannot be recovered from the repo (by design).** After a full wipe:
  STOP and ask the user to re-paste `secrets/github_pat.txt` (PAT,
  read/write on zainkhan122/yt-tts) and `~/.pexels_key`. Never push them.
- Unauthenticated GitHub API is rate-limited fast — use the PAT from
  secrets/ for API calls, or raw.githubusercontent.com.
- ffmpeg: `python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"`.
  ImageMagick = `magick`. Font `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`.
- `/tmp` is tmpfs 993MB. Stock assets live in `/tmp/stockN` (NOT the workspace).
  Per-video `fetch_assets.py` is idempotent — re-run after any reset.
- **git_push.py v3**: ≤35MB → Git Data API (no clone); >35MB → shallow FULL
  clone. `repo_update.py` (Git Data API) = small files + deletes. GitHub file
  limit 100MB → size guard escalates crf 26→28→30→32 to stay <95MB.
- RAM is 2GB → run heavy steps detached (`nohup bash -c '...' >log 2>&1 <
  /dev/null & disown`) and poll flag files/logs. One chunk process at a time.
- Rough runtimes: tts ~6min, render ~13min, assemble ~8min, finalize ~12min.
- Kokoro model ~400MB lives in ~/.cache/kokoro (excluded from snapshots) —
  bootstrap re-downloads it; `du /home/user` will show it, that's expected.

## SECRETS (do NOT push into the PUBLIC repo)
- `/home/user/secrets/github_pat.txt` (read/write on zainkhan122/yt-tts)
- `/home/user/.pexels_key`
- If either is missing after a reset → STOP and ask the user to re-paste.

## NEXT ACTIONS (in order)
1. **Video 16 "Why You're Exhausted as a Deep Thinker"** (pain: cognitive
   drain · mechanism: Ni/Ti energy economics — Jung's psychic-energy economics
   + directed vs fantasy thinking). Step (a) 2026-08-24: script ~205 beats +
   8 sections + 25 captions + 10 AI images (EMBER DUSK palette — v13
   dawn/cool-blue, v14 warm interior, v15 storm grey) + stock /tmp/stock16.
   Next: step (b) storyboard+verify.
2. v16 build (c)–(f) per pipeline; R21.6 purge before final push.
3. v16 thumbnail (R8.7 — vary composition; last 3: bowed figure / padlocked
   door / child's face) + 2 vertical Shorts (hook + self-contained payoff).
4. V17: NOT a "Why…" title (R11). Slate + dedup register in VIDEO_QUEUE.md.
   (Note: #17/#18 flagged as likely-dup retires in the queue — re-check
   register before scripting.)

## KEY FILES
- Workspace: `/home/user/{MASTER_RULES.md, VIDEO_QUEUE.md, MONTH2_PLAN.md,
  HANDOFF.md, README.md, AUDIT_2026-08-18.md, tools/, reusable/, secrets/,
  thumbnails/, videos/}`
- Repo: `vault/{...same docs..., tools/, reusable/, video_001..015/,
  pipeline/}` — plus each video's STATUS.md (per-step build log).
