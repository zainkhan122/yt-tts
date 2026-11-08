# Top 10 topic picks — 2026-11-08

Sources: trend radar (GitHub / Hugging Face models & Spaces, `tools/trend_radar.py --days 3`),
**reference source channels** (33 tracked TikTok + YouTube Shorts creators via
`tools/sources.py scan` → `research/sources/posts.csv`, last 7 days by views), and
AI news feeds (Nov 4–7). Cross-checked against the covered/scheduled ledger —
nothing on this list is already queued or published.

## Source-channel validation (TikTok / YouTube Shorts, last 7 days)
- AI video generation is at peak momentum with channels: WesRoth's HeyGen short hit
  **5.3M views** → reinforces picks #1 (Omni 1.2 Flash) and #5 (LTX-2.5).
- Fireship covered CrowdStrike's AI kill-switch story (~1.4M views) — that item is
  **channel-crowded**, so it's a watchlist item, not a pick.
- mattreflow, matthew_berman, intheworldofai, aiadvantage clusters this week: AI hardware,
  coding agents, practical workflows — pick #6 (agent-desktop) and #7 (phone agents) sit
  exactly in that demand lane but no tracked channel has covered them yet.
- AbhayPSRajawat already covered GPT-6.1 Astra (we pruned that queue item anyway) — stays excluded.

Mixed on purpose: tools and launches, NOT repos-only. Repo candidates flagged as spam/licence-free
crypto-adjacent farm repos (aida-64/aion-2/trx-drainer clones, 244–302★/day) are excluded.

| # | Topic | Type | Why now | Short angle |
|---|-------|------|---------|-------------|
| 1 | **Google Gemini Omni 1.2 Flash video** | Tool/API launch (Nov 5) | 15 s clips, multi-turn editing, price cut to $0.07/s (−30%) | AI video gen is now cheap enough to A/B-test ad creative on a $1 budget |
| 2 | **OpenAI Images 2.6** | Tool launch (Nov 4) | GIFs in ChatGPT/Codex/API, 50% faster, Flare vs Sunburst tiers | You can now animate a product shot without opening an editor |
| 3 | **OpenAI Dots for ChatGPT Enterprise** | Agent feature (GA Nov 4, default Nov 18) | Personal agents that keep working between conversations; admins must opt out NOW | Your ChatGPT is about to get an always-on coworker — admins, check the switch |
| 4 | **Kimi K3.1 Pro (Moonshot AI)** | Model drop | 2.8T-param open-weight multimodal, trending #3 on HF | The biggest open-weight multimodal model you can actually download |
| 5 | **Lightricks LTX-2.5** | Model drop | image-to-video, 11k likes, trending top-5 on HF | Free-weights video model with the fastest momentum this week |
| 6 | **Vercel agent-desktop** | CLI/tool launch (Nov 7) | OS-level computer control for agents across macOS/Windows/Linux, trending on GitHub | A standard way for an agent to literally use your desktop |
| 7 | **pinky / phoneuse — agents on your phone** | Repo + tool pattern | 523★ and 314★ in a day; agent drives a real phone with you in the loop | AI agents moved from your browser to your pocket |
| 8 | **NVIDIA Nemotron 3.5 Transcribe (30B)** | Model drop | open ASR model, top-15 trending on HF | Speech-to-text you can self-host at near-whisper-plus quality |
| 9 | **Mistral Studio** | Platform launch (early Nov) | Agent/workflow builder on Mistral Large 4, fully self-hostable | Europe's answer to agent platforms: runs on your own servers |
| 10 | **Qwen 3.8-27B** | Model drop | image-text-to-text, 19k likes, trending on HF | The mid-size multimodal everyone is fine-tuning this week |

## Watchlist (not top-10 today)
- Alysis Code — open-source multi-model desktop agent, $1/mo hosted (Product Hunt, Nov 7)
- Thinking Machines Inkling 2 Small via Tinker — 594B-param model with image inputs (Nov 5)
- speridlabs/idol — image-to-3D, #1 HF model trend (needs a real visual demo verified)
- Flux 3 Klein (Black Forest Labs) — image-to-image, trending (overlaps past FLUX coverage)

## Excluded (already covered or scheduled — never re-recommend)
unslop · poki · superagent · autoloop · vork · dsh-go · reavideo · sand3d · craft-anything
· muse / muse-spark · scm · papermorph (held), plus the 51 pruned expired entries.
