> **Operating decision — 2026-10-11:** the interactive Arena agent leads research, writing, assets, editing and QA. Optional producer/critic automation is **paused by the owner and NOT qualified for activation**. Existing deterministic rendering, approved-queue posting, metadata and duplicate protections remain intact. See `config/operating-policy.json` and `RESUME.md`.

> **Resume / current authority:** read [`CURRENT_STATE.md`](CURRENT_STATE.md) and [`RESUME.md`](RESUME.md) before running commands. Historical phase notes are not current activation flags.

# Reels Studio: professional vertical-video generator (HyperFrames + free tools)

> **Resume / authority:** start with [`RESUME.md`](RESUME.md) and [`CURRENT_STATE.md`](CURRENT_STATE.md). The OPTIONAL free-model producer/critic is a non-publishing lab, not an active daily production engine. See [`agent/ACCEPTANCE.md`](agent/ACCEPTANCE.md) and [`research/pilots/STATUS.md`](research/pilots/STATUS.md).

Lives in **github.com/zainkhan122/yt-tts → `reels-studio/`**, the single source of truth (SSOT).
It turns a small **brief (JSON)** into an **upload-ready 1080×1920 video** plus a post kit, using only free tools:
- HyperFrames for rendering;
- Chatterbox (approved channel voice, cloned from a Kokoro reference) for TTS; Kokoro for previews;
- whisper.cpp for QA;
- FFmpeg;
- numpy-generated music.

```
radar ──► brief.json ──► voice (Chatterbox channel voice or YOUR recordings) ──► exact line timing ──► word timings
      ──► whisper.cpp intelligibility QA ──► music + SFX (seeded, royalty-free), loudnorm −14 LUFS
      ──► HyperFrames project (template) ──► lint ──► check (layout/contrast/runtime) ──► render
      ──► QA (format, fps, loudness, peak) ──► one-day Actions artifact ──► download to renders/<id>/
      ──► optional, explicit publish (GitHub Release) ──► sync (git)
```

**Strategy (formats, hooks, SEO per platform, cadence):** [`PLAYBOOK.md`](PLAYBOOK.md). **How it works end to end:** [`PIPELINE.md`](PIPELINE.md) covers topic selection, research, voice, how videos are made, QA, publishing and the tools inventory. **Where we are:** [`PHASES.md`](PHASES.md).

## One-click restore (after any sandbox reset)

```bash
bash ~/yt-tts/reels-studio/bootstrap.sh
# workspace wiped completely?  This rebuilds everything from GitHub:
curl -fsSL https://raw.githubusercontent.com/zainkhan122/yt-tts/main/reels-studio/bootstrap.sh | bash
```

Idempotent: it repairs git (snapshots drop `.git/config`), pulls the latest SSOT, installs only what is missing, then runs `reels.py doctor`.
- Takes about 2.5 min from scratch, and seconds when everything is already installed.
- Only `reels-studio/` is downloaded (sparse + blobless clone), never the other ~7 GB in the repo.

## Where things live

| What | Where | Survives reset? |
|---|---|---|
| Code, templates, briefs, research, tracker | git: `reels-studio/` | ✅ GitHub = SSOT |
| Finished videos | Cloud renders are one-day **GitHub Actions artifacts**, downloaded into `renders/<id>/` by `reels.py cloud --wait`; the render workflow never creates a video Release | ✅ local workspace; permanent Release is a separate owner action |
| Capture packs (screens, official clips, region map) | GitHub Release `capture-packs` (`tools/capture_store.py`); render pulls are read-only and hash-verified | ✅ pulled on demand by plan/render jobs |
| Rendering | **GitHub Actions** `render.yml`: owner-selected matrix size, one Ubuntu 24.04 runner (4 vCPU / 16 GiB) per brief, hard maximum 10; reserve/finalize attempt ledger | ✅ one-day artifact only; no scheduled or automatic batch |
| Toolchain (Node, HyperFrames CLI, FFmpeg, Chrome, pinned Chatterbox model `5bb1f6e`, pinned Whisper) | `/usr/local`, `~/.cache/hyperframes`, `~/.cache/huggingface` | ❌ `bootstrap.sh` restores the sandbox subset; `cloud/setup-render.sh` adds the production voice/QA stack |
| Intermediates (voice, mix, HTML project) | `/var/tmp/reels/<id>/` | ❌ regenerated per job |
| GitHub token | `~/.config/reels-studio/gh_token` (chmod 600, **outside the git tree**), or env `GH_TOKEN` | ✅ persists in the private workspace; **never committed** (sync blocks token patterns) |

