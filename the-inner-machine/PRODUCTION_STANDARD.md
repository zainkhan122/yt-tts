# THE INNER MACHINE — PRODUCTION STANDARD (v2)
*Adopted from the reference repo's tested "visual-style analysis v2" + "stock & storage" docs.
This is the enforced bar for every video. A video that doesn't meet it does not ship.*

## The retention bar (market standard, verified)
- **A visual change every 3–5 s.** A "change" = new image, new crop/zoom, text pop, or transition.
  Never hold one frame > ~4 s with no motion change.
- **Kinetic text on screen for every major claim / key phrase**, synced to the word, placed
  **middle or top** (not buried at the bottom). Two styles: big word-POPS for emphasis +
  statement captions for sentences.
- **Every shot moves** — variable zoom/pan; no two shots move the same way.
- **Quick crossfades (~0.3 s)** between shots; zoom-through on section changes.
- **Frame-accurate sync** — synthesize each sentence separately, measure its REAL duration,
  build visuals + captions to those exact timings. Never assume chars ∝ time.

## Asset standard per ~8-min video
- **20–30 unique base images** (generated, palette-locked). **No shot repeats.**
  Each base image may yield 3–4 *different shots* via distinct crops/zooms/pans — but each
  shot is visually different; the same framing never repeats.
- **Real b-roll (Pexels video)** mixed in for motion/realism where it fits — REQUIRES the free
  Pexels key (`~/.pexels_key`). Without it, use generated images only.
- **Images stored compressed** (JPG at target res, ~100–250 KB each), never 2 MB PNGs.

## Script format (write it this way)
Break the narration into **sentences**. Each sentence = one caption timing. Group sentences into
**shots** (a shot = 1 image + motion + 1..n captions, ≤ ~5 s). Tag each shot:
`[SHOT n] image=<base>  crop=<variant>  motion=<zoom/pan>  [TEXT OVERLAY: phrase]`.
Structure: HOOK(30s) / THE MECHANISM / THE WHY / THE SHIFT / CTA. ~150 wpm.

## Storage hygiene (hard rule — workspace is a workbench, not an archive)
- Workspace holds ONLY the current video's working set. Cap ~128 MB / 10k files.
- Images compressed; intermediates (`.work`) deleted after each successful step.
- After a video is confirmed/pushed to the GitHub vault, delete its binaries locally.
- GitHub `zainkhan122/yt-tts` `the-inner-machine/` = permanent vault.

## SOP order (enforced by tooling)
1 long video → 2 thumbnail → 3 metadata → 4 shorts LAST. Build incrementally across sessions;
never generate an entire video's assets + render in one session.
