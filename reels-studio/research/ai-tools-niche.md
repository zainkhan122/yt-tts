# Niche research: Tech / AI-tools explainers (7 Oct 2026)

## 1. Does it really pay well? Yes, but mostly on long-form

| Format | RPM in tech / AI tools (what you keep per 1,000 views) | Source |
|---|---|---|
| **YouTube long-form** | **$4.5–11** creator RPM (AI & tech news / tools) | [OutlierKit, Sep 2026](https://outlierkit.com/resources/faceless-youtube-channels/) |
| YouTube long-form (other estimates) | $5–15, up to $7–25 | [virvid](https://virvid.ai/blog/most-profitable-ai-youtube-shorts-niches-2026-rpm-data), [virvid guide](https://virvid.ai/blog/ai-youtube-shorts-monetization-guide-2026) |
| **YouTube Shorts** | **$0.04–0.08** (top of the Shorts range) | [growcreator, Jul 2026](https://growcreator.pro/blog/youtube-shorts-rpm-2026) |
| YouTube Shorts (other estimates) | $0.07–0.18 | [miraflow](https://miraflow.ai/blog/best-niches-youtube-shorts-2026-rpm-estimates) |

**What this means:**
- Shorts are paid from a **shared pool**, so viewer country matters more than niche.
- A tech Short earns roughly 2× an average Short, but still only **cents per 1,000 views**.
- The niche's money is in **long-form, affiliate programmes (AI SaaS often pays 20–30% recurring), sponsorships, and an owned list** (newsletter or tool directory).
- Plan: **Shorts and Reels for reach → long-form plus affiliates for revenue.**

## 2. Ten accounts that publish AI tools, repos and free generators (what to learn, not what to copy)

| # | Account | Platform | Size (third-party, 2026) | Format | Lesson to borrow |
|---|---|---|---|---|---|
| 1 | Matt Wolfe | YouTube (+ FutureTools.io) | ~973K subs, 2 uploads/week | weekly tool roundups and demos | weekly cadence, plus an **owned directory** that monetises the audience |
| 2 | Futurepedia | YouTube (+ directory) | ~720K subs | project-based tutorials | "finish one workflow", not "list 10 tools" |
| 3 | Matthew Berman | YouTube | ~621K subs, 4 uploads/week | tests new models within days | **speed on releases** (our radar enables this) |
| 4 | The AI Advantage | YouTube | ~459K subs | practical "use X for Y" workflows | one tool, one concrete outcome |
| 5 | AI Explained | YouTube | ~384–400K subs | hype-free analysis | trust through honesty, which is rare in this niche |
| 6 | Riley Brown (@rileybrown.ai) | TikTok / IG / X | ~637K TikTok | builds things live with AI agents | **show the result being made** |
| 7 | Jo Mendes (@nomadatoast) | TikTok + Instagram | ~337K TikTok, ~450K IG | creative tech tips and AI tools | visual before/after hooks |
| 8 | Johanne (@shedoesai) | TikTok | ~220K | free AI tools lists + newsletter | **lead magnet** ("comment TOOLS for the list") |
| 9 | Victor Chirita (@aisavvy) | TikTok | ~131K | AI tools and tutorials | short step-by-step tutorials |
| 10 | Chris Winfield (@thechriswinfield) | TikTok | ~121K | "AI in 90 seconds or less, every day" | a **named daily series** |

Sources: [usefulai](https://usefulai.com/feeds/youtube-channels) (YouTube sizes, Jul 2026), [wyrote](https://wyrote.com/blog/ai-content-generation/top-ai-content-creators-2026-who-s-worth-following) and [chillframe](https://chillframe.com/blog/ai-youtube-channel) (AI Explained), [Feedspot](https://creators.feedspot.com/ai_tiktok_influencers/) (TikTok/IG, Sep 2026).
Follower counts come from third-party lists, not live checks. Instagram-only AI-tool accounts were hard to verify, so treat IG figures as approximate.
For a South-Asian audience, **CodeWithHarry** (Hindi coding/API tutorials) is often recommended ([chillframe](https://chillframe.com/blog/best-ai-youtube-channels)).

**Patterns the winners share:**
1. The **tool working on screen within 3 s**.
2. **One tool, one outcome** per short.
3. A **named series** with a fixed cadence.
4. **Speed** on new releases.
5. An **owned funnel**: newsletter, directory or "comment X".
6. The best ones are **honest about limits**.

## 3. My input: how to enter this niche without becoming "AI slop"

1. **"Tested, not hyped."** Every video shows a real run you did yourself: a screen recording plus HyperFrames zooms, callouts and captions. It ends with a verdict: what it's good at, its limits, and whether it's actually free. That's the originality YouTube's 2026 rules reward, and the thing hype accounts skip.
2. **Data-driven curation is your edge.** `reels.py radar` ranks brand-new GitHub repos by stars per day, and Hugging Face trending models and Spaces. That makes a weekly **"5 AI repos exploding this week"** series possible, with live numbers. It's original curation, not reposts.
3. **"Free AI API keys": careful.** Legit and great content: **official free tiers** (free API quotas, free models on aggregators, free inference credits), *verified on the day*, because limits change often. Never: leaked keys, reverse proxies or "no-key" wrappers around paid models. Those breach terms of service, can be illegal, and put your channel at risk. The radar flags them automatically; today it flagged 11 items (uncensored models, anti-bot/captcha evasion, a "no API key" DeepSeek/Kimi wrapper).
4. **Never re-upload or narrate other creators' clips.** YouTube de-ranks this since 1 Oct 2026. Take *topics* from the accounts above, then test the tool yourself.
5. **Language:** English for RPM and the global audience. Add an Urdu/Hindi version of the best performers. The South-Asian AI-tools demand is huge, and Reels Studio already supports Urdu on screen and experimental Urdu voice.
6. **Money path:** affiliate links in the description and bio, a free "AI tools list" newsletter (lead magnet), then sponsorships. A weekly long-form roundup (8–12 min) built from the week's shorts captures the long-form RPM.

## 4. Weekly production plan (one person + Reels Studio)

| Day | Output | Tool |
|---|---|---|
| Mon | Run the radar; pick 5 candidates; actually install/try 2–3 | `reels.py radar --brief` |
| Tue | "5 AI repos exploding this week" (ranked list, live stars) | `ranked-list` template |
| Wed | Tool spotlight #1: your screen recording + steps + verdict | `tool-spotlight` template (next build) |
| Thu | "Free tier reality": what you really get from service X's free tier | `say-this` / `ranked-list` |
| Fri | Tool spotlight #2 | `tool-spotlight` |
| Sat | Long-form weekly roundup (16:9) from the week's material | (next build) |
| Daily | Log metrics in `tracker/content-tracker.csv`; reply to comments within 24 h | – |

**Where to post:**
- YouTube Shorts and long-form.
- Instagram Reels (use Trial Reels for hook tests).
- TikTok (reach only, since Creator Rewards isn't available in Pakistan).
- Facebook (check Professional Dashboard eligibility).
- X: revenue sharing needs Premium and minimum impression/follower thresholds, and payout availability by country should be verified for Pakistan before counting on it.

## 5. TikTok + Instagram scan: who makes AI-tool / GitHub-repo shorts (Phase 1, 7 Oct 2026)

**Method.**
- TikTok's public "discover" topic pages list the creators and engagement behind a topic. Sources: [github-ai-project](https://www.tiktok.com/discover/github-ai-project), [best-github-ai](https://www.tiktok.com/discover/best-github-ai), [github-open-source-software-must-have](https://www.tiktok.com/discover/github-open-source-software-must-have), [github-repositories](https://www.tiktok.com/discover/github-repositories), [ai-tools-to-learn-2026](https://www.tiktok.com/discover/ai-tools-to-learn-2026).
- **Instagram blocks automated access** (HTTP 403 on its topic pages), and its reels are barely indexed by search engines. Most of these creators cross-post the same shorts to IG Reels, so the TikTok scan doubles as the IG trend scan.

| Account (TikTok) | What they post | Proof of traction (from TikTok discover pages) | Format lesson |
|---|---|---|---|
| @sabrina_ramonov | open-source AI agents (UI-TARS, Browser Use…) | 23.9K likes on one repo video | "underrated open-source alternative to X" + free tutorial funnel |
| @forcceee_ | "free GitHub repo with every free AI API key" | 22K likes, 681 comments | **DM-bait funnel.** Huge engagement, but "free keys" content is often key-sharing/abuse. We cover official free tiers only |
| @zaindevx_ | "This GitHub repo is a GOLDMINE…" (agents, Screenshot-to-Code) | (not stated) | **"Comment 'Clone' to get the link"**: comment-to-DM loop that boosts comments |
| @remy_engineering | "stop paying for tools you can run yourself", 5 repos | (not stated) | money-saving hook + list |
| @will.ai.m | repo star velocity ("191k stars in 11 days") | (not stated) | **star velocity as the hook** (our radar computes stars/day) |
| @thechriscordero | "Stop paying monthly for AI tools", Open Generative AI | (not stated) | "replace your subscriptions" |
| @whitewhoadie | "Slash Claude costs" with an open-source tool | 2.3K likes | cost-cutting for AI coders |
| @ezbackend | "Top 5 trending GitHub repos this week" | (not stated) | weekly countdown (same as our ranked-list) |
| @github.signals | daily open-source repo drops | (not stated) | named daily series |
| @marcinteodoru | "fastest growing AI projects on GitHub" | (not stated) | **greenscreen**: talking over the repo page |
| @aitoolvaultly | AI tool lists (21–25 tools) | 155K–197K views | save-worthy lists |
| @muhib__afghani | new AI tools for creators | 455 likes | regional creator, same playbook |

**What this means for our videos.**
1. Show the **repo or site on screen** (greenscreen-style capture), plus the **demo output**.
2. Hook with **star velocity** or **money saved**.
3. Make one clear claim per video.
4. End with a **comment trigger** ("comment MOD for the link") rather than putting links on screen.

**What we won't copy:** "free API keys" DM-bait, and re-posting their clips.
