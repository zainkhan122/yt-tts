# HyperFrames for viral social videos: honest research and a working system

*Researched and built on 7 Oct 2026 in this sandbox. Every platform rule below is linked to its source. Every number in the demo section was measured here.*

---

## TL;DR

1. **Yes, the MP4s were rendered by the repo.** The engine was HyperFrames `hyperframes@0.8.137`, the published build of `heygen-com/hyperframes`, using `render` and `render --batch`.
   - The scene code (HTML, CSS and GSAP animation) was written by me, following the repo's rules.
   - The voice was Kokoro, run via `hyperframes tts`.
   - Word checks used whisper.cpp, via `hyperframes transcribe`.
   - Music and SFX came from my own synthesiser. (Section 1)
2. **HyperFrames is a renderer, not a "viral button".** It's excellent at motion graphics: kinetic text, charts, quizzes, rankings, UI mockups and captions, all deterministic and scriptable by an AI agent. It does **not** generate footage, characters or realistic AI video.
3. **The 2026 rules changed what a "viral system" can be.** YouTube now refuses to monetise *"template-based"* channels. Since **1 Oct 2026** its Shorts ranking says *"template-based bulk changes"* don't make content original. Meta and TikTok de-rank unoriginal content too. A factory of near-identical videos is exactly what is being punished. (Section 3)
4. **The money reality for a creator in Pakistan is tough.**
   - Shorts pay **cents per 1,000 views**.
   - **TikTok Creator Rewards is not available in Pakistan.**
   - From **1 Feb 2027**, new YouTube partners need **20M Shorts views in 90 days**.
   - Plan income around **clients, products, affiliate deals and long-form video**, and use Shorts for reach. (Section 4)
5. **These niches fit this stack best:**
   - data stories (economy, country comparisons, cricket stats);
   - quizzes;
   - spoken English for Urdu/Hindi speakers;
   - tech/AI-tool explainers;
   - finance concepts (no fake experts);
   - template videos for local businesses, which are the most reliable money. (Section 5)
6. **I built a working system, Reels Studio** (`reels-studio/`). It turns a brief into voice, timing, captions, music and SFX, a HyperFrames render, QA results and a post kit. It has **4 templates, and 5 demo videos in 4 niches pass every automated check.** One demo has **experimental Urdu narration**: whisper heard 88% of the Urdu correctly. (Section 7)
7. **The quality gates are real.**
   - HyperFrames' `check` caught colliding labels, 2:1 contrast and invisible text.
   - whisper.cpp verifies the TTS actually said the script.
   - I caught a **statistical break in World Bank data** that would have produced a false claim.
8. **Expect most uploads to flop.** The system's job is to make every upload **correct, varied, fast and measurable**, so you can double down on what holds attention.

---

## 1. "Did you make the variants using the repo?" Straight answer

| Part of the video | Made with | From the HyperFrames repo? |
|---|---|---|
| Rendering: HTML → 1080×1920 frames → H.264 MP4, plus the audio mix and mux | `hyperframes render` (headless Chrome + FFmpeg) | **Yes**, the core engine |
| The 3 branded variants (`variant-0/1/2.mp4`) | `hyperframes render --batch batch-rows.json --strict-variables`, with 5 declared variables | **Yes**: variables + batch |
| Scene design and animation | HTML/CSS plus GSAP timelines written by me, following the repo's composition rules | Framework yes; the scene code is mine |
| Voice-over | Kokoro-82M via `hyperframes tts` | **Yes** (the CLI wraps Kokoro) |
| Word timings / caption QA | whisper.cpp via `hyperframes transcribe` | **Yes**, plus my alignment code |
| Music ducking (first demo) | the repo's `carve.mjs` audio-carve tool | **Yes** |
| Music and SFX | my seeded numpy synthesiser | No (mine; royalty-free) |
| Lint, runtime, layout and contrast gates | `hyperframes lint` and `hyperframes check` | **Yes** |
| Fonts | Anton, Inter, JetBrains Mono, Noto Nastaliq Urdu (OFL) | No (Google Fonts) |

