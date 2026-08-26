# 🔄 HANDOFF — The Deeper Mind (resume here)
*Rewritten 2026-08-26 (v11 turn). Read this FIRST in a new chat session.
If this file and VIDEO_QUEUE.md disagree, VIDEO_QUEUE.md wins on progress.*

## How to use this file
1. Read this whole file.
2. Run `python3 tools/bootstrap.py` (resets wipe pip/ffmpeg/kokoro).
3. If the workspace is EMPTY (full wipe): recover from the PUBLIC repo —
   blobless sparse clone (see OPERATIONAL FACTS) — then re-ask the user for
   BOTH secrets. Never guess or skip.
4. Continue from NEXT ACTIONS.

## The project in one paragraph
"The Deeper Mind" — faceless YouTube psychology channel for rare intuitive
types (INFJ/INTJ/INFP/INTP) through a Jungian lens. USA/UK. **16 long-form
videos shipped (v1–v16) + Shorts campaign in progress.** Python pipeline
(`tools/pipeline.py`) turns script + stock/AI assets into captioned 1080p
videos; `tools/make_short.py` v2 + `tools/shorts_backlog.py` produce NATIVE
VERTICAL Shorts. Everything backed up to GitHub `zainkhan122/yt-tts`
(branch main — PUBLIC, ~6.8GB history).

## CURRENT STATE (2026-08-26)
- **v16 "Why You're Exhausted as a Deep Thinker" COMPLETE:** final.mp4
  10:57 (74.6MB, midroll-eligible — longest yet), thumbnail NOT LAZY.
  DEPLETED. (approved, registered), metadata pack (v15 pattern), 2 vertical
  Shorts (hook + Maya-experiment payoff). User downloaded everything; local
  copies purged. v16 in repo: vault/video_016/ complete.
