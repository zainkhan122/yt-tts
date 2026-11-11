# Voice study: how the reference creators deliver their scripts (2026-10-09)

Measured, not guessed: whisper.cpp word timings + Praat prosody + Silero VAD; creators' voices separated from music
(UVR MDX-Net) first (tools/voice_study.py). Audio deleted after analysis.

## Creators (12 videos) vs our old voice vs the approved voice (voice-lab option 3) vs published videos (6)

| Metric | Creators (median) | Creators (range) | Old Kokoro voice | Approved sample (option 3) | Published videos (median) |
|---|---|---|---|---|---|
| pitch range (semitones) | 13.4 | 4.1–20.2 | 11.0 | 14.4 | 17.9 |
| pitch variation SD (st) | 5.0 | 3.19–8.19 | 4.7 | 5.3 | 6.9 |
| pitch movement (st / 100 ms) | 4.2 | 3.53–5.96 | 4.8 | 5.4 | 4.8 |
| loudness range (dB) | 24.0 | 13.5–32.9 | 24.8 | 31.4 | 31.8 |
| words per minute | 184.5 | 120–234 | 187.0 | 205 | 174.0 |
| speed change between phrases (%) | 17 | 11–34 | 13.0 | 5 | 13.0 |
| pauses per minute (>=150 ms) | 1.5 | 0.0–24.1 | 19.2 | 7.5 | 13.8 |
| average pause (s) | 0.2 | 0–0.48 | 0.3 | 0.3 | 0.3 |
| stressed words (%) | 3.5 | 1–18 | 2.5 | 5 | 2.0 |
| phrases ending with a pitch fall (%) | 100.0 | 50–100 | 100.0 | 0 | 100.0 |
| phrases ending with a pitch rise (%) | 0.0 | 0–25 | 0.0 | 0 | 0.0 |
| words per sentence | 15.6 | 4.1–164 | 12.8 | 15.9 | 12.1 |
| questions per 100 words | 0.0 | 0.0–2.2 | 0.9 | 0.9 | 1.6 |
| 'you' per 100 words | 3.0 | 0.0–9.5 | 5.2 | 7.3 | 5.1 |
| contractions per 100 words | 1.6 | 0.0–7.2 | 4.7 | 2.7 | 4.3 |

## Creators, per video

