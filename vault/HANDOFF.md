# 🔄 HANDOFF — The Deeper Mind (resume here)
*Rewritten 2026-08-27 (v17 assets turn). Read this FIRST in a new chat session.
If this file and VIDEO_QUEUE.md disagree, VIDEO_QUEUE.md wins on progress.*

## How to use this file
1. Read this whole file.
2. **UPDATE THIS FILE FIRST** (R25): refresh CURRENT STATE + NEXT ACTIONS to
   match reality before doing anything else, push it, THEN work.
3. Run `python3 tools/bootstrap.py` (resets wipe pip/ffmpeg/kokoro).
4. If the workspace is EMPTY (full wipe): recover from the PUBLIC repo —
   blobless sparse clone (see OPERATIONAL FACTS) — then re-ask the user for
   BOTH secrets. Never guess or skip.
5. Continue from NEXT ACTIONS.

## The project in one paragraph
"The Deeper Mind" — faceless YouTube psychology channel for rare intuitive
types (INFJ/INTJ/INFP/INTP) through a Jungian lens. USA/UK. **16 long-form
videos shipped (v1–v16) + Shorts campaign in progress.** Python pipeline
(`tools/pipeline.py`) turns script + stock/AI assets into captioned 1080p
videos; `tools/make_short.py` v2 + `tools/shorts_backlog.py` produce NATIVE
VERTICAL Shorts. Everything backed up to GitHub `zainkhan122/yt-tts`
(branch main — PUBLIC, ~6.8GB history).

## CURRENT STATE (2026-08-27)
- **v16 COMPLETE. Shorts backfill v4–v12 DONE (VIDEO_QUEUE wins).** v1–v3 blocked (no sources).
- **v17 IN PROGRESS — The Psychology of the Friend Everyone Confides In.**
  Script 171 beats + storyboard_config (28 captions) ALL PASS. 10 AI images +
  stock (182 pool). **Storyboard DONE:** 171 beats, 28 captions, 171/182 assets
  (94%), max_uses 1, no consecutive reuse, no intra-chunk reuse.
  **TTS DONE.** **Render chunk 0 DONE + first-chunk gate PASS** (26/26:
  1920x1080, 30fps, SAR 1:1, dur≈beat_len). video_chunk_00.zip on main
  (~40.6MB). git_push freed /tmp/stock17 — refetch before chunks 1–6.
- **Tools consolidated (R25.2):** ALL tools in tools/ (repo vault/tools/):
  + `render_thumb.py` (generalized R8 compositor: `render_thumb.py BASE OUT
    "LINE 1." "LINE 2." [ptsize]`), + `check_script.py` (generalized step-a
    checker: `check_script.py VIDEO_DIR [prev_voiceover.txt]`). Deleted repo
    strays: vault/pipeline/render_thumb16.py, vault/video_016/{check_step_a,
    rebuild_assets}.py. Per-video dirs keep only CONFIG (fetch_assets.py,
    queries_*.txt, stock_urls.json).
- **YT-AUTOMATION REVIEW (2026-08-26, user asked):** gemini-youtube-
  automation (327★, active) = proven GitHub-Actions daily pipeline — the ONLY
  thing worth adopting is its YouTube Data API v3 upload pattern (base64
  OAuth secrets, quota fine: upload=1600 units of 10k/day). darkzOGx/
  youtube-automation-agent (2.7k★, active) = heavy Node dashboard; steal
  IDEAS only (analytics feedback loop, controlled title/thumb A/B). khaoss85/
  youtube-autopilot (24★, stale) = skip. VERDICT: automate plumbing, never
  judgment — our R4/R8/R22/R23 systems beat generic LLM pipes. **Phase 1
  (pending user): `tools/youtube_upload.py` — OAuth once (user creates GCP
  project + OAuth client, token to secrets/ NEVER pushed), reads metadata.md
  pack + final.mp4 + thumbnail.jpg, uploads with synthetic-content
  disclosure + prime-time schedule (R21). Phase 2: yt_analytics.py weekly
  CTR/retention report into the queue. Phase 3 (optional): controlled
  packaging experiments.**

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

- **R26 TRAFFIC QUALITY GATE (2026-08-26):** every pack passes
  `python3 tools/qa_pack.py VIDEO_DIR [keyword_stem]` BEFORE upload. Caught +
  fixed on v16: keyword missing from description's first 150 chars (search
  snippet), 15 hashtags (diluted — now 5, first-3 strongest), tags not
  keyword-first. v16's updated pack is the template. Research-backed: CTR=
  #1 factor, keyword in first 5 title words + first description sentence,
  3-5 hashtags max (first 3 show above title), spoken keyword in first 60s.

- **METADATA PACKS (2026-08-26):** `vault/metadata_packs/` holds ALL 42
  gate-passing packs: 'metadata for video 1..16.md' (v1–v3 reconstructed —
  paste into YouTube Studio; v4–v16 keyword-first snippets, 5 hashtags,
  keyword-first tags) + 'metadata for short N hook|payoff.md' (26, Shorts
  profile incl #Shorts). ALL PASS `tools/qa_pack.py` (R26; --shorts profile).
  Generator: tools/gen_packs.py. User pastes these into YouTube manually.

- **MONTH3_PLAN.md "The Felt Wounds" slate v2 (2026-08-27):** Month-2 slate
  failed R23 audit (#17/#18/#19 retired, #20 benched) — built replacement
  slate V17-V22 in UNOPENED wound-families, each with felt pain + Jungian
  mechanism + demand evidence + thumbnail direction. AWAITING USER APPROVAL.
- **Pacing rule (user-mandated 2026-08-27): ONE thing per turn.** No mega-turns.
- metadata_packs_R26.zip delivered to user (42 packs).

## NEXT ACTIONS (in order)
1. **v17 render chunks 1–6** (this turn) — refetch `/tmp/stock17` before each chunk if git_push freed it.
2. Then render chunk 0 (first-chunk gate) → remaining chunks → assemble → finalize.
3. Optional: v13–v16 Shorts refresh under R24.

## SECRETS (do NOT push into the PUBLIC repo)
- /home/user/secrets/github_pat.txt · /home/user/.pexels_key

## KEY FILES
- Workspace: /home/user/{MASTER_RULES.md, VIDEO_QUEUE.md, MONTH2_PLAN.md,
  HANDOFF.md, README.md, tools/, reusable/, secrets/, thumbnails/, videos/}
- Repo: vault/{docs, tools/, reusable/, pipeline/, video_001..016/} — each
  video keeps final/thumbnail/shorts/sources in its dir.
