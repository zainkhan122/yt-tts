> Dated record. State lives in `queue/publish.json` (see `STATE.md`, `python3 tools/ship.py status`).

# Handoff — 6 Nov 2026 (repo cleanup, agent-desktop removed, repo-poki-01 authored)

## 1. Repo scope (owner instruction, 6 Nov)
Only `reels-studio/` is part of this repo's job. Removed from the working tree:

- `finance/` (26 MB), `the-inner-machine/` (42 MB), `vault/` (152 MB)
- `video.mp4`, `video-1.mp4`

Kept at the repo root: `.github/workflows/` — all 17 workflows (`render.yml`, `post.yml`,
`ship-state.yml`, …) reference `reels-studio/` paths, and GitHub only reads workflows from the
repo-root `.github/`, so the pipeline's CI lives there.

The deletions are **local only** (one commit, not pushed). Git history still contains the old
folders; nothing was rewritten. Pushing the commit is what removes them from the remote.

## 2. Deleted: `repo-agent-desktop-01` (the blocked Short)
Owner instruction, 6 Nov. Removed:

- `briefs/repo-agent-desktop-01.json`
- `briefs/graphics/repo-agent-desktop-01/` (beats.json, features.json, source.md)
- `videos/repo-agent-desktop-01/` (plan.json)
- `research/production/receipts/2026-11-06-repo-agent-desktop-01.json`
- `research/production/viewer-panel-repo-agent-desktop-01.md`
- its entry in `config/topic-approvals.json`

Kept on purpose:
- `tracker/render-attempts.json` and `tracker/capture-pushes.json` are append-only journals. Their
  history was not edited.
- `HANDOFF-2026-11-06.md` is a dated record, not state. Not rewritten.
- It was never in `queue/publish.json`, so the queue and the generated `STATUS.md` did not change.

Follow-on fixes so the suite does not pin a deleted video:
- `tests/test_plan_pipeline.py` used `videos/repo-agent-desktop-01/plan.json` as its fixture. It now
  uses `VID = "repo-craft-anything-01"` (a plan that still has a brief). Same 4 pre-existing
  failures as before the deletion (missing gitignored covers/captures + no credentials), 55 pass.
- `SCRIPT-STYLE.md`: the worked example's label no longer names the deleted video.

## 3. New Short: `repo-poki-01` (topic from `research/radar/radar-2026-11-06.md` #7)

Tool: [JosssphZhou/poki](https://github.com/JosssphZhou/poki) — 369★, 81 forks, AGPL-3.0, created
2026-11-05, homepage poki.bot. Last commit 6 Nov. An open-source MCP server that lets Claude Code,
Codex or another MCP client read and act on a real iPhone or an iOS simulator.

Angle: the viewer's question ("can an AI use my phone?"), the flow (task → agent → taps on the real
phone), the proof (its own tool list and example task), the catch (it acts on the real phone, screen
contents go to your model service, and it needs a macOS machine with full Xcode).

### Files (all new)
| File | What it is | Check |
|---|---|---|
| `videos/repo-poki-01/plan.json` | the plan (4 points, catch, CTA `IPHONE`, SEO, cover concepts) | `tools/video_plan.py` → **PLAN PASS** |
| `briefs/repo-poki-01.json` | built by `tools/brief_from_plan.py`, 7 scenes, `renderer: graphics`, `voice_seed: 0` | `tools/brief_lint.py` → **0 errors** (1 note: no capture pack) |
| `briefs/graphics/repo-poki-01/source.md` | README + docs/tools.md + docs/verification.md snapshot, fetched 6 Nov | — |
| `briefs/graphics/repo-poki-01/features.json` | 7 features, 2 risks, every quote verbatim in source.md | feature-sheet lint **ok** |
| `briefs/graphics/repo-poki-01/beats.json` | 7 beats, one per scene, archetypes: flow_link, terminal_type, toggle_steps, flow_link, concept_card, chip_grid, cta_stack | beat lint **ok** (B1–B8, script fingerprint set) |
| `covers/repo-poki-01/cover-c{1,2,3}.png` | three designed covers, 1080×1920, layouts bleed / window / split | COVER-RULES in code: **ok**; headline contrast 19.34:1; Inter Black, not Anton |
| `covers/repo-poki-01/draw_covers.py` | the drawing source, so a cover can be redrawn or adjusted | — |
| `renders/repo-poki-01/seo.md` | per-platform SEO pack | `tools/seo_pack.py` → **0 errors, 0 warnings** |
| `renders/repo-poki-01/scenes.estimate.json`, `briefs/graphics/repo-poki-01/words.estimate.json` | the lint run's timing estimate (43.07 s). **Not** the render's timing: the voice stage writes the real one. | — |

