# Viewer panel: repo-craft-anything-01 — **FAIL, owner override**

Video: `repo-craft-anything-01.mp4` (cloud run 42038109244, 36.0 s, 9/9 cloud QA, local `short_qa` PASS).
Reviewed by opening all 7 extracted frames (2.6 / 7.7 / 12.9 / 18.0 / 23.2 / 28.3 / 33.5 s).
Evidence: `viewer-panel.md` and `frames/` from `tools/viewer_panel.py`.

## What the frames show

| t | Frame | Verdict |
|---|---|---|
| 2.6 s | Hook: "STUDY BEFORE IT BUILDS" headline on dark grid, faint at start | Text card only. The first 3 s carry no product visual. |
| 7.7 s | Chip list "Studies the original / Real inspection tools / Before any AI writes" | Generated UI chips, clear and readable. Not real product media. |
| 12.9 s | Almost blank stage: faded "CHECKED, NOT GUESSED" ghost and a faint "0" | **Placeholder-like frame.** Looks like a fade or animation gap in the stat scene. Needs a fix. |
| 18.0 s | Stat pop: "3 SCREEN WIDTHS", "Mismatches are listed" | Animated number, strong. Mostly typography plus a graphic. |
| 23.2 s | Terminal: "command line call / MCP tool for the agent" | Generated terminal graphic. Good, but it is a drawing, not a real run. |
| 28.3 s | Toggle steps: "Early alpha / Checking against the original" | Checkboxes on cards. Text-led. |
| 33.5 s | CTA: "WOULD YOU LET AN AI REBUILD IT?" and "COMMENT CRAFT" | Text-led button card. Clear. |

## Panel rules (any one = FAIL)

1. **Placeholder stage (rule 2): FAIL.** The 12.9 s frame is nearly empty. The hook (2.6 s), toggle-steps (28.3 s) and CTA (33.5 s) are text cards that carry their scene alone.
2. **Real product media < 60% of scenes (rule 3): cannot be met under the owner's standing rule** "do not use tool media unless explicitly requested". No scene shows the real tool, so this rule fails by design. This needs an owner decision, not a silent waiver.
3. Swipe-away and "what does the tool do" checks (rules 1 and 4): PASS. The tool's purpose is clear by about 8 s ("Studies the original", "Checking against the original").

## Required before a new panel run

- Fix the near-blank stage around 12.9 s (scene 3 transition or stat scene start).
- Owner to decide the real-media rule: either accept generated-only (waive rule 3 for this batch, recorded in writing) or approve real tool captures.
- Consider stronger motion or visual proof in the hook and CTA (text-led now).

## Owner override (5 Nov 2026)

The panel found the failures above. The owner, after reading this review, chose to override the panel for this batch and to schedule it on Buffer. Owner words: "override". The override waives panel rules 1 and 2 for this batch, including the real-media rule, and is recorded here as the owner's decision, not as a panel PASS. The 12.9 s near-blank frame remains unfixed.

Panel result: PASS (owner override; panel findings above stand)
