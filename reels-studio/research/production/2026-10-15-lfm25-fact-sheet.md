# LFM2.5-24B-A2B — fact sheet (checked 2026-10-15)

Primary sources: HF model card `LiquidAI/LFM2.5-24B-A2B` + HF API (checked 2026-10-15T10:31Z).

- 24.0B total parameters, ~2.45B active per token (say "about two billion"); 64 experts per MoE block, top-4 routing; 40 layers; 131,072-token context; trained on ~36T tokens.
- Purpose: fast, private on-device agents; pure reasoning model that always thinks before answering (mandatory catch).
- Vendor-reported speed: up to 184 tok/s on an Apple M5 Max; up to 1.7x faster than comparable MoEs on-device. These are Liquid AI's figures, attributed on screen and in speech ("Liquid AI reports").
- Agentic claim: 48.09 vs 38.19 (Qwen3.6-35B-A3B) on LiveClaw per vendor card — not spoken (unverified benchmark name risk).
- Formats: native, FP8, GGUF (llama.cpp), ONNX, MLX-4bit (Apple Silicon) — separate HF repos.
- Vendor recommendation: not for knowledge-heavy tasks alone; pair with retrieval/web search (mandatory catch).
- License: weights under Liquid's LFM 1.0 licence (HF `license_name: lfm1.0`) — NOT Apache/MIT; never call it unrestricted open source. HF API at check: 6,286 downloads, 341 likes, created 2026-10-12.
- No local run claimed: the 24B model was not executed in our sandbox; visuals are our own spec/formats cards made for this video.
