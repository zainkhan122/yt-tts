# Audit vs the films we actually have
**Date:** 2026-09-01  
**Audit file:** `uploads/youtube-channel-audit.md` (551 lines)  
**Films checked:** E01 MoviePass recut (8:06) · E02 Quibi recut (7:42) · four native 9:16 Shorts

This is a verdict, not a recap. The audit is a packaging-and-script review with **no YouTube Analytics**. Where it guesses retention percentages, those guesses are not evidence.

---

## 0. What the audit is, and what it is not

| It is | It is not |
|---|---|
| A close read of **scripts, titles, thumbs, descriptions, tags, brand files** | A watch of the mux (it treats the show as “AI stills”) |
| Honest that it has **no APV / AVD / CTR** | A measurement of retention |
| Right about two structural problems that were real on the *old* cut | A shot list we should copy |
| Written against the **pre-recut** voiceovers (spoken disclaimer at ~0:10 / ~0:12; identical stamp opens) | Current. The recut already removed spoken legal and rotated E02’s open |

**Scores (86.3 / 81.3) are not scores.** They are weighted opinions with no denominator. Treat the *arguments*, not the numbers.

The audit’s voice is also salesy: “world-class,” “masterful,” “+15–25% retention,” “absolute goldmine.” That heat does not make the underlying observations false. It does mean we should not implement a fix just because the prose is loud.

---

## 1. Channel / brand — mostly fair

**Logo, name, handle, Education category, Synthetic = YES, YPP clock (4,000h until 31 Jan 2027 / 8,000h after).** Agree. These are not opinions; they are setup facts.

**Promise.** “One real company. Public record. We do not sell a pick.” That is the fence. The audit is right that this is the brand, not “MagnatesMedia with a new hat.”

**Banner.** Atmospheric Banner 1 is the right upload. Caveat the audit does not make: empty red theater seats will read as *MoviePass-channel* after E02. Desk + stamp + paper can stay. Do not rebuild the banner around every corpse.

**Handle alternatives** (`@thepublicrecordyt`) — ignore. Handle is locked. Verify it is free in Studio before first Public.

**“Held for review” on every comment** — too tight for a new channel that needs conversation. Keep spam-word blocklist (giveaway, telegram, forex, binary). Hold *potentially inappropriate*. Do not hold everything.

---

## 2. Claim-by-claim against the recut

### 2.1 Spoken disclaimer at 0:10 / 0:12 — **was right. Now done.**

Old voiceovers spoke “this is education, not investment advice” in breath two. That is the single most plausible *early* drop on a documentary click. Direction is correct.

What the audit gets wrong:

- **“+15% to 25% early retention”** is not a measurement. Do not plan hours around it.
- It then tells us to put a **silent 3s lower-third** in the first 20s. That was our old L1. **Current L1 (user lock): no legal in TTS, script, captions, or on-screen.** Description last block only. We will not put the card back.

E01 S1 now ends at “then the app went dark.” E02 S1 is “One point seven five billion dollars into Quibi.” Zero legal phrases in either voiceover. Gate passes.

### 2.2 Identical intro template — **still half-true**

The audit nailed the *old* open: “This is [Name], a real company founded in [city] in [year]: [number], then the app went dark.”

**Now:** E01 is still that stamp (allowed once). E02 is number-first. L2 is satisfied for this pair.

**Still a template, one layer down.** Both films then do the same dance:

1. “People did not stop [using the thing].”
2. “[Company] died because [mechanism].”
3. “Stay with that. We cash it…”
4. Mid-film “Would you have… / Be honest. Most people…”
5. “Now we cash the sentence from the open.”
6. “This was [Company]. City, year. Numbers. Public record.”
7. Question + “next collapse” + “We show the death. We do not sell a pick.”

A binge viewer will hear the machine even if S1 rotates. **E03 must change beats 1–3 and 5, not only S1.** The closer line can stay (brand). The “People did not stop…” sentence cannot.

The audit’s *rewrite* of the E01 hook (“3 million members signed up for a glitch” before naming MoviePass) **violates P2** (name by second 5). Do not take that rewrite. Take the *diagnosis* (don’t clone the paragraph shape).

### 2.3 “Transcription typos” — **wrong object**