## Brand + accounts
`brand/` holds the logo (vector + PNG), avatar, banners and copy-paste profile text for every platform. Open `brand/brand-kit.html`, or download the zip from Release `brand`. Rebuild after editing `brand/profiles.json`: `python3 tools/brand_kit.py --publish`.

## Commands

```bash
python3 reels.py doctor                                    # all green = ready
python3 reels.py radar --days 14 --brief                   # trending AI repos/models/apps -> research/radar/ (+ draft brief)
python3 reels.py capture <id> --url <site-or-repo>         # screenshots, official demo media, region map, facts -> captures/<id>/
python3 reels.py social --account <tiktok/yt url> --top 2  # competitors' scripts + stats -> research/social/ (lessons digest)
python3 tools/idea_feed.py --days 7                        # what the 21 watchlist channels cover (consensus topics) -> backlog
python3 tools/channel_study.py report                      # benchmark-account study (stats, transcripts, visual)
python3 tools/seo_pack.py briefs/<id>.json                 # validated copy for YouTube/TikTok/IG/FB/X -> renders/<id>/seo.md
REELS_VOICE_PREVIEW=kokoro python3 reels.py make briefs/<id>.json --no-render  # sandbox: Kokoro layout/lint/check preview; no final video
python3 reels.py cloud <id> [<id2> ...] \
  --production-receipt reels-studio/research/production/receipts/<batch>.json \
  --quality looks --crf 23 --wait                          # manual GitHub render -> download one-day artifacts; no Release
python3 reels.py renders                                    # list permanently published videos + post kits (Release links)
python3 reels.py publish renders/<id>                       # separate permanent Release action; only when explicitly authorized
python3 tools/capture_store.py pull <id>                    # read-only pull; does not create the capture-packs Release
python3 tools/capture_store.py push <id>                    # explicit capture-pack Release write
python3 reels.py sync -m "new briefs"                       # commit + push reels-studio/; explicit write
python3 reels.py templates | new tool-spotlight briefs/<id>.json
python3 tools/fetch_worldbank.py NY.GDP.PCAP.CD PAK,IND,BGD 1990 2025   # real data + editor fact sheet
python3 tools/tts_roundtrip.py --suite                     # test any voice/language with whisper
```

**Token safety:** the token lives in `~/.config/reels-studio/gh_token` (outside the repo, chmod 600). `sync` and `publish` read it at call time through a one-shot credential helper, so it never reaches `.git/config`, logs or the repo. `sync` also **aborts if any staged change contains a token-like string**.
Use a fine-grained local CLI token limited to this repo: **Actions read/write** for manual dispatch, logs and artifact cleanup; **Contents read** for capture-pack downloads; add **Contents write** only for explicitly authorized sync/publish actions. In `render.yml`, permissions are per job: matrix renderers get `contents: read`; plan/finalizer get `contents: write` only to reserve/finalize the attempt registry. That workflow never calls Buffer or creates a video Release. Rotate the token if it was ever pasted somewhere public.

## Research inside the repo

