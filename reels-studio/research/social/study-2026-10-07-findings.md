# Channel study #2: findings (agent analysis, 7 Oct 2026)

**Data:**
- 9 benchmark TikTok accounts chosen by the user: @dr_cintas, @github.signals, @ai_vanta_ai, @skip_ci, @m_ai_academy, @wellx.tech, @sebintel, @github.awesome, @beyondtahir.
- **Stats for all 270 videos** (30 each: views, likes, comments, shares, saves, length, caption, hashtags, music).
- **Frame-level visual analysis** of each account's top 3 + bottom 1 (cut rate, on-screen text via OCR, 8-frame strips reviewed by eye).
- **Transcripts** for each account's top videos first (round-robin; whisper.cpp; multilingual model for @beyondtahir).

Auto-generated numbers: [`study-2026-10-07.md`](study-2026-10-07.md) and [`videos-2026-10-07.csv`](videos-2026-10-07.csv). Quotes here are ≤ 20 words, for analysis.

## 1. What separates each account's top 25% from its bottom 25% (all 270 videos)

| Signal | Top 25% | Bottom 25% | Meaning |
|---|---|---|---|
| **Saves per 1k** | **40.4** | 15.3 | top videos are *bookmark-worthy*: install steps, free alternatives, "you'll need this later" |
| **Shares per 1k** | **6.8** | 3.1 | top videos give a reason to send ("your friend who pays for X") |
| Length | 34 s | 34.5 s | length doesn't decide it; value density does |
| Hard cuts per 10 s (visual sample) | **1.7** | 4.0 | repo explainers win with **continuous motion** (scroll, zoom), not frantic cutting |
| Hashtags | 3 | 4 | fewer, specific tags |

**By length** (all 270): **30–45 s has the most saves (34/1k) and shares (5.8/1k)**. Over 60 s only works for personality-led creators (@beyondtahir).

**Voice vs music:**
- 215 of 270 use original sound (voice-over), with a median of 5,004 views.
- Videos on a trending music track get a median of 2,893.
- Music-only + text videos exist (one @ai_vanta_ai hit got 687K), but voice-over is the norm.

## 2. Hooks: the formulas behind the biggest videos

| Formula | Example (excerpt) | Result |
|---|---|---|
| **"Someone just [impossible thing] [number] [constraint]"** | "Someone just ran a 744 billion parameter AI model on a laptop with no graphics card." | **774K views, 33.6K saves** |
| **Unexpected person + free alternative to a paid incumbent** | "A geography professor just built a free, open-source GIS tool that does what … Google Earth Pro charge[s] hundreds…" | 255K, 11K saves |
| **Stakes / scenario** (pilot scan) | "If tomorrow your entire country suddenly lost access to the internet, this GitHub project…" | 378K |
| **Named tool + transformation** | "MeshAvatarStudio transforms a single static illustration into a fully animated 2D character" | 59K |
| **Big number on screen** | "597B → 744B" count-up + "NO GPU AI MODEL" banner | 774K (same video) |
| ✗ Weak: "leaked" framing, straight into instructions | "Someone just leaked over 4,000 n8n automations…" | **14 views** |

**Story spine of the 774K video** (copy the structure, not the words):
1. **Impossible claim with a number** (0–5 s).
2. **Who did it** ("a developer in Italy") + the model name.
3. **Antagonist / status quo** ("NVIDIA's entire pitch is that you need their GPUs… you just prove you don't").
4. **Name reveal at ~17 s.**
5. **Mechanism in one sentence** ("only ~10 GB is actually thinking at any moment, so it keeps that in RAM and streams the rest").
6. **Practical payoff** ("your token bill goes to zero; nothing leaves your machine").
7. **CTA:** "The GitHub link with a full install guide is in the comments."

## 3. Visual styles (from frame strips)

