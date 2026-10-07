# Reels Studio: the production pipeline

> The **strategy** (formats, hooks, SEO per platform, cadence, roadmap) is in [`PLAYBOOK.md`](PLAYBOOK.md). This file is the **technical system**.

One page that answers: **how topics are chosen, how research is done, which voice, how a video is made, how it is checked, and which tools do each job.**
The agent runs every stage. The user's only jobs are an optional veto on topics and uploading (until publishing is automated).

```
 1 DISCOVER ──► 2 SELECT ──► 3 RESEARCH ──► 4 SCRIPT ──► 5 VOICE ──► 6 ASSETS ──► 7 ASSEMBLE ──► 8 QA ──► 9 PUBLISH ──► 10 LEARN
 radar+social    score≥60     fact sheet      brief.json    Kokoro      capture pack   template      gates    Release+kit   metrics
                                                                                                                    └──────► feeds 1-2
```

## 1. Discover: where topic ideas come from

| Source | Tool | What it finds | Cadence |
|---|---|---|---|
| GitHub: new AI repos ranked by **stars/day** | `reels.py radar` | tools, agents, MCP servers, generators that are taking off | weekly (Mon) |
| Hugging Face trending models + Spaces | `reels.py radar` | new open models, free "try it" apps (image/video/voice) | weekly |
| **Watchlist channels** (21 TikTok + YouTube, `research/watchlist.csv`) | `tools/idea_feed.py` (daily) | tools/repos several channels covered this week (**consensus ≥ 2 = trend**) | daily |
| **TikTok / YouTube Shorts / Instagram** explainer accounts | `reels.py social` + `tools/channel_study.py` | which tools creators cover, **which videos got traction**, their scripts, hooks and CTAs | weekly scan of ~6 accounts, top 2 each |
| News / launches | agent web search | big launches (models, free tiers, price drops) | as needed |
| Official free-tier pages | agent + `reels.py capture` | legit free API quotas / free plans, verified on the day | monthly refresh |

Every idea goes into **`topics/backlog.csv`** (SSOT for topics) with its signals and status.

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
- **Pace ~175–185 wpm** (benchmark norm from 194 transcripts), with speed calibrated per voice (`research/voice-audition/index.md`).
- **Length:** spotlights 35–42 s, lists ~60 s.
- **One honest opinion line** (our verdict / "the catch").
- **Value close** ("free and open source") → **CTA: "Comment KEYWORD and I'll pin the link"** + follow. We pin the link ourselves; never promise DMs.
- First sentence ≤ 12 words; every sentence ≤ 18 words; ≤ 7 words on screen per beat; captions always on.
- Every brand name gets a pronunciation hint (`say`).

## 5. Voice

| Option | When | Licence / cost |
|---|---|---|
| **Kokoro TTS** (default): one fixed **channel voice** | all English videos | Apache-2.0: commercial-safe, free, runs offline |
| Your own voice recordings (`"voice": "files"`) | best for trust and monetisation; needed for real Urdu narration | yours |
| Kokoro Hindi voice + Urdu phonemes | experimental Urdu/Hindi versions (88% whisper-intelligible) | Apache-2.0 |

**Quality gates:**
- whisper character-match ≥ 95% on the script (product names excepted);
- loudness −14 LUFS, peak ≤ −1 dBFS.

The channel voice is picked once from `research/voice-audition/` (same line, 3 voices), then fixed in `config/channel.json`.

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

1. `hyperframes lint` (0 errors) + `check` (layout overlap, contrast, runtime).
2. whisper intelligibility ≥ 95%.
3. Output: 1080×1920, 30 fps, H.264/AAC, −14 ±1 LUFS, peak ≤ −1.
4. **The agent reviews the contact sheet by eye** and fixes what it sees.
5. Fact sheet complete; numbers refreshed today; risk gates clean.
6. Originality: it differs from our last 5 videos in format or look, and adds information the viewer can't get from the source creators.

## 9. Package + publish

- **Post kit** (`renders/<id>/post.md`): 3 titles, caption, 3–5 hashtags, pinned comment (links + catches), cover frame, SRT captions, credits.
- **Storage:** GitHub Release (`reels.py publish`) + post kit in git (`reels.py sync`).
- **Upload:**
  - Now: the user uploads natively to each platform (no cross-watermarks).
  - Later, optionally, via official APIs only: YouTube Data API, Instagram Graph API (Business/Creator account), TikTok Content Posting API. Each needs the user's account authorisation. No cookie bots (ban risk).

## 10. Learn

- `tracker/content-tracker.csv`: 24 h and 7 d views, viewed-vs-swiped, avg % watched, comments/1k, follows.
- A monthly social re-scan updates the hook/CTA/pacing benchmarks. The rubric weights get adjusted to what actually performed for us.

## Tools inventory

| Job | Tool | Licence / cost | Installed by |
|---|---|---|---|
| Render (HTML → MP4), lint/check, site capture | HyperFrames CLI **0.8.137 (pinned, self-update off)** | Apache-2.0 | `bootstrap.sh` |
| Headless browser (captures, render) | chrome-headless-shell + puppeteer-core (bundled) | BSD/Apache | bootstrap (via CLI) |
| Animation | GSAP | free standard licence | bundled in templates |
| TTS | Kokoro-82M (kokoro-onnx) | Apache-2.0 | bootstrap |
| Speech-to-text (QA + social scripts) | whisper.cpp (small.en; base for multilingual) | MIT | bootstrap (`-j1` build) |
| Social video audio + stats | **yt-dlp** | Unlicense | bootstrap |
| Audio/video processing | FFmpeg | LGPL/GPL | bootstrap (apt) |
| Images | Pillow | HPND | preinstalled |
| Trend data | GitHub REST API, Hugging Face API | free | none needed |
| Research | agent web search + page fetch | – | agent |
| Storage / SSOT | GitHub repo + Releases | free | token in `~/.config/reels-studio/` (persistent, outside git) |

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
python3 reels.py make briefs/<id>.json --no-render                 # 8 gates without rendering (~2 min)
python3 reels.py make briefs/<id>.json --quality looks --crf 26    # 7 render (~10 min, one per session)
python3 tools/seo_pack.py briefs/<id>.json                         # 9 per-platform SEO copy, validated (limits, hashtag caps, keyword alignment)
python3 reels.py publish && python3 reels.py sync -m "<id>"        # 9 publish (needs token)
```
