# HyperFrames — deep dive, a real render, and a playbook for viral social videos

> **Update (7 Oct 2026):** the follow-up research and the working system are in **`reels-studio/research/VIRAL-SYSTEM-REPORT.md`**. That covers niches, 2026 platform rules, money reality in Pakistan, and 4 rendered demo videos. The pipeline itself is in **`reels-studio/`** (Reels Studio).


*Research + hands-on build, 6 Oct 2026. Repo: [github.com/heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) @ `5fad52f`, CLI `hyperframes@0.8.137`.*

---

## TL;DR

- **What it is.** HeyGen's open-source (Apache-2.0) framework that turns **plain HTML/CSS/JS + a seekable animation timeline into frame-accurate video** (MP4, MOV/ProRes with alpha, transparent WebM, GIF, PNG sequence, HLS). No React, no build step. It was designed for **AI agents to write**, with 21 agent "skills", ~130 lint rules, and a headless QA gate.
- **What I did.** I cloned and read the repo (14 packages, ~433k lines of TypeScript, 1,628 test files) and set up the toolchain on a small Linux box (2 vCPU, 1.9 GB RAM). I rendered a stock example, then **built and rendered an original 23-second vertical short**. Its voice-over came from HyperFrames' own local TTS, its captions were word-timed with its own transcriber, and it has music + SFX and 35 mixed audio tracks. Finally I **batch-rendered three branded variants of it from one template** with `--batch`.
- **Why it matters for social.** A short-form video is a *template* (hook → proof → payoff → CTA, captions, safe zones, a loop point). HyperFrames makes that template **code with declared variables**. So you can A/B test hooks, re-brand per client, localise, and render hundreds of variants locally or on AWS Lambda / Cloud Run, and every render of the same input is identical.
- **Main caveats.** It is young and moves very fast: daily releases, PR #5,100+ in 7 months, and early community reports of bugs. Rendering is CPU-heavy without a GPU. I hit and documented **two real bugs** (an unbounded whisper.cpp build that froze the box, and an audio-carve attribute bug). YouTube's July 2025 "inauthentic content" rules and platform AI-labeling rules apply to mass-produced or synthetic-voice videos, so templating must add real value.

**Deliverables:** `GitHub Release `renders-2026-10-07` → viral-short.mp4` (main demo), `GitHub Release `renders-2026-10-07` → variants/variant-{0,1,2}.mp4` (batch), the full project source, and this guide.

---

## 1. What I did, step by step

| Step | Command / action | Result |
|---|---|---|
| Get the code | `git clone https://github.com/heygen-com/hyperframes` | HEAD `5fad52f` (6 Oct 2026), packages at v0.8.137 |
| Runtime | Node **22** (the CLI requires ≥22), FFmpeg 7.1 | `hyperframes doctor` explains anything missing |
| CLI | `npm i -g hyperframes@0.8.137` (same version as the source I read) | `hyperframes --version` → 0.8.137 |
| Browser | `hyperframes browser ensure` | downloads pinned **chrome-headless-shell 152** (114 MB) |
| Chrome libs | `doctor` printed the exact `apt-get install libnss3 …` line | Chrome check ✓ |
| Smoke test | `hyperframes init smoke --example vignelli` → `render` | 10 s, 1080×1920, 300 frames in **25 s** |
| Voice | `hyperframes tts script.txt --voice af_heart --speed 1.1` | 21.6 s Kokoro-82M voice-over, generated locally on CPU |
| Word timings | `hyperframes transcribe vo.wav --model small.en` | 53 word timestamps (whisper.cpp) |
| Build | hand-written `index.html` (one composition, 9 scenes) | `lint` 0 errors → `check` **passed** |
| QA | `hyperframes snapshot --at …` (16 proof frames) + contact sheets of the renders | found and fixed 9 visual issues the automated gates can't see |
| Mix | `carve.mjs` voice-over carve on the music bed | spectral ducking + my fast release |
| Render | `hyperframes render -o renders/viral-short.mp4` | **23 s / 690 frames in 1 min 48 s**, −14.2 LUFS |
| Determinism | re-rendered the smoke test and compared | **byte-identical MP4** (same MD5, 300/300 frames identical) |
| Batch | `render --batch batch-rows.json --strict-variables` | 3 branded variants (see §3.4) |

Environment notes for small machines: `doctor` flagged that `/tmp` is a RAM-backed tmpfs, so I moved the frame cache with `HYPERFRAMES_EXTRACT_CACHE_DIR`. On machines with ≤ 8 GB RAM the CLI switches to **low-memory mode** automatically: 1 worker, screenshot capture instead of Chrome's BeginFrame path. I turned telemetry off with `hyperframes telemetry disable` / `HYPERFRAMES_NO_TELEMETRY=1`. It is **on by default**.

