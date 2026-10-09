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
| 6 | **Auto-post + daily engine**: render queue on a schedule → auto-post to IG/FB Reels, YouTube Shorts, TikTok, X (plan below) | 3–5 videos/day posted with no manual steps | **next** (after the user creates the accounts) |
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
| YouTube Shorts | YouTube Data API `videos.insert` (resumable) | free | Google Cloud project + OAuth, log in once, **submit the YouTube API audit form** | Until Google approves the audit, API uploads are locked **private**. Upload bucket: 100/day since 2026-06-01 |
| TikTok | Content Posting API | free | TikTok developer app, log in once | Unaudited app: videos land in the TikTok inbox as drafts, then the user taps Post (at most 5 pending drafts / 24 h). Public direct posting needs TikTok's audit |
| X | X API v2 + chunked media upload | pay-per-use: about $0.015 per post plus small media-call fees (≈ $2–7/month at 3–5/day); no free tier since 2026-02-06 | developer console, card, credits | A post containing a URL costs $0.20, so never put links in posts |

**Route proposed by the user 2026-10-09: Buffer, 2 free accounts × 3 channels.** Recommended; it skips the YouTube and TikTok audits.

Accounts:
- Buffer #1: YouTube, Instagram, TikTok.
- Buffer #2: Facebook Page, X, plus Threads or LinkedIn.

Facts checked 2026-10-09:
- **Free plan:** 3 channels, 10 scheduled posts per channel at a time, 1 personal API key, 3,000 requests / 30 days (250 / 24 h).
- **API:** GraphQL `https://api.buffer.com`, `createPost` with `schedulingType: automatic`, `mode: customScheduled` + `dueAt`, and `assets: [{video: {url}}]`.
- **YouTube posts need** `metadata.youtube.title` + `categoryId` (28).
- **Media URL rules:** public, direct (no redirect), stable until publish time. GitHub Release links 302-redirect to expiring URLs, so videos are served from **GitHub Pages**: not used in this repo yet; deploy from an Actions artifact, so nothing goes into git.
- **Do not create a Buffer Start Page:** it uses a channel slot.
- **Terms:** they don't explicitly forbid a second free account, but Buffer may close any account at its discretion. Fallback: direct APIs (table above) or Essentials at $5/channel.

**User to-do:**
1. Create both Buffer accounts and connect the channels.
2. Send both API keys (Settings > API).
3. Add **Secrets: R/W** and **Pages: R/W** to the GitHub token.

**Build:**
- `tools/post/buffer.py`, with captions from the kit.
- `post.yml`: Pages deploy of pending videos, then schedule ≤ 2 days ahead (queue cap), then log post ids.
- Daily `render.yml` schedule + `queue/`.

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
- Instagram/Facebook: switch on "AI info" (Meta's wording covers realistic-sounding synthetic audio).

## Asset policy (what goes into our videos)
- ✅ **Our own captures** of public pages: tool site, GitHub repo, docs. Review/commentary use, with the source credited on screen.
- ✅ **Official demo media from the makers**: repo README/docs media, launch clips on their own site, model-card samples.
  - Credited on screen.
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
