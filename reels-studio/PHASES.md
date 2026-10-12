# Reels Studio: phased roadmap (ONE phase = ONE session)

**Session rules** (they exist because long sessions timed out and the sandbox resets between sessions):
1. Start with `bash bootstrap.sh`, which restores the toolchain in about 3 min. Long jobs always run in the background.
2. At most **one heavy job** per session: a render (~10 min) or a build. Never run two memory-heavy jobs at once (2 GB RAM).
3. End with everything saved in the workspace, `reels.py sync` (when a token is present), and this file's status updated.

## Goal
Fully-made, ready-to-share AI-tools explainer videos (YouTube Shorts, Reels, TikTok, FB, X).
**The agent does all the work:** research, finding the tool, capturing its site and repo, collecting the makers' official demo media, script, voice, animation, render, QA and post kit.
**The user only:** picks or approves topics (optional) and uploads.

## Phases

| # | Session goal | Deliverable | Status |
|---|---|---|---|
| 1 | Social research + **capture kit** + real assets for video #1 | `tools/capture.py`, `captures/universal-modder/`, storyboard | ✅ done |
| 2 | **System pipeline** + social script extractor + voice audition | `PIPELINE.md`, `tools/social_scan.py`, `research/voice-decision.md` (was research/voice-audition/` | ✅ done |
| 3 | **Deep channel study**: 9 benchmark accounts × 30 videos (stats, transcripts, visual analysis), **watchlist** (21 channels), **idea feed**, platform SEO, the end-to-end **PLAYBOOK** | `PLAYBOOK.md`, `research/social/study-*.md`, `research/sources.csv`, `tools/channel_study.py`, `tools/idea_feed.py` | ✅ done (transcripts resume in the background next session if unfinished) |
| 4a | **Foundations for scale**: persistent token + commit secret-scan, **source registry** (32: TikTok/YouTube/web, `tools/sources.py`, post history in `research/sources/posts.csv`), energetic af_heart voice (`voice_fx`), handle options, `seo_pack.py`, 3–5/day architecture | all of these | ✅ done |
| 4b | **Templates** `repo-spotlight` (F1) + `tool-spotlight` (F2): shared scene engine `templates/_spotlight` (10 scene types), winner caption style (ALL CAPS, yellow keywords), display-vs-spoken markup, continuity editing; **video #1 rendered** (QA 6/6) | MP4 + post kit | ✅ done 2026-10-08 |
| 5 | **Cloud render** on GitHub Actions: `render.yml` (one 4-vCPU runner per brief, up to 5 in parallel), `cloud/setup-render.sh`, capture packs in Release `capture-packs`, MP4 + kit.zip per video, `reels.py cloud/renders`. Measured: 2 videos in parallel in ~8 min (render 3.4–4 min each vs 17–27 min in the sandbox), QA 6/6. Repo + workspace cleaned (renders out of git, demos/auditions removed) | cloud-rendered videos #1 + #2 | ✅ done 2026-10-08 |
| 5b | **Brand kit + account profiles**: logo (user-picked, rebuilt as exact vector), avatar, YouTube banner, X header, FB cover, watermark; copy-paste profile text for YouTube/Instagram/TikTok/X/Facebook checked against each platform's limits (`tools/brand_kit.py`, `brand/`) | `brand/brand-kit.html`, Release `brand` | ✅ done 2026-10-09 |
| 6 | **Paced delivery + daily engine**: Buffer queue for YouTube / Instagram / Facebook, stable media hosting, durable dedupe and retries | `tools/post/`, `post.yml`, queue + journal | **6a expanded** (2026-10-10): audience-specific Buffer calendars incl. FB, direct YouTube long uploader, Shorts tags/playlists enrichment, thumbnail QA and storage guards. Google OAuth + live pilots pending; actual long production/daily autonomous research not claimed. See publishing strategy. |
| 7 | optional: long-form versions, Urdu/Hindi line, analytics loop (views → topic picks) | | |

## Auto-posting plan (Phase 6). Facts checked 2026-10-09
**Flow:**
1. `queue/` briefs.
2. Scheduled `render.yml` on GitHub's free runners builds MP4 + kit into a Release.
3. `post.yml` posts each video at its time slot and logs the post links in `tracker/`.

No PC is needed. Logins are stored as encrypted GitHub Actions secrets (never in the repo).

| Platform | Official method | Cost | One-time step by the user | Catch |
|---|---|---|---|---|
| Instagram Reels | Instagram Graph API: create container from the Release video URL, then publish | free | Meta developer app in development mode with our own account (no App Review), log in once | 100 API posts / 24 h per account; needs a Professional (Creator/Business) account |
| Facebook Reels | Graph API Page `video_reels` | free | same Meta app + the Page | — |
| YouTube Shorts | YouTube Data API `videos.insert` (resumable) | free | Google Cloud project + OAuth, log in once, **verify actual public publishing with an approved pilot** | Current insert-method docs say unverified projects are not private-only, while an older generated summary conflicts; verify the actual project via a pilot rather than assume. Separate upload quota bucket; source: current official API docs |
| TikTok | Content Posting API | free | TikTok developer app, log in once | Unaudited app: videos land in the TikTok inbox as drafts, then the user taps Post (at most 5 pending drafts / 24 h). Public direct posting needs TikTok's audit |
| X | X API v2 + chunked media upload | pay-per-use: about $0.015 per post plus small media-call fees (≈ $2–7/month at 3–5/day); no free tier since 2026-02-06 | developer console, card, credits | A post containing a URL costs $0.20, so never put links in posts |

**Current route (owner 2026-10-10): one Buffer account, three channels: YouTube, Instagram, Facebook.** No second key is needed for this scope. TikTok/X are not connected.

Implemented in `tools/post/README.md` (operations + official sources):
- GraphQL `https://api.buffer.com`, personal key in encrypted `BUFFER_API_KEY` Actions secret.
- `config/publishing.json`: global English / US-led audience: America/New_York, separate platform-specific calendars; 3/day baseline, opt-in 4–5; two-day horizon, target <= 8 pending/channel against Free plan cap 10; maximum 9 create operations/run.
- `queue/publish.json`: approved, reviewed, pinned renders only. Rendering/topic approval does not authorize posting; initial entries are held.
- `tracker/publications.json`: per-platform write-ahead journal persisted before every Buffer mutation. Three verified manual YouTube uploads are locked against duplicates; Instagram/Facebook remain separate.
- Read actual RateLimit headers, preserve quota reserve, honor Retry-After, bounded backoff; persist long cooldowns. Never blindly retry an ambiguous create response. Delivery errors are reported against the existing post ID, not re-created.
- `.github/workflows/post.yml`: disabled-by-config cron, serialized media deploy + delivery, explicit dry-run/schedule/reconcile modes, reports and failures in Actions.
- Stable pinned MP4s hosted via Actions-based **GitHub Pages**; all pending assets retained, QA 7/7 and approved Option 3 voice required. No expiring redirect URLs given to Buffer.
- `enabled: false` and `live_pilot_passed: false` until an owner-approved live pilot is actually sent and checked. A dry-run is not claimed as a live publishing test.

**Owner setup received/completed:** all three account URLs, one working Buffer API key, Secrets/Pages permissions, Pages enabled. First-time Pages creation additionally needs Administration: write; that temporary permission can be removed once enabled. Daily workflows use short-lived `GITHUB_TOKEN`, not the personal PAT.

**Still pending:** Google OAuth for direct long uploads and Shorts tags/playlists, first live posting pilots; daily production automation beyond approved rendered backlog. Do not claim 3–5 new researched/rendered videos are autonomously generated each day yet.

**Paid shortcut:** Upload-Post.
- One API key covers every platform.
- Free plan: 10 uploads/month, no TikTok.
- Basic: $16/month billed yearly, or $24 monthly. Unlimited uploads, TikTok included.

**Needed by the developer apps:** a privacy-policy + terms URL. Plan: a free GitHub Pages page that also serves as the link-in-bio hub.

**Build (Phase 6):**
- `tools/post/` with `youtube.py`, `meta.py`, `tiktok.py`, `x.py`; captions come from the existing `seo_pack` output.
- `.github/workflows/post.yml`: time slots plus a retry.
- Queue and schedule in `render.yml`.
- `reels.py post <id> --dry-run`.
- Live test: 1 video per platform, then go daily.

AI labels:
- YouTube: none for a generic narrator over real footage.
- TikTok: none for generic TTS (guidelines updated 2026-09-24).
- Instagram: native `isAiGenerated` supported. Facebook: the owner explicitly removed the hold on 2026-10-10. Include FB with AI-narration caption disclosure; capability discovery enables a native flag if supported. Do not claim caption disclosure is a native label or promise a Buffer rollout. See `tools/post/README.md` for the current disclosure handling and recovery rules.

## Asset policy (what goes into our videos)
- ✅ **Our own captures** of public pages: tool site, GitHub repo, docs. Review/commentary use, with the source credited in descriptions/post kits (owner: no on-screen credit captions).
- ✅ **Official demo media from the makers**: repo README/docs media, launch clips on their own site, model-card samples.
  - Credited in descriptions/post kits, never under the on-screen video.
  - Licence notes are respected. Example: Coucou reserves its name, its Mochi character and its sounds.
- ✅ **Real outputs from running the tool ourselves**, when it runs free and headless.
- ✅ Our own motion graphics, music, SFX and voice.
- ❌ **Clips from other creators' videos** (YouTube/TikTok/Instagram). They mean copyright claims plus "reused content" demonetization. Use them for **topic ideas only**.

## Phase log
- **Phase 1 ✅ (2026-10-07)**
  - TikTok/IG scan: `research/ai-tools-niche.md` §5. Instagram blocks automated access, and its creators cross-post from TikTok.
  - Capture kit: `reels.py capture`, which wraps `hyperframes capture` plus `tools/capture_extra.cjs`.
  - Video #1 pack: `captures/universal-modder/`. It holds:
    - 10 files: desktop/mobile full-page shots, the crisp repo header, README images, and the official teaser as MP4 (12 s, six labeled mods);
    - a 36-element region map (Star button, About box, README sections, install code);
    - live facts.
  - Storyboard: `briefs/spotlight-universal-modder-01.json`, with 7 scenes (hook clip → montage → GitHub reveal with a cursor click on Star → how it works → install terminal → the catch → CTA).
  - Fixed: HyperFrames silently self-upgraded 0.8.137 → 0.8.140. `HYPERFRAMES_NO_UPDATE_CHECK=1` is now set everywhere, and setup re-pins the version.
- **Phase 2 acceptance:**
  - `templates/tool-spotlight/` renders every scene type in the storyboard from the capture pack;
  - `lint` shows 0 errors and `check` passes;
  - `hyperframes snapshot` stills of each scene look professional (reviewed by eye);
  - no full render yet.

## 2026-10-10 expansion decision

Owner selected global English / US-led viewers and has no Google OAuth client yet. Use explicit UTC timestamps from America/New_York calendars, not blindly addToQueue. Target 3–5 shorts/day (3 baseline) and 2–3 long/week (Tue repo, Fri news, Sun tools). FB is INCLUDED by owner instruction.

New source: `tools/youtube/`, `.github/workflows/youtube.yml`, `config/youtube.json`, `queue/youtube-long.json`, `tracker/youtube-publications.json`, mobile thumbnail QA, encrypted resumable checkpoints and playlist duplicate protection. Both delivery workflows share concurrency; no live writes during setup. See `research/publishing/strategy-2026-10-10.md` and `google-connection.md`.

Cleanup verified 36 Muse files against the existing Release tar before deleting their local duplicates (28.55 MB). Finished render releases are immutable; revisions use fresh tags. Other projects/history remain untouched.

## 2026-10-10 — owner authorised live Buffer publishing + five new Shorts

**Live pilot PASSED on all 3 channels** (`news-claude-free-01`). Video-tools list was re-rendered with a conditional watermark caveat before scheduling; it and ai-newtab have six accepted, spaced platform schedules. Original three manual YouTube uploads remain permanently locked.

Five new scripts/capture packs rendered in Actions: Haiku 5.5, Gemini agent, Mosa, Pomelli, Whistle (2 news / 2 tools / 1 repo). All QA 7/7 + visual review; Gemini's first pass failed a clipped URL and was fixed/re-rendered without bypassing checks. These five are queued held for the next batch; no extra same-day dump.

Google Web OAuth client JSON received, moved outside git with mode 600. Expected callback is correct. Channel consent/refresh token is still missing; the private preloaded connector is available. YouTube metadata worker is prepared, but no direct Google API upload/enrichment is claimed. Long-form remains gated on its own live pilot.

Five source capture packs (58 files) archived and byte-verified before local pruning. Current downloadable batch bundle + one MP4 preview are the only large saved deliverables; finished masters and kits remain in Releases. Other projects untouched.

## 2026-10-10 — Google OAuth connected / enrichment verified

Stable callback file handoff completed. Expected Hypeless YouTube channel verified; refresh credentials encrypted into `YOUTUBE_OAUTH_JSON`. Live enrichment run 38056797324 succeeded: all eight Claude Short tags and exactly one membership each in AI News + Shorts playlists confirmed by direct Google read-back. No re-upload and public copy/privacy preserved.

Google issued a seven-day refresh grant, ending 2026-10-17 13:42 UTC (18:42 Pakistan). Owner must check Audience publishing status and re-authorize after switching to In production if still Testing. Access-token refresh does not extend this grant. Expiry warning added to reports. Long-form pilot remains pending; five new Oct 10 videos remain held.

## 2026-10-11 — optional agent parked; verified local delivery cleanup

Owner chose the interactive Arena agent as the main brain. The optional producer/critic remains OFF / NOT QUALIFIED and is now explicitly paused; all five experimental Actions workflows are disabled. No further evaluation/activation without a new owner request. A fail-closed client guard prevents inference while paused.

Verified all five MP4s and five kits against their live immutable Release assets, then removed only the old local delivery ZIP and Mosa preview (74,184,935 bytes). Original package notes, archive links, scripts, source evidence, masters, private credentials, queues and publication receipts are preserved. Core render/posting workflows were not disabled or changed.

## 2026-10-11 — session re-entry made cheap (context discipline)

A work session had ended with "conversation too long for the model"; git held everything,
but a naive re-read of docs + state measured **153.5 KB ≈ 43.7k tokens**. New
`tools/context/` package fixes the failure mode instead of the symptom: `ctxpack.py`
builds a ≤8 KB always-fresh `PACK.md` from the same resume_status source (measured
3.8 KB ≈ 1.1k tokens, **−97.5%**), `ctxgrep.py` answers from docs/state/logs as capped
`file:line` snippets (17.7 KB file → ~0.7 KB answer), `quiet.py` bounds command output
(21.6 KB verbose suite → 0.6 KB summary + greppable log). Rules: `CONTEXT-PROTOCOL.md`.
Also fixed a vaultless-regeneration footgun that silently dropped the recorded Google
grant expiry (`resume_status.carry_forward_expiry` + tests). Local safety suite:
**209 passed** (14 new). Audit: `docs/2026-10-11-session-resume-audit.md`, receipt:
`research/maintenance/2026-10-11-context-audit.json`.

## 2026-10-11 — five Oct-10 productions scheduled; Shorts covers shipped

Owner instruction: schedule today's five held productions (2 news, 2 tools, 1 repo) and add YT Shorts covers.
Queue approvals refreshed (expires 2026-10-12T23:59Z); `tools/post/queue_ctl.py approve` verified each kit. A date-scoped
`daily_target_overrides` entry (2026-10-11=5, clamped by the 5/day cap, 180-min spacing, 1 repo/day; baseline stays 3)
let the paced runs use the researched weekly+optional slots instead of a bulk dump. Live Buffer runs scheduled 9 + 6 = 15
posts across YT/IG/FB, all future-scheduled when created (first slots 07:00 EDT news-haiku fb/ig, last 23:00 EDT
news-gemini/pomelli; nothing was overridden to post-now). Reconcile before claiming anything is public.

Shorts covers: `cover_ctl.py` extracts the reviewed `cover.jpg` from each immutable kit and records `cover_sha256` after
agent visual review of all five previews; the enrichment worker (existing 4x/day cron, mode=enrich) sets `thumbnails.set`,
confirms via `hasCustomThumbnail` read-back, retries bounded, and blocks loudly for agent review on failure (e.g. channel
eligibility). Based on the 2026-07-24 short-thumbnail opening; the Shorts-shelf vertical picture remains provider-only.
Suite at this checkpoint: **217 passed**. Release in use: renders-2026-10-10 (10 assets, digests verified).

## 2026-10-11 — Google consent made permanent (production grant)

The recurring 7-day expiry was root-caused to the OAuth app's **Testing** publishing status (Google caps Testing-grant refresh tokens at 7 days regardless of use). Owner published the app to **In production** (free; verification deliberately skipped — the unverified-warning screen is acceptable for a single-user app), then one fresh consent was completed via the durable Pages handoff: client JSON re-attached privately, PKCE link issued, response exchanged immediately, channel `UCcWh9OdX3rbfHOtDZ6neyrA` verified, encrypted `YOUTUBE_OAUTH_JSON` re-stored (updated_at 2026-10-11T05:58:34Z). The stored bundle has **no `refresh_token_expires_at`** — the production signal — and the live enrichment run 38116539585 confirmed `oauth_connected: true` with no expiry note. No renewal deadline remains. Also fixed: a present vault is now authoritative in `resume_status.carry_forward_expiry`, so a production grant no longer inherits the stale testing-mode expiry (regression test added; suite 218).
## 2026-10-12 — five research-picked shorts; the daily mix is no longer hardcoded

Owner instruction: produce five videos for today and schedule them; the system must not be fixed to
2 tools / 2 news / 1 repo; pick the five by findings (search, relevance, popularity).

Policy first: `config/publishing.json` now ships `required_daily_categories: []` and
`max_repo_videos_per_day: 5`, and `tools/post/cadence.py` orders batches strictly by editorial priority when
no mix is required (the required-mix code path remains for any future config that re-enables it). Tests: the old
"no repo-only day" veto became `test_repo_weighted_batch_is_allowed_when_merit_picks_it`, plus
`test_mix_is_not_hardcoded_in_config`; suite **219 passed**. PIPELINE / PLAYBOOK / RESUME / tools-post README all
updated; `reels.py radar` and the idea-feed header no longer print the old rule.

Selection (`research/ideas/2026-10-12-shortlist.md`): scored radar consensus + views, GitHub stars, HF
likes/downloads/trending, fresh primary-page reads and live YouTube autocomplete. Picks:
`news-gpt61-astra-01` (92), `tool-qwen38-01` (92), `repo-ds4-01` (88), `news-nano-banana-21-01` (86),
`tool-openmontage-01` (80) — which happened to land 2 news / 2 tools / 1 repo as an *outcome*, not a quota
(HeyGen's 5.3M views lost on brand fit; universal-modder on ToS-fit).

Captures (own + makers' official media only): five packs built and pushed to the capture-packs Release.
Hurdles recorded: openai.com 403-blocks headless capture → the Astra story captures from ARC Prize's own
analysis page (charts + replay footage) with openai.com kept as a source link; the Gemini-API docs page crashed
at core-extraction → Nano Banana captures from DeepMind's model page; one batch runner died because its script
was edited mid-run → re-ran the affected ids from a fresh file.

Briefs: five tool-spotlight briefs (7 scenes each, ~150-172 spoken words) pass `tools/seo_pack.py` with
**0 errors / 0 warnings**; all asset, region, sync-word and asterisk references verified against the capture
manifests before dispatch. Cloud render dispatched as run **38216765324** → Release `renders-2026-10-12`
(commit `820a154`). Scheduling follows via queue approvals + paced post.yml runs; date-scoped
`daily_target_overrides` now carries 2026-10-12=5.

### Batch outcome (2026-10-12)

Renders: cloud run **38216765324** — five parallel jobs, all success in ~34 min; Release `renders-2026-10-12`
carries 5 MP4s (13.3–17.6 MB) + 5 kits; each kit's QA block shows 7/7 checks (1080x1920, 30 fps, H.264/AAC,
-14 LUFS, approved voice); covers reviewed from the kit previews and approved (`cover_sha256` recorded).

Scheduling: queue approvals refreshed for all five (YT/IG/FB, reviewed-until 2026-10-14T08:00Z, priority
120–160 in editorial order) and `daily_target_overrides` gained 2026-10-12=5. Two live post runs created **15
posts**: astra 06:00/08:00/09:00 EDT, qwen 09:00/12:00/13:00, ds4 12:00/15:00/17:00, nano-banana
15:00/18:00/20:00, openmontage 18:00/21:00/23:00 (local ET; last slots cross midnight UTC). A reconcile run
(38220493940) follows. Scheduled is not sent — the receipt is the source of truth:
`research/maintenance/2026-10-12-batch.json`.

## 2026-10-12 (later) — hardening pass; production ceiling raised 5 → 10/day

Owner instruction: fix everything that went wrong this session, and remove the 5-video cap — the daily count is
chosen by the researched factors with a ceiling of 10.

Ceiling: the cap was hardcoded in *three* places in `tools/post/cadence.py` (`plan` target, `day_target`,
`clocks_for`) on top of `max_videos_per_day: 5`, and the slot profiles only ever exposed 5 clocks/day. All three
clamps are gone; `max_videos_per_day`/`max_repo_videos_per_day` are 10; spacing changed 180 → 150 minutes because
10 slots/day at 180-min spacing is arithmetically impossible (9 × 150 = 1350 min < 24 h — documented in config);
above the researched windows the calendar now uses an evenly spaced `extended_slots` grid, so a 10/day day is
genuinely placeable. `render.yml` max-parallel 5 → 10. Per-run mutation budget (≤9), the pending-per-channel
guardrail and Buffer plan limits still govern how fast posts appear. Suite 230 passed, including
`test_daily_ceiling_is_ten_and_has_no_hidden_five_clamp` and `clocks_for` coverage to 10.

Fixes shipped for this session's issues: (1) a capture batch died because its script was edited while running —
the script header now mandates copy-to-/var/tmp-before-run and records the openai.com/ai.google.dev capture
blocks; (2) `gh_actions logs` raised a raw 404 traceback for not-yet-written logs — now a friendly message;
(3) `.git/config` dropped by the snapshot — `reels.py` now auto-restores it from the setup template before any
git call; (4) the brief near-misses caught by hand (assets below the captured viewport, unspoken sync words,
`item_at`) are now a reusable `tools/brief_lint.py` with 11 regression tests, a `reels.py lint` command and a
pre-dispatch gate in `reels.py cloud` so a broken brief can never spend a runner again. Details:
`research/maintenance/2026-10-12-batch.json` → `session_fixes`.

Hardening verification (interactive agent, same day): the `5476c56` package was re-checked end to end —
all five shipped briefs pass `brief_lint` clean, the receipt's brief hashes match the committed files byte-for-byte,
the ceiling test genuinely places >5 on an override day, and the suite is **233 passed** (230 + 3 new
`tests/test_gh_actions.py`). One misdiagnosis was corrected: the mid-session GitHub 404s were not transient —
`gh_actions.api()` prefixed absolute `/repos/...` paths with the repo base again; `_url()` now accepts
repo-relative paths, absolute `/repos/...` paths and full URLs, verified live against the API. The remaining
delivery verification is time-gated by the calendar itself: first reconcile after the 10:00Z send, first cover
read-back after the 18:43Z enrichment cron.

## 2026-10-12 (later) — scene rebuild, gate receipts, analytics lane

Owner approved three build items and they are now in the tree (commits `665629c`, `459d8de`):

- **Scene manifest + single-scene rebuild.** `lib/scenes.py` records every scene (id, type, window, narration,
  spec, asset/window digests) into the render manifest, and `reels.py rebuild <brief> --scenes …` re-renders a
  repair from the *published* kit + MP4: unchanged scenes are verified by frame drift (PIL-only, MAD 2.0 /
  heavy-pixel 0.03) and the published audio is reused bit-for-bit (`mux_previous_audio`). Narration change is a
  hard refusal — that is a new render, not a repair. `reels.py scenes` prints the manifest; render.yml gained
  `rebuild_scenes/rebuild_reason/from_tag` inputs; `publish_release.py --download` fetches the previous kit.
- **Rule IDs in receipts.** `tools/brief_lint.py` (BL001–BL900) and `tools/seo_pack.py` (SP001–SP072) now return
  structured findings; `lib/gates.py` writes them into each render's `manifest.json` ("gates": current + history
  + changed_since_last_run), which travels inside the published kit; `reels.py gates` runs both gates and records
  them, `reels.py cloud` writes a pre-dispatch receipt to `research/maintenance/gates/` before spending runners.
- **Analytics lane.** `tools/youtube/analytics.py snapshot|report` records 24 h / 7 d snapshots per sent Short
  (views/likes/comments/engagement) and judges each against the median of our own other videos (baseline needs
  two others). Runner mode `analytics` (also folded into `schedule`/`enrich`) commits `tracker/analytics.json`
  like the other journals. CTR/retention/impressions require `yt-analytics.readonly`, which is not in the current
  grant: the lane records the 403 verbatim rather than inventing numbers; one deliberate owner re-consent (token
  cap applies) unlocks it via `REELS_EXTRA_SCOPES`.

Same session: wave 2 (five more videos) rendered, cover-reviewed, queued with priorities 170–210 and a
2026-10-14T08:00Z review window, then scheduled — 10 of 15 platform slots created by runs `38240589501` /
`38240834720`, the facebook/youtube backlog draining on the next cron. Suite: **274 tests OK**.

## 2026-10-12 — blank frame 0 (owner-reported) and the cover contract

Owner reported queued Buffer shorts showing a "plain frame 0". Root cause: wave-2 briefs open with an `image` hook, and
the theme hides `.sp-heading`/`.sp-sub`/`.sp-imgcard` at `opacity: 0`, fading them in from 0.05 s — so frame 0 of those
renders was empty. Clip hooks (every earlier batch) already forced their headline visible at t=0, which is why the
regression appeared only now. Frame 0 is what Buffer previews, what Facebook Reels publish as the thumbnail, and what
YouTube shows until a custom thumbnail is applied, so the loss was visible everywhere.

Fixes: every hook scene type is now laid out and visible at 0.0 s (`6f5b7e8`, with `tests/test_frame0_cover.py` running
the real `scene.js` in node and a CSS-hidden-class table check); the five affected videos were re-rendered
(`renders-2026-10-12-r3`), covers re-reviewed, queues re-pinned, and the already-created Buffer posts keep their
ORIGINAL URLs, which now serve the corrected bytes (`ebb8b2f`, `2d74088`: superseded assets are served as aliases and
never re-downloaded; `214dbe1`: journal pins no longer clobber the queue item's legacy list). Suite 299 OK.

Lesson recorded in the receipt: the cover frame is part of the renderer contract — a hook must be visible at t=0 — and
any media fix that re-pins a video must keep the URLs already handed to Buffer alive with the corrected file.

## 2026-10-12 (later) — Buffer queue-clear decision + tooling

Owner asked whether to empty the Buffer queue for all channels so we can schedule again (every
scheduled post still shows a plain/empty cover). Decision recorded:

* **No bulk empty.** Two reasons. (1) `reconcile()` treats a known-but-missing post as `uncertain`
  and refuses to recreate it — a blind clear would block recreation of every item, including the
  sends due today. (2) A `sent` row must never be deleted or recreated (duplicate-post risk).
* **Targeted clear instead.** Posts still pointing at pre-fix media are cleared and recreated:
  wave-1 — `tool-qwen38-01`, `repo-ds4-01`, `news-nano-banana-21-01`, `tool-openmontage-01`
  (r4 render 38254745395 → repin → cover approve → recreate). Wave-2 posts already serve corrected
  bytes via aliases, so deleting them would only reset the schedule for no visual gain.
* **Tooling shipped:** `tools/post/buffer_api.py:delete()` (`Mutation.deletePost`, ambiguous-result
  safe), `tools/post/release.py` (`--list`, `--keys|--all-pending`, `--delete`, `--release-removed`,
  requires `--confirm OWNER_APPROVED_QUEUE_CLEAR`), workflow `queue-release.yml` (list/clear,
  refuses to touch sent posts, commits the released rows). 5 tests (73 in the publishing suite).
* **Open question to settle with one observation:** does Buffer refetch the media URL at publish
  time? If yes, the affected posts fix themselves and no delete is needed. Evidence so far says no
  (queue previews stay stale), but a clear answer costs one queued post.

## 2026-10-12 (wave 1) — Buffer media is fixed at create time, not at publish

The queue-clear question ("should I empty the Buffer queue for all channels so we can schedule
again?") is answered by this, one audit run later:

* `tools/post/release.py --audit` reads the media URL each scheduled post holds and compares it with
  the URL the queue publishes now. Before wave 2 was re-pointed it read **9 stale of 24**; the
  wave-1 videos were "matching" but still holding the broken renders.
* Buffer keeps the file it ingested at `createPost`; re-pinning the queue item - and even serving
  fixed bytes from the original URL - does not update a post already scheduled.
* Repair is `editPost` with a replaced `assets` array (the post keeps its slot, caption and metadata
  because we send none of them). `--refresh --confirm OWNER_APPROVED_MEDIA_REFRESH` does that for
  every stale post; it never deletes, and it never touches a sent post. 9/9 wave-2 posts updated,
  then 11/11 wave-1 posts after the r4 re-pin.
* Final audit 2026-10-12T14:10Z: **24 posts, 0 not on the current media.**
* No queue emptying was needed; the tracker rows never left `scheduled`, so no orphaned receipts and
  nothing for `reconcile()` to mark uncertain.
* Durable guard: post.yml schedule runs the freshness check before delivery, and `--clear`
  (deletePost + row release) stays behind its own confirmation for the case where a delete really is
  the right call.