| Video | Views | wpm | pitch range | movement | loud range | speed var | pauses/min | stressed % | stressed words (sample) |
|---|---|---|---|---|---|---|---|---|---|
| [Fireship (YT Shorts)](https://www.youtube.com/shorts/aXcuz6fn8_w) | 5222830 | 159 | 13.8 | 4.63 | 19.4 | None | 0.0 | 3 | 2, invented, angular |
| [GithubAwesome (YT Shorts)](https://www.youtube.com/shorts/mOGbXAjnPg4) | 24969 | 183 | 4.1 | 4.71 | 29.2 | 17 | 14.5 | 3 |  |
| [aiadvantage (YT Shorts)](https://www.youtube.com/shorts/e24bFPEYooY) | 39174 | 219 | 12.6 | 3.53 | 25.6 | None | 0.0 | 2 | syncing |
| [malvaAI (YT Shorts)](https://www.youtube.com/shorts/qQSPmNouL7E) | 210956 | 192 | 13.1 | 4.16 | 32.9 | 21 | 22.3 | 7 | pay, free, after, days, right, now |
| [mreflow (YT Shorts)](https://www.youtube.com/shorts/tqUEnRj0NbM) | 29970 | 206 | 15.5 | 5.68 | 24.3 | None | 1.3 | 4 | sketch, unlit, hologram, opinion, looks, right |
| [vaibhavsisinty (YT Shorts)](https://www.youtube.com/shorts/Vtl1CrwOt6o) | 1082512 | 120 | 18.8 | 5.96 | 31.3 | 13 | 7.3 | 1 | built |
| [remy_engineering (TikTok)](https://www.tiktok.com/@remy_engineering/video/7681328292758113568) | 709100 | 127 | 8.0 | 4.08 | 24.5 | 34 | 24.1 | 9 | convert, everything, windows, press, wt, type |
| [dr_cintas (TikTok)](https://www.tiktok.com/@dr_cintas/video/7689483990666923277) | 38900 | 185 | 16.4 | 4.05 | 19.2 | None | 1.6 | 9 | open, basically, full, production, comes, 100, reference, built-in |
| [sabrina_ramonov (TikTok)](https://www.tiktok.com/@sabrina_ramonov/video/7693210171316784397) | 459500 | 234 | 20.2 | 4.09 | 19.4 | None | 1.3 | 3 | cool, sticky, material |
| [github.signals (TikTok)](https://www.tiktok.com/@github.signals/video/7693953373057453333) | 117200 | 169 | 12.1 | 4.16 | 23.6 | 11 | 11.8 | 7 | graphics, card, performance, much, windows |
| [zaindevx_ (TikTok)](https://www.tiktok.com/@zaindevx_/video/7685703638597111060) | 24900 | 184 | 15.2 | 4.51 | 20.2 | None | 0.0 | 18 | github, has, ai, devops, agent, cursor, codex, i'll |
| [ai_vanta_ai (TikTok)](https://www.tiktok.com/@ai_vanta_ai/video/7688103789248728353) | 255700 | 202 | 7.4 | 4.1 | 13.5 | None | 0.0 | 3 | tool, first, explore |

## Our old voice

| Sample | wpm | pitch range | pauses/min | average pause | speed var | stressed % |
|---|---|---|---|---|---|---|
| ours: kokoro clean (muse script) | 186 | 9.5 | 22.6 | 0.32 | 17 | 3 |
| ours: tool-muse-01 final mix (separated) | 188 | 12.5 | 15.8 | 0.28 | 9 | 2 |

## Voice lab samples (2026-10-09)

| Sample | wpm | pitch range | pauses/min | average pause | speed var | stressed % |
|---|---|---|---|---|---|---|
| lab: 1-kokoro-current | 190 | 9.6 | 23.1 | 0.26 | 21 | 4 |
| lab: 2-kokoro-ear-script | 183 | 11.0 | 25.9 | 0.3 | 25 | 3 |
| lab: 3-chatterbox-michael-neutral | 166 | 10.7 | 25.1 | 0.33 | 19 | 1 |
| lab: 4-chatterbox-michael-energetic | 165 | 14.6 | 19.7 | 0.31 | 11 | 2 |
| lab: 5-chatterbox-default-energetic | 163 | 16.0 | 21.4 | 0.4 | 22 | 2 |
| lab: 6-kokoro-current-onepass | 188 | 7.6 | 17.6 | 0.37 | 14 | 3 |
| lab: 7-kokoro-flow-script | 199 | 13.0 | 19.7 | 0.31 | 17 | 3 |
| lab: 8-chatterbox-michael-flow | 205 | 14.4 | 7.5 | 0.29 | 5 | 5 |
| lab: 9-chatterbox-michael-flow-hype | 205 | 13.2 | 5.5 | 0.31 | 9 | 0 |

## Published videos (approved voice, clean voiceover.mp3)

| Sample | wpm | pitch range | pauses/min | average pause | speed var | stressed % |
|---|---|---|---|---|---|---|
| prod: list-free-video-ai-01 | 176 | 17.4 | 18.0 | 0.27 | 13 | 2 |
| prod: news-claude-free-01 | 192 | 16.9 | 9.6 | 0.26 | 12 | 3 |
| prod: repo-ai-newtab-01 | 172 | 18.3 | 15.0 | 0.33 | 13 | 2 |
| prod: repo-scm-01 | 157 | 13.5 | 12.5 | 0.34 | 13 | 1 |
| prod: spotlight-papermorph-01 | 161 | 19.7 | 15.6 | 0.31 | 14 | 3 |
| prod: tool-muse-01 | 193 | 19.2 | 10.4 | 0.27 | 14 | 2 |

## Hook excerpts (first 20 words)

- **Fireship (YT Shorts)**: "1990. HTML is invented. 94. CSS invented to fix HTML. 95. JavaScript invented to fix HTML and CSS. 06. jQuery"
- **GithubAwesome (YT Shorts)**: "Jev Ultrafast clicks through a web page without generating a single coordinate or selector. Most browser agents screenshot the page,"
- **aiadvantage (YT Shorts)**: "GPT-6 Astra is here and it's not just you know better at doing typical tasks It does a whole new"
- **malvaAI (YT Shorts)**: "Just look, think it's real? It's not. And you probably think you know who made this. Google? Open AI? Nope."
- **mreflow (YT Shorts)**: "This new AI model lets you 3D print anything. It's called TRIPO 2.0 and it can take an image, turn"
- **vaibhavsisinty (YT Shorts)**: "An Indian startup has done something that even the navies of America and China couldn't. A ship sets sail from"
- **remy_engineering (TikTok)**: "Never upload a private video to a random converter. Once you upload it, you have no idea how that website"
- **dr_cintas (TikTok)**: "I just found an open source AI that makes entire YouTube videos from start to finish. It's basically a full"
- **sabrina_ramonov (TikTok)**: "10 secret codes for chat to be team news number one make visual study guide when you type this you're"
- **github.signals (TikTok)**: "Run PS5 games directly on your own computer without any emulation or fake hardware layers. Any PS5 takes the actual"
- **zaindevx_ (TikTok)**: "This GitHub repo is a goldmine for AI developers. It has 230+ specialized AI agents for different jobs. Frontend, backend,"
- **ai_vanta_ai (TikTok)**: "A geography professor just built a free, open-source GIS tool that does what Quantum GIS and Google Earth Pro charge"