“Hammet / artouse / Helio / Quibby / Huelet Packard” are **ASR of Kokoro**, not errors in `voiceover.txt`. Scripts spell Hamet, art-house, Helios and Matheson, Hewlett Packard, Quibi.

**Lesson that survives:** fix *pronunciation* in `speak_map.json` before TTS. This recut still has Kokoro → Vosk “quimby.” Map is now `Kweebee` for the next film. Do not search-replace a clean script because an auditor transcribed the audio.

### 2.4 Titles — **keep ours. Refuse the hybrid.**

| | Audit | Us | Verdict |
|---|---|---|---|
| E01 `Why MoviePass Died With 3 Million Members` | 8.5/10; wants `Why MoviePass Died (The $9.95 Suicide Math)` | Locked. Company in first 5 words. Thumb ≠ title | **Keep.** Stuffing SUICIDE MATH into the title is P9. Search already has MoviePass + died + 3 million |
| E02 `Quibi Raised $1.75 Billion. It Lasted Six Months.` | 9.5/10; keep | Kept | Agree |

`The Company That Lost Money Every Time You Used It` is a good *browse* line and a bad *title*: no company name. That is a Short hook or a thumb, not the YouTube title.

### 2.5 Thumbnails — **half right, and the metric lied on E02**

**E01 SUICIDE MATH.** Audit 9/10. Fair. Red card + seats + wound line, no wordmark. After a brightness lift it passes `thumb_test` at **42.0** (floor 38). Still a dark left scrim; the object (card + red velvet) is the thing that reads at 120px. Do not add a MoviePass logo.

**E02 SIX MONTHS.** Audit 5/10: too dark, phone is a blob. **Human judgment is still right.** We lifted the file to mean luminance **55.6** so L3 passes — mostly because **SIX MONTHS** is white, not because the phone became a readable object. At 120px it is still a dark slab on a dark table. That will lose Browse CTR to colorful finance thumbs.

What we will **not** do: fake a neon Quibi UI on the glass (audit’s exact ask). Trademark + “Public Record” trust.

What we **will** do on E03: one bright object that is not the text. Lamp on glass, paper in a pool of light, a numbered headline. Test at 213×120. If the object dies, the thumb dies.

### 2.6 Visual editing / “AI slideshow” — **overstated, but the remaining hole is real**

The audit scores Visual Editing 7 and 6.5 and talks as if the films are ten generated stills. **That was never the mux.**

| | Shots | Video | Still | Max shot |
|---|---|---|---|---|
| E01 recut | 74 | 37 | 37 | 6.57s |
| E02 recut | 81 | 51 | 30 | 5.71s |

Pexels is live motion, audio stripped, each file once. That is not a slideshow farm. It is also not an investigation documentary yet.

**The real visual problem the audit points at, in different words:**

1. **Picture does not cash the line.** Cinema seats on “Helios bought a majority” is motion without evidence. That is the inauthentic-content signature YouTube actually cares about — *templated B-roll*, not “no motion.”
2. **E01 is 50% stills** because unique cinema clips ran out. Ken Burns on a generated still is closer to slideshow than E02’s 51 clips.
3. **Our “artifacts” are branded quote-cards**, not photographed filings. `01_hmny_8k_moviepass_stake.png` is *our* type on charcoal, citing an accession number. The words are real. The *object* is a graphic we made. A viewer cannot tell it from a listicle card. The audit asked for a Ken Burns on an actual EDGAR page / contemporaneous headline. That is the gap.

**Refuse:** fake MoviePass/Quibi app UIs, 3D exploding bars, rocket animations, slot-machine subscriber counters, TikTok screen recordings we did not capture, “wallet pouring $15.” User already killed chart-sync and mascots. Fake product UI is a trademark and a trust problem.

**Take:** at the *killing* beats, show a real page. For E03: a real NYT/Axios/Semafor headline crop, a real shutdown email screenshot if it was published, a real headcount or revenue figure from contemporaneous press — photographed or archived, not retyped in our font.

### 2.7 Origin drag (E01 0:33–1:41) — **still true. Recut did not touch it.**

The 2011–2017 art-house / $35 / 23k-member chapter is sourced and it is slow relative to the click (“3 million members”). Audit says compress ~30s. Reasonable. We did not compress in the recut (legal strip only).

