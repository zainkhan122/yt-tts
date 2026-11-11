# Posting rules (owner, 2026-10-21) — enforced in code

These rules are part of the system. `tools/post/best_times.py` implements them, `tools/post/cadence.py`
calls it when `config/publishing.json` → `schedule.best_times.enabled` is true, and
`tests/test_best_times.py` checks them.

1. **Daily count: random 1–5 shorts per day.** Each calendar day (America/New_York, the channel calendar)
   draws one number from 1 to 5 with a CSPRNG. The draw is stored in `tracker/daily-counts.json`
   and is never redrawn, so reruns and dry-runs agree. Dated overrides above 5 are ignored.
2. **Best time per channel.** Each channel (YouTube, Instagram, Facebook) ranks posting hours by
   median views (Facebook: impressions) from `tracker/buffer-insights.json` (read-only Buffer
   Insights snapshot). Only hours with at least 3 sent posts are ranked. Hours without enough data
   fall back to the researched profile, then the 150-minute grid. Every fallback is recorded in
   the plan's provenance.
3. **Sequence, no shared times.** When a day has more than one short, the k-th short takes the
   k-th best hour of that channel. Slots on one channel are at least 150 minutes apart, so no two
   shorts share a time on the same channel. Channels rank independently, so the same short can
   land at different times on each channel.
4. **Before any live schedule:** run a dry-run, check the count and per-channel times it prints,
   then schedule. Read back Buffer's state afterwards. Scheduled is not the same as published.

Limits: the insights sample is small (about 35 posts per channel), and view counts favour older
posts. Rankings are directional and will firm up as data accumulates. Rankings are re-read on each
plan, so new Insights snapshots change future slots automatically.
