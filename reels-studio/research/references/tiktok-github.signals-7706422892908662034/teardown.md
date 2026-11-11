# Reference teardown: Musike: Your Ad-Free Music Player Musike is the open-source music pla...

- Source: tiktok · @github.signals · https://www.tiktok.com/@github.signals/video/7706422892908662034
- Teardown dir: `research/references/tiktok-github.signals-7706422892908662034/` · video downloaded 2026-11-10 (frames local-only, git-ignored)
- Outlier at teardown: 19,100 views vs channel median 5,381 → **3.5x**
- Taken as LEAD only. Copying their footage, script sentences, or first-frame layout is a shipping block.

## Verified metrics (auto)

| Metric | Value |
|---|---|
| Duration | 40.4s |
| Resolution / fps | 720x1280 · 30.0 |
| Detected cuts | 19 (2.02s avg shot length) |
| Cuts inside 0-3s hook window | 1 |
| Dark-frame ratio (luma<60) | 0.06 |
| Avg colour saturation | 0.04 |
| Dominant palette | #c0c0c0, #a0a0a0, #a0c0a0, #c0c0a0, #000020, #a0a0c0 |
| Script source | platform-captions |

Shot timeline (s): 2.02, 4.04, 6.06, 8.08, 10.1, 12.12, 14.14, 16.16, 18.18, 20.2, 22.22, 24.24, 26.26, 28.28, 30.3, 32.32, 34.34, 36.36, 38.38
Frames: see `frames/` (keyframe per detected cut, capped 40, plus 0-3s hook window).

## Hook anatomy
Spoken hook: \"Musike is the open source music player that finally strips YouTube Music down to just the music.\" (t=0-3s, word-timed captions).
Panel score: **34/100 WEAK [Unclassified], weakest STAKES 22** — the words are NOT the draw. The video still ran 3.5x over its channel median, which on this channel's format history means the mechanics are carrying it:
- t=0.00: first frame is product proof already — the player UI is visible inside the README hero before a single caption word. Zero seconds to first proof.
- t=2s: giant sync captions land (\"MUSIC PLAYER THAT FINALLY\") with the keyword on a yellow pill — the hook is VISUAL emphasis of the spoken word, not the sentence itself.
- Framing: the repo README is presented inside a browser-chrome mock (tab title + URL bar) with the channel avatar pinned top-right — instant \"this is a real open-source project\" trust signal.
_(their first spoken line / first on-screen text; which hook_panel formula it matches and its score;
seconds until the first concrete proof appears)_

## Script beats
~40.4s, 4 blocks, one continuous delivery:
- 0-8s **claim**: ad-free music, no account, no subscription (the removal list IS the value prop).
- 8-18s **mechanism**: runs locally on your hardware, pulls streams straight from the YouTube catalog.
- 18-34s **breadth stack**: Windows/macOS/Linux/Android/iOS/PWA/Docker — badges on screen while narration lists them; playlists + favourites stored safely.
- 34-40s **CTA**: hard cut to black end card — mascot logo, \"Follow for more open-source projects @GithubSignals\".
Beat spacing ~2s per caption phrase; a new idea every ~8s.
_(beat map: what each ~5s block is doing — setup / mechanism / demo / payoff; BEATS not sentences)_

## Media & animation grammar
Zero hard cuts (scene detect: 0; grid fallback used). All motion is a slow vertical scroll + subtle zoom of ONE web page (the GitHub README) inside a browser mock — the README itself is the b-roll: logo hero -> badges -> app UI screenshots -> contents list -> \"What it is\" section -> end card.
Caption system: word-groups of 1-3 words, heavy rounded sans, black fill + white outline, key noun/verb on a saturated yellow rounded pill, center-lower third, swapped in sync with speech (~2s dwell).
One production trick worth naming: the app UI is shown as README SCREENSHOTS — they never recorded the app; the repo page supplied every visual.
_(what moves and why: layout skeleton, motion type, diagram vs screen-capture, overlay text style)_

## Colour & typography
Measured: dark-frame ratio 0.06, avg saturation 0.04 — this is a LIGHT, desaturated short (GitHub light theme = whites/greys), so the yellow caption pill and the app's lime-green logo are the only saturated elements and own all the attention. Contrast strategy = quiet page, shouting captions. Palette [#c0c0c0, #a0a0a0, #a0c0a0, #000020] with yellow #ffd pill accents.
Type: extra-bold rounded sans for captions (friendly, dev-toy register); README page stays in system GitHub type (authenticity cue).
_(mood read vs the palette above; type scale/weight; contrast choices)_

## What we take
1. **Proof-in-frame-one discipline** — our first frame must already show the tool's UI/diagram, not a title card. Our current openings spend 1-2s on a headline before visuals; this reference shows feature first at t=0.
2. **One emphasised keyword per caption phrase, on a highlight chip** — we can adapt this to OUR brand accent (not yellow pill verbatim): pick the noun that carries the claim and physically mark it.
3. **Removal-list opening** — \"no ads, no account, no subscription\" converts better than feature-add claims for OSS tools (\"no X, no Y, no Z\").
4. **Beat cadence** — claim (0-8s) -> mechanism (8-18s) -> breadth stack (18-34s) -> CTA end card; a new idea every ~8s, caption swap every ~2s.
5. **The repo IS the b-roll** — README hero + badges + screenshots as scrollable source-of-truth footage; we can build OUR rendered pages/scenes to carry the same authenticity weight (real interface, not stock).
_(mechanics worth borrowing for OUR short, stated as principles)_

## What we avoid
1. Their browser-chrome README mock, pinned avatar, and mascot end card — all brand property of github.signals. Our end card / framing must be our own.
2. The exact yellow-pill caption template and heavy rounded font — we adapt the keyword-emphasis IDEA to our caption style; no lookalike styling.
3. Scroll-the-webpage as the entire motion language — their crutch (0 cuts) is also their weakest craft point; our pipeline renders real animated scenes, which can beat this mechanic while using its proof-first timing.
4. Their script sentences — preflight now flags any shared 5-gram automatically; rewrite every borrowed claim in our words.
5. Do not re-score ourselves against their hook words: our hook_panel reads their hook as WEAK/34 — format, not phrasing, won here.
_(anything too close to their execution; how our version must visibly differ)_

---
## Their transcript (for overlap checking — never quoted verbatim in our script)

Musique
is the open source music player that finally strips YouTube Music
down to just the music. It runs locally on your own hardware,
fetching audio streams directly from YouTube's catalog
without ever asking for an account,
showing an ad or demanding a subscription.
The most surprising part is how it handles video.
It automatically finds the official music video for any song
and lets you flip between pure audio and full
cinematic video with a single click,
all while keeping your playlists and favorites
stored safely in a local file
you can export anywhere. It turns a messy web platform into a clean,
private listening experience.