**E03 rule:** origin gets **45–60s**, then the killing number. Founding color is a chapter, not a second thesis.

### 2.8 Quibi TV-app stretch (audit 5:30–6:10) — **mildly true**

AirPlay / Chromecast / Apple TV two days before shutdown is a *good* detail (“eulogy with a remote”). It is not the villain. Keep it. Do not grow it. E03: one patch chapter, not a product-changelog.

### 2.9 Descriptions — **ours are cleaner than the rewrite**

Audit wants emoji bells, “greatest suicide pact in tech history,” “Silicon Valley’s most expensive mistake.” Those are claims we cannot source as rankings. Our descriptions already: keyword in sentence one, mechanism, dates, subscribe, chapters, sources, **disclaimer last**. That matches L8.

Take from the rewrite: **tighter chapter labels** (“The $9.95 price” is dull; “Paid full ticket” is the wound). Do not take the adjectives.

### 2.10 Shorts maps — **right mechanism, our execution is thinner**

| Audit wanted | We shipped | Fit |
|---|---|---|
| MoviePass: gyms/breakage | Payoff Short is exactly that | **Yes** |
| MoviePass: Fallout processor blackout | Not a Short. Hook is name + 3 million + dark | Hook is valid; Fallout would be a third Short — we do not do original-topic Shorts, and L6 is hook+payoff, not three |
| Quibi: didn’t own the shows / Roku pennies | Payoff Short | **Yes** |
| Quibi: $5 vs free buffet | Inside the hook Short, not a separate film | Fine |

Gaps to fix on **future** Shorts, not a recut:

- E02 hook is **27s** (P10 = 30–45). Hit 30.
- Portrait B-roll is generic (seats / phones). A Short about breakage should *show* a gym vs a ticket, not eight similar vertical theater clips.
- Native 9:16 is correct. Do not pillarbox.

### 2.11 Competitors — **learn frequency, not heat**

Jake Tran / SunnyV2 / Company Man table is generic and mostly right at one altitude: **interrupt every few seconds; don’t gossip; don’t sell a pick.**

We already change picture every ~6s. What we do not have is a *meaning* interrupt: a number, a real headline, a question card. New Pexels clip ≠ pattern interrupt if it is the same cinema.

Do **not** take Tran thumb heat or SunnyV2 gossip as north star. Brand is the filing.

### 2.12 YPP / inauthentic content — **the clock is real; the slideshow panic is aimed at the wrong object**

5 months to 31 Jan 2027 is real. Hours come from **finished longs**. Shorts are discovery. Cadence 1 long/Tue + 2 Shorts is the plan; do not jump to 2 longs/week.

YouTube’s 2026 inauthentic pass hits **templated slideshows with stock + TTS**. Defense is not “more AI stills” and not “fake app UI.” Defense is **original script + mixed live B-roll + photographed public-record pages.** We have the first two. The third is still a card we designed.

### 2.13 Hook rewrites in the audit — **do not shoot**

They delay the company name, invent a rocket graphic, invent a glitch effect, invent TikTok recordings, and put legal back on screen. That is a different show.

---

## 3. What is actually strong (without inflating it)

- **One villain per film.** Unit econ vs breakage; paid snack vs free feed + licensed library. That is the product.
- **Sourced dates, named press, no invented boardroom talk.** Metadata accuracy is the one 10/10 in the audit that is earned.
- **Title/thumb split** on both films (P9).
- **E02 title** is the better of the two. E01 is a search title and a weaker browse title. That is an acceptable trade for episode 1.
- **Scripts are above the faceless-finance median.** They are not unique in the business-doc niche. MagnatesMedia / Company Man / ColdFusion exist. Our edge is *one mechanism, no pick*, not “literary genius.”

---

## 4. Lessons to implement — E03 and every Short after this

Ranked by how much they change the next film, not by how loud the audit was.

### Do (fence-safe)

