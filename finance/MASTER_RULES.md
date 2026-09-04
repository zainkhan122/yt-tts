# MASTER RULES — The Public Record
Locked 2026-08-31 (L1–L8 in `tools/gate.py`). If a gate fails, the video is not done.

**Show:** The Public Record · `@thepublicrecord`  
**Fence:** One real named company per film. Public record. One mechanism. No fiction. No stock pick.  
THRESHOLD is paused. Do not resume it here.

---

## P1. FENCE
Named company + one rule that built or killed it, from press / filings / court.  
Banned spines: WeWork, Theranos, FTX, and a second “sold it for less than it cost” unless the mechanism is actually new.

## P2. FORM (not a stamp)
Company identifiable in the first seconds.  
**The last film is not a template.** Open, midpoint, closer, thumb layout, and description shape are chosen from `sources.md` for *this* company.  
`tools/check_script.py` fails a cloned S1 or a canned closer shared with a sibling. It does **not** require a question, a stamp sentence, or a four-shape rotation menu.  
Write `FORM.md` (see `reusable/FORM.md`) before TTS. `PRODUCTION.md` is the system.

## P3. ONE VILLAIN
One mechanism. CEO / lawsuit / relaunch are chapters, not the spine.

## P4. REAL ONLY + ARTIFACTS (L4)
No invented dialogue. `sources.md` required.  
`artifacts/` ≥3 real files (headline, filing/docket, contemporaneous photo) + `artifacts.md`. Not a fake app UI.

**Ident:** real historical logo (nominative, once) + one object that is **this** death + 2–4 word wound.  
Layout follows the object. Do not stamp the last film. Do not put a scrap on every thumb.  
Family resemblance = gold/white wound type, not a locked split. **`split` is fallback only** (object would double-print the name or sit the wound on another brand). No white-slab OS. No arc arrow on every film.  
`tools/compose_flex_thumb.py` — add a layout when the story needs one.

## P5. NOT ADVICE (L1)
**No legal line in the script, the TTS, captions, or any on-screen card.**  
Disclaimer = description **last block**, longs only. Not pinned. Not on Shorts.

## P6. VOICE
Kokoro `am_michael` @ 1.0. `tts_all.py` + `speak_map.json`. Never Arena long-form chunks.

## P7. PICTURE (L3, L5)
B-roll `-an` + Ken Burns + artifacts. New picture every **4–6.5s**. Each file once. **Never loop.** Vary shot length. Thumb passes `thumb_test.py`.

First seconds: match the thumb’s **object** if that object is the story (2–4s). Not a 10s logo-kill ritual. Not a disclaimer card.

## P8. CAPTIONS
2–4 words on a spoken keyword. Not karaoke. No legal words.

## P9. PACKAGING
Title ≤60 (Shorts ≤50), company in first 5 words, **not** the thumb wound. No three Why in a row.  
Wound is true. Shorts titles all different. Description is this film’s promise — `qa_pack.py` fails a cloned first sentence. Blank line between paragraphs.

## P10. RUNTIME
Long ~8–11 min (research can run short if the record is thin — don’t pad). Shorts 30–45s.

## P11. CADENCE (month 1)
1 long / Tue + 2 Shorts (Wed hook, Sat payoff).

## P12. YOUTUBE
Synthetic = YES. Not for kids. Education.

## P13. BUILD
```
(0) sources.md  →  FORM.md (why this open / thumb / closer)
(a) script + metadata
    python3 tools/gate.py EP_DIR KEYWORD
(b) artifacts/
(c) stills + B-roll chosen for THIS mechanism
(d) tts_all.py
(e) cut_long.py + stamp_caps.py
(f) thumb (layout for this object) + Unlisted watch
```

## P14 / P15
Workbench = this folder. `secrets/` never committed. HANDOFF; QUEUE wins.

Run: `python3 tools/gate.py episodes/NAME Keyword`