- **SHORTS BACKFILL CAMPAIGN (user-directed):** vertical Shorts for the
  Month-1/2 back-catalog. Status: **v4 v5 v6 v7 (rebuilt) + v8 v9 v10 v11
  (native) DONE — 2 Shorts each, all R24-compliant.** Remaining: v12, then
  optional v13–v16 refresh (v16's payoff reused hook images pre-R24).
- **⚠ v1–v3 CANNOT get Shorts:** repo has only thumbnails (no script/
  storyboard/audio — Month-1 backups started at v4). If user still has the
  final.mp4s locally, upload → transcribe → rebuild. Otherwise skip.
- **R24 (user-mandated 2026-08-26):** every Short gets its OWN fresh media —
  per-kind portrait stock (queries_hook.txt / queries_payoff.txt, THEMED to
  the actual beats) + per-kind AI images in shorts_ai/{hook,payoff}/. Never
  shared between the two Shorts of a video. make_short seeds RNG per
  (video, kind). ASSETS MUST BE BEAT-MATCHED (mirror the spoken line).

## KEY TOOLS (all in vault/tools/ — verified in sync 2026-08-26)
- `pipeline.py` — long-form builder (steps a–f; branch-aware part push/pull)
- `make_short.py` v2 — vertical Shorts (per-kind pools per R24; --beats A B
  exclusive upper bound; --skip list; re-TTS af_heart w/ long-form keyword
  splits; CTA text+spoken appended; self-verifies 1080x1920/30fps/25–50s)
- `shorts_backlog.py` — ROBUST backfill driver: pre-flight (deps/secrets//
  tmp), duration pre-check window [28,47]s incl CTA ext ~3.6s, idempotent
  state (shorts/SHORTS_STATE.json), logs to SHORTS_LOG.txt, per-kind queries
  files. Usage: `plan NNN` / `build NNN hook|payoff|both --pay-a A --pay-b B
  --skip 78,79` + videos/NNN/shorts/queries_{hook,payoff}.txt
- `refetch_stock.py` — URL-harvest stock refetcher (API-frugal; stock_urls.json)
- `git_push.py` v3 — ≤35MB → Git Data API; >35MB or `--branch X` → shallow
  FULL clone pushed to refs/heads/X (side branches keep main's tip slim)
- `repo_update.py` — small files + deletes via API
- `render_thumb16.py` (vault/pipeline/) — R8 thumbnail compositor (argv-list
  labels, per-op geometry, 50% glow — fixes the corrupted-text bug)

## SHORTS RECIPE (one video per turn, ~10 images = the gen cap)
1. `python3 tools/shorts_backlog.py plan NNN` + read the storyboard beats.
2. Pick payoff = best SELF-CONTAINED arc (never the subscribe tail; the
   auto-picker lands on it — override with --pay-a/--pay-b). Compute the
   window; trim with --skip (drop signposts/redundant beats, never the
   punchline). REMEMBER: --beats A B means A..B-1.
3. Generate 5 hook + 5 payoff verticals (9:16, distinct per Short, each
   mirroring its exact narration beat) into shorts_ai/{hook,payoff}/.
4. Write shorts/queries_{hook,payoff}.txt (mkdir shorts FIRST or the
   printf fails silently → defaults get used — happened once, caught).
5. `build NNN hook` then `build NNN payoff --pay-a .. --pay-b .. [--skip ..]`
   (start_process, ~4 min each; poll log+state).
6. Verify log lines (short built … 1080x1920), push shorts_ai + state +
   queries to repo, register rows in VIDEO_QUEUE.md Shorts register,
   present payoff to user. Clean PREVIOUS video's local shorts/shorts_ai.

## LOCKED RULES (full text in MASTER_RULES.md R1–R24)
- Voice R5: Kokoro af_heart @1.0. Audio R20: pad 0.55 + sidechain 0.05:3,
  loudnorm -16. Cadence R21: 2 long/wk + 3 Shorts/wk. Thumbnails R8: cryptic
  2–3 word diagnosis, used-lines register in VIDEO_QUEUE.md. Titles R11:
  **V17 must NOT be "Why…"**. Scripts R4/R12: hook ≤2 sentences, midpoint
  interrupt ~50%, comment-driving closer; ~200 beats ≈ 11 min at 2.3s/beat.
  Captions R2: 20–28, word-synced. Dedup R23 + retired topics in queue.
  Niche R22. **R24: Shorts media independence (see above).**

## OPERATIONAL FACTS (hard-won)
- Two reset flavors: (1) pip+~/.cache/kokoro+/tmp wiped → bootstrap;
  (2) FULL workspace wipe → blobless sparse clone recovery:
  `git clone --filter=blob:none --no-checkout --depth 1
  https://github.com/zainkhan122/yt-tts.git /tmp/ytrepo && cd /tmp/ytrepo &&
  git sparse-checkout init --cone && git sparse-checkout set vault/tools
  vault/reusable && git checkout main` → copy to /home/user. NEVER full-clone
  (repo ~6.8GB; partial clone + commit lazy-fetches ~600MB promisor pack).
- Secrets cannot be recovered from repo: `secrets/github_pat.txt` +
  `~/.pexels_key` — after a wipe, STOP and ask user to re-paste.
- /tmp = 993MB tmpfs, WIPED OFTEN (between turns too!). Stock lives in
  /tmp/stockN; use refetch_stock.py (URL-based, API-free). Kokoro ~400MB in
  ~/.cache (excluded from snapshots; bootstrap re-downloads).
- git_push >35MB uses shallow FULL clone of main's tip — **keep main's tip
  <~700MB**: v16 lesson = purge intermediates aggressively; parts went to
  side branches `parts/NNN-kk` (deleted after finalize). Root junk removed
  (_t2.bin). Repo total ~6.8GB (blobs never GC'd — consider fresh repo/LFS
  if it hurts).
- RAM 2GB: heavy steps via start_process/nohup detached, poll logs. Image
  gen cap: 10/turn. Foreground bash dies ~30-50s under load but orphans
  children (they finish — check state/log before relaunching).
- Unauthenticated GitHub API rate-limits fast — use the PAT.
- Image-model safety filter: avoid "child + darkness", underwater people;
  rephrase with objects/landscapes instead.

## NEXT ACTIONS (in order)
1. **v12 Shorts** (last backfill): "There Are 4 People Living Inside You"
   (persona–shadow–anima–Self). Sources ✓ in repo. Same recipe.
2. Optional (user's call): v13–v16 Shorts refresh under R24 (v16's payoff
   reused its hook's 5 images; v13–15 also predate R24 but are published).
3. **Video 17** (fresh turn, step a): title NOT "Why…" (R11). Slate #17
   "Can't Do Small Talk" is a likely R23 dup-retire (brushes #2+#4) — check
   register; candidates #18 Rest-Guilt / #19 Never Good Enough (⚠ differentiate
   from v16's "stop earning worth with processing") / #20 (⚠ center Si memory
   not rumination). MONTH2_PLAN.md + VIDEO_QUEUE.md for the slate.
4. Keep registering every Short in the queue's Shorts register same-day.

## SECRETS (do NOT push into the PUBLIC repo)
- /home/user/secrets/github_pat.txt · /home/user/.pexels_key

## KEY FILES
- Workspace: /home/user/{MASTER_RULES.md, VIDEO_QUEUE.md, MONTH2_PLAN.md,
  HANDOFF.md, README.md, tools/, reusable/, secrets/, thumbnails/, videos/}
- Repo: vault/{docs, tools/, reusable/, pipeline/, video_001..016/} — each
  video keeps final/thumbnail/shorts/sources in its dir.
