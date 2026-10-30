# Reels Studio: system overview (v2)

Goal: a small number of high-quality shorts for three niches (AI tools, AI and repos news,
quick demos). Quality over volume. Each short is made by judgment, checked by rules, and
published only with read-back evidence.

## Responsibilities

| Layer | Owner | Where | Job |
|---|---|---|---|
| Study | human + `tools/channel_decode.py` | `research/social/`, `research/reference-study/` | Learn delivery from referred channels before making anything. Learn, do not copy. |
| Radar | `tools/trend_radar.py` | `research/radar/` | Surface candidates. Flags risky items. Writes no copy or angle. |
| Topic choice | `studio/topics.py` + `config/topic-mix.json` | `topics/candidates.csv` | Rank candidates on value, freshness, proof, deadline and category balance. Refuses to rank without a study ≤7 days old. |
| Brief | a human (with the guidelines) | `briefs/*.json` | Script, claims with dated sources, shot plan, captions. No `template` field. |
| Shot plan | `studio/shotplan.py` | `tests/test_shotplan.py` | Validates timing, real-media share (≥55%), text share (≤20%), sourced stats, callouts on real media, and that captures exist. |
| Studio rules | `studio/rules.py`, `studio/check.py` | `tests/test_studio.py` | Copy rules, URL and disclosure rules, licence badge, per-platform assembly. |
| Draw and render | `studio/draw.py`, `lib/pipeline.py` | renders in CI | Draws the schedule for the day (random 1–5 videos). Renders with `DEFAULT_SKIN` (`tool-spotlight`). |
| Covers | Cover Lab (`tools/cover_lab.py`) | renders | One cover per short, from the product's real media. |
| Publishing | `tools/post/` (planner, publisher, cadence) | Buffer via `post.yml` | Plans and schedules at each channel's best times. Writes to Buffer only after a dry run. Read-back verified. |
| Production gate | `tools/production_gate.py` | `research/production/receipts/` | Blocks publishing unless receipts and hashes match. |

## Hard rules (approved, plan section 2)
1. No credits, attribution, capture dates or "own captures" in visible copy.
2. Niche hashtags only. No #AI, #Coding, #Video, #shorts-as-filler.
3. Facebook AI-narration disclosure is kept as a short tail line (`disclosure.facebook_caption`).
4. The licence is a one-time trust badge, not repeated copy.
5. Every factual claim traces to a dated source (`claims` with URLs and retrieval dates).
6. Captions never cover media.
7. Every PASS, scheduled or published claim has read-back evidence.
8. The daily draw is accurate: random 1–5 videos per day, recorded as drawn.
9. Every spoken script is viewer-first and follows `SCRIPT-STYLE.md` (owner, 2026-10-30). Start from the viewer's question, not the product's pitch. Examples and the checklist are in that file.

## Copy and production principles
- Open on the viewer's problem. Show how the tool helps in their next project.
- Viewer-first script style is mandatory: see `SCRIPT-STYLE.md` (rules, hook sugar with an accuracy test, examples, self-check).
- No promotional or robotic language. No fixed templates or formula copy.
- Use the product's real media, animations, charts, stickers and captions where they best deliver the point.
  Default to none of the repo-page scrolling or README display.
- Treatments change composition and pacing. They are not fixed scene lists.
- Per-platform variants (title, caption, CTA verb). Never one caption everywhere.

## Retired
- Brief `template` field, PLAYBOOK §8A (superseded by `GUIDELINES.md`).
- The v1 system is kept for reference at `/home/user/legacy/reels-studio-v1` (tag `legacy/reels-studio-v1`).
- Legacy briefs are blocked from scheduling by design (studio check: 43 fail). They are not migrated.
- Sent posts (40) are not edited.

## Tests
Run modules by name (discovery with `-s tests -t .` is not supported):

    python3 -m unittest tests.test_studio tests.test_shotplan tests.test_topics tests.test_publishing tests.test_brief_lint tests.test_creative tests.test_best_times tests.test_production_gate tests.test_copy_rules

Rendering and the `tool-spotlight` skin test run in CI (`render-validation.yml`). Local tooling
(ffmpeg, yt-dlp, chromium, whisper) is not installed in the sandbox.
