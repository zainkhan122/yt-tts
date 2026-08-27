# ⚖️ MASTER RULES — THRESHOLD
### Faceless finance explainer. The face of the channel is the graphics.
*Forked from yt-tts R1–R26 (psychology) — only rules that still apply. Finance-specific rules added.*
*If a rule is violated, the video is NOT done.*
*Last updated: 2026-08-27*

**Show:** THRESHOLD  
**Fence (F22):** Sourced money *mechanisms* and *milestones*, shown as motion graphics, for English-speaking 25–40 year olds who feel behind.  
**We are NOT:** stock tips, crypto, day-trading, tax prep, hustle porn, talking-head, Pexels slideshows, generic “10 money tips.”

---

## F22. NICHE FENCE (was R22 — rewritten)
Every topic must pass:
> “Does this name a money mechanism or milestone the viewer can *see on a chart*, with a sourced number — without telling them what to buy?”
If a motivation channel, a trading channel, or a hustle channel could publish it unchanged → **REJECT**.

---

## F1. VISUAL SYSTEM (was R1 — rewritten, no Pexels-as-look)
1. The default visual is a **chart, diagram, stat card, or branded illustration**. Not stock footage.
2. Every long-form gets a **new** scene pool: ≥8 original chart/diagram scenes + ≥6 branded illustrated stills. Never reuse another video’s renders.
3. Photographic stills only when the **object is the point** (a specific car, house, receipt). Ban: “man with laptop,” “woman holding coins,” Bitcoin neon, yacht flex, handshake-skyline.
4. No Pexels/Pixabay/Storyblocks as the *look* of the channel. (F29)
5. One chart style across the channel (F13 tokens). Data changes; the system does not.
6. **CAP:** no single scene used more than 2× per video.
7. VERIFY at storyboard: distinct-scene count. FAIL if any scene >2×.

---

## F2. CAPTION SYNC (was R2 — keep)
1. Every caption is anchored to a **keyword** in the script.
2. Captions applied on the absolute shared timeline. Hold ~2.6s. Each display once.
3. Numbers on captions use the brand accent color.
4. VERIFY at finalize: print every caption time. Missing/duplicate → fail.

---

## F3. REPO IS SOURCE OF TRUTH (was R3 — keep, new path)
1. **GitHub `zainkhan122/yt-tts` folder `finance/` = source of truth. Workspace = scratch.**
2. Every step idempotent + resumable (`videos/NNN/state.json`).
3. Fail LOUD. Never mark a failed step done.
4. Push via `tools/repo_sync.py`. Do not full-clone the psychology vault.
5. Back up generated charts/illustrations to the repo the same turn they are made.

---

## F4. QUALITY BAR (was R4 — keep, finance timing)
1. Visual change every 3–5s.
2. 8–11 min long-form ≈ 100–140 beats, 20–28 captions.
3. Hook in the first 2 sentences. End with a comment-driving question.
4. First visual must **mirror** the first spoken line (a number or contradiction on screen).

---

## F5. VOICE (was R5 — UNLOCKED until audition)
- Do **not** reuse Kokoro `af_heart` (that is The Deeper Mind).
- Lock one voice after an `add_voice` audition. Then never change it.
- Until locked: scripts are written as if spoken; TTS is a later step.
- Voice config lives in `reusable/voice_config.json`.

---

## F6. DELIVERY CHECKLIST (was R6 — keep)
- [ ] final.mp4 1080p/30fps, ~8–11 min, decode spot-check 4 timestamps
- [ ] caption schedule printed + verified (F2)
- [ ] visual-system verified (F1) — charts present, no banned stock
- [ ] every on-screen number sourced (F27)
- [ ] disclaimer spoken in first 15s + in description (F28)
- [ ] synthetic-content disclosure ready (F30)
- [ ] metadata.md passes `qa_pack.py` (F26)
- [ ] thumbnail approved (F8)
- [ ] pushed to `finance/` in the repo

---

## F7. BUILD ORDER (was R7 — adapted)
```
(a) topic + sources + script + metadata pack (qa_pack)
(b) storyboard + chart list + verify F1/F27
(c) render motion scenes (motion_kit) + illustrated stills
(d) TTS (after voice lock)
(e) assemble + captions
(f) thumbnail + finalize + qa_pack again + push
```
**One step per turn (F16).**

---

