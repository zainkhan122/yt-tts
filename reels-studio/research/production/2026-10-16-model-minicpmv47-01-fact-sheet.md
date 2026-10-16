# MiniCPM-V 4.7 (35B-A3B) — fact sheet (checked 2026-10-16)
Sources: HF model card openbmb/MiniCPM-V-4.7-35B-A3B + HF API (2026-10-16T08:20Z).
- Vision-language MoE: 35B total, 3B active; single/multi-image + video understanding. Apache-2.0 (HF API). 9,278 downloads, 808 likes.
- Vendor claim (attribute): 13+ tok/s at ~3 GB memory on iPhone 17 Pro Max via Lookahead Expert Scheduling + layer-wise quantization + DSpark. We did not run it.
- iOS/Android/HarmonyOS; GGUF/BNB/AWQ/GPTQ + FP8; SGLang, vLLM, llama.cpp, Ollama.
- Catches spoken: phone speed is the vendor's own test; full weights are still a large download (quantized builds exist).
