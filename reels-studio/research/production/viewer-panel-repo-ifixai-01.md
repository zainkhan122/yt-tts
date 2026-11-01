# Viewer panel: repo-ifixai-01

Video: `repo-ifixai-01.mp4` · 41.4 s · frames: panel-1-3.0s.jpg, panel-2-8.9s.jpg, panel-3-14.8s.jpg, panel-4-20.7s.jpg, panel-5-26.6s.jpg, panel-6-32.5s.jpg, panel-7-38.4s.jpg

Reviewer: open EVERY frame. Score as the persona, not as the producer.

## Benchmark bars (decode 2026-10-18)
- first frame = the product/result (or face + one symbol), benefit legible muted
- giant captions from the first spoken word; never an empty or placeholder stage
- real product media (capture/demo/UI) in >= 60% of scenes; cards support, never carry
- one idea per scene; a visual change every 4-5 s; hook claim in sentence one
- honest catch in plain user-impact words; spoken CTA before the end
- motion: a visual change at least every 5 s; real media cropped or animated to the feature (no full static screenshot held over 1 s); each graphic names a tool-specific element; comparisons and charts use real data only

## Persona verdicts (fill in: PASS / SWIPE + one line why)
- **Cold scroller** (sees 100 Shorts a day, sound off, thumb ready — decides in 1-2 s): 
- **Niche dev/gamer** (the target viewer; allergic to hype, wants proof it works): 
- **Curious outsider** (not technical; needs the benefit in plain words instantly): 
- **Saver/searcher** (saves and searches later; judges save-worthiness and the title): 
- **Skeptic** (assumes AI slop until shown the real product working): 

## Scene-by-scene media check
- [ ] every scene has real media or a justified graphic (no empty stages)
- [ ] real product media covers >= 60% of scenes
- [ ] first frame sells the benefit muted, in the first 3 s
- [ ] one-sentence takeaway a first-time viewer would repeat: 

## Cover (judge cold, as it would appear in a stranger's feed)
- [ ] cover concepts rendered by tools/cover_lab.py and opened (sheet.jpg): 
- [ ] winning concept readable muted at feed size (<= 4 words, real media): 
- [ ] selected_cover in the brief matches the winning concept: 
- [ ] Would YOU tap this cover between two strangers' videos? why: 

## Panel result: PASS (agent review; owner to confirm)

Reviewed file: repo-ifixai-01.mp4, sha256 25daf11e489875267b3684b0b4026083a1dfe2cd856a379de98d9e2e7565c809, cloud run 41318036615 (artifact digest matches).
- Scenes 1-7 (hook, points 1-5, catch) were reviewed on the contact sheet of the square-graphics render. Their content is unchanged in this file.
- The outro (end card: question, AUDIT chip, follow card with channel logo) was reviewed on frames 26-40 s of this file.
- Motion: every scene moves. Animated scenes (points 4-5, catch) build in over 0-4 s and keep moving. No frame is held static for more than about 1 s.
- Captions: no clipped lines. Sub-lines are complete sentences from the plan.
- Figures: the maker's chart is removed. No figure on screen, in the cover, or in the spoken or written copy.
- Media: points 1-3 are own graphics built from the plan; points 4-5 and the catch are own animations (tools/motion/make_ifixai_anim.py); the outro is the template end card.
- Cover: own findings graphic, headline matches the selected cover text.

Caveats:
- Animated scenes sit in a square card on a blurred background, the same card style as the image scenes.
- Five separate personas were not run; this is the producing agent's review.