---

## 2. How HyperFrames works

### 2.1 Snapshot

| | |
|---|---|
| Owner / license | HeyGen · Apache-2.0 (no source-available restrictions on commercial use) |
| Created / activity | repo created 10 Mar 2026; ~57.8k stars, ~5.2k forks; releases almost daily (`@hyperframes/core` 0.8.138 appeared the same day as CLI 0.8.137) |
| Size | 14 packages · ~433k LOC TypeScript (non-test) · 1,628 test files · 546 docs pages |
| Catalog | 164 blocks + 222 components + 8 examples (394 registry items) |
| Agent layer | 21 skills (`/hyperframes` router + workflows + domain skills) |
| Output | MP4 (H.264; H.265 for HDR), MOV ProRes 4444 (alpha), WebM VP9 (alpha), GIF, PNG sequence, HLS |

### 2.2 Repository map

| Package | Role |
|---|---|
| `core` | Composition contract, runtime injected into the page (`window.__hf`, `__hyperframes.getVariables()`, `fitTextFontSize`, pretext text measurement), frame adapters (GSAP, CSS, WAAPI, Anime.js, Lottie, Three.js, TypeGPU, D3, maps …), linter, audio model |
| `engine` | Puppeteer + FFmpeg: Chrome launch, **BeginFrame / screenshot capture**, video-frame injection, streaming encoder, audio mixer, parallel workers |
| `producer` | Render orchestration: HTML compiler, capture planning, distributed (chunked) renders, HDR, render server |
| `cli` | `hyperframes` command (41 commands: init, add, catalog, lint, check, snapshot, preview, render, tts, transcribe, beats, remove-background, capture, lambda, cloudrun, cloud, skills …) |
| `studio`, `studio-server`, `player` | Browser editor (timeline, inspector), the embeddable player |
| `sdk`, `sdk-playground` | Programmatic API |
| `aws-lambda`, `gcp-cloud-run` | Distributed rendering stacks |
| `shader-transitions`, `lint`, `parsers` | WebGL transitions, shared lint/parsers |

### 2.3 The composition model (what you or an agent writes)

```html
<div id="root" data-composition-id="main" data-start="0" data-duration="23"
     data-width="1080" data-height="1920" data-fps="30">
  <section id="hook" class="clip" data-start="0" data-duration="2.1" data-track-index="1">
    <h1 id="stop">STOP</h1>
  </section>
  <audio id="vo" src="assets/audio/vo.wav" data-start="0" data-volume="1"></audio>
</div>
<script>
  const tl = gsap.timeline({ paused: true });                       // one paused timeline
  tl.fromTo("#stop", { scale: 1.75, opacity: .35 }, { scale: 1, opacity: 1, duration: .14 }, 0.02);
  window.__timelines["main"] = tl;                                  // key = composition id
</script>
```

The rules that matter:

- **Timing lives in the DOM.** `data-start`/`data-duration` make an element a clip, and the framework shows or hides it. `data-track-index` is just a Studio lane; paint order is CSS `z-index`.
- **One paused GSAP timeline per composition**, registered on `window.__timelines`. The renderer *seeks* it to `t = frame / fps`; it never plays it. Async builds (after `document.fonts.load()`) are fine if you register at the end.
- **The framework owns media.** Never play or seek `<audio>`/`<video>` yourself. At render time videos are replaced by pre-extracted frames.
- **Determinism.** No `Date.now()`/`performance.now()`, no unseeded `Math.random()` (use a seeded PRNG), no network fetches mid-render, no hover/scroll state, and finite loops only. Same input → same pixels. `--docker` pins Chrome, fonts and FFmpeg for byte-level reproducibility.
- **Variables** (`data-composition-variables` on `<html>`: string, number, color, boolean, enum, font, image) bind through `data-var-text`, `data-var-src`, CSS `var(--id)`, or `getVariables()`. They are supplied with `--variables`, `--variables-file` or `--batch`. They **cannot** change viewport, root duration, fps or format.
- **Sub-compositions** (`data-composition-src="compositions/x.html"`, wrapped in `<template>`) keep big projects modular and editable in Studio.

### 2.4 What happens when you run `hyperframes render`

