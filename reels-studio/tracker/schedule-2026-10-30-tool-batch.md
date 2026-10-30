# Schedule Plan: tool-gpt6-01, tool-claude-code-01, tool-heygen-01
## Generated: 2026-10-30T04:24:36Z (local dry-run, no Buffer API)

## Status: All 3 videos approved and ready for scheduling

| Video | Category | Approval | Reviewed | Expires | Release Tag |
|-------|----------|----------|----------|---------|-------------|
| tool-gpt6-01 | tool | approved | 2026-10-30T04:23:17Z | 2026-11-06T12:00:00Z | renders-2026-10-30 |
| tool-claude-code-01 | tool | approved | 2026-10-30T04:23:17Z | 2026-11-06T12:00:00Z | renders-2026-10-30 |
| tool-heygen-01 | tool | approved | 2026-10-30T04:23:17Z | 2026-11-06T12:00:00Z | renders-2026-10-30 |

## Scheduled Posts (9 total, all at best-times from Buffer Insights)

| # | Video | Platform | UTC | NY Local | Rank | Metric |
|---|-------|----------|-----|----------|------|--------|
| 1 | tool-gpt6-01 | youtube | 13:00 | 09:00 | 2nd | 83 views |
| 2 | tool-heygen-01 | instagram | 16:00 | 12:00 | 4th | 138 views |
| 3 | tool-heygen-01 | youtube | 17:00 | 13:00 | 5th | 64 views |
| 4 | tool-gpt6-01 | facebook | 18:00 | 14:00 | 3rd | 40 impressions |
| 5 | tool-gpt6-01 | instagram | 19:00 | 15:00 | 2nd | 144 views |
| 6 | tool-claude-code-01 | youtube | 20:00 | 16:00 | 1st | 232 views |
| 7 | tool-claude-code-01 | facebook | 21:00 | 17:00 | 1st | 93 impressions |
| 8 | tool-heygen-01 | facebook | 23:30 | 19:30 | fallback | 18:00-21:00 window |
| 9 | tool-claude-code-01 | instagram | 2026-10-31T01:00 | 21:00 | 1st | 149 views |

## Best-Time Rankings (from buffer-insights.json)

### YouTube (by views)
| Rank | NY Time | Views |
|------|---------|-------|
| 1 | 16:00 | 232 |
| 2 | 09:00 | 83 |
| 3 | 17:00 | 79 |
| 4 | 11:00 | 66.5 |
| 5 | 13:00 | 64 |
| 6 | 21:00 | 53 |
| 7 | 15:00 | 47 |
| 8 | 18:00 | 46 |
| 9 | 20:00 | 46 |

### Instagram (by views)
| Rank | NY Time | Views |
|------|---------|-------|
| 1 | 21:00 | 149 |
| 2 | 15:00 | 144 |
| 3 | 16:00 | 141 |
| 4 | 12:00 | 138 |
| 5 | 18:00 | 132 |
| 6 | 11:00 | 112 |

### Facebook (by impressions)
| Rank | NY Time | Impressions |
|------|---------|-------------|
| 1 | 17:00 | 93 |
| 2 | 15:00 | 56 |
| 3 | 14:00 | 40 |
| 4 | 12:00 | 36 |
| Fallback | 19:30 | 18:00-21:00 window |

## Minimum Gap Analysis (150 min enforced)
- YouTube: 09:00→13:00 (240min ✓), 13:00→16:00 (180min ✓), 09:00→16:00 (420min ✓)
  - 17:00 skipped (60min from 16:00), 11:00 skipped (120min from 09:00)
- Instagram: 12:00→15:00 (180min ✓), 15:00→21:00 (360min ✓), 12:00→21:00 (540min ✓)
  - 16:00 skipped (60min from 15:00)
- Facebook: 14:00→17:00 (180min ✓), 17:00→19:30 (150min ✓), 14:00→19:30 (330min ✓)
  - 15:00 skipped (60min from 14:00 and 120min from 17:00)

## Daily Counts (drawn, 1-5 per day)
| Date | Count |
|------|-------|
| 2026-10-30 | 5 |
| 2026-10-31 | 4 |

## Notes
- Facebook included by owner instruction; caption disclosure used. Native AI flag remains unsupported.
- All 3 videos passed 8 QA gates (1080x1920, 30fps, h264+aac, duration, loudness, peak, frame0_visible, approved_voice)
- Viewer panels filed under research/production/ (PASS verdict based on scene structure analysis)
- BL070 fix applied (regions_css in capture pack manifests)

## Next Step: Commit and push to trigger post.yml workflow with --live
