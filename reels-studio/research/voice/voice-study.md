# Voice study: how the reference creators deliver their scripts (2026-10-09)

Measured, not guessed: whisper.cpp word timings + Praat prosody (tools/voice_study.py). Audio deleted after analysis.

## Creators (27 videos) vs our current voice (2 videos)

| Metric | Creators (median) | Creators (range) | Ours (median) |
|---|---|---|---|
| pitch range (semitones) | 13.2 | 4.1–20.2 | 11.0 |
| pitch variation SD (st) | 5.2 | 3.18–8.19 | 4.7 |
| pitch movement (st / 100 ms) | 4.7 | 3.49–7.19 | 4.8 |
| loudness range (dB) | 29.1 | 13.5–33.9 | 24.8 |
| words per minute | 184 | 120–234 | 187.0 |
| speed change between phrases (%) | 14.0 | 5–34 | 13.0 |
| pauses per minute (>=150 ms) | 11.8 | 0.0–25.9 | 19.2 |
| average pause (s) | 0.3 | 0–0.48 | 0.3 |
| stressed words (%) | 3 | 0–18 | 2.5 |
| phrases ending with a pitch fall (%) | 100.0 | 0–100 | 100.0 |
| phrases ending with a pitch rise (%) | 0.0 | 0–25 | 0.0 |
| words per sentence | 12.7 | 4.1–164 | 12.8 |
| questions per 100 words | 0.9 | 0.0–2.6 | 0.9 |
| 'you' per 100 words | 5.4 | 0.0–9.5 | 5.2 |
| contractions per 100 words | 2.7 | 0.0–7.2 | 4.7 |

## Per video

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
| [lab: 1-kokoro-current](file:1-kokoro-current.mp3) |  | 190 | 9.6 | 5.05 | 24.7 | 21 | 23.1 | 4 | sends, asks, first, logs |
| [lab: 2-kokoro-ear-script](file:2-kokoro-ear-script.mp3) |  | 183 | 11.0 | 5.11 | 25.8 | 25 | 25.9 | 3 | before |
| [lab: 3-chatterbox-michael-neutral](file:3-chatterbox-michael-neutral.mp3) |  | 166 | 10.7 | 7.19 | 29.1 | 19 | 25.1 | 1 | asks |
| [lab: 4-chatterbox-michael-energetic](file:4-chatterbox-michael-energetic.mp3) |  | 165 | 14.6 | 5.34 | 33.9 | 11 | 19.7 | 2 | asks |
| [lab: 5-chatterbox-default-energetic](file:5-chatterbox-default-energetic.mp3) |  | 163 | 16.0 | 6.23 | 32.7 | 22 | 21.4 | 2 | first |
| [lab: 6-kokoro-current-onepass](file:6-kokoro-current-onepass.mp3) |  | 188 | 7.6 | 4.28 | 24.0 | 14 | 17.6 | 3 | sends, first |
| [lab: 7-kokoro-flow-script](file:7-kokoro-flow-script.mp3) |  | 199 | 13.0 | 5.21 | 23.6 | 17 | 19.7 | 3 | before, buys |
| [lab: 8-chatterbox-michael-flow](file:8-chatterbox-michael-flow.mp3) |  | 205 | 14.4 | 5.38 | 31.4 | 5 | 7.5 | 5 | own |
| [lab: 9-chatterbox-michael-flow-hype](file:9-chatterbox-michael-flow-hype.mp3) |  | 205 | 13.2 | 5.54 | 33.0 | 9 | 5.5 | 0 |  |
| [lab: production list-free-video-ai-01 (option 3, new script)](file:voiceover.mp3) |  | 176 | 17.4 | 4.96 | 30.4 | 13 | 18.0 | 2 | five, short, vel |
| [lab: production news-claude-free-01 (option 3, new script)](file:voiceover.mp3) |  | 192 | 16.9 | 4.54 | 33.4 | 12 | 9.6 | 3 | formatting, actually, survives, people |
| [lab: production repo-ai-newtab-01 (option 3, new script)](file:voiceover.mp3) |  | 172 | 18.3 | 3.49 | 31.6 | 13 | 15.0 | 2 | load |
| [lab: production repo-scm-01 (option 3, new script)](file:voiceover.mp3) |  | 160 | 9.7 | 4.62 | 33.6 | 19 | 11.3 | 2 | 6, days |
| [lab: production spotlight-papermorph-01 (option 3, new script)](file:voiceover.mp3) |  | 162 | 11.8 | 5.26 | 31.4 | 14 | 12.8 | 1 |  |
| [lab: production tool-muse-01 (option 3, new script)](file:voiceover.mp3) |  | 193 | 19.2 | 5.21 | 30.8 | 14 | 10.4 | 2 | first |
| [ours: kokoro clean (muse script)](file:ours-kokoro-clean.wav) |  | 186 | 9.5 | 5.12 | 24.8 | 17 | 22.6 | 3 | sends, asks, first |
| [ours: tool-muse-01 final mix (separated)](file:tool-muse-01.mp4) |  | 188 | 12.5 | 4.38 | 24.7 | 9 | 15.8 | 2 | logs |

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
- **lab: 1-kokoro-current**: "Meta's new AI agent Muse doesn't just chat. It fills in forms, shops, and books trips for you. Here it"
- **lab: 2-kokoro-ear-script**: "Meta just dropped an AI that actually does your chores. It's called Muse. You text it and it fills out"
- **lab: 3-chatterbox-michael-neutral**: "Meta just dropped an AI that actually does your chores. It's called Muse. You text it and it fills out"
- **lab: 4-chatterbox-michael-energetic**: "Meta just dropped an AI that actually does your chores. It's called Muse. You text it and it fills out"
- **lab: 5-chatterbox-default-energetic**: "Metagis dropped an AI that actually does your chores. It's called Muse. You text it and it fills out forms,"
- **lab: 6-kokoro-current-onepass**: "Meta's new AI agent muse doesn't just chat. It fills in forms, shops, and books trips for you. Here it"
- **lab: 7-kokoro-flow-script**: "Meta just dropped an AI that actually does your chores and it's called Muse. You text it like a friend,"
- **lab: 8-chatterbox-michael-flow**: "Metagis dropped an AI that actually does your chores and it's called Muse. You text it like a friend and"
- **lab: 9-chatterbox-michael-flow-hype**: "Meta just dropped an AI that actually does your chores and it's called Muse. You text it like a friend"
- **lab: production list-free-video-ai-01 (option 3, new script)**: "Okay, three AI video generators that are actually free, and I checked the real limits so you don't get burned."
- **lab: production news-claude-free-01 (option 3, new script)**: "Okay, this is a big one. Clawed slides. Docs in design just left beta and they're now on the free"
- **lab: production repo-ai-newtab-01 (option 3, new script)**: "Okay, someone at Anthropic just built an AI homepage that literally writes itself. It reads your browsing history, opens up"
- **lab: production repo-scm-01 (option 3, new script)**: "Okay, imagine describing a memory, and this AI photo search finds the exact shot. You just type something like "Happy"
- **lab: production spotlight-papermorph-01 (option 3, new script)**: "Okay, this AI turns a boring PDF into a narrated, animated book, and it's kind of amazing. This algebra book"
- **lab: production tool-muse-01 (option 3, new script)**: "Okay, meta just dropped an AI agent called Muse, and it doesn't just chat, it actually does your chores. You"
