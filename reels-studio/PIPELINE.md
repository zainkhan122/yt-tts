> **Current control:** interactive Arena-agent-led production. The optional OpenRouter producer/critic is paused by owner instruction (2026-10-11), not qualified, and must not restart without explicit permission. This does not disable approved cloud rendering or existing delivery safeguards.

# Reels Studio: the production pipeline

> The **strategy** (formats, hooks, SEO per platform, cadence, roadmap) is in [`PLAYBOOK.md`](PLAYBOOK.md). This file is the **technical system**.

One page that answers: **how topics are chosen, how research is done, which voice, how a video is made, how it is checked, and which tools do each job.**
The interactive agent runs research/production; approved-render Buffer delivery and YouTube metadata have cloud automation. The optional producer/critic lab is OFF and unqualified, not an activated daily content engine. Current state and safe recovery are in CURRENT_STATE.md / RESUME.md.

```
 1 DISCOVER ──► 2 SELECT ──► 3 RESEARCH ──► 4 SCRIPT ──► 5 VOICE ──► 6 ASSETS ──► 7 ASSEMBLE ──► 8 QA ──► 9 PUBLISH ──► 10 LEARN
 radar+social    score≥60     fact sheet      brief.json    Chatterbox  capture pack   template      gates    one-day Actions artifact (Release opt-in)   metrics
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

### Executable pre-render contract (added 2026-10-14)

A new full video render cannot start from the Actions UI, `reels.py cloud`, or local `reels.py make/batch`
unless the batch has a fresh `research/production/receipts/<batch-id>.json` receipt. Local `--no-render`
layout iterations and reasoned scene rebuilds of a previously published video are exempt. `tools/validate_dispatch.py`
enforces cloud dispatch; `reels.py` applies the same six-stage/score/Insights/asset preflight to local renders.
The receipt is not a substitute for owner approval or publishing permission.

A cloud render creates a short-lived Actions artifact by default. A public GitHub Release is created only when the
operator explicitly selects `publish_release: true` in Actions or passes `--publish-release`; this does not authorize
Buffer scheduling or posting.

- `DISCOVER`: dated idea-feed/radar/social evidence paths.
- `SELECT`: the exact PIPELINE §2 scorecard, explicit `selection_status: selected`, the backlog row status `selected`,
  matching topic title and score, all category values within their weights, total **≥60**, and cleared automatic risk/licence/claim gates.
- `RESEARCH`: primary HTTPS sources in the brief, source-check times, and dynamic facts refreshed within 24 h.
- `SCRIPT`: hash of the ordered spoken lines must match the committed brief.
- `VOICE`: English uses the approved Chatterbox Option-3 profile. Per-chunk Whisper stays **≥92%** and
  final English voiceover stays **≥95%**; the config cannot lower either floor. At most two alternate-seed
  retries are allowed inside a render. A failed deterministic seed sequence is not dispatched again unchanged.
- `ASSETS`: rights and approval constraints acknowledged; capture manifest and every file digest are checked
  in a lightweight preflight before any render runner starts.
- `Buffer Insights`: the receipt pins a complete snapshot fetched within 36 h, cites all sent video posts,
  and records concrete findings plus explicit topic/script/voice/visual decisions. Missing expected posts or
  a channel with no fresh usable metrics blocks production. Buffer's daily refresh may lag the network by a day.

`tracker/render-attempts.json` is a write-ahead idempotency ledger. A SHA-256 fingerprint binds brief bytes,
voice seed, capture manifest and file digests, quality/CRF, and renderer inputs. The workflow reserves it before starting a render;
failed, interrupted, and successful exact repeats are blocked. Fix the source, choose a reviewed voice seed,
update the asset pack, or correct the renderer before a new full dispatch. The scene-rebuild path remains separate
and reuses the published audio. See `research/production/README.md` for the receipt schema.

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
2. The makers' **official demo media** (README GIF/MP4, launch clip, model-card samples), credited in the post copy/pinned comment; no on-screen credit captions.
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
- **Pace benchmark ~175–185 wpm** (194-transcript social scan), but treat it as an editorial target, not a substitute for listening: record delivered WPM, preserve natural pauses, and keep spotlights within 35–42 s.
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
| Your own voice recordings (`"voice": "files"`) | local/layout use and separately approved profiles; current English final gate requires Chatterbox, and Urdu needs an explicitly approved profile | yours |
| Kokoro Hindi voice + Urdu phonemes | experimental Urdu/Hindi versions (88% whisper-intelligible) | Apache-2.0 |

**Quality gates:**
- Chatterbox is mandatory for final English media; Kokoro is reference/preview only.
- Whisper character match must be ≥ 92% per flow chunk after at most two alternate-seed retries; a remaining mismatch blocks the final render.
- Overall Whisper character match must be ≥ 95% for final English renders; if the QA tool is unavailable, the final render fails closed.
- Failed voice gates log the expected and Whisper-heard chunk text, plus unmatched script words for the whole-VO check, before aborting. Keep the thresholds fixed; correct the spoken script or add `{display form|spoken form}` markup for numbers, dates, acronyms, and product names, then rerender only the affected brief.
- Loudness −14 ±1 LUFS, peak ≤ −1 dBFS; every measured video/cover/voice check in the final QA manifest must pass or publishing is blocked.

The channel voice is fixed in `config/channel.json` → `tts` (Chatterbox, option 3); how it was chosen: `research/voice-decision.md`. The pipeline records delivered WPM and pitch-range; a take below the 12-semitone liveliness advisory is surfaced for human review, not silently reported as clean.

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
- **Browser address labels** are auto-compacted to host + final path segment when too long for the fixed bar; the complete URL remains in the brief’s source list.
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
- Shared Spotlight karaoke captions and yellow montage-label pills use the single `--sp-caption-size` token (74 px, Inter 900); pills are measured against the bundled font and kept clear of the footage card.
- Every `clip-montage` cut anchor is checked against an exact normalized spoken word before TTS, then checked against actual word timings after TTS. A timing mismatch is a hard render error, not a warning.

**Audio:** VO on top, music ducked under the voice, SFX on cuts and clicks, then loudnorm.

## 8. QA gates (a video ships only if all pass)

1. Brief, source, and SEO gates: zero errors; claims have primary-source trails; dated numbers are refreshed before render.
2. `hyperframes lint` (0 errors) + `check` (layout overlap, contrast, runtime). Montage anchors must be exact spoken words before TTS; label/voice timing must pass after TTS. Either failure blocks rendering.
3. Final English voice uses approved Chatterbox flow. Whisper character match must be ≥92% per flow chunk after at most two alternate-seed retries and ≥95% overall; failed or unavailable Whisper QA blocks final media. `tts.min_match` cannot be configured below 92%. QA canonicalizes equivalent spoken/display numerals (including ordinals such as “fourteenth” vs “14th”); it does not forgive unmatched brand words. Failures retain expected/heard diagnostics, and a repeated identical render fingerprint is blocked.
4. Output: 1080×1920, 30 fps, H.264/AAC, duration within the brief target, loudness −14 ±1 LUFS, peak ≤ −1 dBFS. Every recorded QA check must pass; failed measured checks block delivery.
5. Cover and decoded frame zero are visible. The agent reviews the contact sheet, title/label type, mobile readability, media rights/source, and animation timing by eye, then fixes issues.
6. Fact sheet complete; license/media credits and risk gates clean. Credit goes in post copy/description, never on-screen.
7. Originality: differs from our last 5 videos in format or look, and adds information unavailable from the source creators.

## 9. Package + publish

- **Post kit** (`renders/<id>/post.md`): 3 titles, caption, 3–5 hashtags, pinned comment (links + catches), cover frame, SRT captions, credits.
- **Render delivery:** cloud jobs upload one-day Actions artifacts. `reels.py cloud --wait` downloads them into `renders/<id>/` for review and deletes the temporary artifacts. The render workflow is artifact-only by default; a failed or incomplete batch is not delivered.
- **Permanent storage:** a public GitHub Release is created only if the owner separately authorizes and explicitly enables `publish_release` / `--publish-release`. `reels.py publish` is also a separate explicit action for local renders; `reels.py sync` is a separate git write. Large video binaries stay out of Git history. None of these actions schedules or posts to Buffer.
- **Upload:**
  - Now: the user uploads natively to each platform (no cross-watermarks).
  - Later, optionally, via official APIs only: YouTube Data API, Instagram Graph API (Business/Creator account), TikTok Content Posting API. Each needs the user's account authorisation. No cookie bots (ban risk).

## Execution allocation: sandbox control plane vs GitHub render plane

| Work | Arena/developer sandbox | GitHub Actions (`ubuntu-24.04`, 4 vCPU / 16 GiB per render runner) |
|---|---|---|
| DISCOVER → SELECT → RESEARCH → SCRIPT → VOICE → ASSETS | Prepare and review briefs, score ≥60, exact current spoken-word counts, verified capture assets, and a fresh read-only Buffer Insights snapshot. No credentials in chat. | The main-only plan job validates the committed six-stage receipt, freshness, batch IDs, asset bytes, and attempt ledger before allocating render runners. |
| Code hardening / dry-run validation | Static review, shell/Python syntax, unit tests, checksums, and optional `--no-render` layout checks. | `render-validation.yml` runs pinned lightweight dependencies, focused regressions, workflow/shell syntax, and all-brief spoken-script parity; no TTS/Whisper weights, attempt reservation, video render, Release, or Buffer action. |
| Final video generation | Do not use the sandbox for the new production batch. | Manual `render.yml`; one runner per approved brief, hard maximum 10, final Chatterbox/Whisper/MP4 gates; one-day artifact by default. |
| Delivery | Review downloaded artifacts; request changes if needed. | No public Release, Buffer schedule/post, or platform upload unless separately authorized. |

**Handoff:** do not dispatch until the owner confirms batch size and the committed receipt passes DISCOVER → SELECT ≥60 → RESEARCH → SCRIPT → VOICE → ASSETS, fresh Buffer Insights, exact spoken-word count, and capture-byte verification. The renderer is artifact-only by default.

## 10. Learn

- `tracker/content-tracker.csv`: 24 h and 7 d views, viewed-vs-swiped, avg % watched, comments/1k, follows.
- A monthly social re-scan updates the hook/CTA/pacing benchmarks. The rubric weights get adjusted to what actually performed for us.

## Tools inventory

| Job | Tool | Licence / cost | Installed by |
|---|---|---|---|
| Render (HTML → MP4), lint/check, site capture | HyperFrames CLI **0.8.137 (pinned, self-update off)** | Apache-2.0 | `bootstrap.sh` |
| Headless browser (captures, render) | chrome-headless-shell + puppeteer-core (bundled) | BSD/Apache | bootstrap (via CLI) |
| Animation | GSAP | free standard licence | bundled in templates |
| TTS (final media) | Chatterbox flow, approved option 3; model revision `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18`; all five model files size/SHA-256 verified before and during load | MIT | `cloud/setup-render.sh` |
| TTS (reference/layout preview only) | Kokoro-82M (kokoro-onnx) | Apache-2.0 | bootstrap |
| Speech-to-text (English QA) | whisper.cpp v1.9.5 commit `d1be6fde11ac6e0407606b4e42fe72d34add8037`; `small.en` model revision `5359861c739e955e79d9a303bcbc70fb988958b1`, SHA-256 verified | MIT | `setup/setup-whisper.sh` (bounded build) |
| Social video audio + stats | **yt-dlp** | Unlicense | bootstrap |
| Audio/video processing | FFmpeg | LGPL/GPL | bootstrap (apt) |
| Images | Pillow | HPND | preinstalled |
| Trend data | GitHub REST API, Hugging Face API | free | none needed |
| Research | agent web search + page fetch | – | agent |
| Cloud render (owner-selected, hard maximum 10 per run) | GitHub Actions matrix; one Ubuntu 24.04 runner (4 vCPU / 16 GiB) per brief; one-day artifact by default; public Release is an explicit opt-in | free | Actions read/write for dispatch, logs, and cleanup; render jobs use Contents read; plan/finalizer use Contents write only for the attempt ledger |
| Storage / SSOT | GitHub repo; capture packs are read-only during render; video artifacts expire in one day unless an owner separately authorizes Release publication | free | Contents read for source packs; explicit sync/publish actions need Contents write |

**Known access limits (tested 2026-10-07):**
- TikTok profiles and videos work without login.
- YouTube Shorts works.
- **Instagram needs login cookies**. Use the cross-posted TikTok/YouTube versions instead; cookies are optional, kept in `/var/tmp` only.

## One video, end to end (commands)

```bash
bash bootstrap.sh                                                  # every session (~3 min)
python3 reels.py radar --brief                                     # 1 discover
python3 reels.py social --account https://www.tiktok.com/@x --top 2   # 1 discover / 10 learn
python3 reels.py capture <id> --url <repo-or-site>                 # 6 assets
#   agent: score topic (2), write fact sheet + brief (3-5)
REELS_VOICE_PREVIEW=kokoro python3 reels.py make briefs/<id>.json --no-render  # sandbox layout/lint preview only
python3 tools/seo_pack.py briefs/<id>.json                         # validated per-platform SEO copy
# After explicit batch-size approval and a committed, passing six-stage receipt:
python3 reels.py cloud <id> [<id2> ...] --receipt reels-studio/research/production/receipts/<batch>.json \
  --quality looks --crf 23 --wait                                  # GitHub render -> one-day artifacts; no Release by default
# A permanent Release, git push, Buffer schedule/post, or platform upload is a separate owner-authorized action.
```
