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
| 6 | **Daily engine: 3–5 shorts/day** | 3–5 videos/day | **next** |
| 7 | optional: official upload APIs, cloud render, Urdu/Hindi line | | |

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
