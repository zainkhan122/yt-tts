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

## 4. NOT done, and exactly why
- **No MP4.** The render runs on GitHub Actions only (owner standing order). This session has no
  GitHub token: `uploads/` is gitignored and absent from the clone, `/var/tmp/gh/token` and
  `~/.config/reels-studio/gh_token` do not exist, `GH_TOKEN` is unset. `tools/preflight.py` and
  `tools/capture_store.py` both stop with **401 Bad credentials**. Nothing was dispatched.
- **No production receipt.** `tools/receipt_build.py` needs `captures/repo-poki-01/manifest.json`.
  The capture pack needs `tools/capture_pw.py` (playwright + Chromium, not installed here).

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