Script (7 spoken lines, one per scene):
1. "Ever wanted AI to use your iPhone for you?"
2. "It's called Poki, it's open source, and it runs on your Mac. Clone it, run the setup script, then start it."
3. "Then add it to Claude Code or Codex as an MCP server, so your own subscription drives the phone."
4. "Give it a task, like searching the web in Chrome and summarizing the top result. It taps and types for real."
5. "It remembers past tasks, so the same job runs faster the second time."
6. "The catch: it controls your real iPhone, so the screen goes to your model service. And you need a Mac with Xcode."
7. "Would you hand your phone to an agent? Comment IPHONE and I'll pin the repo."

Primary keyword `AI iPhone automation`; on-screen first 3 s "CAN AI USE YOUR IPHONE?".

## 4. Token handling (owner instruction, 6 Nov)
The owner supplied one fine-grained PAT. It is **not** printed, not in git, not in the repo:
`~/.config/reels-studio/gh_token`, directory mode 700, file mode 600. The owner's uploaded copy was
moved, not copied, so no second copy exists in the workspace. `lib/secrets.py` reads it; every helper
uses `GH_TOKEN` in the environment only.

Done at the end of the session, on the owner's word:
- Topic approved: `python3 tools/make_shorts.py --approve-topic repo-poki-01 --note "..."` wrote the
  entry in `config/topic-approvals.json`.
- Cover picked: **c1** ("CAN AI USE YOUR IPHONE?", bleed). `covers/repo-poki-01/selection.json` +
  `cover-selected.jpg` written, sha256 `aa6277d5…`; `tools/cover_store.py verify repo-poki-01` passes.

## 5. To finish (in order)
1. Owner: give a token (fine-grained, repo push + Actions dispatch) or run the steps below.
2. `git push` the commits (removes the three folders, deletes agent-desktop, adds repo-poki-01).
4. Build the capture pack, then the receipt, then dispatch:
   ```sh
   python3 tools/capture_pw.py captures/repo-poki-01 --url https://github.com/JosssphZhou/poki
   python3 tools/receipt_build.py 2026-11-06-shorts-02 repo-poki-01
   gh workflow run render.yml -f briefs=repo-poki-01 -f production_receipt=research/production/receipts/2026-11-06-shorts-02.json
   ```
5. QA the returned MP4 (`tools/short_qa.py video`), run the viewer panel, then write
   `Video sha256` + `Panel result` in `research/production/viewer-panel-repo-poki-01.md`.
6. Nothing is queued, approved or scheduled. Publishing is a separate owner decision.

## 6. Operational notes
- The beat plan's `script_sha256` is `sha256:4a72a465a0e0…`. It is the fingerprint of the script's
  own words, so the cloud voice stage reproduces it exactly; if any spoken line changes, re-run the
  pack (`graphics` lint fails closed on a mismatch).
- `covers/` is gitignored: the PNGs live in this working copy only. Share them or re-run
  `covers/repo-poki-01/draw_covers.py` to redraw.
