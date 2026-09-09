# Live channel — locked 2026-09-09

**Do not guess this again. Measured.**

| | |
|---|---|
| Name | The Public Record |
| Channel ID | `UCGqHrMgsra_dX9RnGylDbjQ` |
| Studio | https://studio.youtube.com/channel/UCGqHrMgsra_dX9RnGylDbjQ |
| Public | https://www.youtube.com/channel/UCGqHrMgsra_dX9RnGylDbjQ |
| Handle (live) | **`@thepublicrecord-yt`** |
| Handle we planned | `@thepublicrecord` — **not this channel.** That URL 200s with “This channel doesn't have any content.” Different/empty property. |

Allow-listed in `youtube_channels.json` slot 1.

They uploaded from Studio (or another client), **Public**, not via `youtube_publish.py`. Our tool still refuses public. That is their choice. Record it; do not nag every turn.

---

## What is actually up (2026-09-09)

| Piece | ID | Published (UTC) | Length | Views (watch page) | Category |
|---|---|---|---|---|---|
| Long E01 | [ZdmURmo43vY](https://www.youtube.com/watch?v=ZdmURmo43vY) | 2026-09-04 23:00 | 8:06 | **9** | Education |
| Hook Short | [lZ_7MyJ_ego](https://www.youtube.com/watch?v=lZ_7MyJ_ego) | 2026-09-07 19:30 | 0:32 | **28** | Education |
| Payoff Short | [BBF_6JsQsqg](https://www.youtube.com/watch?v=BBF_6JsQsqg) | 2026-09-08 21:15 | 0:33 | **1** | Education |

E02–E07 are **not** on the channel. The live identity is one MoviePass film and two MoviePass Shorts.

Cadence vs plan (Tue long / Wed hook / Sat payoff, 6–9pm Eastern):
- Long Fri 4 Sep 23:00 UTC = **7pm Eastern** — window is right; day is not Tuesday.
- Hook Sun 7 Sep 19:30 UTC = 3:30pm Eastern — afternoon, not evening.
- Payoff Mon 8 Sep 21:15 UTC = 5:15pm Eastern — early.

Sample is tiny. Do not rebuild the channel around 28 views. Do use what is *wrong on the files they shipped*.

---

## Fence breaks on the live long (transcript + description)

Grandfathered E01. **Do not recut unless asked.** Do not copy these onto E08+.

Spoken (watch-page transcript):
- “People did not stop going to the movies.”
- “Stay with that sentence.” / “We will cash it at the middle of this story.” / “Now, we cash the sentence from the open.”
- Closer: “if you want the next collapse… stay. We show the death. We do not sell a pic.”
- `check_script.py` would fail this VO today.

On-screen / metadata:
- Chapter **`0:10 Not investment advice`**. Legal in the chapter list. L1. Overlay disclaimer was retired. If that is a card, kill it on future uploads. If it is only a chapter label, delete the chapter.
- Description: disclaimer block **then** chapters **then** hashtags. L8 wants disclaimer **last**. Fix on E02+ uploads.
- No `@thepublicrecord` subscribe line — live handle is `@thepublicrecord-yt`. Use the live handle in descriptions going forward.

Shorts descriptions: clean. `#shorts`. Link to the long. No legal. That part is right.

---

## Thumbs (downloaded 2026-09-09)

`research/live/e01_*.jpg` + `*_120.jpg`.

| File | 120px lum | Read at 213×120 |
|---|---|---|
| Long | **30.8** (gate fail &lt;38) | SUICIDE MATH is large and still readable because of stroke. **No MoviePass mark.** Cinema, not this company. |
| Hook | **23.4** | Gold “3 MILLION” is a smudge. Dark faces. No name. |
| Payoff | **20.9** | “PAID FULL TICKET” gone. Popcorn cup looks like another brand’s mascot. |

Improvements that are not taste:

1. **Company mark on the long thumb.** We already do this from E04. E01 live does not. People browsing Mobile will not know this is MoviePass.
2. **Lift the plate / do not ship lum &lt;38.** Dark theater looks like every cinema Short.
3. **Shorts need a 9:16 thumb, not a 16:9 letterbox of faces.** YouTube Shorts shelf is vertical. These 1280×720 crops are mud.
4. Do not put a recognizable popcorn character that is not ours on a thumb.
5. Hook Short (28 views) beat the long (9) and crushed the payoff (1). Keep the hook as **name + corpse number**. Payoff Shorts that start on “Gyms survive…” without the company in the first breath are how you get 1 view.

---

## What to change in production (E08+)

- Descriptions: live handle `@thepublicrecord-yt`. Disclaimer last block only. **No chapter named after legal.**
- Do not speak the brand motto. It is already on E01. `check_script.py` will fail a clone.
- Long thumb: real mark + object + wound, 120px test, lum ≥38. We have this OS. Use it on upload, not a darker re-export.
- Shorts: native 9:16 thumb as well as the video. Hook = name + number. Payoff = mechanism, company still in title (already).
- **Publish the backlog before the catalog is 8 unreleased films.** E02–E07 sitting in `finance/` while the live channel is three MoviePass URLs is the actual growth problem. 9 views will not teach us CTR. Shipping Quibi / Messenger / Toys R Us / Convoy / Jawbone / Katerra will.

---

## What we cannot see without Studio

Impressions, CTR, average view duration, traffic source, Shorts vs long graph, subs. User: if you paste a Studio analytics screenshot, we use it. Until then we do not invent a diagnosis from 9 views.
