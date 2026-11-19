# Script production audit — viewer-first correction

## Findings
- The accepted MoneyPrinterTurbo video's opening is “Turn one topic into a short video. This is Money Printer Turbo.” It contains an outcome, but sounds like a detached product summary and delays the direct “you” perspective; the following lines list operations instead of carrying the viewer through a useful result. The user accepted the video, and it must remain byte-identical; this critique applies to future writing, not an unauthorized replacement.
- `tools/video_plan.py` required every plan's `question` to end in a question mark. `tools/brief_from_plan.py` copied this directly as the hook. That enforced a question shape and made a strong outcome statement impossible in the standard plan path.
- `PIPELINE.md` already says “payoff or stakes” and “viewer-benefit first,” but also prescribes rigid reveal/traction timing. `tools/brief_lint.py` checks length and name timing, not whether the viewer's result is specific, demonstrated or paid off. The general hook scorer is formula- and keyword-based; its score is advisory, not a retention forecast or a substitute for editorial review.
- Render/QA checks measure technical timing and pixel changes, not whether the story is viewer-first. A recorded editorial review is required; filled fields still need judgment and source verification.

## Change made
New `hook` plans accept a statement or question and require an editorial `script_review`. The builder carries the exact hook and review into the brief. Historical `question` plans continue working without retroactive changes. New writing guidance and review protocol: `docs/VIEWER-FIRST-SCRIPTS.md`. Focused regression tests cover statement hooks, missing review, legacy compatibility and builder propagation. Direct-authored briefs still depend on editorial discipline; this isn't a semantic guarantee.

## Example for a future MoneyPrinterTurbo-style video (not a replacement for the accepted video)
“Turn one topic into a video you can share. This tool drafts the script, finds stock footage—or uses your clips—and adds a voice, subtitles and music. Review the result and media rights before you post.”

The source describes a generated video, not automatic posting, verified accuracy, universal free use or a guaranteed publication-ready result. Avoid asserting a recent launch without a verified date. Use age-matched first-party retention and view data where available; existing small samples are directional and cannot prove that a hook caused an outcome.