- Tests: `python3 -m pytest -q graphics/tests tests/test_gates.py tests/test_pipeline.py
  tests/test_cover_rules.py tests/test_plan_pipeline.py` → 55 passed, 4 pre-existing failures.

## 7. Render: DONE (owner authorised the dispatch)
Run **257** (`42260970838`) on `main` at `1ee28df`: **success**. plan ✓, voice ✓, render ✓,
finalize-attempt ✓; `publish verified GitHub Release` skipped (artifact-only, as dispatched).

| | |
|---|---|
| MP4 | `renders/repo-poki-01/repo-poki-01.mp4` (local, `renders/` is gitignored) |
| sha256 | `72e3a71bf3914bf518a2e9982a619d5da789629ffde4e16e19e4b8d41b60a412` |
| Format | 40.37 s, 1080×1920, 30 fps, H.264/AAC, −13.9 LUFS, −2.0 dBFS peak, 13.1 MB |
| Artifact | `render-repo-poki-01` (13524909816), expires 2026-11-07; voice artifact 13526020792 |
| Whisper | 99.8% character match; voice reused from the voice job (`8adab7da…`) |
| `short_qa` plan gates | 11/11 PASS |
| `short_qa` video gates | **PASS** — speech visual change 0.882, graphic-only 0.143, motion gap 0.5 s, WPM 178.9, longest pause 0.56 s |
| Kit gates | 0 errors, 0 warnings |
| Panel | `research/production/viewer-panel-repo-poki-01.md` — **PASS** with 4 findings |

Packs in the `capture-packs` release: `repo-poki-01.tar` (3.3 MB, 4 assets + live GitHub facts) and
`repo-poki-01-covers.tar` (256 KB). The cover pack was missing on run 255/`42257153709`, which is why
that attempt failed before rendering; `tools/cover_store.py push repo-poki-01` is now part of the
checklist below.

