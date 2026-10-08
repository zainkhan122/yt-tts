# Channel voice: decision record

**Chosen (user, 2026-10-08): Kokoro `am_michael` ×1.15, no voice FX**, set in `config/channel.json`.
Speech runs at about 150–165 wpm, so a 35–45 s video needs about 90–105 words.

## History (all auditions were done with the same script; audio files deleted 2026-10-08 to keep the repo lean)
1. Five Kokoro voices compared (af_heart, af_bella, bf_emma, am_michael, am_puck at ×1.15). The user first picked af_heart.
2. "More energetic" round 1: DSP presets B (energetic), D (hype: per-line accents, +0.8 st, EQ, 4:1 compression), E (D + af_bella).
3. "Max hype" round: F = D + Praat melody expansion ×1.45. The user said it was **robotic**. Measured naturalness (UTMOS) confirmed it:
   3.68 vs 4.51 for raw Kokoro. Lesson: DSP pitch/melody tricks cost naturalness. Real energy must come from the engine or the script.
4. Free engines audition on GitHub Actions (same script, UTMOS + whisper scoring). See the table below.
5. The user approved D-hype for video #1, then switched to **am_michael ×1.15** (plain Kokoro, as in the first audition).

## Free engines measured 2026-10-08 (UTMOS = predicted human naturalness 1–5; melody = pitch range in semitones)
| option in `00-compare-6-free-voices.mp3` | sample | naturalness | melody | wpm | whisper | gen | license |
|---|---|---|---|---|---|---|---|
| 1 | af_heart voice via Chatterbox, emotion 1.0 | 4.43 | 9.6 | 167 | 2.7% ("Okay" dropped) | 109 s | MIT (inaudible PerTh watermark) |
| 2 | af_heart voice via Chatterbox Turbo | **4.47** | 8.9 | 147 | 0% | **30 s** | MIT |
| 3 | Microsoft Emma (Edge online voice) | 4.38 | **12.3** | 174 | 0% | 3 s | free but UNOFFICIAL endpoint (official route: Azure free tier F0) |
| 4 | Microsoft Ava (Edge online voice) | 4.35 | 9.7 | 165 | 0% | 8 s | same as Emma |
| 5 | Orpheus Tara | 4.33 | 6.6 | 162 | 0% | 123 s | Apache-2.0 (Llama-3.2 base) |
| 6 | Chatterbox default voice (male), emotion 0.8 | 4.23 | 11.7 | 227 | 0% | 67 s | MIT |

Licences: Chatterbox MIT (inaudible PerTh watermark), Orpheus Apache-2.0, Qwen3-TTS Apache-2.0, Kokoro Apache-2.0.
The Microsoft Edge voices use a free but unofficial endpoint; Azure Speech F0 is the licensed route.
If the voice ever changes, re-audition with the same script and keep this record updated.
