# PRODUCTION — flexible, research-first

Nothing here is a script to paste. The last film is not a template.  
**Fence is fixed. Form is not.**

---

## Fixed (do not “flex” these)

- One real named company. One mechanism. Public record only. No fiction.
- No legal in speech, captions, or on-screen. Description last block, longs only.
- Company identifiable early (name spoken; real mark on the thumb).
- Title: company in first 5 words, not the thumb wound. Wound is true.
- Picture: no looped clips. Unique files. Thumb passes brightness.
- Shorts: from that long only. Hook title ≠ payoff title ≠ parent.
- Synthetic = YES. Not for kids.

## Not fixed (decide from *this* record)

| Decision | How you choose it |
|---|---|
| **Open** | What does the record actually give you? A corpse date, a number, a quote, an object, a filing. Use that. Do not use the previous film’s sentence shape. |
| **Spine order** | Origin first only if the origin *is* the trick. Otherwise corpse or machine first. No mandatory 8-block clock. |
| **Closer** | A leftover the viewer can answer — or a sourced last fact. Do not end every film with the same brand slogan. Brand line lives in the description if needed. |
| **Thumb** | One object that *is this death* + one real mark + a 2–4 word gold/white wound (not the title). Layout follows the object. Family resemblance is the **wound type**, not the grid. **Split is a fallback** when the object would double-print the name or hide the wound under another brand (E04). Not the OS. No white-slab right half. No arc arrow. No scrap because the last film had a scrap. |
| **Open picture** | First seconds should feel like the thumb continued *if that object is the story*. 2–4s push on the object. Not a 10s logo-assassination ritual. No on-screen disclaimer. |
| **Metadata** | Search vs browse for *this* name. First paragraph is this film’s promise, not a clone of “Founded in… then… then dark.” Chapters exist if they help; they are not a law. |
| **Shorts** | One unfinished why + one mechanism. Pick the two lines the long actually earned. |

Before TTS, write `FORM.md` in the episode folder (see `reusable/FORM.md`). If you cannot fill “why this open” from `sources.md`, you do not have an open — you have a habit.

## Gate

`python3 tools/gate.py EP_DIR KEYWORD`

Fails on fence, legal, dark thumbs, looped shots, **and** on cloning a sibling’s open or closer.  
Does **not** require a question, a stamp sentence, or “People did not stop…”.