```
index.html ──► compile (inline sub-comps, resolve assets, stamp media ids, lint)
           ──► local file server ──► chrome-headless-shell (Puppeteer)
           ──► runtime waits for fonts / media / timelines (__renderReady)
           ──► for each frame f:  seek every timeline/adapter to t=f/fps
                                  inject pre-extracted video frames
                                  capture: HeadlessExperimental.beginFrame (deterministic)
                                           or Page.captureScreenshot (fallback / low-memory)
           ──► frames stream into FFmpeg while capturing (no PNG pile-up)
audio: FFmpeg filter graph (trim, volume, fades, delay, amix) + FX chains/carve rendered in an
       OfflineAudioContext in Chrome (same graph as preview) + true-peak protection (≤ −1 dBTP)
──► mux ──► validate ──► renders/<name>.mp4  (+ metadata tags hyperframes_renderer/_version)
```

Workers split the frame range across several Chrome processes (about 256 MB each). Lambda and Cloud Run split the timeline into chunks and assemble the result.

### 2.5 Quality gates (very useful for automation)

- `hyperframes lint`: static rules covering GSAP pitfalls, clip misuse, missing media ids, fonts without `@font-face`, overlapping audio lanes, timelines registered before an async build, and more.
- `hyperframes check`: lint plus **runtime** (JS errors, missing assets), **layout** (text overflow, overlap, canvas overflow sampled across the timeline), **motion**, and **WCAG contrast**. It is a single pass/fail gate you can put in CI before any render.
- `hyperframes snapshot --at 0,1.5,…`: proof PNGs plus a contact sheet. With `GEMINI_API_KEY` set, `--describe` adds an AI vision review.
- `hyperframes preview`: the Studio, with live reload, a timeline, and a human approval step.

### 2.6 Built-in media toolchain (all local)

| Command | What it does | Social-video use |
|---|---|---|
| `tts` | Kokoro-82M voices (en/es/fr/hi/it/pt/ja/zh) | faceless narration, drafts, localisation |
| `transcribe` | whisper.cpp / Parakeet, word-level timestamps, SRT/VTT export | karaoke captions, recuts |
| `beats` | beat detection → `beats/<audio>.json` | cut on the beat, beat-pulse backgrounds |
| `remove-background` | matting for video/images | captions *behind* the speaker, cut-outs |
| `capture` | captures a website for video | product promos, app demos |
| `normalize-audio`, audio FX, **voice-over carve** | loudness match, EQ/compressor/limiter/reverb, spectral ducking of music under voice | clean mixes without a DAW |

### 2.7 The catalog: ready-made viral building blocks

`npx hyperframes catalog` / `npx hyperframes add <name>`. The ones most relevant to social:

- **Social cards and overlays:** `tiktok-follow`, `instagram-follow`, `x-post`, `x-follow-card`, `reddit-post`, `yt-comment-card`, `yt-lower-third`, `spotify-card`, `social-proof-card`, `testimonial-card`.
- **Story formats:** `message-thread-reveal` (fake text conversation), `notification-cascade`, `chatgpt-exchange` / `claude-exchange` / `ai-chat-reveal`, `news-ticker`.
- **Captions:** 17 `caption-*` styles (`caption-highlight` TikTok-style sweep, `caption-pill-karaoke`, `caption-emoji-pop`, `caption-kinetic-slam`, `caption-neon-glow`, `caption-glitch-rgb` …). The embedded-captions workflow adds 35 caption "identities", including captions composited **behind** the subject.
- **Hooks and emphasis:** `headline-slam`, `char-slam-explode`, `shutter-slam`, `camera-shake`, `rgb-glitch-text`, `beat-accent`, `beat-pulse-background`, `confetti`.
- **Numbers and data:** `count-up`, `number-wheel`, `slot-machine-roll`, `apple-money-count`, `bar-chart-race`, `data-chart`.
- **Transitions and FX:** `whip-pan-cut`, `flash-through-white`, `glitch`, `light-leak`, `beat-freeze-cut`, shader transitions, `logo-outro`, `cta-lockup`.

### 2.8 Agent skills (the "built for AI" part)

Install with `npx skills add heygen-com/hyperframes`, the Claude Code plugin, or `npx hyperframes skills update`. The `/hyperframes` router sends a request to a workflow:

| Workflow | Use for |
|---|---|
| `motion-graphics` | < 10 s kinetic type, stat count-ups, logo stings, animated tweet/news/webpage |
| `faceless-explainer` | text/topic → narrated explainer (listicles, how-tos) |
| `music-to-video` | beat-synced lyric/kinetic promos from a track |
| `embedded-captions` | captions on an existing talking-head clip (rail + embedded "behind subject") |
| `talking-head-recut` | overlay cards, lower-thirds and callouts synced to a podcast/interview transcript, on 16:9 / 9:16 / 4:5 |
| `product-launch-video` | URL/brief → promo or launch video |
| `pr-to-video`, `slideshow`, `general-video`, `remotion-to-hyperframes`, `figma` | the rest |

