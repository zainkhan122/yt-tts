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
