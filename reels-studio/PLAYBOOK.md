# Reels Studio PLAYBOOK: the end-to-end plan

How we go from "a new tool appeared" to "a highly professional video posted on YouTube, TikTok, Instagram, Facebook and X". Built on evidence:
- **270 videos** (30 each) from 9 benchmark TikTok accounts, with transcripts and frame-level visual analysis;
- an 11-video pilot scan;
- a 32-source registry (TikTok, YouTube, web feeds);
- 2026 platform SEO rules.

Technical details (tools, commands) live in [`PIPELINE.md`](PIPELINE.md). Session plan: [`PHASES.md`](PHASES.md). Raw evidence:
- [`research/social/study-2026-10-07-findings.md`](research/social/study-2026-10-07-findings.md) (analysis)
- [`research/social/study-2026-10-07.md`](research/social/study-2026-10-07.md)
- [`research/social/videos-2026-10-07.csv`](research/social/videos-2026-10-07.csv)

---

## 0. What "winning" means (targets per video)

| Signal | Why it matters | Target (from benchmark medians) |
|---|---|---|
| Viewed vs swiped / 3-s hold | first gate of every feed | ≥ 70% |
| Avg % watched | retention = distribution | ≥ 60% (spotlights ≤ 42 s make this realistic) |
| **Saves per 1k views** | the #1 signal in this niche. Repo/tool explainers are bookmark content | ≥ 30 (benchmarks: dr_cintas 42, github.awesome 41, github.signals 33) |
| **Shares/sends per 1k** | Instagram's top-3 ranking signal ("sends") | ≥ 5 (benchmarks 6–7) |
| Comments per 1k | social proof + reach; only accounts with a keyword CTA get > 3 | ≥ 3 with the keyword CTA |

## 1. What the benchmark accounts taught us

1. **Two winning production styles:**
   - **A, faceless repo-scroll:** github.awesome and github.signals. The real README scrolls in a browser frame, with bold ALL-CAPS 2–4-word captions and one yellow keyword. It has almost no hard cuts (0–1.5 per 10 s) but constant motion. **Highest saves.** This is our core: it needs no face, and our capture kit produces exactly this material.
   - **B, face + screen:** ai_vanta_ai, dr_cintas, beyondtahir. The creator is on camera, with the screen or B-roll above, fast cuts (4–7 per 10 s) and big count-up numbers. It reaches further and drives more comments, but needs a human.
     - Our substitute: motion graphics + official demo clips + count-ups.
     - Later, optionally, the user's own voice or face for trust.
2. **Hooks that win** state a payoff, a number or stakes in the first sentence:
   - "NO GPU AI MODEL" + "744B parameters" count-up (774K);
   - "this GitHub project could become extremely useful if…" (378K);
   - "[Tool] transforms a single illustration into an animated character" (59K).
   
   Context-first and mid-tutorial openings lose.
3. **Name reveal by ~7 s, then one new feature or visual every 4–5 s.**
4. **Pace:** the niche norm is ~175–190 wpm (194 transcripts: top 183 vs bottom 189, so pace is table stakes, not an edge). Up to 226–243 wpm for rapid lists.
5. **CTA economics:**
   - CTAs don't change views (36% of top and bottom videos have one). They change comments.
   - **What lifts views:** paid-vs-free contrast (14% vs 7%), a "someone just built" story opener (14% vs 7%), and a number in the first line (29% vs 22%).
   - A comment-keyword CTA gives 8–10× more comments.
   - Saves come from "bookmark-worthy" value: lists, install steps, free alternatives.
   - Shares come from "send this to someone who…" relevance.
6. **South Asia signal:** @beyondtahir speaks Hindi/Urdu, is personality-led and gets the highest engagement in the set (median 17.2K views, 5.1 comments/1k). An Urdu/Hindi version line is a real opportunity.
7. **What we refuse even though it gets views:**
   - movie/TV clips (ai_vanta_ai used Stranger Things);
   - piracy roundups;
   - "free API keys" DM bait;
   - fake "I'll DM you" promises.
   
   These risk strikes, demonetization and trust.

## 2. Content engine: where every video idea comes from