The CLI was installed from npm. That package is the published build of the GitHub repo. I used the clone to read the source, docs and skills.

---

## 2. What HyperFrames is (and isn't) good for in social video

**Strengths**
- **Anything a browser can draw becomes video:** typography, SVG charts, maps, app UIs and code. These are the core visuals of explainer, data and quiz channels.
- **Deterministic.** An unchanged project re-renders byte-identically, which I proved earlier. You get no "random" encoding surprises.
- **Built for scale.** Variables, `--batch` and Lambda batch rendering cover one template × many brands, languages or listings.
- **Agent-native.**
  - It ships **21 agent skills**, including `/faceless-explainer`, `/talking-head-recut`, `/embedded-captions` and `/motion-graphics`.
  - Its catalog has **392 blocks and components**. Examples: `bar-chart-race`, `data-chart`, `chart-story`, `world-map`, `count-up`, `tiktok-follow`, `instagram-follow`, `x-post`, `reddit-post`, `yt-comment-card`, `comparison-split`, `testimonial-card`, `code-typing`, `split-flap-board`, and 17 caption styles.
- **Real quality gates.** `lint` and `check` audit the runtime, overlaps, motion and contrast.
- **Free.** Apache-2.0 licensed, and it runs locally.

**Limits (honest)**
- **CPU-heavy.** On this 2-vCPU box, a 36–42 s video takes **4.5–5.5 minutes** to render, roughly 7–8 s of rendering per second of video.
- **No footage or character generation.** It animates what you give it. For realistic scenes you need your own footage or other (mostly paid, GPU-hungry) AI video tools.
- **Young and fast-moving.** I hit two real bugs: an unbounded whisper build, and audio-carve attribute quoting. Pin your versions.
- **Needs code, or an AI agent writing code.** It's not a drag-and-drop editor.
- **The official agent workflows prefer a HeyGen account** for voices and music. They do fall back to local engines, as Reels Studio does.

---

## 3. The 2026 platform rules that decide whether any "viral system" works

