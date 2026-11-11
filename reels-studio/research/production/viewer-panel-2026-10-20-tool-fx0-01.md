# Viewer panel: tool-fx0-01

Video: `tool-fx0-01.mp4` · 38.8 s · 1080×1920 · scenes hook 0.25–6.55, build 6.55–13.04, proof 13.10–19.34, catch 19.40–32.51, cta 32.57–37.28

Frames opened (extracted from the published release asset, sha256 `93193f79722a001691707055ca889728c47ce628eb64369ffb58d62e1f6780f2`):
0.6 s, 5.0 s, 11.0 s, 17.0 s, 22.0 s, 28.0 s, 34.0 s, 37.5 s — plus the seven-frame panel sheet `qa-panel-fx0.jpg`
(2.8 / 8.3 / 13.9 / 19.4 / 24.9 / 30.5 / 36.0 s). Every one opened and read; nothing scored from a manifest.

## Benchmark bars (decode 2026-10-18)
- first frame = the product/result, benefit legible muted
- giant captions from the first spoken word; never an empty or placeholder stage
- real product media in >= 60% of scenes; cards support, never carry
- one idea per scene; a visual change every 4-5 s; hook claim in sentence one
- honest catch in plain user-impact words; spoken CTA before the end

## Persona verdicts (score as the viewer, not the producer)
- **Cold scroller** (sound off, thumb ready, 1-2 s) — PASS. 0.6 s is the real fx0 landing page under "ONE PROMPT. A WHOLE PAGE." with "NO DESIGNER," already on screen; the claim is readable with the sound off and the page is visibly a real product.
- **Niche dev/indie maker** (allergic to hype, wants proof) — PASS. 11.0 s shows the *published live page* it built; 17.0 s shows the fx0 dashboard with real numbers (47,074 / 127,100 / 41.2 %); the running app carries 19.4 s of the 38.8 s video (build start 13.1 s to catch end 32.5 s).
- **Curious outsider** (not technical) — PASS. "describe the page, the agent builds it, it publishes it" is one plain sentence, and "2 free prompts left" at 22.0 s is a cost statement anyone understands.
- **Saver/searcher** — PASS. The catch scene names both real limits (five free prompts, then sign in and bill your own model; placeholder copy you still edit) before any link is asked for; the title carries the searchable name.
- **Skeptic** (assumes AI slop) — PASS. The catch scene admits the paywall and the copy edit; the "THE GOOD" card claims only "One HTML file, no build step" and "Free and open source", both verifiable on the repo page.

## Scene-by-scene media check
- [x] every scene has real media or a justified end card; no empty or placeholder stage (hook 2-up real capture, build = the built page, proof = live dashboard, catch = dimmed app + evidence cards, cta = brand end card)
- [x] real product media in 4/5 scenes (the cta end card is graphic-only by design)
- [x] caption band is clear of the media in every frame opened: captions bottom-centre under the plate, media never enters `#cap-zone` (80,1160,920,338); `tools/layout_audit.py` clean on all five sampled frames
- [x] catch scene dims from frame one and shows the callout without a white flash: catch luma 46-55 (old 215-222), ring appears instantly
- [x] one-sentence takeaway a first-time viewer would repeat: *type one sentence about a page, an agent writes and publishes it — five free prompts, then you pay your own model*
- [x] CTA is spoken before the end card and the question ("What would you have it build first?") is the same on screen and in the voice

## Caveats recorded honestly (not hidden)
- The hook holds one composition from 0.25 s to 6.55 s. It is not frozen — a slow push-in runs under it (mean luma delta 2.7 at +2 s, 3.0 at +4.9 s inside the media band) and the caption advances per phrase — but the second visual event lands at 6.55 s, one beat later than the 4-5 s bar. Watch item for the next treatment cycle, not a fail: the first frame already sells the claim.
- The end card shows the Hypeless brand mark (`brand/logo/mark-transparent-1024.png`, the yellow/blue H) inside the avatar ring with the wordmark and "AI tools, minus the hype" — the logo, not a bare letter.

## Panel result: PASS
