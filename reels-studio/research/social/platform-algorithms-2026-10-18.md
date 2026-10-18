# Per-platform optimization: what each algorithm rewards (2026-10-18)

We do **not** post one generic package everywhere. Each platform's algorithm pays for
different first signals, so the same video gets a different heading, caption shape, CTA verb
and slot per platform (PLAYBOOK §9 holds the copy rules; this file holds the *why* + evidence).

Evidence sources, in order of trust for each claim:
1. Our own Buffer Insights + `tracker/performance.json` (93 posts; within-platform percentiles).
2. `tools/socialinsider_probe.py` 30-day public snapshots (`platform-snapshots-2026-10-18.json`).
3. `tools/channel_decode.py` winner/loser decode (`decode-2026-10-18.md`), TikTok-heavy.
Snapshots from free tools are approximate (the same account's 30-day totals moved between two
probes an hour apart) — use them for direction and competitor shape, never as exact truth.
Public tools see likes/comments/views only; reach, saves, shares and watch time are
owner-only (for us: Buffer Insights; for competitors: unknowable — do not pretend otherwise).

## The matrix

| | YouTube Shorts | Instagram Reels | Facebook Reels | TikTok |
|---|---|---|---|---|
| **Algorithm pays for** | swipe-away rate in the first 1–2 s, % viewed / loop, then click to channel | **sends (shares)**, saves, watch time; trial-reel cold tests | shares, comments, **originality** (no watermarks/reposts), watch time | completion, rewatch, shares; search indexing of speech + captions |
| **Heading** | keyword title ≤60 chars, benefit in first words (§9) | line 1 = keyword-rich hook (caption *is* the heading) | keyword-first first line | caption line 1 = keyword + hook |
| **Caption/description** | 2–3 keyword sentences; link below fold; #Shorts + 2–4 tags | short benefit lines; **first line sells the comment-keyword** (see below) | short + a question; AI-narration disclosure (owner rule) | **~400-char keyword mini-article** (decode: winners' median), ≤3 hashtags, link optional |
| **CTA verb** | subscribe / watch next | **"Comment KEYWORD — I'll send the guide"** (lead-magnet pattern, below) | comment / share to a friend who… | comment keyword + follow |
| **Posting slot (ours, ET)** | evening 16:00–21:00 (median 132, n=8) | morning 10:00 lead (median 197, n=4) | midday 12:00 lead (median 82, n=9) | not connected (owner: Buffer covers YT/IG/FB only) |
| **Kill signals** | slow first frame, context-first title | save-worthy value missing; >5 hashtags (hard cap) | cross-platform watermark, reused content | text-free first frame; generic #fyp tags |

## Competitor evidence (niche set from `research/ai-tools-niche.md`, 2026-10-18)

Tracked set = the accounts in the niche file (AI tools/repos), **not** general AI educators.
sebintel/Github Signals snapshots from the first probe round are background only; the
format-relevant evidence is:

- **Repo-spotlight TikTok decode** (`decode-2026-10-18.md`, 6 niche accounts, 11 usable
  top/bottom decodes — @zaindevx_, @remy_engineering, @ezbackend, @marcinteodoru,
  @sabrina_ramonov, @aitoolvaultly): top tier median **174K views, 38 s, 136 words, 193 wpm,
  pitch 14.7 st, 5.8 cuts/10 s, spoken CTA 62%**. Winning hooks are stakes/scenario and
  gold-mine framings ("If tomorrow your entire country suddenly lost access to the internet,
  this GitHub project could become extremely useful…"). Bottom tier runs **74 s** — length
  without density is the niche's main failure mode. (marcinteodoru's top hook uses profanity;
  noted, **not** copied — brand safety.)
- **@nomadatoast (Instagram, 607.5K followers):** 11 posts/30 d, 809.8K views, **avg 729
  comments/post** at ER 0.37% — comment volume is the IG engine in this niche.
