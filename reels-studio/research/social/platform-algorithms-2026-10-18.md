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

## Competitor evidence (Socialinsider 30-day snapshots, 2026-10-18)

- **@sebintel (Instagram, 352.7K followers):** 58 posts/30 d, 5.04M views, avg 741 likes but
  **avg 1,141 comments/post** — the comments are manufactured: every top Reel opens its caption
  with *"Comment 'CLAUDE' and I'll send you the full setup guide."* The caption's first line is
  a lead-magnet CTA; the keyword sentences follow. ER/post of top Reels 2.1–3.5%.
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
- **Social Blade / vidIQ free tiers:** fine for one-off follower-grade checks in a browser;
  no advantage over the two tools above for our pipeline. Not integrated.
- **YouTube deep decode** still needs login cookies (bot gate) — owner decision, not a tooling gap.

## What would sharpen this further (owner inputs)
1. **Competitor handles per platform** beyond the TikTok list (IG/FB/YT names) — probe runs
   are cheap once named.
2. **Facebook page username** (the numeric page id is rejected by the probe) — or accept
   Buffer-only FB data, since FB competitor pages matter less than IG/YT in this niche.
3. **YouTube cookies export** if deep YT competitor decode (scripts/voice/covers) is wanted;
   without it, YT competitor work stays at headings/views level.
