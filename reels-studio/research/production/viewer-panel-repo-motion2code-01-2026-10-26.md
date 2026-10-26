# Viewer panel: repo-motion2code-01

Video: `repo-motion2code-01.mp4` · 40.5 s · frames: panel-1-2.9s.jpg, panel-2-8.7s.jpg, panel-3-14.5s.jpg, panel-4-20.2s.jpg, panel-5-26.0s.jpg, panel-6-31.8s.jpg, panel-7-37.6s.jpg

Reviewer: open EVERY frame. Score as the persona, not as the producer.

## Benchmark bars (decode 2026-10-18)
- first frame = the product/result (or face + one symbol), benefit legible muted
- giant captions from the first spoken word; never an empty or placeholder stage
- real product media (capture/demo/UI) in >= 60% of scenes; cards support, never carry
- one idea per scene; a visual change every 4-5 s; hook claim in sentence one
- honest catch in plain user-impact words; spoken CTA before the end

## Persona verdicts (fill in: PASS / SWIPE + one line why)
- **Cold scroller** (sees 100 Shorts a day, sound off, thumb ready — decides in 1-2 s): SWIPE — frame 1 (2.9 s) is a white/yellow bar mid-animation; the product result is not legible until frame 3.
- **Niche dev/gamer** (the target viewer; allergic to hype, wants proof it works): PASS — frames 3–5 show the gallery output and the frame-by-frame claim; the catch is honest.
- **Curious outsider** (not technical; needs the benefit in plain words instantly): SWIPE — 'A MOTION VIDEO, AS CODE' is clear, but 'SVG', 'GSAP' and 'seeks frame by frame' are jargon with no visual anchor.
- **Saver/searcher** (saves and searches later; judges save-worthiness and the title): PASS — the topic is searchable (motion video as code); the title is set in post.md.
- **Skeptic** (assumes AI slop until shown the real product working): PASS — the gallery output is shown working; catch and MIT licence are spoken.

## Scene-by-scene media check
- [ ] every scene has real media or a justified graphic (no empty stages) — FAIL: the catch scene (frame 6) is a text card on an empty dark stage
- [ ] real product media covers >= 60% of scenes — FAIL: 2 of 4 scenes (hook, example) carry footage; catch and CTA do not
- [ ] first frame sells the benefit muted, in the first 3 s — FAIL: frame 1 is an abstract mid-animation bar
- [ ] one-sentence takeaway a first-time viewer would repeat: 'Motion videos can be rebuilt as code an agent can edit.'

## Cover (judge cold, as it would appear in a stranger's feed)
- [x] cover concepts rendered by tools/cover_lab.py and opened (sheet.jpg)
- [x] winning concept readable muted at feed size (festival-map gallery frame, 'MOTION VIDEO → CODE')
- [x] selected_cover in the brief matches the winning concept (0)
- [x] Would YOU tap this cover between two strangers' videos? Yes — real gallery output, clear headline.

## Panel result: FAIL (back to production, no queueing)

Reason: scenes 3–4 of 4 lack media (catch, CTA); first frame is abstract; media coverage 50% (< 60%). Fix: open on the finished gallery result, give the catch scene gallery footage behind it, then re-render and re-run the panel.