- **@shedoesai (Instagram, 463.5K followers):** 9 posts/30 d, 3.35M views, **avg 393
  comments/post** — her niche-file lesson ("comment TOOLS for the list") is measurable, and
  it works. Low posting frequency, high per-post payoff: quality + lead magnet beats volume on IG.
- **@mreflow / Matt Wolfe (YouTube, 1.02M subs):** 16 posts/30 d, 1.49M views, ER 0.16% —
  long-form-led; Shorts are a feeder there, titles/descriptions carry the search load.
- **Comment-keyword mechanics (also @sebintel, background):** top IG Reels open the caption
  with *"Comment 'CLAUDE' and I'll send you the full setup guide."* (1,141 avg comments).
  → Adopted: IG caption line 1 = comment-keyword promise where we can fulfil it (we pin the
  link ourselves — never promise DMs we can't send; PLAYBOOK §4 close stack already does this,
  now it moves to line 1 on IG).
- **@GithubSignals (YouTube, 1,010 subs):** 114 posts/30 d (~3.8/day), 127.6K views,
  avg 14.3 likes, 0.44 comments. Volume + consistency on a small channel; per-video medians
  are low — Shorts there compound via catalogue, not single hits.
  → Our YT is a catalogue game: keep daily cadence, titles carry the search load.
- **@github.signals (TikTok, 20.2K followers):** ER 7.9%, avg 12.1 comments, 1.9–2.3M views/30 d.
  Same content as their YouTube — ~15× the views. TikTok is their discovery engine; YouTube
  is the archive. (We are not on TikTok; treat its decode as format research, not a channel.)
- **Ours (@hypelessai.ai IG):** 6 followers, 31 posts/30 d, 5,093 views, ER 13.4% on a tiny
  base, 0 comments — distribution, not content quality, is the current IG bottleneck:
  comment-keyword line-1 + sends-bait ("send this to someone who…") are the cheapest fixes.

## Free-tool verdicts (checked 2026-10-18)
- **Socialinsider free tools — USEFUL, adopted.** No-login API behind the public pages
  (`tools/socialinsider_probe.py`): IG/FB/YT/TikTok 30-day snapshots + top posts with
  captions. Limits: business/public accounts only, 30-day window, async (poll), rate limits,
  numbers drift between calls.
- **SocialStats.info — not adopted.** Dashboard-first (search loads an in-page report;
  compare/PDF/email features are account-shaped), no clean machine-readable endpoint found,
  and its public pages are a 2018-era wrapper. Socialinsider covers the same need better.
- **Owner-listed YouTube tools (checked 2026-10-18):** Social Blade — 403 bot wall for
  machines, official API is paid; vidIQ / Viewstats — browser extensions/JS apps (Viewstats
  loads, but its data API is not openly callable), useful for a human in a browser, not for
  this pipeline; YTface / SocialFetch / SubSub / SearchVector — simple lookup pages, no data
  beyond what yt-dlp already returns for free. **Verdict:** yt-dlp (listings, titles, views,
  media) + Socialinsider snapshots (30-day channel stats + top posts) already cover the
  programmatic need better than all of them. YouTube *deep* decode (per-video script/voice)
  remains bot-gated without cookies — parked by owner choice of free tools instead.
- **Facebook:** owner decision 2026-10-18 — **Buffer-only**. No FB competitor probing
  (the probe also rejects numeric page ids); FB optimization runs on our own Insights data.

## Tracked competitor set (from `research/ai-tools-niche.md`)
- TikTok decode: @zaindevx_, @remy_engineering, @ezbackend, @marcinteodoru,
  @sabrina_ramonov, @aitoolvaultly, @github.signals (+ the 9 Oct-07 benchmarks as background).
- Instagram snapshots: @nomadatoast, @shedoesai (lead-magnet lane); @rileybrown.ai pending
  (free-tool rate limits — retry next run).
- YouTube snapshots: @mreflow (Matt Wolfe); @Futurepedia/@MatthewBerman pending rate limits.
  (@ai-explained is **not** AI Explained's handle — 1.2K-sub channel; do not use.)
