> **Graphics implementation and open issues:** See [`HANDOFF-GRAPHICS-CURRENT.md`](HANDOFF-GRAPHICS-CURRENT.md). It records the current shared caption/outro, local-preview vs production distinction, actual gate scope, quality review, dependencies and outstanding failures. Technical gates do not constitute visual approval.

# Current state

This file holds no state. The state is in `queue/publish.json`, shown by the generated `STATUS.md`.

- Status: `python3 tools/ship.py status` (CI fails if `STATUS.md` is stale).
- Next step for one Short: `python3 tools/ship.py next <video_id>`.
- Rules and stages: `STATE.md`.
- History: git log. Dated handoffs (`HANDOFF-*.md`) are historical records, not state.