```
sources (32: TikTok, YouTube, web feeds) ──► idea_feed (daily, 2 min) ──► consensus topics (≥2 channels in 7 days)
GitHub/HF radar (stars/day) ───────────────┘                                   │
                                                  verify on primary sources ◄──┘
                                                  score (rubric ≥ 60) ──► topics/backlog.csv ──► today's 1–2 videos
```

- **Ride the wave (the user's rule):** when watchlist channels converge on a tool, we cover it **within 24–72 h** to sit in the same search and recommendation cluster. Our video must still be **our own research + our own angle** (the honest catch, a real demo, a comparison). Same topic, not the same video.
- **Original picks:** the radar finds repos before the watchlist does (stars/day). Roughly 1 in 3 videos should be "first to cover".
- **Add sources any time:** `python3 tools/sources.py add <url>` (verified on add). Every scan is saved to `research/sources/posts.csv` (git-tracked history). **Daily:** `python3 tools/idea_feed.py`. **Weekly:** `radar` + `channel_study` on 3 new accounts. **Monthly:** re-study the benchmark accounts.

## 3. Formats (what we produce)

| Format | Length | Style | Beat sheet | Cadence |
|---|---|---|---|---|
| **F1 Repo Drop** | 22–35 s | A: README scroll + kinetic captions + demo media | hook (payoff) → name + what it does → 2–3 features over scroll/zoom → install line → value close + CTA | daily |
| **F2 Tool Spotlight** | 35–42 s | A+: official demo clip first, then page with cursor/zoom, steps, terminal, verdict | hook (most striking visual) → proof montage → reveal + stars → how (3–5 steps) → the catch → value close + CTA | 3×/week |
| **F3 Weekly Top 5** | 45–60 s | ranked list with live stars | "5 AI repos exploding this week" countdown, open loop to #1 | weekly |
| **F4 Urdu/Hindi cut** (later) | as source | same visuals, Urdu/Hindi voice | best English performers re-voiced (user's voice preferred) | weekly |

## 4. Script system

**Story spine** (from the 774K-view benchmark; copy the structure, never the words):
1. impossible claim with a number;
2. who did it;
3. status quo / antagonist ("you'd think you need a $2,000 GPU…");
4. name reveal (~7 s, ≤ 17 s);
5. mechanism in ONE sentence;
6. practical payoff;
7. CTA.

**Hook formulas** (pick one, ≤ 12 words, keyword spoken within 3 s):
- **"Someone just…" impossible + number:** "Someone just ran a 744-billion-parameter model on a laptop with no GPU." (774K)
- **Unexpected maker + free vs paid incumbent:** "A geography professor built a free tool that replaces a $150/month app." (255K)
- **Number shock:** "This AI model has 744 billion parameters and needs no GPU."
- **Transformation:** "[Tool] turns [input] into [impressive output]."
- **Stakes / scenario:** "If [problem], this free GitHub project fixes it."
- **Replace-paid:** "Stop paying for [paid tool]. This open-source one does it free."
- **Proof-first:** "An AI agent built this." (over the demo clip)
- **Countdown promise:** "5 AI repos that exploded this week. Number one is wild."
- ✗ **Never:** "leaked"/sketchy framing (14 views), or starting mid-tutorial.

**Retention devices** (one every 4–5 s):
- count-up numbers;
- zoom to a real page element;
- cursor click;
- clip cut;
- step chip pop;
- open loop ("wait for the catch", "number one").

**Our differentiator line:** one honest verdict ("The catch: …"). It also drives likes (opinion lines scored 107 likes/1k).

**Close + CTA stack (last 5 s):**
1. value close ("free and open source");
2. **save prompt** ("save this for later");
3. **comment keyword** ("comment MOD and I'll pin the link");
4. follow.

Never promise DMs we can't send.

**Rules:**
- first sentence ≤ 12 words; sentences ≤ 18 words;
- ≤ 4 caption words on screen;
- brand names get a `say` pronunciation;
- every claim is in the fact sheet.

## 5. Voice and audio

- **Channel voice (user's choice, 2026-10-08): Kokoro `am_michael` ×1.15, no voice FX** (plain Kokoro + loudness normalisation; record: `research/voice-decision.md`). About 150 wpm, so scripts for a 35–45 s video are about 90–105 words.
  - History: af_heart D-hype was approved and used for the first render of video #1; the DSP "maxhype" was rejected as robotic (UTMOS 3.68).
  - Measured free-engine alternatives (Chatterbox, Orpheus, Edge, Qwen3): `research/voice-decision.md`.
  - Script energy still matters: an exclamation-led hook and payoff, rhetorical questions, short punchy lines, honest facts.
- **Mix:** VO at −14 LUFS integrated, peak ≤ −1 dBFS. Our own generated music sits under the voice. SFX:
  - whoosh on transitions;
  - click on cursor taps;
  - key-taps on terminal typing;
  - riser before reveals;
  - "pop" on step chips.
- **Own-voice mode** is available any time (phone recordings are fine). It's the best path for trust and for the Urdu/Hindi line.

## 6. Production: the "highest professional touch" spec

**Brand kit** (`config/channel.json`): 2 accent colours, Inter/Anton fonts, a small logo bug, an end card.

**Caption style (from the winners):**
- ALL CAPS, 2–4 words, centred in the upper-middle safe zone;
- white with a dark stroke;
- **the keyword highlighted in yellow**;
- synced word by word to the voice.

**Scene library** (the `tool-spotlight` + `repo-drop` templates, Phase 3):

| Scene | Look | Source |
|---|---|---|
| Browser frame over wallpaper | dark-mode browser with traffic lights + URL bar, page **scrolls smoothly** (README) | `desktop-full.jpg` capture |
| Camera move to region | eased zoom/pan to a real element (Star button, install block, demo GIF) | capture region map |
| Cursor + click | animated cursor glides along a curve, click ripple + SFX, button state change | region map |
| Count-up number | huge animated number (stars, params, downloads) with label | GitHub/HF API facts |
| Official demo clip | full-bleed with blurred fill, or a framed card; label chips | makers' media |
| Split screen | demo clip top / repo page bottom (Style-B energy without a face) | clip + capture |
| Terminal typing | install commands typed live with key-tap SFX | README |
| Logo reveal | official logo/og-image punch-in for the name reveal | capture |
| Verdict card | ✅ pros / ⚠ catches | fact sheet |
| End card | follow + keyword CTA + save prompt | brand kit |

**Motion and layout rules:**
- something moves at all times;
- Repo Drops use continuous camera moves;
- Spotlights cut every 1.5–3 s;
- **safe zones:** top 220 px, bottom 380 px, right 120 px are kept free of key text;
- the cover frame (frame 0) shows the hook text + the most striking visual.

**Built (2026-10-08): `templates/repo-spotlight` (F1) + `templates/tool-spotlight` (F2)** on one shared engine `templates/_spotlight/`:
- **Scene types:** clip (official demo, blurred fill + card, hook headline), clip-montage (word-anchored cuts + label chips, whip), page (browser frame, camera to regions, cursor click + button state, stat count-up), scroll (README camera with highlight boxes + chips), steps (lit as spoken, optional figure), terminal (typed live), verdict (catches/pros as said), stat, image (Ken Burns), endcard (question + keyword chip + follow press).
- **Layout bands:** heading 240–420 · media 430–1160 · captions centred at 1330 · bottom 380 px free. Captions sit *below* the media band (not upper-middle) because the media occupies the middle.
- **Text:** `{GTA V|GTA Five}` shows "GTA V" but speaks "GTA Five" (channel lexicon applies too); `*word*` in a heading = yellow.
- **Editing rules in code:** every event is anchored to the real voice words; montage cuts never outlive their shot; a montage continues where the previous clip of the same source stopped; frame 0 shows headline + sub (cover).
- **Fact gate worked:** re-verifying video #1 on render day caught 2 outdated claims (stars passed 5k; the repo's rules changed from "single-player only" to "any game you own, no online anti-cheat"). Keep `verify_before_render` mandatory.

**AI labels:** if a video ever uses AI-generated realistic footage, apply the platform's AI label (TikTok shows "AI-generated", as dr_cintas does). Our motion graphics + TTS narration don't require it.

## 7. Assets policy

- ✅ Our own captures of public pages.
- ✅ The makers' official demo media and logos (credited, identification use).
- ✅ Real outputs from running the tool.
- ✅ Our own music, SFX and graphics.
- ❌ Clips from other creators.
- ❌ Movie, TV or sports footage.
- ❌ Music we don't own.
- ❌ Assets the maker explicitly reserved.

## 8. QA gates (automatic + agent review)

- lint 0 errors;
- `check` (layout, contrast, runtime);
- whisper intelligibility ≥ 95%;
- 1080×1920 / 30 fps / H.264 + AAC / −14 LUFS;
- contact-sheet review by eye;
- fact sheet refreshed the same day;
- risk gates clean;
- originality vs our last 5 videos.

**Automatic safeguards added 2026-10-08** (all found while making video #1):
- **Timing aligner:** each sentence break snaps to the pause nearest its syllable-expected position, with a proportional fallback. The old "largest gaps" method squeezed a whole sentence into 0.12 s with am_michael.
- **Caption guard:** a caption group can never stay stuck on screen.
- **Footage caps:** a clip or montage scene ends when its footage does (the next scene's visuals lead its voice), so footage never runs into a wrong shot. Montage cuts never outlive their shot, and the first cut continues where the previous clip stopped.
- **Montage label/voice gate:** a warning fires if a card's name is not spoken while that card is on screen.
- **Final loudness guard:** after the render, if the MP4 is off −14 LUFS by more than 0.5 dB, the audio alone is limited and normalised with the video stream copied. The renderer had shifted am_michael from −14.3 to −15.3 LUFS.
- **Footage truth:** shot boundaries come from frame-by-frame checks of the source (`teaser_shots` in the brief), not from scene-detect alone, which fire flicker fooled.

## 9. Packaging + SEO per platform

**Universal rule: triple keyword alignment.** The primary keyword (usually the tool name + what it does) is:
1. **spoken in the first 3–5 s**;
2. **on screen in the first 2–3 s**;
3. **in the first line of the caption/title**.

TikTok, YouTube and Instagram all index speech and on-screen text in 2026.

| Platform | Title / first line | Caption / description | Hashtags | Platform specifics |
|---|---|---|---|---|
| **YouTube Shorts** | ≤ 60 chars (100 max), **keyword in the first 3 words**, number if any | 2–3 keyword sentences (first 100 chars weigh most) + repo link + credit | **3–5 in the description** (first 3 show above the title), always incl. `#Shorts`. Never more than ~15 (they all get ignored) | backend tags 5–8 phrases (500 chars); upload our SRT; spoken keyword helps |
| **TikTok** | caption line 1 = keyword + hook | 100–300 chars, conversational, ends with a **question** (raises comments) | **3–5 specific** (one = exact keyword); no #fyp/#viral | on-screen keyword in 0–3 s; choose the cover frame; keep auto-captions on |
| **Instagram Reels** | line 1 = keyword-rich hook (IG search reads captions) | 2–3 keyword sentences; CTA "comment KEYWORD" | **max 5 (hard cap since Dec 2025)** | ranking = watch time, likes, **sends**; test hooks with **Trial Reels**; no TikTok watermark |
| **Facebook Reels** | keyword-first line | short description + question | 3–5 | native upload (no cross-platform watermark); originality matters (Meta 2025 rules) |
| **X** | 1 punchy line ≤ 280 chars with keyword + the repo link | (none) | 1–2 max | native video upload; burned-in captions (autoplay is muted); reply to self with credits |

Instagram, TikTok and YouTube rules come from current 2026 sources (see `research/ai-tools-niche.md`). The X and Facebook rows are standard practice, to be re-verified in Phase 4.

Each render's `post.md` will carry **one ready block per platform** (Phase 4: `tools/seo_pack.py`). It validates the limits automatically: char counts, the hashtag cap, keyword in the first line.

**Worked example (video #1, universal-modder):**
- YT title: "AI Mods Any PC Game: Minecraft Inside GTA V 🤯". Description: "Universal Modder is a free open-source plugin that lets Claude Code, Codex or Gemini mod PC games you own… github.com/rehan-remade/universal-modder" + `#Shorts #AItools #gaming`.
- TikTok: "AI mods PC games you own 🎮 Minecraft inside GTA V with Universal Modder. Which game would you mod first? #AItools #gaming #modding #ClaudeCode #opensource".
- IG: the same first line + "comment MOD for the link" + 5 tags max.
- X: "An AI coding agent put real Minecraft inside GTA V. Universal Modder (free, MIT) 👇 github.com/rehan-remade/universal-modder #AI".

## 10. Publishing workflow and cadence

- **Cadence target: 3–5 shorts/day.** Daily mix rule (owner, 2026-10-09): **max 1 × F1 Repo Drop per day**; at least 1 AI tool (F2 Tool Spotlight / ranked list) and 1 AI news or paid-to-free story; F3 Weekly Top 5 on Sundays. The day's shortlist goes to the owner for approval before production.
- **How 3–5/day is possible:**
  - **Cloud render on GitHub Actions** renders all of the day's videos **in parallel**. It's free for this public repo; GitHub's standard runner for public repos has 4 vCPU and 16 GB.
  - The sandbox renders only ~1 video per 10 min and resets between sessions, so it is used for drafts and previews only.
- **Daily agent session (~45–60 min):**
  1. bootstrap;
  2. `idea_feed` + radar;
  3. pick 3–5 topics (rubric);
  4. capture packs;
  5. write briefs + `seo_pack`;
  6. `--no-render` gates;
  7. push → dispatch cloud renders;
  8. review the contact sheets;
  9. post kits ready in Releases.
- **Requires:** the GitHub token's **Workflows: Read and write** and **Actions: Read and write** permissions. Tested on 2026-10-07: currently missing (HTTP 403).
- **Order:** TikTok + YouTube Shorts first (search indexing), then IG Reels (or a Trial Reel first), then FB and X. Always upload the clean MP4 natively; never repost a watermarked file.
- **First hour:** pin the link comment, reply to early comments (engagement velocity), and log the 24 h metrics in `tracker/content-tracker.csv`.
- **Posting times:** no data yet. Test 3 slots for 2 weeks and keep the best.

## 11. Learning loop

- **Weekly:** compare our videos vs benchmarks on 3-s hold, % watched, saves/1k, shares/1k and comments/1k, and adjust the hook type, length and CTA.
- **Monthly:** `channel_study` re-run (benchmarks + 3 new accounts) to update hook/pace/CTA rules. Retire formats that underperform 3 times in a row.

## 12. Build roadmap (one phase = one session)

| Phase | Build | Output |
|---|---|---|
| ✅ 1–2 | capture kit, social scan, pipeline doc, voice audition | done |
| ✅ 3 (this) | channel study (270 videos), watchlist, idea feed, this PLAYBOOK, platform SEO research | done |
| ✅ 4a | token persistence, 32-source registry + post history, energetic voice, channel handles, 3–5/day design | done |
| 4b | **templates**: `repo-drop` + `tool-spotlight` (scene library + winner caption style) | preview stills |
| 5 | **cloud render** (GitHub Actions matrix: N briefs in parallel → Releases) + **video #1** | ready-to-post MP4 + 5 platform blocks |
| 6 | **daily engine: 3–5 shorts/day** (idea feed → briefs → capture → cloud render → post kits); tracker | 3–5 videos/day |
| 7 | optional: official upload APIs (YouTube Data API, IG Graph API, TikTok Content Posting), GitHub Actions cloud render, Urdu/Hindi line | |

## 13. Risk register

| Risk | Mitigation |
|---|---|
| Copyright (clips, music) | asset policy §7; our own music/SFX; credit makers |
| Platform "reused/unoriginal content" rules | our research + angle + honest verdict; never re-upload; rotate formats |
| Promoting harmful tools | radar risk flags (NSFW, ToS bypass, bot evasion, piracy, scraping) + manual check |
| Fact errors | primary sources only; numbers refreshed on render day; catch line |
| Sandbox resets / limits | one-click bootstrap, one heavy job per session, GitHub SSOT (**needs a token each session**) |
