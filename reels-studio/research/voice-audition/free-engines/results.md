# Free voice engines: audition 2026-10-08

All engines read the same script: "Okay, this is wild! Someone just put Minecraft inside GTA Five, and an AI agent built the
whole thing. The best part? It's completely free, and it hit almost five thousand GitHub stars in one week!"
Generated on GitHub Actions (4 vCPU, free for public repos) by `.github/workflows/voice-audition.yml` and scored by
`voice-score.yml` (`cloud/tts_audition.py`).

- **naturalness** = UTMOS (predicted human rating 1-5; real speech ~4.0-4.5)
- **melody** = pitch range p10-p90 in semitones (higher = livelier)
- **whisper** = words wrong; **gen** = seconds to generate on 4 vCPU

| option in `00-compare-6-free-voices.mp3` | sample | naturalness | melody | wpm | whisper | gen | license |
|---|---|---|---|---|---|---|---|
| 1 | af_heart voice via Chatterbox, emotion 1.0 | 4.43 | 9.6 | 167 | 2.7% ("Okay" dropped) | 109 s | MIT (inaudible PerTh watermark) |
| 2 | af_heart voice via Chatterbox Turbo | **4.47** | 8.9 | 147 | 0% | **30 s** | MIT |
| 3 | Microsoft Emma (Edge online voice) | 4.38 | **12.3** | 174 | 0% | 3 s | free but UNOFFICIAL endpoint (official route: Azure free tier F0) |
| 4 | Microsoft Ava (Edge online voice) | 4.35 | 9.7 | 165 | 0% | 8 s | same as Emma |
| 5 | Orpheus Tara | 4.33 | 6.6 | 162 | 0% | 123 s | Apache-2.0 (Llama-3.2 base) |
| 6 | Chatterbox default voice (male), emotion 0.8 | 4.23 | 11.7 | 227 | 0% | 67 s | MIT |

Also measured (not in the comparison file):

| sample | naturalness | melody | note |
|---|---|---|---|
| Kokoro af_heart raw x1.1 | 4.51 | 8.8 | natural but flat; **interim channel default** |
| Chatterbox af_heart, emotion 0.75 | 4.46 | 8.8 | |
| Chatterbox default (male), emotion 0.5 | 4.44 | 13.8 | |
| Edge Andrew (male) | 4.07 | 13.2 | |
| Orpheus Leo (male) | 3.98 | 12.9 | 5.4% whisper errors |
| Qwen3 Ryan (male), "excited" instruct | 3.95 | 13.6 | slow (131 wpm) |
| Chatterbox Turbo default voice | 3.95 | 7.7 | |
| Qwen3 VoiceDesign "energetic female" | 3.71 | 9.0 | pitch 345 Hz, unnaturally high |
| **Kokoro "maxhype" DSP chain** | **3.68** | 11.6 | **user: robotic, retired** |
| Chatterbox af_heart, emotion 1.3 | 3.67 | 12.4 | too much: naturalness collapses |
| Chatterbox Nano | 3.18 | 9.0 | fast (1x realtime) but low quality |

**Lessons**
- DSP pitch/melody tricks add energy but cost ~0.8 naturalness: the "robotic" sound.
- Real energy has to come from the engine.
- Chatterbox copies the reference clip's *style* as well as its timbre, so the flat Kokoro reference limits liveliness. Emotion 1.0 is the ceiling before artifacts.
- Edge voices are the liveliest natural female voices, but they use an unofficial endpoint. The same voices are licensed via Azure Speech free tier F0 (0.5M chars/month; needs an Azure account with card verification).
