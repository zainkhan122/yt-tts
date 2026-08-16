# 🎙️ FREE TTS — The Plan (Tested & Working)

**Verified August 2026:** I tested the options live in the workspace. Here's what works.

---

## ✅ WHAT I CONFIRMED WORKS (in my workspace)

| Option | Status | Quality | Cost |
|---|---|---|---|
| **Kokoro 82M** (local, ONNX) | ✅ Works — near real-time on CPU | Very good — natural, warm voices | **$0 forever** |
| **Microsoft Edge-TTS** (neural voices) | ✅ Works | Excellent (Microsoft neural) | $0 (unofficial API) |

Samples generated for you to listen to: `tts_test/`
- `kokoro_af_heart.mp3` — warm female (my top pick for this niche)
- `kokoro_am_michael.mp3` — warm deep male
- `kokoro_am_adam.mp3` — male
- `kokoro_af_nicole.mp3` — expressive female
- `edge_christopher.mp3` — Microsoft "Christopher" (warm male)
- `edge_andrew.mp3` — Microsoft "Andrew" (deep male)

---

## 🏆 MY RECOMMENDATION: Let ME generate voiceovers with Kokoro

**Why this beats everything else for you right now:**

1. **$0, forever** — open-source Apache/MIT licensed, no account, no API key, no usage limits
2. **Zero setup for you** — I run it in the workspace and hand you the MP3
3. **Perfectly consistent voice** — same voice name + same speed = identical voice identity across all 100 videos (this is the #1 rule for faceless channels)
4. **No monthly cap** — ElevenLabs free = 10 min/month; Kokoro = unlimited
5. **Good enough quality** — honest take: it's ~85-90% of ElevenLabs. For a calm psychology narration, listeners won't know the difference. ElevenLabs has slightly more emotion/expressiveness — worth upgrading to later, but not required to start.

**The workflow:**
```
I write voiceover.txt → I run Kokoro in the workspace → you get voiceover.mp3 → I assemble the video
```

You do *nothing* for TTS. I handle it end-to-end.

**When you're earning:** switch to ElevenLabs ($5/mo Starter) and just attach the MP3 instead — the pipeline accepts either. No rework.

---

## 📋 THE OTHER FREE OPTIONS (ranked)

### 1. Kokoro 82M — run it YOURSELF (if you ever want to)
- **On your PC:** install [Kokoro TTS](https://github.com/hexgrad/kokoro) or use [LM Studio](https://lmstudio.ai) / [Pinokio](https://pinokio.computer) (one-click local AI apps)
- **No GPU needed** — Kokoro was built for CPU
- Full list of voices: af_heart, af_nicole, am_michael, am_adam, bf_emma (British!), and more

### 2. Microsoft Edge-TTS (free, no key)
- `pip install edge-tts` → one line generates an MP3
- Excellent quality, but: **unofficial API** (could break), and the voices are recognizable as "the Microsoft voice" used by thousands of AI channels

### 3. Chatterbox (Resemble AI, best open-source quality)
- **Not in my workspace** — it needs a GPU/heavy build, so I can't run it here
- **You CAN host it free yourself:**
  - **LM Studio** (free desktop app) — download the Chatterbox GGUF model, runs on your PC
  - **Google Colab** (free tier) — run the official Chatterbox notebook
  - **Hugging Face Space** (free CPU) — there's a community Chatterbox space you can duplicate
- Best used when you're earning and want near-ElevenLabs quality for $0

### 4. Official cloud free tiers (stable, need account signup)
| Service | Free tier |
|---|---|
| **Google Cloud TTS** | 1M characters/month (~2 hrs audio) |
| **Amazon Polly** | 5M characters/month (12 months) |
| **ElevenLabs** | 10 min/month |

---

## 🎯 VOICE SELECTION (pick ONE, forever)

For a psychology channel aimed at INFJ/INFP (skews female but attracts both), warm + calm + slightly low is ideal.

| If you want… | Pick |
|---|---|
| Warm female narrator (soft, soothing — most common in this niche) | Kokoro **af_heart** |
| Warm deep male (calm authority) | Kokoro **am_michael** |
| Male, Microsoft polish | edge **Christopher** |

**Speed:** 1.0 is good. For a more "slow, contemplative" psychology feel, try **0.95**.

**Listen to the samples in `tts_test/` → tell me which voice + speed → I'll lock it in and generate ALL the month's voiceovers with it.**