1. **Rotate the whole open, not only S1.** E03 = corpse-first *or* sourced-quote-first. Ban “People did not stop…” and “Stay with that. We cash it.” Write a new second beat.
2. **Origin ≤ 60s.** Founding color, then the killing number. Messenger: West Palm / May 2023 is a postcard, not a second act.
3. **Real artifacts, photographed.** ≥3 files that a stranger would recognise as a *page that existed*: archive.org / press screenshot / EDGAR HTML capture / published shutdown memo. Sourced quote-cards in our font **do not count** toward the “this is not a slideshow” defense even if they count for today’s L4. Tighten L4 for E03: at least **one** file must be a crop of a real page, not a card we typeset.
4. **Picture cash the line at the killing beats.** When we say “$50 million,” the viewer should see a number that came from the Times, not a newsroom B-roll. Random Pexels can cover connective tissue. It cannot cover the autopsy.
5. **More unique motion than stills.** Target ≥60% video shots. E01’s 50/50 is the ceiling of stills we should ever ship.
6. **Thumb: one bright object at 213×120, not a black slab with white type.** No fake wordmark. E03 candidates: a dark newsroom with one lit screen, or a printed “NO AUDIENCE” on paper in a pool of light — test small.
7. **Shorts: 30–45s, one mechanism, native 9:16, parent title.** Hook = corpse + unfinished why. Payoff = the machine. B-roll must illustrate *that* machine. No legal anywhere on Shorts.
8. **`speak_map` before TTS.** Awkward names get a spoken spelling. Listen to the first 20s of the wav before we cut picture.
9. **One meaning-interrupt per ~20s** in the long: artifact, on-screen number (2–4 words, already our caption style), or the mid-film question. Not a new theater clip.
10. **Playlist + Studio.** “The Record” (not “Company Autopsies” — we will do rises). Phone verify. Custom thumbs. Spam blocklist. Synthetic = YES. Education. Not for kids.
11. **YPP math.** 1 long/week that people *finish* beats 2 longs that they abandon. Shorts are the top of the funnel, not the hours.

### Maybe (cheap, if it does not become a gimmick)

12. **One sound event at the thesis.** Paper stamp or a low whoosh when the killing sentence lands. No music bed until we can do it without sounding like a Tran clone. If we cannot do it well, silence is better.
13. **Tighter chapter titles** in the description (wound, not “New York, 2011”).

### Do not

- Speak or draw legal copy. Description last block only.
- Put the thumb line in the title.
- Fake apps, fake 10-Ks, fake TikTok, exploding 3D bars, rockets, mascots, chart-as-face.
- Clone WeWork / Theranos / FTX / another “sold it for less than it cost” unless the mechanism is actually new.
- Use the audit’s “glitch / rocket / neon UI” hook boards.
- Hold every comment for review.
- Treat 86.3/100 or “+15–25%” as a KPI.
- Recut E01/E02 again unless a specific shot is unusable.

---

## 5. E03 application (The Messenger) — concrete

| Beat | Do |
|---|---|
| Open | Corpse-first *or* quote-first. Example shape: “Fifty million dollars. Eight months. Then an email. This is The Messenger.” Company still inside 5s. Not “This is The Messenger, a real company founded in…” |
| Second sentence | Not “People did not stop reading the news.” |
| Origin | Finkelstein / JAF / West Palm / 15 May 2023 in under a minute |
| Villain | 2010s newsroom + Google/Meta traffic in 2023. $50M in, ~$3M revenue. Not “media is dead.” |
| Artifacts | Real NYT shutdown piece crop; real “biggest busts” line if we use it; contemporaneous staff-size reporting. One photographed page minimum |
| Thumb | **NO AUDIENCE** or **EIGHT MONTHS**. Bright object. No Messenger wordmark |
| Shorts | Hook: $50M / 8 months / email. Payoff: they built a newsroom for a traffic deal that had ended. 30–45s |
| Title | Already queued: `The Messenger Spent $50 Million In 8 Months.` Keep. Not Why |

---

## 6. One-line verdict

The audit correctly identified the **hook tax**, the **cloned open**, the **dark Quibi object**, the **need for real pages**, the **Shorts-as-mechanism** map, and the **YPP clock**. It incorrectly treated ASR as script typos, sold unmeasured retention percentages, pushed fake UIs and a P9-illegal title, scored visuals without the mux, and asked for a silent legal card we have since banned.

We already spent the two cheapest wins (no spoken legal; E02 number-first). The next film wins or loses on **origin length, a third intro shape, photographed record, and a thumb that is an object rather than a mood.**
