# One line: make Shorts

    python3 tools/make_shorts.py "make 3 shorts today"                 # produce and queue; no Buffer write
    python3 tools/make_shorts.py "make 3 shorts today and schedule"    # also dry-run, verify, then schedule
    python3 tools/make_shorts.py --resume                              # continue the open batch
    python3 tools/make_shorts.py --status                              # where it stands
    python3 tools/make_shorts.py --approve-cover <id>                  # after you have looked at the cover

Run it in the background for long stages (cloud render takes minutes): `start_process`, then poll the
batch with `--status`. Every subprocess writes a log under `/var/tmp/reels/make-shorts/`.

## What the agent must do first
- **Topics are approved by the owner, always.** Ask, then record the owner's words:
  `python3 tools/make_shorts.py --approve-topic <id> --note "<owner's words>"`. The approval is bound to the
  plan's sha256; an edited plan must be approved again. `select` stops and lists unapproved topics.
- N valid plans in `videos/<id>/plan.json` (`tools/video_plan.py` PASS), and a reviewed cover in
  `covers/<id>/selection.json`.

## Legacy briefs
`python3 tools/mark_legacy.py` regenerates `config/legacy-briefs.json` from `tracker/publications.json`: a
brief is legacy when a platform record is `sent` or `published_manual`. For legacy briefs the cloud-source
checks (assets, capture-pack release, cover) are notes, not blocks. `scheduled` and `uncertain` are not legacy.

## Stages
| # | Stage | Stops when |
|---|---|---|
| 1 | select | fewer than N valid plans with no queue item |
| 2 | build | plan no longer valid; brief or receipt fails (receipt is validated before it is written) |
| 3 | gate | any BLOCK in `tools/preflight.py` for any brief in the batch |
| 4 | source | capture packs or covers not pushed; commit, rebase, push fails; origin != HEAD |
| 5 | render | cloud workflow not success (log path printed) |
| 6 | fetch | release asset missing or downloaded bytes differ from the release digest |
| 7 | panel | WAIT for the viewer-panel verdict file; FAIL returns the video to production |
| 8 | cover | WAIT for `--approve-cover <id>` after you look at `renders/covers/<id>-cover.jpg` |
| 9 | queue | queue or commit fails |
| 10 | buffer | dry-run or verify not success; schedule runs only with "and schedule" / `--schedule` |

## Rules the driver enforces (see config/failure_ledger.json)
- No schedule without the words "schedule" or `--schedule`.
- A repeat cloud dispatch within 6 h is refused by `reels.py cloud`; the driver never passes `--redispatch`.
- Media the brief names must be on disk or recorded in the pushed capture pack.
- The cover text in the plan must equal the reviewed selection, and the cover file must match its sha256.
- Origin must be readable and equal to HEAD before any cloud dispatch.