- [`research/ai-tools-niche.md`](research/ai-tools-niche.md): AI-tools niche with real RPM figures, 10 accounts to learn from, the strategy and a weekly plan.
- [`research/VIRAL-SYSTEM-REPORT.md`](research/VIRAL-SYSTEM-REPORT.md): what makes short videos work in 2026, platform rules and money from Pakistan.
- [`research/HyperFrames-Viral-Video-Guide.md`](research/HyperFrames-Viral-Video-Guide.md): HyperFrames deep dive.
- `research/radar/`: dated trend snapshots from `reels.py radar`. Flagged items (ToS bypass, NSFW, bot evasion) are never put into briefs.

## Templates (each = `template.py` + `scene.html/css/js` on top of `templates/_base`)

| Template | Format | Best niches | Viral mechanics built in |
|---|---|---|---|
| `quiz` | hook → N questions (read-along, options, 3 s countdown with ticks, reveal + fact) → score CTA | trivia, geography, science, exam prep, language quizzes | play-along game, comment-your-score, rewatch on wrong answers |
| `data-race` | real time-series → racing line chart + live leaderboard → final ranking | economy, countries, sport stats, tech adoption, prices | "guess who wins", lead changes as payoffs, screenshot-worthy ranking |
| `ranked-list` | countdown #N → #1 with counted stat bars, filling leaderboard, suspense before #1 | tools/apps, records, products, "top 5" facts | open loop ("wait for #1"), escalating reveals, opinion CTA |
| `say-this` | wrong phrase (struck) → right phrase → spoken explanation + **Urdu on screen** | spoken English for Urdu/Hindi speakers, tips, myth vs fact | instant usefulness (saves/sends), daily series, bilingual reach |

Shared by all templates:
- hook slam with read-along text;
- karaoke captions;
- progress bar and watermark;
- follow end-card with a "press";
- 4 style presets (`neon`, `editorial`, `midnight`, `sunset`) plus brand colours;
- automatic text fitting;
- deterministic motion.

## Brief format

```jsonc
{
  "id": "quiz-geography-01",            // output folder name (unique per video)
  "template": "quiz",
  "title": "...", "niche": "...",
  "lang": "en-us",                      // en-us | en-gb | hi | es | fr-fr | it | pt-br | ja | zh  (Kokoro)
  "voice": "af_bella",                  // any Kokoro voice, or "files" for your own recordings
  "speed": 1.05,
  "style": "midnight",                  // neon | editorial | midnight | sunset
  "brand": {"handle": "@you", "name": "Your Channel", "tagline": "...", "accent": "#FFD23F", "accent2": "#38BDF8"},
  "content": { ... template-specific, see the docstring at the top of templates/<name>/template.py ... },
  "post": {"titles": [...], "caption": "...", "hashtags": [...], "pinned_comment": "..."},
  "sources": ["every fact needs a source line"],
  "music": {"bpm": 104, "key": 2}       // optional overrides; the seed is derived from the id
}
```

### Mixed languages / experimental Urdu TTS

Any segment can override `voice`, `lang` and `speed`. `say-this` uses this when the brief has
`"urdu_voice": {"voice": "hf_alpha"}` and each pair has a `"say_ur"` line: English phrases are spoken by an English voice, and explanations are spoken in Urdu.
Urdu uses espeak-ng's `ur` phonemizer with a Hindi Kokoro voice. whisper heard 88% of the demo's Urdu correctly, with an audible accent.
Check any voice and language yourself with `python3 tools/tts_roundtrip.py --suite`.

### Own-voice mode (where the active production profile permits it)

Set `"voice": "files"` and record one file per spoken line into `briefs/vo/<segment-id>.wav` (or `.mp3` or `.m4a`).
Segment ids are printed in `renders/<id>/manifest.json` → `timing`.
Phone recordings are fine: silence is trimmed automatically and loudness is normalised.
The current English final-render receipt gate specifically approves Chatterbox Option-3; own recordings cannot bypass that VOICE gate. The pipeline's file-recording mode remains available for local/layout use and any separately approved profile.

## Quality gates (a video ships only if all pass)