### YouTube
- **15 Jul 2025:** the "repetitious content" policy was renamed **"inauthentic content"**, explicitly covering mass-produced and repetitive videos ([air.io](https://air.io/en/monetization/youtube-monetization-policy-changes-2026-a-complete-dated-timeline)).
- **Jan 2026:** in one wave, YouTube terminated **16 channels** with **35M subscribers and 4.7B lifetime views**, earning about $10M a year. These were AI mass-production channels ([aituber.app](https://aituber.app/blog/faceless-youtube-channels-demonetized-2026/), [flocker.tv](https://flocker.tv/posts/youtube-inauthentic-content-ai-enforcement/)).
- **16 Jul 2026:** three categories of content are now ineligible for monetisation ([outlierkit](https://outlierkit.com/blog/youtube-updates-july-2026), [metamusicmedia](https://metamusicmedia.com/blogs/news/youtube-demonetization-rules-2026)). Eligibility is judged at the **channel** level.
  1. Generic, repetitive or **template-based** videos.
  2. Unsatisfying or manipulative videos.
  3. **AI personas** giving advice on health, finance, legal or political topics.
- **1 Oct 2026:** Shorts recommendations now favour original Shorts. YouTube's Rene Ritchie said *"VO descriptions of what's happening on screen, minor technical edits, or template-based bulk changes"* do **not** count as adding value ([relevantaudience](https://www.relevantaudience.com/youtube/youtube-shorts-original-content-reach-update/), [androidheadlines](https://www.androidheadlines.com/2026/10/youtube-cuts-reach-reuploaded-shorts-originality-push.html)).
- **Announced 10 Aug 2026, effective 1 Feb 2027:** new Partner Program applicants need 1,000 subscribers plus **8,000 watch hours or 20M Shorts views in 90 days**. That's double today's bar. Existing partners need 10M Shorts views per 90 days to keep earning Shorts revenue ([Forbes](https://www.forbes.com/sites/gabrielalinzainescu/2026/08/11/youtube-doubles-the-monetization-bar-for-new-creators/), [podderapp](https://www.podderapp.com/post/youtube-doubles-podcast-monetization-thresholds)).
- **AI disclosure** is required for *realistic* synthetic people, places or events. It isn't required for clearly animated content ([digitalapplied](https://www.digitalapplied.com/blog/ai-content-labeling-rules-advertisers-2026-reference)).

### Meta (Facebook / Instagram)
- **14 Jul 2025:** accounts that repeatedly repost others' content lose reach and monetisation. Meta also says "stitching together clips" and adding a watermark isn't enough ([TechCrunch](https://techcrunch.com/2025/07/14/following-youtube-meta-announces-crackdown-on-unoriginal-facebook-content/)).
- **30 Apr 2026:** Instagram's originality rule was extended to photos and carousels.
  - Instagram's own examples of original content include **"content you designed… a how-to guide or a visual story"** and **"new graphics that add information"**, which is the lane this stack is built for.
  - Its main ranking signals are **watch time, sends per reach and likes per reach**.
  - **Trial Reels**, which show a video to non-followers first, are now schedulable for hook tests ([creatorflow](https://creatorflow.so/blog/instagram-algorithm-2026/), [kompozy](https://kompozy.io/news/instagram-mosseri-ranking-signals-guidance)).

### TikTok
- Reused or minimally edited content is **ineligible for the For You feed**. Content ineligible for the For You feed can't earn Creator Rewards ([contentiq](https://contentiq.media/rules/tiktok), [monetizednow](https://monetizednow.com/ai-tiktok-content-monetization)).
- Realistic AI content needs an AI label. Generic TTS narration does not. Labelled content stays eligible ([usefastlane](https://www.usefastlane.ai/blog/tiktok-community-guidelines)).
- Since **Nov 2025**, viewers can reduce how much AI content they see ([monetizednow](https://monetizednow.com/ai-tiktok-content-monetization)).

### Design rules Reels Studio follows because of this
1. **Every video carries original information:** your data analysis, your curated questions, your explanation. It must never be a reworded article.
2. **Rotate formats and looks.** Never re-render the same script skeleton with swapped nouns at volume. Reels Studio seeds unique music per video and has 4 presets × 4 formats.
3. **Cadence:** at most 1 templated video per day per channel. 3–5 a week is sustainable.
4. **A human editor stays in the loop** (`post.md` checklist): check facts against sources, check the sound-off hook, and ask "is this different from my last 5?"
5. **Use your own voice for monetised channels and for Urdu** (own-voice mode). If you use TTS, disclose "AI voice".
6. **Never use fake experts** on health, finance or legal topics.

---

## 4. Money reality for a creator in Pakistan

| Platform | Pays creators in Pakistan? | Typical rate | Notes |
|---|---|---|---|
| YouTube Shorts | Yes, via the Partner Program | **$0.01–0.07 per 1,000 views** typical; South Asian audiences ~$0.003–0.015 ([makeviral.ai](https://www.makeviral.ai/blog/youtube-shorts-monetization), [fluxnote](https://fluxnote.io/guides/youtube-shorts-monetization-2026-updates)) | 1M views ≈ $10–70. The bar doubles on 1 Feb 2027 |
| YouTube long-form | Yes | ~$1–30 per 1,000 views depending on niche ([Shopify](https://www.shopify.com/blog/youtube-shorts-monetization)) | Finance and tech are the highest |
| TikTok Creator Rewards | **No.** Available in the US, UK, DE, FR, JP, KR, BR, MX and a few others ([toptal](https://www.toptal.com/creator/post/how-to-join-the-tiktok-creator-rewards-program), [buyfollowers](https://buyfollowers.com/blog/tiktok-monetization-countries-list)) | n/a | TikTok is for reach and brand deals |
| Facebook | **Mixed reports.** Some say it's available ([connectedpakistan](https://blog.connectedpakistan.pk/facebook-monetization-pakistan-2026-guide)), others say not yet ([Epidemic Sound](https://www.epidemicsound.com/blog/how-to-monetize-facebook/)). A 300k-views/28-days route is rolling out to limited users ([BOL News](https://www.bolnews.com/latest-news/facebook-makes-easier-strategy-for-pakistani-creators-to-earn-money/)) | South Asia CPM ~$0.30–2 | Check your Professional Dashboard |

**Honest conclusion:** "go viral and earn from ads" barely works for Shorts aimed at South Asian audiences. These routes work:
- **(a) Services.** Make these videos for local businesses: real-estate listings, restaurants, clinics, academies, e-commerce products. HyperFrames' variables and `--batch` turn one template into a video per listing.
- **(b) Products and affiliate links**, such as an English course or a templates pack.
- **(c) Long-form YouTube**, with Shorts as the funnel.
- **(d) English content for global audiences** if you want ad revenue.

---

## 5. Which niches? Scored for *this* stack

★ = fit with HyperFrames (motion graphics, no footage). RPM figures are third-party estimates and vary widely.

| Niche | Fit | Free data / content source | Why it can spread | Money | Saturation / risk | Verdict |
|---|---|---|---|---|---|---|
| **Data stories / country comparisons** | ★★★★★ | World Bank API (CC BY 4.0), Our World in Data | "Who wins?", rankings people screenshot, comment debates | Mid RPM; "data visualization" is a low-competition faceless niche ([faceless.my](https://faceless.my/niches/top-faceless-youtube-niches/)) | Low, **if you check the data** (see 7.3) | **Top pick** (demo built) |
| **Cricket stats** (PK/IN audience) | ★★★★★ | **Cricsheet** ball-by-ball data, ODC-BY ([tigzig](https://www.tigzig.com/post/cricket-full-data-download-live-aug2026)) | Rivalry, records, instant debate | Low RPM, huge reach, sponsors | Use stats graphics only (match footage is copyrighted) | **Top pick for reach in Pakistan** |
| **Quiz / trivia / geography** | ★★★★★ | Your research plus Wikipedia, CIA Factbook | Play-along, "comment your score", rewatches | Low RPM | Medium-high saturation. Vary themes, never mass-clone | **Strong as a series** (demo built) |
| **Spoken English for Urdu/Hindi speakers** | ★★★★☆ | Your teaching | Saves, sends, daily habit | Courses and coaching | Big demand; use your own voice | **Strong** (demo built, Urdu on screen) |
| **Tech / AI tools** | ★★★★☆ | GitHub API, docs, **your own testing** | "Free tool that does X", saves | High RPM | Hype and false claims hurt trust | **Strong if you test tools yourself** (demo built) |
| **Finance concepts** (compound interest, inflation) | ★★★★☆ | Calculators, central-bank data | Calculators, "you vs inflation" | Highest RPM | Never an AI "advisor" persona (YouTube category 3) | Good, with care |
| **Local business promos** | ★★★★★ | Client data (prices, listings) | Not viral; it sells | **Direct money** | None of the YouTube Partner Program risk | **Best money** |
| History / maps / timelines | ★★★☆☆ | Wikipedia, Wikimedia (check licences), `world-map` block | Curiosity | Mid | Needs strong research | OK |
| Islamic reminders | ★★★☆☆ | Scholarly sources | Huge in Pakistan | Low RPM | Accuracy and respect; quote-slideshow risk | Only with original commentary |
| Motivational quotes | ★★☆☆☆ | none | – | Low | **Saturated + "slideshow" pattern targeted** | Avoid |
| AI stories / "what if" / skeleton 3D | ★☆☆☆☆ | Needs AI video and imagery | Works for others | – | Not this stack; high policy risk | Skip |
| Re-uploads / compilations with voice-over | ✗ | – | – | – | **Explicitly de-ranked since 1 Oct 2026** | Avoid |
| Kids content | ✗ | – | – | Made-for-kids limits | – | Avoid |

---

## 6. Video formats that work, and which HyperFrames pieces build them

| Format | Retention mechanic | Template | Catalog blocks/components (verified in v0.8.137) |
|---|---|---|---|
| Quiz with timer | play-along, payoff every ~10 s | `quiz` | `count-up`, `conic-progress-ring`, `caption-*` |
| Data race / chart story | "who wins", lead changes | `data-race` | `bar-chart-race`*, `data-chart`*, `chart-story`, `mk-line-graph`*, `decline-chart` |
| Countdown #5 → #1 | open loop | `ranked-list` | `number-wheel`, `star-rating-fill`, `split-flap-board`* |
| Say this / myth vs fact | instant usefulness | `say-this` | `comparison-split`, `before-after-wipe`, `strikethrough-replace` |
| Map explainer | curiosity, geography | – | `world-map`*, `us-map`*, `nyc-paris-flight`* |
| Story with social proof | relatable "screenshots" | – | `x-post`*, `reddit-post`*, `yt-comment-card`*, `chat-thread`, `chatgpt-exchange`, `notification-stack` |
| **Your face + designed captions** | human trust (the strongest under 2026 rules) | – | skills `/embedded-captions`, `/talking-head-recut`; `caption-pill-karaoke`, `caption-highlight` |
| Product / app promo | clarity, offer | – | `app-showcase`*, `device-frame-stage`, `testimonial-card`, `cta-lockup`, `logo-outro` |
| Code / tech demo | "watch it work" | – | `code-typing`, `terminal-simulator`, `code-diff`, `browser-device-stage` |

\* = a 1920×1080 block. Use it in 9:16 by scaling or cropping, or with `yt-vertical-fill`. Components with no fixed size drop straight into vertical.

---

## 7. What I built: Reels Studio (formerly VVS)

**Folder:** `reels-studio/`. Read `README.md` for usage.

```
brief.json ─► segments ─► voice: Kokoro TTS (local, Apache-2.0)  or  YOUR recordings (own-voice mode)
           ─► exact per-line timing ─► word timings anchored to each line's real pauses
           ─► whisper.cpp intelligibility QA (did the voice say the script?)
           ─► seeded royalty-free music ducked ~9 dB under speech + SFX on template events ─► loudnorm -14 LUFS
           ─► HyperFrames project ─► lint ─► check (runtime/layout/motion/contrast) ─► render
           ─► QA: 1080×1920 · 30 fps · H.264/AAC · duration · loudness · peak
           ─► renders/<id>/: video.mp4 · cover.jpg · contact.jpg · captions.srt · post.md · manifest.json
```

### 7.1 Three ways to use HyperFrames for viral video, ranked by policy safety

1. **Human-led (safest):** you record yourself on a phone, and HyperFrames adds captions, titles, data callouts and overlays. Use the `/embedded-captions` and `/talking-head-recut` skills, or Reels Studio own-voice mode with any template.
2. **Bespoke agent-made:** an AI agent writes a *custom* composition per video using HyperFrames skills such as `/faceless-explainer`. Each video is unique, but it's slower.
3. **Series templates (Reels Studio):** this is fast and repeatable. It stays safe **only** when each video brings new information and formats rotate. Use it for your recurring series, such as "Quiz Tuesday" and "Data Thursday".

### 7.2 Demo results (measured in this sandbox, 2 vCPU / 1.9 GB RAM)

| Video | Niche | Template | Length | Size | Render / whole pipeline | Loudness / peak | Whisper heard the script | QA |
|---|---|---|---|---|---|---|---|---|
| `renders/quiz-geography-01/quiz-geography-01.mp4` | trivia / geography (edutainment) | `quiz` | 38.1 s | 4.1 MB | 270 s / 336 s | -14.2 LUFS / -1.3 dBFS | 100.0% | 6/6 |
| `renders/data-gdp-south-asia-01/data-gdp-south-asia-01.mp4` | data / economics explainer | `data-race` | 42.1 s | 5.3 MB | 324 s / 400 s | -14.4 LUFS / -1.3 dBFS | 93.3% | 6/6 |
| `renders/ranked-free-tools-01/ranked-free-tools-01.mp4` | tech / AI tools (high-RPM) | `ranked-list` | 35.7 s | 4.4 MB | 272 s / 345 s | -14.1 LUFS / -1.4 dBFS | 100.0% | 6/6 |
| `renders/say-this-english-01/say-this-english-01.mp4` | education / spoken English for Urdu & Hindi speakers | `say-this` | 29.7 s | 3.6 MB | 244 s / 310 s | -14.1 LUFS / -1.4 dBFS | 98.6% | 6/6 |
| `renders/say-this-urdu-voice-01/say-this-urdu-voice-01.mp4` | education / spoken English for Urdu & Hindi speakers | `say-this` | 36.0 s | 3.7 MB | 274 s / 353 s | -14.0 LUFS / -1.5 dBFS | 100.0% | 6/6 |

All were rendered with `--quality looks --crf 26`, which keeps files about 5 MB. Three came from one `reels.py batch` run, and that batch correctly *refused* to render the fourth until a `check` error was fixed. Use `--quality looks` without `--crf` (CRF 16) for maximum upload quality.

### 7.3 What the gates caught while building (why "automation + checks" beats "automation")

| Gate | What it caught | Fix |
|---|---|---|
| `hyperframes check`, layout | Value labels riding the chart lines **collided at every lead change** (India and Pakistan cross six times) | Redesigned as a live leaderboard with rank-slot pills |
| `hyperframes check`, contrast | White text on a sky-blue badge at 2.14:1, and on the reveal green at 2.28:1 (unreadable in sunlight) | Text colour computed from the accent's luminance, and a darker green (~5:1) |
| `hyperframes check`, text paint | Outline-only "#" with a transparent fill counted as invisible | A faint fill under the stroke |
| `hyperframes check`, occlusion | A strike-through line covering a short phrase failed as `text_occluded`. Gotcha: `data-layout-allow-occlusion` only counts when it's on **each text element itself** (the audit doesn't look at parents), and read-along splits text into word spans | The flag is set on every word span |
| `hyperframes lint` | Fonts used without `@font-face` (emoji, Urdu) would fall back unpredictably | Fonts are shipped with every project |
| whisper.cpp | Its timestamps drift across 3-second silences (quiz countdowns) | Timing now comes from the waveform; whisper is used for intelligibility QA |
| Contact-sheet review | Stat bars visible "full" before counting; hook spoken for 7 s (too long) | Hidden initial states; hook cut to ~3 s |
| **Editor (data check)** | Pakistan's GDP jumps **+75% in nominal rupees** in 2000, while real GDP grows **+4%**. It's a **statistical revision, not a boom** | Not narrated; footnoted on the chart and in the pinned comment |

### 7.4 Free tools used, and their licences

| Tool | Licence | Notes |
|---|---|---|
| HyperFrames | Apache-2.0 | |
| Kokoro-82M TTS | Apache-2.0 | 8 languages including **Hindi**. It has no Urdu voice, but a Hindi voice plus espeak's Urdu phonemizer works experimentally (7.5) |
| whisper.cpp | MIT | |
| FFmpeg | LGPL/GPL | |
| GSAP | free standard licence, including commercial use | |
| Fonts | OFL | |
| World Bank Open Data | CC BY 4.0 | |
| Cricsheet | ODC-BY | |

Licences to avoid for monetised use:
- **XTTS-v2** and **F5-TTS** are **non-commercial** ([promptquorum](https://www.promptquorum.com/power-local-llm/local-tts-voice-cloning-piper-coqui-xtts)).
- **YouTube Audio Library** "standard licence" tracks are **YouTube-only**. CC-BY tracks can be used elsewhere with credit ([licenseorg](https://www.licenseorg.com/guide/music-audio/youtube-audio-library)).
- Platform music libraries don't transfer between platforms ([foximusic](https://www.foximusic.com/blog/youtube-shorts-music-licensing-guide/)).
- **Pexels and Pixabay** allow commercial use but give **no indemnification**. The Pexels **API** requires attribution ([picdefense](https://picdefense.io/resources/source-intel/pexels/)).

Alternatives, honestly:
- **MoneyPrinterTurbo** (MIT, about 129k stars) auto-makes stock-footage Shorts, but its default templated output is exactly what YouTube's 2026 rules target ([review](https://www.topuseai.com/blog/moneyprinterturbo-review)).
- **Remotion** (React) is free for individuals and teams of up to 3 people; companies need a licence ([websites2know](https://websites2know.com/remotion-review/)).

### 7.5 Can free TTS speak Urdu/Hindi? (measured, not assumed)

**Method:** Kokoro synthesises a sentence. whisper.cpp's multilingual `base` model transcribes it. I then compare the characters (`tools/tts_roundtrip.py`). This is a machine proxy: a native listener is still the real test.

| Test | Voice | Result |
|---|---|---|
| English control | `af_heart` | **100%** match (the method works) |
| Hindi text (Devanagari) | `hf_alpha`, `hm_omega` | whisper understood the whole sentence but **wrote it in Urdu script** (spoken Hindi and Urdu are the same language), so a literal Devanagari comparison scores 0% |
| **Urdu text** via espeak-ng `ur` | `hf_alpha` | **87%** on the test sentence |
| **The demo's 3 real Urdu lines** | `hf_alpha` (`ur`) | **82% / 98% / 80% (88% overall)**. Slips: مطلب heard as "ماتلاب", نہیں as "نحن", so there's an accent |

**Verdict:** free Urdu TTS is **usable for drafts and experiments**, and Reels Studio supports it (`"urdu_voice"`, or per-line `"lang": "ur"`). For trust and monetisation, your own voice is better.

---

## 8. How to use it

### 8.1 Inside this agent (Arena), the "INSIDE your" part
You just ask. For example:
- *"Make a quiz video: 3 questions about Pakistan's geography, handle @quiz.pk, midnight style."*
- *"Make a data race of internet users (% of population) for Pakistan, India, Bangladesh and Sri Lanka since 2000."*
- *"Plan and render 5 spoken-English videos for this week; I'll send my own voice recordings."*

I then:
1. research and verify the facts, with sources;
2. fetch the data and check it for series breaks;
3. write the brief;
4. run `reels.py`;
5. inspect the contact sheet and fix what I see;
6. deliver the MP4 and `post.md`.

Sandbox limits:
- about 6 min per video;
- the sandbox resets between sessions, after which `bash reels-studio/bootstrap.sh` restores the tools in about 2.5 min (files persist);
- about 128 MB of storage, so download finished videos.

### 8.2 On your own PC (Windows, macOS or Linux)
```bash
# Node 22+, FFmpeg, Python 3.10+
npm i -g hyperframes@0.8.137 && hyperframes browser ensure
pip install kokoro-onnx soundfile numpy scipy
python3 reels.py make briefs/quiz-geography.json --quality looks
```
A normal 6–8 core laptop should render noticeably faster than this 2-vCPU sandbox, because HyperFrames runs parallel Chrome workers. That's an estimate; measure your own machine.

### 8.3 With AI coding agents (Claude Code, Cursor, Codex…)
Install the official skills with `npx hyperframes skills`. Then prompt, for example: *"/faceless-explainer: a 45-second vertical explainer on why Bangladesh's income passed India's in 2019."* This is best for bespoke, flagship videos.

---

## 9. Operating plan: how to actually run a channel with this

**Weekly rhythm (one channel, 4–5 posts):**

| Day | Post |
|---|---|
| Mon | Data story |
| Tue | Quiz |
| Wed | Tip / say-this (your voice) |
| Thu | Tool or tech |
| Fri | Data story |
| Weekend | Optional repost natively to the other platforms; a monthly long-form compilation of your *own* Shorts with added commentary |

**Hook rules (first 2 seconds):**
- The hook is readable with **sound off** (on-screen text from frame 1).
- The first spoken words **are** the hook.
- No logo intro.
- Promise a payoff, such as "wait for #1" or "who's richest today?".

**Metrics and benchmarks:**
- **YouTube "viewed vs swiped away":** community studies put below 60% as weak and 70–90% as good ([3.3B-view study](https://medium.com/@antoinelacombled/cracking-the-youtube-shorts-algorithm-a-study-of-3-3-billion-views-4711fdf7931b)).
- **Average percentage viewed:** 70–85% is strong, and loops push it past 100% ([prepublish](https://prepublish.ai/blog/viewed-vs-swiped-away-youtube-shorts)).
- **Instagram:** sends per reach, plus Trial Reels for hook tests.

**Decision rules (log everything in `reels-studio/tracker/content-tracker.csv`):**
- Judge at 48–72 h **against your own channel median**, not raw views.
- A format earns a weekly slot when **3 of 5** uploads beat the median retention.
- Drop a format after **5–8** uploads below the median.
- Change **one variable per test**: the hook line, the first frame, the length or the topic.
- Upload natively to each platform (no TikTok watermark on Reels or Shorts). **Never re-upload the same file to the same channel.**

**A 30-day plan for you (Karachi):**

| Week | What to do |
|---|---|
| 1 | Pick **two** niches (suggested: South Asia data stories + spoken English with your voice). Make 10 videos with Reels Studio. |
| 2 | Post daily. Fill in the tracker. Test hooks with Trial Reels. |
| 3 | Double down on the better-retaining format. Make sample videos from **3 local businesses' real data** (listings, menus, course schedules) and pitch them. |
| 4 | Refine the templates and branding. Decide what to keep. Start one long-form video per week. |

---

## 10. Honest limitations and risks

- **No system can guarantee virality.** Most uploads will underperform. The edge comes from correctness, originality, speed and learning from your metrics.
- **TTS sounds good but is recognisably synthetic.** Instagram's head argued in his Dec 2025 memo that raw, human content is becoming the proof of authenticity ([creatorflow](https://creatorflow.so/blog/instagram-algorithm-2026/)). **Your own voice is the strongest upgrade.**
- **Urdu narration:** Kokoro has no Urdu voice, and the best open voice-cloning models are non-commercial. A Hindi voice speaking Urdu text through espeak's Urdu phonemizer measured **88% machine intelligibility** with an audible accent (7.5). That's good for drafts. For a channel people trust, **record Urdu yourself** with own-voice mode; the pipeline handles everything else.
- **Data honesty is on you:** see the Pakistan 2000 break. Templates render whatever you feed them.
- **Compute:** about 5–6.5 min per 36–42 s video in this sandbox. Lambda can scale, but costs money.
- **HyperFrames is young:** pin `0.8.137`, keep `check` in the loop, and read the bugs/caveats table in `reels-studio/research/HyperFrames-Viral-Video-Guide.md`.
- **Synthesised music is basic.** For trend moments, add a platform-licensed sound in-app (it doesn't transfer between platforms).
- **Rules keep moving.** Several items above changed in the last 90 days. Re-check before scaling.

---

## 11. Files

| Path | What |
|---|---|
| `reels-studio/README.md` | usage, brief format, own-voice mode, adding templates |
| `reels-studio/reels.py`, `lib/pipeline.py`, `lib/synth.py` | CLI, pipeline, and music/SFX engine |
| `reels-studio/templates/{_base,quiz,data-race,ranked-list,say-this}/` | Templates |
| `reels-studio/briefs/*.json` | The 4 demo briefs (with sources) |
| `reels-studio/tools/fetch_worldbank.py` | Real data and an editor's fact sheet (lead changes, growth) |
| `reels-studio/renders/<id>/` | Rendered demos: mp4, cover, contact sheet, SRT, post kit, manifest |
| `reels-studio/tracker/content-tracker.csv` | Metrics log and decision columns |
| `reels-studio/research/HyperFrames-Viral-Video-Guide.md` | Earlier deep-dive on the repo's architecture, rendering, bugs and platform specs |
| `reels-studio/setup/setup-sandbox.sh`, `setup-whisper.sh` | One-command toolchain restore |
