# 📅 MONTH 2 PLAN — The Deeper Mind

*Prepared 2026-08-19. Videos 1–12 shipped (Month 1 ≈ 3/wk).*

## ✅ DECISIONS (user-confirmed 2026-08-19)
1. **Cadence: 2 long-form/week + 3 Shorts/week** (Tue+Fri long; Mon/Wed/Sat Shorts).
2. **Shorts: repurposed from existing long-forms only** (hook + midpoint), no
   original-topic Shorts in Month 2.

## SCHEDULE (locked)
| Day | Format |
|---|---|
| Tue | long-form (new video) |
| Wed | Short (from Tue's video) |
| Fri | long-form (new video) |
| Sat | Short (from Fri's video) |
| Mon | Short (from a high-CTR back-catalog video) |

---

## 1. Where we actually are (no sugar)

- **12 long-form videos done.** Monetization (1,000 subs + 4,000 watch hours) is
  still far. The channel is firmly in the "algorithm is still learning who we are"
  phase.
- The research is consistent on one thing: the algorithm needs **~30 videos** of
  data before it confidently recommends you [3](https://virvid.ai/blog/faceless-channel-monetization-timeline-2026).
  We're at 12. That means **Month 2 + early Month 3** is the runway to the
  30-video inflection point.
- Our real bottleneck is **NOT production** (the pipeline automates render/TTS/
  captions). It is **topic quality + thumbnail/title** — which decide ~80% of
  whether a video gets clicked [5](https://becomeviral.com/blog/faceless-youtube-channel-guide-2026).
  Uploading faster does not fix a weak thumbnail; it just burns topics faster.

---

## 2. Q3 — Should Month 2 keep 3 long-form/week? → No. Do 2.

**Recommendation: 2 long-form/week + 3 Shorts/week.** Here's the honest logic:

1. **Our niche is narrow by design** (rare personality types + Jungian depth).
   At 3/wk we spend ~12–13 topics/month. This specific lane has maybe 30–50
   genuinely strong topics before we're scraping [5](https://becomeviral.com/blog/faceless-youtube-channel-guide-2026).
   At 2/wk we spend 8–9/month and buy **~2 extra months of runway** — more time
   for each topic to be sharp, not recycled.
2. **Frequency is not the growth lever — consistency + quality is.** "Consistency
   beats frequency every time" [2](https://aliservicess.medium.com/how-id-start-a-faceless-youtube-channel-from-scratch-in-2025-and-actually-make-money-a7870ce506c8);
   for a sub-1K channel the recommended long-form rate is **1–2/week** while
   scaling [4](https://ventress.app/blog/youtube-posting-frequency-guide-2025/).
   Two/week is the "minimum for growth" line; one/week is maintenance
   [5](https://becomeviral.com/blog/faceless-youtube-channel-guide-2026).
3. **The freed capacity goes to Shorts** — which is where discovery actually
   happens at this stage (see Q4). 2 long + 3 short = 5 publishes/week, but the
   *mix* is what drives growth.

> If we later see 2–3 videos in a row with CTR ≥5% and retention ≥45%, we can
> afford to push back to 3 long/week. Scale from data, not from hope.

**Schedule:** Tue + Fri long-form (prime US/UK evening scroll), Shorts Mon/Wed/Sat.

---

## 3. Q4 — Do we need Shorts? → Yes, but as REPURPOSED clips, not a new pipeline.

**Honest verdict: yes, Shorts — but not as a second topic pipeline (yet).**

- **Shorts = discovery engine, not revenue.** Psychology Shorts RPM is
  $0.05–0.14/1K views [3](https://miraflow.ai/blog/best-niches-youtube-shorts-2026-rpm-estimates),
  while long-form self-improvement earns $4–8 RPM and mid-rolls on 8–10 min
  videos push it higher [4](https://flowshorts.app/youtube-money/motivation).
  Shorts are the **advertisement**, long-form is the **product**
  [2](https://scalelab.com/en/youtube-shorts-vs-long-videos-what-works-in-2025).
- **They measurably accelerate growth:** channels mixing formats grow ~41% faster
  [3](https://marketingagent.blog/2026/02/15/how-to-balance-youtube-shorts-and-long-form-content-for-maximum-roi-in-2026-optimizing-both-formats/),
  and Shorts posters gain subscribers 2–3× faster
  [1](https://www.sooperblooper.in/blog/youtube-shorts.html).
- **Posting Shorts on the same channel does NOT hurt long-form** — YouTube has
  said so directly [4](https://www.pandavideo.com/blog/shorts-and-long-form-videos-same-channel).
  Keep them on the main channel as the funnel.
- **Do we need Shorts from made videos or separate topics? → From made videos
  first.** We already have, for every video: the exact caption timestamps, the
  kinetic-caption PNGs, the script, and all assets. Cutting 1–2 Shorts per
  long-form (the hook + the R12 midpoint interrupt) is *cheap*. Separate-topic
  Shorts double the scripting/research cost and dilute the niche — not worth it
  in Month 2.

**Shorts system (to build):** a `tools/make_short.py` that takes a long-form
video + its caption schedule → crops 1080×1920 from the 16:9 frame (or renders
from the same assets at 9:16), picks a 30–45s segment (hook or midpoint), keeps
the captions, re-mixes audio to the same R20 balance, and outputs a ready Short.
Estimated: 1 build turn. → **Ask for go-ahead before building.**

---

## 4. Q5 — The niche fence (what we are, what we are NOT)

**We are:** deep psychology for the rare intuitive types — INFJ / INTJ / INFP /
INTP — filtered through Jungian concepts (Ni, Fe, Ti, Fi, shadow, individuation).

**We are NOT:** generic self-help (habits, motivation, dopamine, productivity) or
general "dark psychology" (narcissism, manipulation, dark-triad clickbait).
That's the ocean. Every stray "motivation" video we publish trains the algorithm
to show us to the wrong audience — which tanks CTR on the videos we actually
care about.

**The niche fence test (apply to every future topic):**
> *"Does this topic name an experience a rare intuitive type secretly has —
> or explain it with a Jungian mechanism?"*
> If a generic motivation channel could publish it unchanged → **reject it.**

**Why this fence is financially right:** Jungian psychology/self-discovery is a
verified sub-niche at **$7.13 RPM** with only ~70K competing channels (low
competition, "stable not explosive") [5](https://outlierkit.com/blog/most-profitable-youtube-niches) —
better RPM and far less competition than generic motivation (20K channels,
10× growth, saturated) [5](https://outlierkit.com/blog/most-profitable-youtube-niches).

---

## 5. Month-2 topic slate (2/wk = 8 core + bench)

Every title is user-centric (no Jung name-drops). Jung stays in the script.
Title formulas rotate per R11.

| # | Title | Pain point | Jungian mechanism |
|---|---|---|---|
| 13 | Why You Feel Like an Old Soul | Rarity burden | Precocious Ni |
| 14 | The Psychology of People Who Apologize for Existing | Fe over-accommodation | Fe dominance / weak Fi |
| 15 | Why INFJs Push People Away When They Need Them Most | Self-sabotaged closeness | Fe–Ti loop under stress |
| 16 | Why You're Exhausted as a Deep Thinker | Cognitive drain | Ni/Ti energy economics |
| 17 | The Psychology of People Who Can't Do Small Talk | Small-talk dread | Ni–Ti depth vs inferior Se |
| 18 | Why You Feel Guilty for Resting | Rest-guilt | Inferior-function pressure / output-linked worth |
| 19 | The Psychology of People Who Never Feel Good Enough | Ti self-criticism | Perfectionism / inferior Fe |
| 20 | Why You Replay Conversations Years Later | Rumination | Si/Ti loops (INTP/INTJ) |

**Dedup pass (2026-08-19, per R23):** the original #17 ("Alone in a Room Full of
People") duplicated #4 + #10 (loneliness) and the original #18 ("Gut Feelings Keep
Coming True") duplicated #11 (Ni foresight). Both are RETIRED and replaced above.
Every shipped video/short is registered by title + pain point + mechanism in
VIDEO_QUEUE.md; new topics must clear that register before being approved.

**Bench (if we scale to 3/wk, or for Month 3):**
Why You Feel Every Emotion in the Room · Why You Keep Your Best Ideas to
Yourself · Why You're Drawn to Your Complete Opposite (anima/animus) · The
Psychology of People Who Read the Room Too Well · Why You Plan for Disasters
That Never Come (Ni catastrophizing).

**Shorts per week:** 1 from each of the 2 new long-forms (hook / midpoint) +
1 from a high-CTR back-catalog video.

---

## 6. KPI targets for Month 2 (track, don't guess)

- **CTR ≥ 4%** (new-channel target; 8% is established-channel)
  [2](https://aliservicess.medium.com/how-id-start-a-faceless-youtube-channel-from-scratch-in-2025-and-actually-make-money-a7870ce506c8).
- **Average view duration ≥ 40%** of video length
  [2](https://aliservicess.medium.com/how-id-start-a-faceless-youtube-channel-from-scratch-in-2025-and-actually-make-money-a7870ce506c8).
- Hit the **30-video mark** by end of Month 2 / early Month 3.
- **Honest timeline:** monetization is realistic at 3–6 months of consistent
  uploads, not Month 2 [3](https://virvid.ai/blog/faceless-channel-monetization-timeline-2026).
  Expect slow growth until video ~30; that's the normal curve, not failure.

---

## 7. Decision needed from you

1. **Cadence:** 2 long-form/week (recommended) — or keep 3/wk?
2. **Shorts:** build the repurposed-Shorts system now (recommended) — or later?
