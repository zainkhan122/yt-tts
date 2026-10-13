# Shorts topic shortlist — 2026-10-13

**Status (updated 2026-10-14): SolidCraft r3 pilot accepted; the owner authorized production of the remaining four candidates on 2026-10-13.** The original target was five total, including the pilot. This authorizes production/rendering only—not scheduling, posting, Buffer writes, or permanent Release creation. Dynamic repository/model facts were refreshed in the briefs on 2026-10-14. Reconcile live queue capacity and duplicate locks before any scheduling.

## Selection basis and publishing constraints

- The configured target is **5 videos today**; topics are selected from findings, not a fixed category mix. The eventual publish count still depends on live Buffer capacity.
- Discovery inputs: [today's 7-day idea feed](feed-2026-10-13.md) and [today's 14-day GitHub/Hugging Face radar](../radar/radar-2026-10-13.md). Channel views, consensus, stars/day, and HF trend scores are discovery signals, **not factual proof**.
- Primary sources below were checked for the core claims. Do not turn vendor benchmark claims into independent results.
- Local queue/tracker searches found known collisions for Meta Muse, Claude Motion, and Cloudflare Clef; those are excluded below. Exact-name searches for the candidates listed here did not surface a matching local queue/receipt item, with the Qwen and GPT-6 family-overlap caveats called out. **Live Buffer queue occupancy and duplicate locks remain unverified**; reconcile through the documented GitHub Actions route before scheduling anything.
- Scheduling remains `America/New_York`. No Buffer writes have been made.

## Candidates

### 1. Qwen-Image-2.1-Turbo — strongest broad-interest option

- **Discovery:** Qwen appeared in 6 watchlist channels (129,000 combined views across the broad Qwen topic). Separately, the exact `Qwen-Image-2.1-Turbo` entry ranked #3 on today's HF radar (trend score 633; 670 likes). The channel/view total is for Qwen generally, not this Turbo checkpoint.
- **Verified:** Qwen's repository dates Turbo to Oct 9 and says it supports text-to-image generation and image editing in 8 denoising steps, using the same 7B visual-generation architecture as Qwen-Image-2.1. The repository also announces the hosted Turbo API. [2](https://github.com/QwenLM/Qwen-Image-2.1)
- **Short angle:** “Qwen's image model gets an 8-step Turbo checkpoint.”
- **Guardrail:** Eight denoising steps do **not** prove 5× faster end-to-end generation. Downloaded weights use the Qwen Research License; don't describe them as commercially unrestricted. This is a different task/model from yesterday's Qwen3.8 video, but the brand is adjacent—check pacing before a same-day batch.

### 2. GPT-6 Intelligent UI — highest mainstream discovery signal

- **Discovery:** GPT-6 appeared in 4 watchlist channels (1,019,502 combined views across the broad GPT-6 cluster); that total is not specific to Intelligent UI.
- **Verified:** OpenAI announced the ChatGPT feature on Oct 7: answers can combine text, visuals, and interactive elements such as calculators, bill splitters, and games; the rollout began with paid plans and expanded to Free/Go the next day. [1](https://openai.com/index/gpt-6-for-everyone/)
- **Short angle:** “ChatGPT can answer with a tool you can use—not just a paragraph.”
- **Guardrail:** Keep the story on Intelligent UI, not model benchmarks. This is adjacent to the recent GPT-6.1 Astra coverage, but the feature itself is distinct; confirm the live queue before any scheduling.

### 3. EmbeddingGemma 2 — strongest model-specific HF signal

- **Discovery:** #1 on today's HF radar (trend score 1,838; 2,005 likes).
- **Verified:** Google's Oct 6 launch says the 740M-parameter model maps text, code, images, audio, and video into a shared embedding space and is released under Apache 2.0. Google's model card gives the technical details. [1](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/) · [Model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2)
- **Short angle:** “One search space for a voice memo, image, and video clip.”
- **Guardrail:** It is an embedding model, not a chat or media-generation model; a user-facing search experience still needs an app/pipeline. Attribute on-device and performance claims to Google.

### 4. SolidCraft — visual, agent-drivable CAD project

- **Discovery:** #11 on the Oct 13 GitHub radar. The fresh GitHub API snapshot at 10:06 UTC on Oct 13 superseded the earlier 1,314-star count with **1,339 stars**; the project released v0.3.2 on Oct 12. [Release page](https://github.com/bherbruck/solidcraft/releases)
- **Verified:** Its repository describes a pure-Rust parametric CAD app for desktop and browser, with agent control through MCP. The project says it is “early but usable for simple parts”; its reference-part checks do not establish full CAD compatibility. [1](https://github.com/bherbruck/solidcraft)
- **Short angle:** “An AI agent can edit a parametric 3D model—not just produce a mesh.”
- **Guardrail:** Do not call it a Fusion 360 replacement or imply production-grade compatibility. Show the app's actual early-stage status.

### 5. ManimGX — developer-focused animation engine

- **Discovery:** #17 on today's GitHub radar (1,053 stars; +150/day), with a repository change logged today.
- **Verified:** The project offers a Manim CE-compatible Python API, with a Rust/wgpu renderer and a browser path using WebGPU. [1](https://github.com/academa-labs/manimgx)
- **Short angle:** “Write Manim-style Python; render math animation through a Rust GPU engine.”
- **Guardrail:** The speed comparison on the repository is the project's own benchmark, not an independent test. Its own code is MIT-licensed, while native wheels include GPL-licensed x264; preserve that distinction if discussing licensing.

### Alternate: Anatomy — reconsider only with the updated signal in view

- **Discovery:** Today's radar lists 7,099 stars and +1,775/day; today's feed includes one 32,000-view mention. These are discovery measures, not validated audience demand.
- **Prior evaluation:** The Oct 12 shortlist scored Anatomy **47/100** (weak search signal/relevance at that time). The new surge is a material change worth reconsidering, but I have not rerun the search-demand scoring.
- **Verified:** The official repo describes an MIT Claude skill that builds interactive isometric SVG figures, with optional WebGL effects and 3D parts; v1.0.0 was released Oct 10. [1](https://github.com/wheresryan22/anatomy) · [v1.0.0](https://github.com/wheresryan22/anatomy/releases/tag/v1.0.0)
- **Short angle:** “A coding skill turns a technical idea into an interactive machine diagram.”
- **Guardrail:** Don't imply it is engineering CAD or that every generated diagram is technically validated. Re-score demand before putting it into a full batch.

## Deliberately excluded to protect existing coverage

- **Meta Muse / Muse Wonder:** local queue and publication records already contain `tool-muse-01` (“Meta Muse: The AI Agent That Does Your Chores”). Hold a follow-up until the live queue is reconciled.
- **Claude Motion:** already appears in `briefs/news-claude-free-01.json` and existing publication records.
- **Cloudflare Clef-omni:** the current queue and publication records contain `news-clef-01` (“Cloudflare Clef: a 27B Model That Can't Ramble”). Despite Clef-omni's newer multimodal update, do not add a second Clef video without an explicit owner decision after reconciliation.

## Next gate

The SolidCraft r3 pilot passed and the owner explicitly approved today's remaining four candidates for production. Render with approved Chatterbox Option-3; QA the actual font, first frame, cover crop, and mobile readability. No on-screen credit captions. The remaining renders do not imply scheduling or posting permission. Before scheduling any channel, use the documented GitHub Actions route to reconcile the live queue, capacity, duplicate locks, and cover behavior; preserve existing posts and use `America/New_York`.
