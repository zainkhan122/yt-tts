> **Current control:** interactive Arena-agent-led production. The optional OpenRouter producer/critic is paused by owner instruction (2026-10-11), not qualified, and must not restart without explicit permission. This does not disable approved cloud rendering or existing delivery safeguards.

# Reels Studio: the production pipeline

> The **strategy** (formats, hooks, SEO per platform, cadence, roadmap) is in [`PLAYBOOK.md`](PLAYBOOK.md). This file is the **technical system**.

One page that answers: **how topics are chosen, how research is done, which voice, how a video is made, how it is checked, and which tools do each job.**
The interactive agent runs research/production; approved-render Buffer delivery and YouTube metadata have cloud automation. The optional producer/critic lab is OFF and unqualified, not an activated daily content engine. Current state and safe recovery are in CURRENT_STATE.md / RESUME.md.

```
 1 DISCOVER ──► 2 SELECT ──► 3 RESEARCH ──► 4 SCRIPT ──► 5 VOICE ──► 6 ASSETS ──► 7 ASSEMBLE ──► 8 QA ──► 9 PUBLISH ──► 10 LEARN
 radar+social    score≥60     fact sheet      brief.json    Chatterbox  capture pack   template      gates    temp artifact; explicit Release only when authorized   metrics
                                                                                                                    └──────► feeds 1-2
```

## 1. Discover: where topic ideas come from

| Source | Tool | What it finds | Cadence |
|---|---|---|---|
| GitHub: new AI repos ranked by **stars/day** | `reels.py radar` | tools, agents, MCP servers, generators that are taking off | weekly (Mon) |
| Hugging Face trending models + Spaces | `reels.py radar` | new open models, free "try it" apps (image/video/voice) | weekly |
| **Source registry** (32+: TikTok, YouTube Shorts/long-form, web feeds such as GitHub Trending, Product Hunt, Hugging Face, Reddit; `research/sources.csv`, add with `tools/sources.py add <url>`, history in `research/sources/posts.csv`) | `tools/idea_feed.py` (daily) | tools/repos several channels covered this week (**consensus ≥ 2 = trend**) | daily |
| **TikTok / YouTube Shorts / Instagram** explainer accounts | `reels.py social` + `tools/channel_study.py` | which tools creators cover, **which videos got traction**, their scripts, hooks and CTAs | weekly scan of ~6 accounts, top 2 each |
| News / launches | agent web search | big launches (models, free tiers, price drops) | as needed |
| Official free-tier pages | agent + `reels.py capture` | legit free API quotas / free plans, verified on the day | monthly refresh |

Every idea goes into **`topics/backlog.csv`** (SSOT for topics) with its signals and status.

**Daily mix (owner, 2026-10-11): NOT hardcoded.** The channel covers AI tools + AI news + repos; each batch's composition follows the researched editorial ranking (consensus, views, freshness, searchability) recorded as queue priorities. Pacing limits (ceiling **10/day** — owner 2026-10-12, 150-minute spacing, per-channel queue limits) still apply. Supersedes the 2026-10-09 fixed news/tool minimum.
- `reels.py radar` runs the watchlist idea feed (AI tools + AI news, tool lexicon in `config/ai-tools.txt`) first, then the repo radar.
- Per day: the count follows the researched factors up to a ceiling of **10/day** (owner 2026-10-12) — factors: rubric scores of available candidates, per-channel pending capacity (≤8), 150-minute spacing across the 48-hour lookahead, and review expiry. The category mix is editorial — the strongest researched topics win (owner 2026-10-11; see config `required_daily_categories`).
- Shortlist 3 topics with facts checked on official pages → **owner approves** → briefs → cloud render.

## 2. Select: the scoring rubric (0–100, produce at ≥ 60)

| Criterion | Points | How it's measured |
|---|---|---|
| Trend velocity | 25 | stars/day (radar), HF trend score, launch recency (≤ 14 days = full points) |
| Demo-ability | 20 | the makers publish demo media (clip/GIF), a public page to capture, or it runs free and headless so we can show real output |
| Audience breadth | 15 | general/creators/gamers > developers only > niche dev tooling |
| Social proof + gap | 15 | other creators' versions got traction (social scan) **but** nobody has done our angle (honest test, the catch) |
| "Free / saves money" value | 10 | usable free, or replaces a paid tool |
| Freshness of angle | 15 | not something we covered in the last 30 days, and a format we didn't use in the last 3 videos |

**Hard gates (automatic reject):**
- radar risk flags: NSFW/uncensored, ToS bypass / "free API keys", bot or anti-cheat evasion, cracks/leaks, scraping personal data;
- medical/financial/legal advice;
- unclear licence for the media we'd show;
- we can't verify the core claim.

**Weekly mix** (one person + agent):
- 1 × "repos exploding this week" (ranked-list);
- 2 × tool spotlight;
- 1 × "free tier reality" or comparison;
- rotate looks and formats.