## F8. THUMBNAIL (was R8 — rewritten for no-face)
1. **Title identifies. Thumbnail diagnoses.** They never repeat each other.
2. Thumbnail text: **2–4 words**. White or gold, thick dark stroke, readable at 120px. No questions.
3. Image = a chart-still, object, crowd, or branded graphic. **Not a creator face we don’t have.**
4. Diagnosis-line bank in VIDEO_QUEUE.md. Never repeat a concept.
5. Vary composition vs the last 3 (chart-hero / object-hero / split / big-number).
6. Measure text width before composite. Never overflow the frame.
7. Present for approval before it is final.

---

## F9. DOUBLE-VERIFY (was R9 — keep)
After every step: check, print, stop on fail. First-chunk gate still applies once we render.

---

## F10. CONTINUOUS IMPROVEMENT (was R10 — keep)
When a mistake ships, add a check so that class of mistake cannot ship again.

---

## F11. TITLE FORMULA VARIETY (was R11 — keep, finance templates)
No 3 consecutive videos share the same formula. Rotate:
- Why…
- Claim-statement (no question)
- List + number (“3 Net Worth Numbers…”)
- If I started…
- Don’t / Never…
- Signs / Once you…

Track last 2 formulas in VIDEO_QUEUE.md.

**F26 overlay:** ≤60 chars. Primary keyword in first 5 words.

---

## F12. SCRIPT (was R12 — keep + finance hook)
1. Hook ≤ 2 sentences. First sentence = contradiction, number, or diagnosis. No greeting.
2. Midpoint interrupt ~50%: a sourced story, a question, or a chart reveal.
3. Never reuse signpost furniture two videos in a row.
4. Closer = comment-driving question.
5. Spoken keyword in first 60s.
6. **Numbers are required** (the old psych TTS “no digits” check is **void**). Write numbers in speakable form (“twenty thousand dollars”) in `voiceover.txt`; digits OK on-screen.

Skeleton:
```
0:00–0:15  HOOK + spoken disclaimer
0:15–2:00  MIRROR the viewer’s life
2:00–6:00  MECHANISM (named, sourced, on a chart)
6:00       MIDPOINT interrupt
6:00–9:30  SHIFT (framework, not a ticker)
9:30–11:00 CLOSER question
```

---

## F13. BRAND / PALETTE (was R13 — rewritten)
Locked tokens in `brand/tokens.json`:
- Navy `#0B1F33` · Gold `#F4C15D` · Paper `#F4F1EA` · Alert `#E23D28` · Grid `#1C3348`
- Type: DejaVu Sans Bold (thumb/captions) until a licensed font is added
- Chart: gold fills, paper labels, navy ground, source line in 10px grid-grey
Adjacent videos may shift *mood* (gold-on-navy vs paper-on-navy vs alert accent) but never the tokens.

---

## F14 / F20. AUDIO (was R14/R20 — keep mix targets, new bed later)
- Loudnorm −16 LUFS / TP −1.5
- Bed ducked under voice (pad ~0.55, sidechain ratio 3) once a bed exists
- No lyric music. No stock “corporate ukulele.”

---

## F15. AUTO-CLEANUP (was R15 — keep)
When a video is downloaded / before a new one: delete that video’s workspace renders, keep sources + finals in repo. Clean `/tmp` at the start of build work.

---

## F16. ONE STEP PER TURN (was R16 — keep, user-mandated)
Do not chain a whole build in one turn. End every turn with one-line status + exact next step in HANDOFF.md + STATUS.md.

---

## F17. PRE-FLIGHT (was R17 — keep)
Before heavy steps: `df /tmp` (>300MB), workspace size, time budget. Print the numbers.

---

## F18. SCENE VARIETY (was R18 — adapted)
Use unused scenes before reusing. Min reuse distance 26 beats. Seeded-random motion. `verify.py storyboard` must FAIL if reuse is tight.

---

## F19. SESSION RESET (was R19 — keep, secrets changed)
1. Run `python3 tools/bootstrap.py` at the start of every *build* session.
2. **Update HANDOFF.md first** every session (F25), even if not building.
3. Secrets: `secrets/github_pat.txt` only (no Pexels key). If missing → stop and ask. Never guess.

---