### Findings worth one more render (owner's call)
1. The point1 terminal sits empty for ~2.4 s before the first command types (lines are bound to "run the
   setup script" and "start it"). Fix: earlier `cue_phrases` or a prompt line at the scene start.
2. In point3 the outer flow nodes land before the middle one, so the flow reads out of order for ~1 s.
3. The catch's third chip (Mac + Xcode) arrives last; it is the cost viewers care about.
4. Cover asks "CAN AI USE YOUR IPHONE?", the first frame asks "CAN POKI USE YOUR IPHONE?". Cosmetic;
   changing the cover changes the render input.

Any of 1–3 needs a graphics edit plus a new dispatch. The duplicate guard will refuse identical inputs,
so the change has to be real.

### Render 259 (the fixed build) — DONE
First attempt, run `42266164457`, was **cancelled at the 60-minute job limit**: that runner took 19 min
just to install the toolchain, then was still synthesising at 60 min. Nothing was rendered, and the
attempt was recorded `failed`, which locks the input fingerprint. The retry needed a real change, so it
came with one: the concept title's per-letter stagger is now capped (`8b50d96`), i.e. a 21-letter title
is fully up 0.34 s after its cue instead of 0.8 s. That is the last piece of "kinetic text is out of
sync".

| | |
|---|---|
| Run | **259** (`42341933288`) on `8b50d96`, all jobs success, `publish` skipped (artifact-only) |
| MP4 | `renders/repo-poki-01/repo-poki-01.mp4` (13.06 MB, 40.37 s) |
| sha256 | `c8b9d5752924ffe8a8166d4186570a0175e7cc2c3cc0dd6360032173b0894912` |
| Voice | re-synthesised by the voice job, `vo_sha256 04692c95…`; whisper char match 99.8 % |
| `short_qa video` | **PASS** — visual change 0.868, graphic-only 0.168, motion gap 0.75 s, WPM 178.9, longest pause 0.56 s |
| Panel | `research/production/viewer-panel-repo-poki-01.md` round 2 — **PASS**, round-1 findings 1–2 fixed |
| Cue fallbacks | none (7 phrases, 7 scenes) |

## 8. Still not done
- Nothing is queued, approved for publishing or scheduled. `queue/publish.json` is untouched.
- No GitHub Release for the video (`publish_release` was false by design; artifacts expire 2026-11-07).
- `tools/ship.py status` still shows the three pre-existing drift items (`tool-muse-01`, `repo-scm-01`,
  `spotlight-papermorph-01`), untouched.

## 9. Owner review of run 257: sync + end-card fix (this section)

Owner, on the run-257 MP4: *"animations, TTS, kinetic text is out of sync. Outro is shit"* and
*"this pipeline already using an outro with channel logo and click on follow animation, where is that???"*

### Where the end-card was
It existed, but only in the HyperFrames template path — `templates/_base/base.js` `endCard()` (logo,
name + verified badge, handle, tagline, Follow button, cursor press) with `#endcard` styled in
`templates/_base/base.css`, its press time shared with the click SFX through `DATA.events.press`.
`repo-poki-01` renders with `renderer: graphics`, and the graphics engine (`graphics/templates/engine.js`)
had **no end-card at all**: the CTA was three stacked pills. The mix still played the template's
`click` SFX at `ev["press"]` (38.65 s), so the finished video had a click with nothing to click.

### What was wrong with the sync (measured, not guessed)
Audio drift was **not** the cause: VO vs kit word timings best shift **+10 ms**, final mix vs VO
waveform **0 ms** (corr 0.918). The defects were cue-level and structural:
1. every list bound its items to *later* words inside the phrase (`_seq_match` preferred the item's
   "distinctive" word), so pictures trailed the voice;
2. `cue_phrases` shorter than the item list was silently ignored, which is why point2's ticks and
   point3's nodes fired out of order (`result` before `taps and types`);
3. the first item of a scene waited for its own cue phrase, so scenes opened on an empty stage
   (terminal: 2.4 s of blank window);
4. the caption line led with the **previous** word (window started at `cur - 1`), which reads as one
   word behind.

### The fix (commit `21ab236`, receipt `cc1d3f1`)
- `graphics/templates/engine.js` — new `ARCH.endcard`: real brand logo (data URI from
  `brand/logo/avatar-1080.png`, never a text initial), name + badge, handle, tagline, the spoken
  keyword chip, Follow button, cursor that arrives and presses (scale dip, ring, label → "Following").
  Terminal shows a live `$` prompt + "waiting" status from the first frame. Caption window starts on
  the spoken word.
- `graphics/stage.py` — `brand_block()`, `_attach_events()`; `render_for_pipeline(..., events=…)`.
- `lib/pipeline.py` — passes `self.events` into the graphics render, so the press is the *same number*
  the click SFX uses (verified: doc `ev.press` = 38.65 = audio `press`).
- `graphics/cues.py` — first item lands at the scene's first word; item binding takes the run that
  starts the item's own wording and fires on the run's first word; no two items on one frame; a short
  `cue_phrases` list no longer disables all of them; `endcard` binds keyword + press.
- `briefs/graphics/repo-poki-01/beats.json` — CTA is now `endcard` (`keyword: IPHONE`); terminal lines
  carry their `$`; flow nodes follow the sentence ("Your task" → "Searches the web" → "Taps and types").
- `graphics/tests` — 28 pass (one expectation updated deliberately: an item fires on the first word of
  its phrase). Full suite: 621 passed, 9 pre-existing failures (cover lab, workspace budget, network).

### Verification before dispatch
The new document was rendered locally against the existing mix (`/tmp/preview.mp4`, preview only,
never published) and checked frame by frame: card at 35.2 s, keyword chip 36.9 s, cursor 38.4 s,
press + ring + "Following" 38.8 s, hold to the last frame; terminal prompt at 4.2 s; ticks at
10.4/12.0; nodes 16.2/18.0/21.4; chips 27.4/30.9/33.5 — every element in spoken order, no fallbacks.
