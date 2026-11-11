# 2026-10-12 batch — the five videos, chosen by findings (not by a fixed mix)

Owner instruction (2026-10-11): make 5 videos for today, scheduled; the system must **not** be hardcoded to
2× tools / 2× news / 1× repo, and the five topics must come out of the research — search demand, relevance,
popularity.

That policy change is in code: `config/publishing.json` (`required_daily_categories: []`; ceiling `max_videos_per_day: 10` since later on 2026-10-12 — the old 5/day cap is gone)
and `tools/post/cadence.py` now orders a batch strictly by editorial priority when no mix is required.
Suite: 230 passed (`test_mix_is_not_hardcoded_in_config`, `test_repo_weighted_batch_is_allowed_when_merit_picks_it`, `test_daily_ceiling_is_ten_and_has_no_hidden_five_clamp`).

Evidence base: `research/radar/radar-2026-10-12.md` (32 safe candidates from 14 days of channel scans),
`research/ideas/feed-2026-10-12.md` (154 topic candidates), GitHub REST API (stars/created/licence verified
per repo), Hugging Face trending, primary pages checked for the release facts, and YouTube autocomplete
(`suggestqueries.google.com/complete/search?client=youtube`) sampled 2026-10-12 as a live search-demand signal.

## Rubric (weights set before scoring)

| Axis | Weight | Measured by |
|---|---|---|
| Popularity | 40 | union of views across independent channels in the radar (consensus count noted), GitHub stars, HF likes |
| Search | 25 | YouTube autocomplete: does the exact term surface, how many expansion queries, do query clusters exist |
| Relevance | 20 | fit to this channel (AI tools/news/repos), demo-ability as a 60-second visual, evergreen-ness |
| Freshness | 15 | age of the release/story at production time |

## Scored candidates (all safe; flagged items excluded upstream by the radar)

| # | Topic | Cat | Popularity /40 | Search /25 | Relevance /20 | Freshness /15 | Total |
|---|---|---|---|---|---|---|---|
| 1 | **GPT-6.1 Astra scrapped by OpenAI** (safety) | news | 38 — GPT-6 cluster 1.02M views + Astra 902k across 4+ channels each | 21 — "gpt 6.1 sol", "gpt astra" surface; huge breakout story | 18 — agent-safety story, fully narratable | 15 — Sept 28/29, still the talk of the niche | **92** |
| 2 | **Qwen3.8-27B runs on one RTX 3090** | tool | 34 — 5 channels / 119.6k union views; HF #1 trending (17,521 likes) | 23 — exact cluster "qwen 3.8 27b", "qwen 3.8 flash next" | 20 — local inference is the channel's strongest performing category | 15 — release week, still climbing | **92** |
| 3 | **Nano Banana 2.1** (Image model refresh) | news | 27 — 2 channels / 65k views; official Oct 6 launch | 25 — "nano banana" = 14 suggestions incl. tutorial/photoshop/2.1; massive evergreen cluster | 20 — imagegen tool users can try today | 14 — 6 days old and in AI Mode/Flow/AI Studio | **86** |
| 4 | **OpenMontage** (agentic video production, 67.1k★) | tool | 36 — 67,149 stars / 8,557 forks in ~6 months | 12 — low volume; only the term itself autocompletes | 20 — AI video production is the channel's exact beat; excellent demo footage | 12 — trending now, created 2026-03-29 | **80** |
| 5 | **ds4** (DeepSeek 4 local inference by antirez, 23.8k★) | repo | 30 — 23,783 stars, Redis-creator author, high niche heat | 24 — "deepseek local" = 14 suggestions (install/setup/mac/coding) + "deepseek 4" 9 | 20 — runs on your own machine; Metal/CUDA/ROCm story | 14 — very recent activity | **88** |
| — | open-code-review (Alibaba, 46.3k★) | repo | 28 | 14 | 16 — dev-focused, less visual | 13 | 71 |
| — | universal-modder (Claude mods any game) | tool | 20 | 10 | 12 — game-modding ToS grey area, weak for brand-safe AI coverage | 12 | 54 |
| — | anatomy (isometric agent skill, 4.1k★) | tool | 12 | 8 | 14 | 13 | 47 |
| — | artcraft (19k★ Rust) | repo | 16 | 8 | 14 | 12 | 50 |
| — | LTX-2.5 (HF 7.3k likes) | tool | 14 | 8 | 16 | 14 | 52 |
| — | HeyGen (5.3M views) | tool | 34 | 20 | 8 — paid avatar product; promo-heavy, brand overlap with our own voice product | 8 | 70 |

Runners-up lost on search or safety-fit, not on a category quota. HeyGen is the closest miss: huge views,
but it is a competitor product to the channel's own TTS workflow and reads as an ad.

## The five (final)

1. `news-gpt61-astra-01` — OpenAI scrapped GPT-6.1 Astra (news)
2. `tool-qwen38-01` — Qwen3.8-27B on one RTX 3090 (tool)
3. `news-nano-banana-21-01` — Nano Banana 2.1 (news)
4. `tool-openmontage-01` — OpenMontage agentic video production (tool)
5. `repo-ds4-01` — ds4 local DeepSeek 4 (repo)

Resulting distribution: **2 news / 2 tool / 1 repo** — the same shape the old constant enforced, but here it is
an *outcome* of the ranking above, and the machinery no longer requires it.

## Source discipline for this batch

* GPT-6.1 Astra cancellation: reported by WSJ 2026-09-28; OpenAI head of safety systems Saachi Jain on record
  (Al Jazeera, 9to5Google). Capability numbers from OpenAI's GPT-6 Astra page; action-efficiency + the
  62.7%→99.9% harness asterisk from ARC Prize's own analysis (`arcprize.org/blog/astra` — also the capture source,
  openai.com blocks automated capture with 403).
* Qwen3.8-27B: Hugging Face model card + community throughput reports (attributed, not our own measurement).
* Nano Banana 2.1: Google's model docs list it (image-search grounding, video-to-image, 1K/2K/4K, 14 reference
  images) + the Oct 6 announcement; pricing attributed to provider, not independently measured.
* OpenMontage / ds4: GitHub REST API facts (stars, licence, created) verified 2026-10-12.
