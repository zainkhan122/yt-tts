# 🎬 THE COMPLETE CONTENT PIPELINE — Step by Step

Every step, in order, with exactly who does what and what tool to use.

---

## OVERVIEW: The 8 Steps

| # | Step | Who | Tool |
|---|---|---|---|
| 1 | Topic + angle | Me | 30-day plan |
| 2 | Script | Me | Workspace |
| 3 | Voiceover | **You** | ElevenLabs |
| 4 | Scene images | Me (+ you for B-roll) | Image gen + Pexels |
| 5 | Video assembly | Me (or you in CapCut) | ffmpeg / CapCut |
| 6 | Thumbnail | Me | Image gen + ImageMagick |
| 7 | Title/description/tags | Me | Workspace |
| 8 | Publish + promote | **You** | YouTube |

---

## STEP 1: TOPIC + ANGLE (Me)

Every topic comes from the 30-day plan (`pipeline/02_30_day_plan.md`). Each topic has:
- A title that creates a curiosity gap
- The pain point it addresses (from `research/pain_points_master.md`)
- The Jungian concept anchoring it
- A 1-line hook

**Rule:** never do a topic that isn't tied to a real, documented pain point. "Interesting" is not enough — it has to make someone feel *seen*.

---

## STEP 2: SCRIPT (Me)

I write a full script to `videos/video_XXX/script.md` with this structure:

```
[H00K — 30 seconds]  ← question or statement that makes the viewer feel personally identified
[THE PAIN — 2 min]   ← describe their experience back to them (they feel seen)
[THE WHY — 4 min]    ← the Jungian/cognitive-function explanation (this has a NAME)
[THE SHIFT — 3 min]  ← the perspective change or practical insight
[CTA — 30 seconds]   ← discussion question + subscribe
```

The script includes:
- `[VISUAL CUE: ...]` markers → tells us what image goes where
- `[TEXT OVERLAY: ...]` markers → key phrases burned onto the screen
- Word count targeting ~150 words/minute (8-11 min video = 1,300-1,700 words)

I also create `voiceover.txt` — the same script cleaned of markers, ready to paste into ElevenLabs.

**Your job:** read it, cut anything that doesn't sound like something you'd say, add ONE personal observation. This is what keeps us from sounding like every other AI channel.

---

## STEP 3: VOICEOVER (You — the one external step)

1. Open [ElevenLabs](https://elevenlabs.io) → Speech Synthesis
2. Paste `voiceover.txt`
3. Pick a warm, calm male or female voice (test 5-10, then LOCK IN one forever)
4. Generate → download `voiceover.mp3`
5. **Attach it in your reply to me** (or name-drop it if you've placed it in the folder)

**Voice settings that work for psychology content:**
- Stability: ~55-65% (natural, not robotic, not erratic)
- Clarity: ~75-85%
- Style: ~25-35% (slightly expressive, not dramatic)

**Free tier limit warning:** ElevenLabs free = ~10 min audio/month. That's ONE 10-min video. Upgrade to **Starter ($5/mo = 30 min)** when you publish more than 1 video/month. It's the first thing worth paying for.

---

## STEP 4: SCENE IMAGES (Me + optional you)

**Me:** I generate 6-10 original scene images per video (moody, atmospheric, no text) into `videos/video_XXX/images/`, matched to the script's `[VISUAL CUE]` markers.

**You (optional but recommended):** grab 3-5 real stock B-roll clips/images from [Pexels](https://www.pexels.com) or [Pixabay](https://pixabay.com) (free, no attribution) — rain on a window, a person walking alone at dusk, a foggy forest, etc. Real footage mixed with AI images makes the video feel less "AI-generated" to both viewers and the algorithm.

---

## STEP 5: VIDEO ASSEMBLY (Me, with ffmpeg)

**Once you've attached `voiceover.mp3`, I assemble the finished video:**

1. I install the ffmpeg binary (2 seconds, on demand)
2. Each scene image gets **Ken Burns motion** (slow zoom/pan) — the exact technique successful faceless psychology channels use
3. Scene durations are timed to the narration
4. `[TEXT OVERLAY]` phrases are burned onto the screen at the right moments
5. Voiceover + optional background music are mixed in
6. Output: `videos/video_XXX/final.mp4` (1080p, YouTube-ready)

**You just:** download `final.mp4` → upload to YouTube.

### Fallback path (if you don't want to attach audio):
I give you a **scene-by-scene assembly guide** in `videos/video_XXX/assembly_guide.md`:
- Which image goes in which order
- How many seconds each image stays on screen
- The exact Ken Burns settings (zoom %, pan direction) per scene
- Which text overlays appear when

Then you assemble in **CapCut (free)** in ~20-30 minutes following the guide.

---

## STEP 6: THUMBNAIL (Me)

1. I generate an emotive base image (a face, a silhouette, a striking visual metaphor — NO text)
2. I overlay **3-5 word bold title text** using ImageMagick (gold/white text, dark background, high contrast)
3. Output: `videos/video_XXX/thumbnail.jpg` (1280×720)

**Thumbnail rules (from the data):**
- Text ≤ 5 words, huge and readable at phone size
- One focal point, high contrast against the dark palette
- The text + image together must create a curiosity gap (e.g., a shadowed face + "TOO AWARE")
- Never repeat the title verbatim — the thumbnail says what the title doesn't

---

## STEP 7: TITLE / DESCRIPTION / TAGS (Me)

I write `videos/video_XXX/metadata.md` containing:
- **5 title options** ranked by curiosity gap (you pick or I recommend one)
- **Full description** (2-3 sentences summary + keyword paragraph + hashtags + disclaimer + affiliate placeholder)
- **Tags** (10-15, though YouTube says they matter little now — hashtags matter more)
- **Pinned comment** idea to seed discussion

---

## STEP 8: PUBLISH + PROMOTE (You)

1. Upload `final.mp4` + `thumbnail.jpg`
2. Paste title, description, hashtags from `metadata.md`
3. **Mark "Altered or synthetic content" = YES** (AI voice/imagery disclosure — required)
4. Category: Education. Made for kids: No.
5. Schedule for **4-6 PM EST / 9-10 PM UK** (peak for the 18-35 psychology audience)
6. Post the community post I write (quotes/questions drive early engagement)
7. Reply to the first 10 comments within the first hour (signals YouTube the video is active)

---

## 🧰 THE TOOL STACK (Recap)

| Layer | Tool | Cost |
|---|---|---|
| Scripts | Me (workspace) | $0 |
| Voiceover | ElevenLabs | $0 → $5/mo |
| Images | Me (image gen) + Pexels | $0 |
| Assembly | Me (ffmpeg) or CapCut | $0 |
| Thumbnails | Me (image gen + ImageMagick) | $0 |
| Music | YouTube Audio Library / Pixabay | $0 |
| **Total** | | **$0 → $5/mo** |

**The only thing that will ever cost real money is ElevenLabs ($5/mo).** Everything else is free — because I'm doing the heavy lifting in the workspace.

---

## ⏱️ TIME PER VIDEO (Once the pipeline is warm)

| Task | Who | Time |
|---|---|---|
| Script + images + thumbnail + metadata | Me | (you wait ~a few min) |
| Voiceover generation | You | 10 min |
| Attach audio + I assemble | Us | 5 min |
| Upload + description + publish | You | 10 min |
| **Total your time per video** | | **~25 min** |

That's how 3-5 videos/week becomes sustainable without burning out.