1. `hyperframes lint`: 0 errors.
2. `hyperframes check`: runtime, layout overlap, motion and contrast. It caught real bugs while building these templates: colliding chart labels, 2:1 contrast on the answer badges, and invisible outline text.
3. Whisper/TTS QA: every spoken chunk must match at ≥92%; retries use distinct seeds and are bounded to four (channel default: two). English final voiceover must reach ≥95% overall Whisper character match. Missing/disabled Whisper QA or a low score aborts the final render.
4. Output QA: 1080×1920, 30 fps, H.264 + AAC, duration matches, −14 ±1 LUFS, peak ≤ −1 dBFS; every measured check must pass.
5. **The human checklist in `post.md`**: facts against sources, sound-off hook, and "is this different from my last 5 uploads?". The pipeline renders; you edit.

## Using it inside this AI agent (Arena)

Ask in plain language. For example:
- "Make a quiz video about world capitals for @quiz.minute, 3 questions, midnight style."
- "Make a data race of internet users (% of population) for Pakistan, India and Bangladesh since 2000."
- "Research a proposed batch, prepare the briefs and receipt, and wait for my approval before rendering."

The agent:
1. discovers and scores topics; researches the claims and records sources;
2. prepares the brief, exact spoken script, approved voice plan, assets and fresh Buffer Insights evidence;
3. runs local syntax/tests and optional `--no-render` layout checks in the sandbox;
4. proposes the batch size; only after owner approval does the manual GitHub workflow render one matrix job per brief;
5. downloads the short-lived artifacts for contact-sheet/cover review and hands over the approved MP4 and `post.md`.

Sessions start cheap and stay small: the agent reads `.context/PACK.md`
(≤8 KB, built by `tools/context/ctxpack.py` from the same source as
`CURRENT_STATE.md`) instead of re-reading the whole doc set, retrieves with
`tools/context/ctxgrep.py`, and runs noisy commands through
`tools/context/quiet.py`. Measured re-entry cost: ~1.1k tokens instead of ~44k.
Rules: [`CONTEXT-PROTOCOL.md`](CONTEXT-PROTOCOL.md).

Execution limits and handoff:
- **Sandbox (control plane):** use for research/briefs, production-receipt preparation, code review, syntax/unit tests, checksum checks, and optional `--no-render` layout/lint checks. Do not spend this constrained workspace on the approved Chatterbox + Whisper + HyperFrames final batch.
- **GitHub render plane:** the manual `render.yml` workflow runs one Ubuntu 24.04 matrix job per owner-approved brief (4 vCPU / 16 GiB each, hard maximum 10), performs the final TTS/Whisper/MP4 work, and stores each result as a one-day artifact.
- No render is dispatched until the batch size is explicitly confirmed and the committed receipt passes DISCOVER → SELECT ≥60 → RESEARCH → SCRIPT → VOICE → ASSETS, fresh Buffer Insights, exact word count, and capture-byte verification.
- Sandboxes can reset without warning; `bootstrap.sh` restores the toolchain. The workspace snapshot is capped near 128 MB. `reels.py cloud --wait` downloads artifacts for review; a permanent Release, git push, Buffer schedule/post, or platform upload is a separate owner-authorized action.

## Adding a template

Create `templates/<name>/` with these files:
- `template.py`: `DEFAULTS`, plus `segments(brief)`, `events(brief, T, D)`, `sfx(...)`, `music(...)` and an optional `data(...)`.
- `scene.html` / `scene.css`: absolute layout on the 1080×1920 canvas. Keep critical content inside x 90–990 and y 220–1600.
- `scene.js`: `async function buildScene(tl, V)`. Use `V.show`, `V.karaoke`, `V.fit`, `V.countText`, `V.endCard` and friends from `_base/base.js`.