## F21. CADENCE + SHORTS (was R21 — keep counts, rewrite media)
1. **2 long-form / week** (Tue + Fri), prime US evening.
2. **3 Shorts / week** (Mon/Wed/Sat) = hook + best self-contained payoff of existing longs. Never original-topic Shorts. Never the midpoint.
3. Shorts are **native 1080×1920**, 25–50s, own chart/illustration pool (F24).
4. End-CTA both text and spoken: “Full video on this channel.” Appended, never overlapping the last line.
5. Fence (F22) applies to Shorts.

---

## F23. TOPIC DEDUP (was R23 — keep, new columns)
VIDEO_QUEUE.md register: TITLE + MECHANISM + MILESTONE/NUMBER + thumb line + Short hook.
Duplicate if same “this is about me” hit OR same mechanism+number, even if title is reworded.

---

## F24. SHORTS MEDIA INDEPENDENCE (was R24 — keep, charts not stock)
Every Short gets its own motion scenes. Hook pool ≠ payoff pool. Never share renders between the two Shorts of a video.

---

## F25. HANDOFF FRESHNESS (was R25 — keep)
Update HANDOFF.md at the **start** of every session (and after any milestone). Push it. If HANDOFF and VIDEO_QUEUE disagree, VIDEO_QUEUE wins on progress.

---

## F26. TRAFFIC QUALITY GATE (was R26 — keep, finance hashtags)
`python3 tools/qa_pack.py VIDEO_DIR [keyword]` before any upload.
1. TITLE ≤60 chars, keyword in first 5 words, formula rotation (F11).
2. DESCRIPTION: keyword in first 150 chars, ≥200 words, chapters, comment CTA, F28 disclaimer.
3. HASHTAGS 3–5. First 3 = audience → topic → brand (`#personalfinance` `#networth` `#threshold`). Shorts must include `#Shorts`.
4. TAGS: exact keyword first, 5–10 variants, ≤500 chars.
5. THUMBNAIL F8.
6. SCRIPT: keyword spoken in first 60s; hook 2 sentences; first visual mirrors first line.
7. Pinned comment ready.

---

## F27. SOURCED NUMBERS (new — finance)
1. Every statistic on screen or in speech has a primary source (Fed SCF, BLS, CBO, IRS, ONS, academic paper).
2. Sources listed in the description under **Sources**.
3. Round for speech; exact figure + year in description.
4. Invented “average net worth” numbers = FAIL the build.
5. `videos/NNN/sources.md` exists before storyboard.

---

## F28. YMYL DISCLAIMER (new — finance)
1. Spoken in the first 15 seconds: “This is education, not financial advice.”
2. Full disclaimer in description (see `reusable/disclaimer.txt`).
3. Pinned comment repeats it.
4. Never “buy this,” “guaranteed,” “cheat code” about a specific security. “Cheat code” for a *public rule* (e.g. tax-advantaged account *as a concept*) requires extra care and a source.

---

## F29. NO PEXELS-AS-LOOK (new)
Stock photo/video libraries are not the channel’s visual identity. Motion kit + branded illustration only, with the F1 photographic exception.

---

## F30. SYNTHETIC DISCLOSURE (new — 2026 policy)
Every upload: YouTube Studio → Altered / synthetic content = **YES**. Original scripts + original charts are the defense against the inauthentic-content policy. Templated sameness across videos is a monetization risk — F1/F11/F12/F13 exist to prevent it.

---

## Rule map (psychology R* → this file)
| Psych | Finance | Keep / change |
|---|---|---|
| R1 new assets | F1 visual system | rewritten (charts, no Pexels) |
| R2 captions | F2 | keep |
| R3 git truth | F3 | keep, path `finance/` |
| R4 quality | F4 | keep |
| R5 Kokoro af_heart | F5 | **do not reuse that voice** |
| R6 checklist | F6 | + F27/F28/F30 |
| R7 build order | F7 | + sources step |
| R8 face thumb | F8 | rewritten no-face |
| R9–R10, R16–R17, R19, R25 | F9 F10 F16 F17 F19 F25 | keep |
| R11 titles | F11 | keep + finance templates |
| R12 script | F12 | keep; digits allowed |
| R13 mood | F13 | brand tokens |
| R14/R20 audio | F14/F20 | keep targets |
| R15 cleanup | F15 | keep |
| R18 variety | F18 | scenes not stock clips |
| R21 cadence | F21 | keep 2+3 |
| R22 Jungian fence | F22 | **rewritten** |
| R23 dedup | F23 | mechanism + number |
| R24 shorts media | F24 | own charts |
| R26 qa_pack | F26 | finance hashtags |
| — | F27–F30 | new |