The domain skills (`hyperframes-core`, `-animation`, `-creative`, `-audio`, `media-use`, `-cli`, `-registry`) contain hard-won rules, for example: "vary eases, don't start at t=0, prefer `fromTo` inside clips, ambient loops must live on the seekable timeline". Read `skills/hyperframes-creative/references/motion-principles.md`; it is a good motion-design primer in its own right.

---

## 3. The demo I built: `viral-short.mp4`

A 23-second, 1080×1920, 30 fps short in a classic "tool reveal" format. It is about HyperFrames itself, so every on-screen fact was verified from the repo or the GitHub API.

### 3.1 Script and structure (hook → proof → payoff → CTA)

| Time | Scene | Voice-over | Techniques |
|---|---|---|---|
| 0.0–2.0 | **Hook** | "Stop editing videos by hand." | frame 0 already reads STOP (thumbnail-safe); slam + 7-frame camera shake + white flash + impact SFX; words enter from alternating directions; red ✕ stamped on a mock editor timeline |
| 2.0–5.3 | Promise | "HyperFrames turns plain HTML into real video." | staggered 3D letter reveal; HTML card → animated beam → video card |
| 5.3–8.4 | Proof | "Write the code. Hit render. Get an MP4." | code types itself (stepped clip-path) + typing SFX; cursor clicks Render; frame counter 0→690 (this video's real frame count); MP4 badge + confetti + ding |
| 8.4–10.9 | Social proof | "Over 57,000 stars on GitHub." | star spin-in, count-up to the real 57,784, particle burst |
| 10.9–13.0 | Depth | "Almost 400 ready-made blocks." | count to 386 (the real published blocks + components) over a drifting wall of real block names |
| 13.0–15.0 | Rapid-fire | "Captions, charts, transitions." | three cards slam in exactly on each word, each with a live micro-demo |
| 15.0–17.7 | Twist | "…your AI agent can write it all for you." | chat UI: prompt → typing dots → code streams → "Rendered video.mp4"; 2 s riser |
| 17.76 | **Drop** | "One template." | music drop on the bar line; card slams with flash + shake; the card shows its variable slots `{hook} {caption} {cta}` |
| 18.8–19.9 | Scale | "100 videos." | 100 seeded variants zoom out, big ×100 |
| 19.9–23.0 | CTA + loop | "Follow for more tools like this." | follow card (handle/name/tagline are **variables**), cursor tap → "Following ✓" + hearts; fades back to the opening background for a clean loop |

Always-on retention devices: **karaoke captions** (word-timed, active word in the accent color, groups of ≤ 3 words, hard cuts between groups), a **progress bar** at the top, a handle watermark, and a background that **pulses on every beat** (121.6 BPM grid, stronger after the drop). All key content stays inside the ~900×1400 universal safe area; captions sit at y≈1250–1540, above the platform UI.

### 3.2 Audio pipeline (all local, all reproducible)

1. `hyperframes tts` (Kokoro `af_heart`, 1.1×) → loudness-normalised with FFmpeg two-pass `loudnorm` (−16 LUFS).
2. `hyperframes transcribe` (whisper.cpp `small.en`) → `tools/align_captions.py` maps whisper's words onto the display script ("MP4", "AI", numerals) and snaps them to speech segments detected in the waveform. Whisper had stamped "hand." inside the following silence; the snap fixes it. Reproducibility check: after a full sandbox rebuild, re-running `transcribe` and the aligner reproduced `captions.json` byte for byte.
3. `tools/synth_audio.py` → an **original, royalty-free** 121.6 BPM music bed whose 9th bar line lands exactly on "One template", plus whoosh, impact, pop, click, typing, ding, riser and sparkle SFX. It is seeded and deterministic, so there are no licensing questions.
4. In the composition: 35 `<audio>` clips with per-clip volume, fades and a volume automation lane, plus a **voice-over carve** on the music. The carve gives speech-band EQ dips that follow the voice and a level envelope; I sped up its release so the music swells for the CTA.
5. Final mix: **−14.2 LUFS integrated, −1.5 dBFS peak** (the renderer adds true-peak protection), which matches common platform normalisation targets.

### 3.3 Output and performance

| | |
|---|---|
| File | `renders/viral-short.mp4`: H.264 High 1080×1920 30 fps (690 frames) + AAC 48 kHz stereo, 14.2 MB, ~5 Mbps |
| Determinism | re-rendering an unchanged project gave a **byte-identical file** (MD5 `b3232b35…` both runs), which proves the "same input → same pixels" claim on this machine |
| Render time | **1 min 48 s** on 2 vCPU / 1.9 GB RAM, software GL, 1 worker, screenshot capture (~6.4 fps). A normal 8-core laptop with BeginFrame and several workers is several times faster |
| QA | `check` passed (0 lint, runtime, layout, motion and contrast errors). Snapshot and contact-sheet review caught 9 more issues the gates cannot see (see §4.6 and §5) |

### 3.4 One template → many videos (`--batch`)

The composition declares five variables: `handle`, `name`, `tagline`, `accent`, `accent2`. `batch-rows.json`:

```json
[
  { "handle": "@studio.nova",   "name": "Studio Nova",   "tagline": "Design systems · motion · UI", "accent": "#2EE6D6", "accent2": "#3B5BFF" },
  { "handle": "@growth.daily",  "name": "Growth Daily",  "tagline": "Marketing tips every morning",   "accent": "#FF4D8D", "accent2": "#FF8A00" },
  { "handle": "@karachi.codes", "name": "Karachi Codes", "tagline": "Dev tools · AI · open source",   "accent": "#FFD23F", "accent2": "#00A86B" }
]
```

```bash
hyperframes render --batch batch-rows.json --strict-variables \
  --output "renders/variants/variant-{index}.mp4" --quality draft
```

Result: **3/3 rows completed** (`renders/variants/manifest.json` records variables, timings and status per row). Every variable propagated: the watermark and card handle, the name with auto-computed initials (`HL` → `SN`/`GD`/`KC`), the tagline, the caption highlight, the progress bar, glows, gradients, the avatar ring and the confetti. See `renders/variants/variants-comparison.jpg`.

| Row | Handle | Accent | Render time (run 1 / run 2) | Size |
|---|---|---|---|---|
| 0 | `@studio.nova` | `#2EE6D6` / `#3B5BFF` | 104 s / 103 s | 9.6 MB |
| 1 | `@growth.daily` | `#FF4D8D` / `#FF8A00` | 107 s / 99 s | 9.7 MB |
| 2 | `@karachi.codes` | `#FFD23F` / `#00A86B` | 103 s / 99 s | 9.6 MB |

Run 2 came after the sandbox was wiped and rebuilt from scratch with `reels-studio/setup/setup-sandbox.sh`. Every output matched run 1: 690 frames, 23.000 s, −14.2 LUFS and −1.5 dBFS on all three. The manifest reported 3 completed and 0 failed.

Total **5.2 min (run 1) and 5.0 min (run 2) for three 23-second videos** on 2 vCPU, rendered sequentially (`--batch-concurrency 1`, the safe default). On a bigger machine raise `--workers` / `--batch-concurrency`, or move the same rows to `hyperframes lambda render-batch`.

---

## 4. Playbook: generating viral animated videos for social networks

### 4.1 Why this tool fits short-form

1. **Short-form is formulaic in the best sense.** Hook in the first 1–2 s, captions for sound-off viewers, a visual change every 1.5–3 s, a payoff, a CTA, a loop. A HyperFrames template turns that formula into code you can version, test and reuse.
2. **Variables + batch = cheap experiments.** Hooks, palettes, CTAs, languages and handles become data rows. Render ten hook variants, post them, keep the winner.
3. **Deterministic output.** The same row always renders the same file, so A/B tests compare content rather than render noise, and re-renders after a typo fix change only what you changed.
4. **Agent-native.** An LLM can write a composition from a prompt; `lint` and `check` turn its mistakes into machine-readable errors that it can fix on its own.
5. **Local media stack.** TTS, transcription, beats and matting run on your machine. No per-minute SaaS fees for drafts.

### 4.2 Platform specs that matter (2026)

| Platform | Canvas | Max length | Keep clear of (UI) |
|---|---|---|---|
| TikTok | 1080×1920 (9:16) | 10 min in-app, up to 60 min via web upload | bottom ~320 px, right ~120 px, top ~108 px |
| Instagram Reels | 1080×1920 (9:16) | up to 3 min | top ~210 px, bottom ~310 px, right ~84 px; grid shows a ~4:5 crop |
| YouTube Shorts | 1080×1920 (9:16) | up to 3 min (since Oct 2024) | bottom ~300 px, right ~96 px, top ~120 px |
| Facebook Reels / Stories | 1080×1920 (9:16) | — | similar bottom/right UI |
| One master for all | **1080×1920, keep text/faces/CTA inside a centred ~900×1400 box**, MP4 H.264 + AAC, 30 fps | | |

Sources: bevyl.ai, adaptlypost.com and picto.video 2026 spec guides (links in §8). Exact margins shift as apps redesign; confirm in-app for high-stakes campaigns.

For feeds (X, LinkedIn, the Facebook feed) use 1:1 or 4:5. Since variables can't change the viewport, keep **one composition per aspect ratio** that shares sub-compositions, scenes and the same variables. `--resolution portrait-4k` etc. only upscales (same aspect ratio).

### 4.3 Retention anatomy → how to build it in HyperFrames

| Retention lever | Implementation |
|---|---|
| **Frame 0 = thumbnail**; hook lands < 0.3 s | big type visible at `t=0`; `headline-slam` / `char-slam-explode`; impact SFX at the landing; deterministic `camera-shake` |
| **Pattern interrupt every 1.5–3 s** | one scene `.clip` per VO phrase; alternate directions and eases (the motion-principles reference forbids "same ease everywhere"); `whip-pan-cut`, `flash-through-white`, hard cuts on beats |
| **Captions for sound-off** (word-level) | `hyperframes transcribe` → `caption-highlight` / `caption-pill-karaoke`, or the custom karaoke in this demo; ≤ 3 words per group, active word in the accent color |
| **Proof and numbers** | `count-up` / `number-wheel` with real data; `bar-chart-race`; `data-chart` |
| **Sound design** | per-event SFX `<audio>` clips, `hyperframes beats` to cut on the beat, voice-over carve so music never fights the voice |
| **Open loop / progress cue** | top progress bar; "wait for #1" list structures; a counter |
| **Payoff → CTA** | `tiktok-follow`, `instagram-follow`, `x-follow-card`, `cta-lockup`, `social-proof-card` |
| **Seamless loop** (replays count) | end on the opening background/colour; keep the last 0.3 s visually close to frame 0 |

### 4.4 Formats that work well (and the blocks for them)

1. **Faceless explainers and listicles** ("3 AI tools that…"): `faceless-explainer` skill, TTS, karaoke captions, count-ups.
2. **Fake chat / notification stories**: `message-thread-reveal`, `notification-cascade`, `ai-chat-reveal`. These are a high-retention format.
3. **Screenshot stories**: `x-post`, `reddit-post`, `yt-comment-card` as overlays on footage or gradients. Use real posts only with permission.
4. **Stat reveals and data races**: `apple-money-count`, `bar-chart-race`, `data-chart`.
5. **Talking-head upgrades**: `embedded-captions` (captions behind the speaker via matting) and `talking-head-recut` (lower-thirds, callouts, PiP).
6. **Beat-synced edits**: `music-to-video`, `beat-freeze-cut`, `beat-pulse-background`.
7. **Product launches and app demos**: `product-launch-video` + `capture` for real UI.
8. **Transparent overlays for editors**: render `--format mov` (ProRes 4444) or `webm` and drop it into CapCut/Premiere.

### 4.5 An automated content pipeline

```
 ideas (trends, RSS, product DB, top comments)
   │
   ▼
 LLM writer ── produces: 5 hook variants · 15–30 s script · on-screen text · CTA · rows.json
   │
   ├─► hyperframes tts  (or a human / licensed voice)  ──► loudnorm
   ├─► hyperframes transcribe ──► align to script (word timings → captions JSON)
   ▼
 template project (declared variables; scene timing from the captions JSON)
   │   hyperframes check   ◄── hard gate in CI (lint + runtime + layout + contrast)
   │   hyperframes snapshot --at <proof times>  (optional AI review: --describe)
   ▼
 render:  local  hyperframes render --batch rows.json
          cloud  hyperframes lambda render-batch --batch rows.jsonl --max-concurrent 10
   ▼
 publish via official APIs / schedulers  ──►  retention analytics (3 s hold, avg watch %)
   │                                                     │
   └──────────────── winners feed back into hook generation ◄┘
```

Practical notes:

- **Brand or format variants** (same script, different look/handle/CTA): pure variables + `--batch`, as in §3.4.
- **Content variants** (different scripts, so different durations and timings): the root `data-duration` is fixed at compile time. Either have a build step (or the agent) write `index.html` per video from a template, or pass the word timings as a string variable that the composition parses with `getVariables()` and set the root duration per job.
- **Lambda** (`hyperframes lambda deploy`, then `lambda sites create` once, then `lambda render-batch`): the project upload is content-addressed and reused. Keep variables small (Step Functions input ≤ 256 KiB) and pass media as URLs.
- Pin the CLI version (`npx --yes hyperframes@0.8.137 …`, which `init` already writes into `package.json`) because releases land daily.

### 4.6 Using an AI agent effectively

```bash
npx skills add heygen-com/hyperframes        # or: claude plugin marketplace add heygen-com/hyperframes
```

Prompt patterns that map onto the workflows:

- *"Using /hyperframes, make a 20-second 9:16 faceless explainer about <topic>: hook in the first second, karaoke captions, three count-up stats, follow CTA. Expose `handle`, `accent` and `hook` as variables."*
- *"Using /motion-graphics, turn this tweet into a 6-second animated card with a count-up on the likes."*
- *"Using /embedded-captions, caption clip.mp4 in a bold karaoke style with the climax word behind me."*

Then insist on the loop: **`lint` → `check` → `snapshot` → look at the frames → fix → render.** In my build, lint warnings went from 28 to 13 (the remaining 13 only suggest splitting the file into sub-compositions) and `check` layout errors went from 12 to 0. The visual reviews caught 9 more bugs that no gate could see: a cropped first frame, a stray particle, cursors missing their buttons, overlapping caption groups, an active word eating its neighbour's space, hearts over text, an empty frame between scenes, and counters idling at "0".

### 4.7 Rules of the road (don't get demonetised or labelled)

- **YouTube Partner Program:** since 15 Jul 2025 "repetitious" content is called **"inauthentic content"**: mass-produced or repetitive videos are not monetisable. YouTube says reused content stays eligible if you add significant original commentary, modifications, or educational or entertainment value. Use templates to *produce* original ideas, not to spam near-duplicates.
- **AI disclosure:** TikTok, Meta and YouTube require labels for realistic synthetic media, and the rules cover AI voices (YouTube focuses on cloned voices of real people). TikTok's own built-in TTS is auto-labelled, and AI-written scripts don't need a label. When in doubt, switch on the platform's AI-content toggle.
- **Music:** use licensed or platform-library tracks, or generate your own (as this demo does). Don't bake copyrighted songs into renders.
- **Screenshots of real people's posts** (X/Reddit cards): get permission, or use them as commentary.

---

## 5. Caveats, bugs and gotchas I hit (with fixes)

| # | Issue | Impact | Fix / workaround |
|---|---|---|---|
| 1 | **whisper.cpp auto-build runs `cmake --build … -j` with no job limit** (`packages/cli/src/whisper/manager.ts`). On 2 vCPU / 1.9 GB it spawned 10+ compiler processes, exhausted RAM and froze the machine for ~20 min. Its error path then deletes the partial build. | transcription setup can hang small VMs and CI runners | build whisper.cpp yourself with `-j1`/`-j2` into `~/.cache/hyperframes/whisper/whisper.cpp`, which the CLI checks before auto-building. `reels-studio/setup/setup-whisper.sh` does this: 2 min 11 s including the 488 MB model, with one compiler at ~185 MB RAM. Then pass `--no-runtime-install` so the auto-build can never start. Alternatives: set `HYPERFRAMES_WHISPER_PATH`, or use Parakeet |
| 2 | **`carve.mjs` only parses double-quoted attributes** (`skills/hyperframes-audio/scripts/carve.mjs` ~L270/545). A single-quoted `data-automation='…'` (the style the docs use for JSON) is not seen, so a **duplicate** attribute is appended. HTML keeps the first, and the carve is silently ignored. | the music never ducks, with no error | write JSON attributes double-quoted and entity-escaped before carving (verified: "6 carve + 1 kept") |
| 3 | The carve's level envelope releases slowly (~5 dB/s) | music stays ducked through a short CTA tail | post-edit the lanes after the voice ends, or lower `--strength` |
| 4 | GSAP `fromTo` defaults to `immediateRender: true` | particle "from" states show before their burst (stray confetti); invisible to lint/check | hide particles in CSS + `immediateRender: false`; review snapshots |
| 5 | Lint can't see through object spreads (`{...IR}`) | false `gsap_repeated_fromto_without_baseline` warnings | write `immediateRender: false` literally |
| 6 | The layout audit uses font content boxes | tight display leading (Anton) = "overlap" errors even when the glyphs don't touch | `data-layout-allow-overlap` on the specific text element (it is not inherited) |
| 7 | ≤ 8 GB RAM → low-memory mode (1 worker, screenshot capture) | heavy comps render at ~6 fps on 2 vCPU | more RAM/cores, `--workers`, a GPU, or Lambda/Cloud Run |
| 8 | Templates load GSAP from jsDelivr | network needed at load time (offline previews fail) | vendor `gsap.min.js` locally for air-gapped/CI use |
| 9 | Telemetry is on by default; `init` checks/updates global AI skills on every run | privacy / CI noise | `hyperframes telemetry disable`, `DO_NOT_TRACK=1`, `HYPERFRAMES_SKIP_SKILLS=1` |
| 10 | MP4s carry `hyperframes_renderer` / `hyperframes_version` tags | reveals the tool used | keep for provenance, or `ffmpeg -i in.mp4 -map_metadata -1 -c copy out.mp4` |
| 11 | Very fast release cadence; early users called it buggy compared with Remotion (r/heygen, Apr 2026) | upgrades can change behaviour | pin versions; keep `check` + snapshot in CI |

Lint also recommends splitting large single-file compositions into sub-compositions (Studio shows one row per top-level element). I kept the demo in one file for readability; for team or Studio editing, split each scene into `compositions/*.html`.

---

## 6. Cheat sheet

```bash
# setup
npm i -g hyperframes@0.8.137 && hyperframes doctor && hyperframes browser ensure
hyperframes init my-short --example blank --resolution portrait --non-interactive
hyperframes add tiktok-follow           # pull a block/component from the catalog

# media
hyperframes tts script.txt --voice af_heart --speed 1.1 -o assets/vo.wav
hyperframes transcribe assets/vo.wav --model small.en      # word timings → assets/transcript.json
#   small VM? pre-build whisper with reels-studio/setup/setup-whisper.sh and add --no-runtime-install
hyperframes beats                                           # beat grid for the music track

# quality gates
hyperframes lint && hyperframes check
hyperframes snapshot --at 0,1.5,5,10,18,21
hyperframes preview                                         # Studio (human review)

# render
hyperframes render -o renders/out.mp4                       # MP4 (default quality: CRF 16)
hyperframes render --format mov -o overlay.mov              # ProRes 4444 with alpha
hyperframes render --variables '{"handle":"@me"}' --strict-variables
hyperframes render --batch rows.json --output "renders/{index}.mp4" --strict-variables
hyperframes lambda render-batch . --batch rows.jsonl --width 1080 --height 1920 --max-concurrent 10
```

---

## 7. Files in this workspace

| Path | What |
|---|---|
| `GitHub Release `renders-2026-10-07` → viral-short.mp4` | **main demo** (23 s, 1080×1920, with audio) |
| `GitHub Release `renders-2026-10-07` → variants/variant-*.mp4` | batch-rendered brand variants |
| `reels-studio/archive/viral-short/index.html` | the composition (9 scenes, captions, 35 audio clips, 5 variables) |
| `reels-studio/archive/viral-short/batch-rows.json` | batch input |
| `reels-studio/archive/viral-short/tools/synth_audio.py` | seeded music + SFX synthesiser (royalty-free) |
| `reels-studio/archive/viral-short/tools/align_captions.py` | whisper → display-script word alignment |
| `reels-studio/archive/viral-short/assets/` | voice-over (script, raw and mastered), captions JSON (from the whisper transcript), music/SFX, OFL fonts |
| `reels-studio/archive/viral-short/snapshots/contact-sheet.jpg` | proof-frame contact sheet from `hyperframes snapshot` |
| `(removed: stock smoke test, regenerable with `hyperframes init --example vignelli`)` | first smoke-test render of a stock example |
| `reels-studio/setup/env.sh` | the environment I used (telemetry off, cache dirs) |
| `reels-studio/setup/setup-sandbox.sh` | one-shot toolchain setup (Node 22, FFmpeg, Chrome libs, CLI, Kokoro, Chrome) for a fresh sandbox; `WITH_WHISPER=1` also runs the next script |
| `reels-studio/setup/setup-whisper.sh` | optional add-on: safe whisper.cpp build (`-j1`, `whisper-cli` target only) plus the `small.en` model, so `transcribe` never triggers the unbounded auto-build (bug #1) |
| *(not stored)* `hyperframes/` | the repo clone is ~139 MB / ~9k files, which exceeds this workspace's snapshot limit. Re-clone it outside the workspace with `git clone --depth 1 https://github.com/heygen-com/hyperframes /var/tmp/hf/hyperframes` |

---

## 8. Sources

- Repository, docs and skills: https://github.com/heygen-com/hyperframes (read locally at `5fad52f`); docs site https://hyperframes.heygen.com
- GitHub API stats (stars 57,784, forks 5,157, created 2026-03-10): https://api.github.com/repos/heygen-com/hyperframes
- Platform sizes, lengths and safe zones: https://www.bevyl.ai/tools/social-media-sizes · https://adaptlypost.com/blog/social-media-safe-zones-2026-complete-guide · https://picto.video/en/social-media-video-specs/
- YouTube "inauthentic content" update (15 Jul 2025): https://www.socialmediatoday.com/news/youtube-clarifies-monetization-update-inauthentic-repeated-content/752892/
- AI-content labelling across platforms: https://www.auditsocials.com/blog/cross-platform-ai-content-labeling-requirements-2026-meta-google-tiktok-youtube-comparison · https://www.auditsocials.com/blog/tiktok-ai-content-disclosure-rules-2026
- Early community feedback: r/heygen launch thread, Apr 2026: https://www.reddit.com/r/heygen/comments/1snl38i/