Rules that keep renders deterministic:
- no `Math.random` (use `V.rnd`), no `Date`, no network calls, no CSS transitions;
- use `fromTo` with `immediateRender: false` for every tween after the first;
- don't put CSS transforms on animated nodes.

## Licences of what's inside

| Component | Licence |
|---|---|
| HyperFrames | Apache-2.0 |
| Kokoro-82M | Apache-2.0 |
| whisper.cpp | MIT |
| FFmpeg | LGPL/GPL |
| GSAP | free standard licence, including commercial use |
| Fonts (Anton, Inter, JetBrains Mono, Noto Nastaliq Urdu) | OFL |
| Music and SFX | generated by `lib/synth.py`, so you own them |
| Data in the demos | World Bank (CC BY 4.0), GitHub API (public metadata) |

## Paced publishing — expanded 2026-10-10

- One Buffer key: YouTube Shorts, Instagram, Facebook. **Facebook is included** by owner instruction, with caption disclosure until a native AI flag is available.
- Global English / US-led audience: America/New_York calendars, explicit UTC scheduled timestamps. Baseline 3 shorts/day, optional 4–5; max 8 pending/channel, quota/backoff and durable duplicate protection. Existing Buffer UI slots are not overwritten.
- Direct long-form YouTube uploader: private-first resumable uploads, encrypted checkpoints, thumbnail/metadata/playlist gates, max one upload/run and three weekly publication lanes. Also enriches Buffer Shorts with backend tags/playlists.
- Bold thumbnail generator + actual 250px preview, automatic readability/contrast checks and mandatory agent visual review.
- **Buffer is now live:** Claude pilot sent on all three; remaining two scheduled. Five new Oct 10 Shorts completed. Google OAuth is connected and Shorts tags/playlists are live-verified; the seven-day grant needs renewal after checking app publishing status. Long uploads remain pilot-gated.
- Read-only: `python3 reels.py post --dry-run` and `python3 reels.py youtube --mode dry-run`. No heavy TTS bootstrap needed.
- Timing research + full calendar: [`strategy-2026-10-10.md`](research/publishing/strategy-2026-10-10.md). One-time connection: [`google-connection.md`](research/publishing/google-connection.md).
- Operations: [`tools/post/README.md`](tools/post/README.md), [`tools/youtube/README.md`](tools/youtube/README.md). Storage: [`tools/maintenance/README.md`](tools/maintenance/README.md).


### 10 Oct production / first live delivery

- First live post: Claude free Docs/Slides/Design, verified sent on YT/IG/FB.
- Corrected video-tools list + ai-newtab accepted into today's spaced Buffer schedule (six platform posts, not a bulk immediate publish).
- Five NEW Option-3 Shorts, all QA 7/7: Haiku 5.5, Gemini agent, Mosa, Pomelli and Whistle. Release: https://github.com/zainkhan122/yt-tts/releases/tag/renders-2026-10-10
- New batch is enqueued HELD, not secretly added to the already-full daily calendar.
- Evidence / delivery index: `research/batches/2026-10-10-delivery.json`, `research/publishing/first-live-pilot-2026-10-10.json`, `research/publishing/today-schedules-2026-10-10.json`.

## OPTIONAL producer–critic lab — not activated

The optional free-only OpenRouter system is a **shadow comparison lab**, not the daily production engine. It has versioned evidence/tools/prompts, an independent critic, locked Option-3 rendering and hard gates. Current measured outcome is **OFF / UNQUALIFIED**: drafts have factual/editorial weaknesses, the critic is rate-limited, and audio access has an unmet balance requirement. No candidate reached full paired video/audio comparison or social publication.

Read [`research/pilots/PILOT_REPORT.md`](research/pilots/PILOT_REPORT.md), [`agent/ACCEPTANCE.md`](agent/ACCEPTANCE.md) and [`docs/SECURITY-BOUNDARIES.md`](docs/SECURITY-BOUNDARIES.md). Source/checkpoints are preserved for exact operational resumption; model scores never enable publishing.
