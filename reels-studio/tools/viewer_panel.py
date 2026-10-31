#!/usr/bin/env python3
"""
Viewer panel: simulated-user review of a rendered Short BEFORE it may be queued.

Why: the 8 automatic QA gates measure technical validity (duration, loudness,
non-blank frames) — on 2026-10-18 they passed videos whose scenes were static
text cards and one empty "?" stage, and frame QA checked text overlap instead
of watchability. This tool is the watchability gate: it extracts one frame per
scene from the rendered mp4 and writes a review sheet with five viewer personas
and the benchmark bars from the channel decode (research/social/decode-2026-10-18.md).
The reviewing agent must open every frame, fill the sheet in honestly, and the
video may not be queued unless the panel passes.

  python3 tools/viewer_panel.py <render-dir-or-mp4> [<video-id>]
  -> <render-dir>/viewer-panel.md + frames/ (frames are the review evidence)

Panel rules (any one = FAIL, video returns to production):
  - a majority of personas would swipe away in the first 3 seconds;
  - any scene is an empty/placeholder stage or a text card carrying the scene alone;
  - real product media (captured page / demo / UI) covers < 60% of scenes;
  - a first-time viewer cannot say what the tool does for them after one watch.
"""
import sys
from pathlib import Path

PERSONAS = [
    ("Cold scroller", "sees 100 Shorts a day, sound off, thumb ready — decides in 1-2 s"),
    ("Niche dev/gamer", "the target viewer; allergic to hype, wants proof it works"),
    ("Curious outsider", "not technical; needs the benefit in plain words instantly"),
    ("Saver/searcher", "saves and searches later; judges save-worthiness and the title"),
    ("Skeptic", "assumes AI slop until shown the real product working"),
]
BARS = [
    "first frame = the product/result (or face + one symbol), benefit legible muted",
    "giant captions from the first spoken word; never an empty or placeholder stage",
    "real product media (capture/demo/UI) in >= 60% of scenes; cards support, never carry",
    "one idea per scene; a visual change every 4-5 s; hook claim in sentence one",
    "honest catch in plain user-impact words; spoken CTA before the end",
    "motion: a visual change at least every 5 s; real media cropped or animated to the feature (no full static screenshot held over 1 s); each graphic names a tool-specific element; comparisons and charts use real data only",
]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = Path(sys.argv[1])
    mp4 = src if src.suffix == ".mp4" else next(src.glob("*.mp4"), None)
    if not mp4 or not mp4.exists():
        print(f"no mp4 found at {src}")
        return 2
    vid = sys.argv[2] if len(sys.argv) > 2 else mp4.stem
    out_dir = mp4.parent
    frames = out_dir / "frames"
    frames.mkdir(exist_ok=True)
    import cv2
    cap = cv2.VideoCapture(str(mp4))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = n / fps
    picks = 7
    saved = []
    for i in range(picks):
        t = dur * (i + 0.5) / picks
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if ok:
            name = f"panel-{i + 1}-{t:.1f}s.jpg"
            cv2.imwrite(str(frames / name), fr, [cv2.IMWRITE_JPEG_QUALITY, 85])
            saved.append(name)
    cap.release()
    lines = [f"# Viewer panel: {vid}", "",
             f"Video: `{mp4.name}` · {dur:.1f} s · frames: {', '.join(saved)}", "",
             "Reviewer: open EVERY frame. Score as the persona, not as the producer.", "",
             "## Benchmark bars (decode 2026-10-18)"]
    lines += [f"- {b}" for b in BARS]
    lines += ["", "## Persona verdicts (fill in: PASS / SWIPE + one line why)"]
    for name, desc in PERSONAS:
        lines += [f"- **{name}** ({desc}): ", ]
    lines += ["", "## Scene-by-scene media check",
              "- [ ] every scene has real media or a justified graphic (no empty stages)",
              "- [ ] real product media covers >= 60% of scenes",
              "- [ ] first frame sells the benefit muted, in the first 3 s",
              "- [ ] one-sentence takeaway a first-time viewer would repeat: ",
              "", "## Cover (judge cold, as it would appear in a stranger's feed)",
              "- [ ] cover concepts rendered by tools/cover_lab.py and opened (sheet.jpg): ",
              "- [ ] winning concept readable muted at feed size (<= 4 words, real media): ",
              "- [ ] selected_cover in the brief matches the winning concept: ",
              "- [ ] Would YOU tap this cover between two strangers' videos? why: ",
              "", "## Panel result: PASS / FAIL (fail = back to production, no queueing)", ""]
    out = out_dir / "viewer-panel.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out} ({len(saved)} frames, {dur:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
