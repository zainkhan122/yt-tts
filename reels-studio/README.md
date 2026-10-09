# Reels Studio: professional vertical-video generator (HyperFrames + free tools)

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
      ──► QA (format, fps, loudness, peak) ──► renders/<id>/ ──► publish (GitHub Release) ──► sync (git)
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
| Finished videos | **GitHub Releases**: `<id>.mp4` + `<id>-kit.zip` per video (`python3 reels.py renders` lists them) | ✅ Releases; local `renders/` is scratch (git-ignored) |
| Capture packs (screens, official clips, region map) | GitHub Release `capture-packs` (`tools/capture_store.py`) | ✅ pulled on demand by cloud jobs |
| Rendering | **GitHub Actions** `render.yml`: one 4-vCPU runner per video, up to 5 in parallel (free for this public repo) | ✅ |
| Toolchain (Node, HyperFrames CLI, FFmpeg, Chrome, Kokoro, whisper) | `/usr/local`, `~/.cache/hyperframes` | ❌ `bootstrap.sh` reinstalls it |
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
python3 reels.py cloud <id> [<id> ...] --wait               # RENDER IN THE CLOUD: up to 5 videos in parallel -> Release
python3 reels.py renders                                   # all published videos + post kits (download links)
python3 reels.py make  briefs/<id>.json --quality looks --crf 23   # local render (sandbox: ~17-27 min per video)
python3 reels.py make  briefs/x.json --no-render           # fast iteration: build + lint + check only
python3 reels.py publish renders/<id>                      # upload a LOCAL render: <id>.mp4 + <id>-kit.zip
python3 tools/capture_store.py push <id> | pull <id>       # capture packs <-> Release 'capture-packs'
python3 reels.py sync -m "new briefs"                      # commit + push reels-studio/ (SSOT)
python3 reels.py templates | new tool-spotlight briefs/<id>.json
python3 tools/fetch_worldbank.py NY.GDP.PCAP.CD PAK,IND,BGD 1990 2025   # real data + editor fact sheet
python3 tools/tts_roundtrip.py --suite                     # test any voice/language with whisper
```

**Token safety:** the token lives in `~/.config/reels-studio/gh_token` (outside the repo, chmod 600). `sync` and `publish` read it at call time through a one-shot credential helper, so it never reaches `.git/config`, logs or the repo. `sync` also **aborts if any staged change contains a token-like string**.
Use a fine-grained token limited to this repo, with **Contents, Workflows and Actions: read & write** (cloud render). Rotate it if it was ever pasted somewhere public.

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

### Own-voice mode (recommended for monetized channels and for Urdu narration)

Set `"voice": "files"` and record one file per spoken line into `briefs/vo/<segment-id>.wav` (or `.mp3` or `.m4a`).
Segment ids are printed in `renders/<id>/manifest.json` → `timing`.
Phone recordings are fine: silence is trimmed automatically and loudness is normalised.
Everything else stays automatic, including timing, captions, music ducking and the render.

## Quality gates (a video ships only if all pass)

1. `hyperframes lint`: 0 errors.
2. `hyperframes check`: runtime, layout overlap, motion and contrast. It caught real bugs while building these templates: colliding chart labels, 2:1 contrast on the answer badges, and invisible outline text.
3. whisper.cpp intelligibility: the character-level match of what whisper heard vs the script. It catches TTS mispronunciations.
4. Output QA: 1080×1920, 30 fps, H.264 + AAC, duration matches, −14 ±1 LUFS, peak ≤ −1 dBFS.
5. **The human checklist in `post.md`**: facts against sources, sound-off hook, and "is this different from my last 5 uploads?". The pipeline renders; you edit.

## Using it inside this AI agent (Arena)

Ask in plain language. For example:
- "Make a quiz video about world capitals for @quiz.minute, 3 questions, midnight style."
- "Make a data race of internet users (% of population) for Pakistan, India and Bangladesh since 2000."
- "Plan 7 videos for an English-learning channel this week and render them."

The agent:
1. researches and verifies the facts with sources;
2. writes the brief;
3. runs `reels.py make`;
4. looks at the contact sheet and fixes what it sees;
5. hands you the MP4 and `post.md`.

Limits of this sandbox:
- about 6–8 minutes per 35–45 s video on 2 vCPU;
- sandboxes reset without warning. `bootstrap.sh` restores the toolchain in about 3 min (measured: 189 s after a real reset), while files persist;
- the workspace holds about 128 MB. Videos go to GitHub Releases (`reels.py publish`), not the workspace;
- **2 GB RAM: run one heavy job at a time.** A render (Chrome + FFmpeg) needs about 1.2 GB. Never load Kokoro or whisper in parallel; doing so once got the render OOM-killed. The pipeline frees the TTS model before rendering for this reason.

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
