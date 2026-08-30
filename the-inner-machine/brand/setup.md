# THE INNER MACHINE — Channel Setup
*The authoritative setup for this channel. This strategy & SOP are ORIGINAL — they are
not copied from, and do not follow, the reference channel (`vault/` "The Deeper Mind").
The reference is consulted for production technique only, never for strategy.*

## 1 · Identity
| Field | Value |
|---|---|
| **Name** | The Inner Machine |
| **Handle** | @TheInnerMachine (verify availability at launch) |
| **One-liner** | The hidden machinery of your mind. |
| **Niche** | Animated explainers on *how the mind works* — psychology, behavior, consciousness. |
| **Angle** | We explain the **mechanism** (the how/why) behind what you think, feel, and do — science first, human takeaway last. Not personality typing, not self-help preaching. |
| **Audience** | Curious adults 18–40 who want to understand themselves and others. Smart-curious, not academic. |
| **Tone** | Clear, warm, a little wondrous. Never preachy, never jargon-dumped. |

### Differentiation (why this isn't the reference)
- Reference = Jungian personality/archetype content for rare types. **We are not that.**
- We are **mechanism explainers**: every video answers "what is actually happening in your
  brain/behavior right now?" with a real mechanism + a relatable hook.

## 2 · Brand
- **Logo** — `logo.png` (1024) / `logo_800x800.png` (profile): graphite head silhouette whose
  brain is interlocking copper gears + cyan neural sparks.
- **Banner** — `banner.jpg` (2560×1440): neural-network (left) meeting clockwork (right),
  title in the safe area.
- **Palette**
  - Graphite `#14181D` (base)
  - Steel `#2E4756` (secondary)
  - Copper `#E0A458` (accent / titles)
  - Cyan-spark `#6FD3E0` (neural / highlights)
  - Cream `#F4EFE6` (body text on dark)
- **Type** — clean geometric sans for titles/captions (Montserrat/Poppins ideal; DejaVu-Bold is the
  offline fallback used by the pipeline).
- **Motion/visual style** — flat 2D storybook animation, soft radial glows, subtle grain;
  16:9 long-form, 9:16 Shorts. See `../plan/video-01…/project.json` `"style"`.

## 3 · Voice
- Engine: **Kokoro** (offline, free). This channel picks its own voice — do not assume the
  reference's `af_heart`.
- Audition set in `voices/` (28 samples). Current demo voice: `bm_george`; **confirm before launch**.

## 4 · Content strategy (original)
**Pillars**
1. **The Machinery** — how your brain does X (dreams, memory, attention, déjà vu, chills).
2. **Behavior Explained** — why you do that (habits, gut feelings, procrastination).
3. **The Self** — who's operating the machine (consciousness, identity, mind-wandering, time).
4. **Glitches** — when the machine misfires (overthinking, anxiety, burnout, forgetting).

**Formats** — 1 long-form (7–10 min)/wk + 4 Shorts/wk (hook + payoff from long-form + 2 standalones).
**Title/hook formulas** — "Why your brain does X" · "The mechanism behind X" ·
"What's actually happening when X" · "It's not laziness/you — it's <mechanism>."
**Packaging** — thumbnail = one bold idea + ≤4 words; title leads with the mechanism or the myth it busts.

**Initial slate (12, own — mechanisms, not archetypes)**
1. Where Do Dreams Come From? *(Machinery — done: video-01)*
2. Why Your Brain Deletes Most Memories
3. The Mechanism Behind Overthinking
4. Why You Procrastinate (It's Not Laziness)
5. Why You Forget Why You Walked Into a Room
6. What Happens When You Zone Out
7. The Science of Déjà Vu
8. Why Music Gives You Chills
9. Why Time Speeds Up as You Age
10. Why You Can't Tickle Yourself
11. Why Your Mind Wanders (The Default Mode Network)
12. Why Habits Are So Hard to Break

## 5 · SOP (one video)
1. **Topic** — pull from the slate; confirm pillar + hook formula.
2. **Script** — write as beats: `narration` + `caption` + `visual` + `motion` (+ `est`).
3. **Keyframes** — generate storybook art, palette-locked, any aspect (cropped to 9:16).
4. **Produce** — `python3 pipeline/produce.py plan/video-NN…/project.json`
   → `output/<Title>/` (long-form + 2 Shorts + metadata + cover), auto-verified.
5. **Metadata** — keyword in title + first description line; 3–5 hashtags; chapters; pinned comment.
6. **QA** — `state.json` must read `ok` (dims/fps/audio/duration verified) before upload.
7. **Upload** — you click upload; I supply video + cover + metadata pack.

## 6 · Toolchain (this channel's tools — all in `pipeline/`)
- `produce.py` — config → verified output folder (self-bootstrapping, pre-flight, crash-safe).
- `tts.py` — Kokoro wrapper, self-healing model download.
- `sample_voices.py` — renders the 28-voice audition set.
- `repo_push.py` — pushes THIS folder to GitHub (single commit, preserves the reference).
- `brand/make_brand.py` — rebuilds logo/banner finals from `_raw` art.

## 7 · Files
- `brand/` — logo.png, logo_800x800.png, banner.jpg, setup.md (this),
  **channel_metadata.md** (About text + channel/video tags + launch fields), make_brand.py (+ `_raw` sources).
- `plan/video-NN-<slug>/` — per-video source (project.json + keyframes).
- `output/<Title>/` — deliverables (mp4 + metadata + cover + shorts/ + state.json).
- `handoff/HANDOFF.md` — operational resume doc.

## 8 · Separation & security
- Independent of the reference channel (`vault/`); never merge tools, voices, plans, or strategy.
- GitHub PAT from env only; never hardcoded/committed. `*.mp4` not committed (regenerable).