## 3. Research: how facts get into a video

**Source ladder:**
1. **Primary**: the repo README, docs, official site, pricing page, GitHub/HF API numbers.
2. **Secondary**: reputable tech press.
3. **Social**: ideas only, never facts.

Per video the agent writes a **fact sheet**, inside the brief as `sources` + `verify_before_render`:
- every spoken or on-screen claim maps to a source and a date;
- numbers (stars, prices, quotas) are **re-fetched right before rendering**;
- the **catch** is mandatory: cost, limits, licence, platform, what it can't do.

Hands-on evidence ladder (best first):
1. Real output from running it ourselves, where possible: free, headless, legal.
2. The makers' **official demo media** (README GIF/MP4, launch clip, model-card samples), credited on screen.
3. **Our own captures** of the site or repo: screens, smooth scroll, camera zoom, cursor clicks on real elements (`reels.py capture` region map).

Never used: other creators' clips (copyright + "reused content" demonetization).

## 4. Script: structure and rules (from the social scan)

| Beat | Time | Job |
|---|---|---|
| **Hook** | 0–2 s | the most striking visual + one claim, ideally with a number. Must work with sound off (on-screen text) |
| Proof | 2–10 s | demo footage / real output (show, don't tell) |
| Reveal | ~10–16 s | what it is, where it lives, traction ("4,900 stars in a week") |
| How | ~16–28 s | 3–5 short steps |
| Catch | ~28–36 s | honest limits/costs: our differentiator |
| CTA | last 4 s | one question + follow. No fake "DM me" promises we can't fulfil |

**Rules** (calibrated by `research/social/digest-2026-10-07.md`, 11 videos):
- **Hook** = a payoff or stakes, never context. Types that won: stakes, transformation, countdown promise, "gold mine + number". Never start mid-tutorial.
- **Name reveal by ~7 s**, after the hook.
- **One feature or visual change every 4–5 s.**
- **Pace ~175–185 wpm** (benchmark norm from 194 transcripts), with speed calibrated per voice (`research/voice-decision.md`).
- **Length:** spotlights 35–42 s, lists ~60 s.
- **One honest opinion line** (our verdict / "the catch").
- **Value close** ("free and open source") → **CTA: "Comment KEYWORD and I'll pin the link"** + follow. We pin the link ourselves; never promise DMs.
- First sentence ≤ 12 words; every sentence ≤ 18 words; ≤ 7 words on screen per beat; captions always on.
- Every brand name gets a pronunciation hint (`say`).

## 5. Voice

| Option | When | Licence / cost |
|---|---|---|
| **Chatterbox (APPROVED channel voice, 2026-10-09)**: clone of the Kokoro am_michael reference, exaggeration 0.7, cfg 0.4, flow reading | every English video (QA gate `approved_voice`) | MIT (inaudible PerTh watermark), free, CPU in the cloud render |
| Kokoro TTS | makes the reference clip; local layout previews only (`REELS_VOICE_PREVIEW=kokoro`) | Apache-2.0 |
| Your own voice recordings (`"voice": "files"`) | local/layout use and separately approved profiles; current English final gate requires Chatterbox, while real Urdu narration needs an explicitly approved profile | yours |
| Kokoro Hindi voice + Urdu phonemes | experimental Urdu/Hindi versions (88% whisper-intelligible) | Apache-2.0 |

**Quality gates:**
- English Whisper character-match ≥ 95% on the final voiceover (spoken/display variants are compared); Whisper errors, a disabled check, or a score below the floor abort a final render.
- Per-flow-chunk Whisper alignment ≥ 92%; retries are bounded to four (channel default: two), each with a distinct deterministic seed. If the floor still fails, stop and fix pronunciation/script or approve a new voice seed—no identical retry loop.
- loudness −14 LUFS, peak ≤ −1 dBFS; all measured render QA checks are ship gates.

The channel voice is fixed in `config/channel.json` → `tts` (Chatterbox, option 3); how it was chosen: `research/voice-decision.md`. English full renders must use that engine and cannot disable Whisper QA.

## 6. Assets

- **Capture pack** (`reels.py capture <id> --url …` → `captures/<id>/`):
  - desktop + mobile full-page screens;
  - crisp header crop;
  - official demo media as MP4;
  - README images;
  - a **region map** (positions of Star button, About box, headings, code blocks);
  - live facts;
  - credits.
- Music and SFX: generated by `lib/synth.py` (we own them, so there's no Content ID risk).
- Fonts: OFL (Anton, Inter, JetBrains Mono, Noto Nastaliq Urdu) + Noto Color Emoji.
- Logos: the official ones, only to identify the product.
- **No credit captions on screen (owner rule 2026-10-09).** `credits_on_screen` is printed only in `post.md`
  ("Media credit") and appended to the YouTube description by `seo_pack.py` (skipped if the links are already there).
- **Non-repo tools (AI apps, AI news): official maker media first.**
  - Newsroom / product-page videos are usually plain MP4s in the HTML (`grep -oE 'https?://…\.(mp4|webm)'`);
    CDNs may hide MP4s behind `.image` URLs (`<source … type="video/mp4">`, e.g. Dreamina).
  - Official YouTube videos: `yt-dlp --extractor-args "youtube:player_client=tv_embedded" -f "bv*[height<=1080]"`
    (the default client is bot-blocked from the sandbox). Transcode AV1 to H.264 720p before packing.
  - Pages that scroll inside the app (e.g. muse.ai) capture only one screen: regions below it render black, so use
    images/clips instead of page regions there. Heavy pages (e.g. Dreamina) can time out the capture: pull media directly.
  - Skip samples that show third-party IP (film/TV titles, Disney-like characters, celebrities).
- **Phone / tall footage:** a `clip` scene without a headline sizes its card to the source aspect (no crop, 180–1220 px).
  Crop phone recordings to the device first. For white-UI footage set `"fit": "card"` (dark theme instead of a light
  blurred fill, so the white captions stay readable).
- **Anchor words** (`at`, `item_at`, camera `at`) match case-insensitively and by normalised form ("6.6" = "66").

## 7. Assemble: how the video is made

Template = HTML/GSAP scenes rendered by HyperFrames (deterministic, frame-exact). The scene grammar for tool videos (`tool-spotlight`):

| Scene | What the viewer sees | Made from |
|---|---|---|
| `clip` | full-bleed demo footage, blurred-fill background, punchy headline | official media |
| `clip-montage` | 3–4 fast cuts with labels, whip transitions | official media |
| `page` | browser mockup; **camera zooms** to real regions; **animated cursor clicks** the real Star button; stat counter | capture + region map |
| `steps` | README scrolls behind 3–5 step chips that pop on the beat | capture + script |
| `terminal` | install commands typed live, with key-click SFX | README commands |
| `verdict` | ✅ pros / ⚠ catches card | fact sheet |
| `endcard` | follow card + question CTA | brand config |

**Motion and layout rules:**
- the picture changes every 1.5–3 s; no static frame longer than 3 s;
- camera moves are eased;
- karaoke captions, 3 words at a time;
- **safe zones**: keep text out of the top 220 px, bottom 380 px and right 120 px (TikTok/IG/Shorts UI).

**Audio:** VO on top, music ducked under the voice, SFX on cuts and clicks, then loudnorm.

## 8. QA gates (a video ships only if all pass)

1. Brief/source/SEO gates: zero errors; every factual claim has a primary-source trail; dated numbers are refreshed before render.
2. `hyperframes lint` (0 errors) + `check` (layout overlap, contrast, runtime). A missing or mistimed `clip-montage` `at` anchor is a **build failure before rendering**, not a warning.
3. English final voice: approved Chatterbox Option-3; every flow chunk clears the ≥92% Whisper/TTS match floor with distinct-seed retries bounded to four (channel default: two); overall Whisper character-match ≥95%. Disabled, missing, failed, or below-floor Whisper QA blocks shipping.
4. Output: 1080×1920, 30 fps, H.264/AAC; duration inside the format target; loudness −14 ±1 LUFS and peak ≤ −1 dBFS. Every measured QA check must pass.
5. **The agent reviews the contact sheet, cover, frame zero, mobile readability and typography by eye**; fix issues before delivery. Montage label pills share the lower-caption font size and remain clear of the media card.
6. Fact sheet complete; license/media credits and risk gates clean.
7. Originality: it differs from our last 5 videos in format or look, and adds information the viewer can't get from the source creators.

## 9. Package + publish

- **Post kit** (`renders/<id>/post.md`): 3 titles, caption, 3–5 hashtags, pinned comment (links + catches), cover frame, SRT captions, credits.
- **Render delivery:** cloud jobs upload a one-day Actions artifact; `reels.py cloud --wait` downloads it into `renders/<id>/` and deletes the temporary artifact. No permanent Release is created by the render workflow.
- **Permanent storage:** only if explicitly authorized, `reels.py publish` creates a GitHub Release; `reels.py sync` is a separate git write.
- **Upload:**
  - Now: the user uploads natively to each platform (no cross-watermarks).
  - Later, optionally, via official APIs only: YouTube Data API, Instagram Graph API (Business/Creator account), TikTok Content Posting API. Each needs the user's account authorisation. No cookie bots (ban risk).

## Execution allocation: sandbox control plane vs GitHub render plane

| Work | Arena / developer sandbox | GitHub Actions (`ubuntu-24.04`, 4 vCPU / 16 GiB per render job) |
|---|---|---|
| DISCOVER → SELECT → RESEARCH → SCRIPT → VOICE approval → ASSETS evidence | Agent + owner prepare and review the briefs, fresh read-only Buffer Insights snapshot, exact current spoken-word count, score ≥60, source/rights records, capture hashes, and the committed production receipt. No credentials in chat. | Plan job rechecks the committed receipt, freshness, batch IDs, capture packs, and attempt registry before allocating render runners. |
| Code hardening and validation | Static review, syntax checks, focused tests, hash verification, and optional `--no-render` layout/lint checks. Keep heavyweight TTS/Whisper/MP4 work off the sandbox. | Runs the same lightweight dispatch/receipt regression tests before reservation; any failure blocks the batch. |
| Final video generation | Do not run the new batch here. Use this machine for planning and post-render review only. | One isolated matrix runner per approved brief installs Chatterbox + pinned Whisper, enforces ≥92% per-chunk and ≥95% overall English Whisper QA, renders, runs SEO/manifest gates, then uploads a one-day artifact. |
| Durable state and delivery | Review downloaded artifacts; request fixes if needed. No automatic public Release, Buffer schedule/post, or social upload. | Plan/finalizer write only the attempt ledger (CAS); render artifacts expire in one day. The workflow is manual `workflow_dispatch` from `main` and never creates a video Release. |

**Handoff contract:** commit the approved briefs and `reels-studio/research/production/receipts/<batch>.json`; pass only the owner-confirmed IDs, receipt path, quality, and CRF to the manual workflow. Matrix size is owner-selected per run (hard maximum 10); there is no automatic daily batch size or scheduled render. `reels.py cloud --wait` can download the temporary artifacts for review, but that is a separate, explicitly initiated action.

## 10. Learn

- `tracker/content-tracker.csv`: 24 h and 7 d views, viewed-vs-swiped, avg % watched, comments/1k, follows.
- A monthly social re-scan updates the hook/CTA/pacing benchmarks. The rubric weights get adjusted to what actually performed for us.

## Tools inventory

| Job | Tool | Licence / cost | Installed by |
|---|---|---|---|
| Render (HTML → MP4), lint/check, site capture | HyperFrames CLI **0.8.137 (pinned, self-update off)** | Apache-2.0 | `bootstrap.sh` |
| Headless browser (captures, render) | chrome-headless-shell + puppeteer-core (bundled) | BSD/Apache | bootstrap (via CLI) |
| Animation | GSAP | free standard licence | bundled in templates |
| TTS | Chatterbox flow (approved Option 3), pinned Hugging Face revision `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18`, conditioned on the Kokoro am_michael reference | MIT | `cloud/setup-render.sh` |
| Speech-to-text (QA + social scripts) | whisper.cpp v1.9.5; small.en model pinned by revision + SHA-256 | MIT | `setup/setup-whisper.sh` (bounded build; model checksum verified) |
| Social video audio + stats | **yt-dlp** | Unlicense | bootstrap |
| Audio/video processing | FFmpeg | LGPL/GPL | bootstrap (apt) |
| Images | Pillow | HPND | preinstalled |
| Trend data | GitHub REST API, Hugging Face API | free | none needed |
| Research | agent web search + page fetch | – | agent |
| Cloud render (owner-selected batch, hard maximum 10) | GitHub Actions matrix; one Ubuntu 24.04 runner per brief; one-day artifact; attempt ledger updated with compare-and-swap | free | plan/finalizer need Contents write; render jobs use Contents read |
| Storage / SSOT | GitHub repo; capture-pack Release is read-only during renders; render workflow never creates a video Release | free | explicit capture-pack push / video publish are separate owner actions |

**Known access limits (tested 2026-10-07):**
- TikTok profiles and videos work without login.
- YouTube Shorts works.
- **Instagram needs login cookies**. Use the cross-posted TikTok/YouTube versions instead; cookies are optional, kept in `/var/tmp` only.

## One video, end to end (commands)

```bash
# Sandbox / control plane
bash bootstrap.sh
python3 reels.py radar --brief
python3 reels.py social --account https://www.tiktok.com/@x --top 2
python3 reels.py capture <id> --url <repo-or-site>
# Agent + owner: select at score >=60; research; approve exact script/voice; verify assets;
# refresh read-only Buffer Insights; write and commit the full-batch production receipt.
REELS_VOICE_PREVIEW=kokoro python3 reels.py make briefs/<id>.json --no-render  # local layout/lint preview only

# GitHub / render plane (manual, owner-approved; choose batch size explicitly)
python3 reels.py cloud <id> [<id2> ...] \
  --production-receipt reels-studio/research/production/receipts/<batch>.json \
  --quality looks --crf 23 --wait
# Review downloaded artifacts locally. A public Release, git push, Buffer schedule/post,
# or platform upload is a separate action and is not performed by the render workflow.
```