| Style | Accounts | Look | Fits us? |
|---|---|---|---|
| **A: faceless README scroll** | @github.awesome (111K), @github.signals (59K), @skip_ci | dark-mode GitHub page in a browser over a desktop wallpaper; continuous scroll; **ALL-CAPS 2–4-word captions, one keyword in yellow**; series banner ("TRENDING ON GITHUB") | ✅ **core format**: our capture kit produces exactly this |
| **B: face + screen split** | @ai_vanta_ai (774K), @dr_cintas (43K) | creator's face bottom half, screen/B-roll top; big count-up numbers; red hook banner; cuts every ~1.5 s; small lowercase word captions | partly: we replace the face with demo clips + motion graphics; own face/voice optional later |
| **C: personality talking head** | @beyondtahir (174K) | cinematic bokeh background, hand gestures, occasional text pops ("AI trading house", "5 Agents"), **speaks Urdu/Hindi** to Pakistan/India/Bangladesh | future Urdu/Hindi line (needs the user's voice/face) |
| **D: consumer tech tips** | @wellx.tech (5.7M) | iPhone/iOS tips (#apple #ios18), mass reach, very low saves | off-niche; reach reference only |

**Seen but refused:**
- a **Stranger Things** clip in an @ai_vanta_ai video (copyright);
- TikTok's "AI-generated" label on @dr_cintas B-roll. That's fine, but it shows labels apply when AI footage is realistic.

## 4. What drives comments, shares and saves

- **Comments:** only accounts with a **keyword CTA** reach 3–6 per 1k (@sebintel 3.2, @beyondtahir 5.1, pilot @sabrina_ramonov 6.2). Everyone else gets 0.0–0.9.
- **Link-in-comments CTA** ("full install guide is in the comments"): it creates a reason to open comments and is used by the 774K and 255K videos. Our honest version is "Comment KEYWORD and I'll pin the link", with the link pinned by us.
- **Saves:** utility density (install guide, "free alternative to $150/month", lists) plus explicit "save this".
- **Shares:** a contrast with something people pay for, or a "your friend who…" angle.

## 5. Rules adopted into PLAYBOOK.md

1. Hooks come from the formula table above. Never use "leaked"/sketchy framing; never start mid-tutorial.
2. **Story spine:** claim with a number → who → status quo/antagonist → name (≤ 17 s, ideally ~7 s) → mechanism → payoff → CTA.
3. **Repo Drop = Style A**: README scroll + ALL-CAPS keyword captions + series banner ("NEW ON GITHUB").
4. **Spotlight = Style A+**: official demo clip first, count-up numbers, cursor/zoom, one cut or move every 1.5–3 s.
5. **Length:** 30–45 s.
6. Voice-over always (our channel voice). Music under the voice, never music-only.
7. Close: payoff → "save this" → "comment KEYWORD, I'll pin the link".
8. A South Asian Urdu/Hindi line is validated by @beyondtahir. Plan it as F4 once the English line is running.

## 6. Transcript statistics (194 transcripts: 22 per account, 18 for @beyondtahir)

| Signal | Top 25% (n=70) | Bottom 25% (n=45) | Takeaway |
|---|---|---|---|
| Paid-vs-free contrast ("$", "subscription", "instead of", "charges") | **14%** | 7% | **2× more common in winners**: always state what it replaces or costs |
| Story opener ("someone / a developer / just built / just released") | **14%** | 7% | **2×**: human story > feature list |
| Number in the first sentence | **29%** | 22% | numbers help |
| Transformation hook | 9% | 4% | github.signals' signature (12 of 22) |
| Median pace | 183 wpm | 189 wpm | not a differentiator; the niche norm is ~175–190 |
| Name reveal | ~8 s | ~7 s | standard everywhere |
| Spoken CTA | 36% | 36% | **CTAs don't drive views. They drive comments** (separate goal) |

**Account patterns:**
- **@m_ai_academy**: the same "stop/problem" hook 18 of 20 times, 243 wpm, CTA 91%, low median views (2K). This is **formula fatigue**: rotate hook types.
- **@dr_cintas**: CTA in 95% of videos.
- **@github.signals**: transformation hooks, almost no CTA, the best median of the repo accounts (7.1K).
- **@skip_ci**: the slowest pace (150 wpm) and the lowest median (0.9K).

**Pace target updated:** ~175–185 wpm (repo-explainer benchmark: github.signals 174, github.awesome 180).
