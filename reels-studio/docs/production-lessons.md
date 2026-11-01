# Production lessons → pipeline checks

Each lesson from a failed or slow cycle is enforced by a check, not left as a note.
Update this table whenever a new failure teaches us something.

| # | Lesson (where it cost time) | Enforced by |
|---|---|---|
| 1 | Clip scenes are boxed in a card with black margins. Use image scenes with focus moves, the layout that passed the viewer panel. | `preflight` brief rule: image scenes for tool media; clip only for full-frame motion (review) |
| 2 | Tool media at 640 px is soft when enlarged. Make own vector graphics at 1920×1080 for diagrams and text. Native pixels are never upscaled past 3×. | `captures` kit rule (review); the kit is in `captures/<id>/kit/` |
| 3 | A focus box that clips a label looks broken in the render. | `tools/motion/focus_check.py` (scene `keep_visible`), run by `preflight` |
| 4 | Static scenes hold too long. A visual change must come every 4.5 s. | `focus_check.py` hold limit; panel frames |
| 5 | Cloud renders run from origin `main`. A dispatch from unpushed work renders an old brief. | `reels.py cloud` calls `preflight.check_dispatch_head` and refuses when origin ≠ local or brief/receipt are uncommitted |
| 6 | `origin` disappears after a restore (`.git/config` is not snapshotted). | Re-add without credentials; token only in the push header (never written to config) |
| 7 | A brief edit makes the receipt stale (brief sha, script sha, word count). | `production_gate.validate_receipt`; refresh after every brief edit |
| 8 | A cover change is required before a failed-input render can be re-dispatched (duplicate guard). | cover pack pushed with `cover_store.py`, and `selection.json` sha updated |
| 9 | Captures and covers are gitignored; `git add` silently skips them. Use `-f` for spec and selection files. | Commit step checklist (below) |
| 10 | Stale local render files block preflight (no QA manifest). Delete a render folder before re-rendering. | `preflight` render check |
| 11 | Panel is the last gate, so one cycle costs about 15 minutes. Check locally first: focus steps, contact sheet, receipt, origin head. | Local-first order in the checklist |
| 12 | Workspace snapshot limit (128 MB / 10,000 files). Keep only current renders locally; the GitHub release holds the rest. | Cleanup after every render: compare sha with release asset before deleting a local copy |

## Per-video checklist (in order; stop at the first failure)

1. Media: tool's own media checked; own graphics built at 1920×1080 where the tool's media is small.
2. Brief: `brief_lint` 0 errors; `focus_check` PASS; SEO pack 0 errors.
3. Receipt: script and assets stages refreshed; `validate_receipt(verify_assets=True)` passes.
4. Cover: built by `covers/system`; text matches `treatment.cover_concepts[0].text`; pushed with `cover_store.py push`.
5. Commit (use `-f` for ignored spec/selection files), rebase on origin, push; check `ls-remote origin main` equals local HEAD.
6. Dispatch with `--receipt`. Wait for QA. Download the artifact. Remove any stale local render first.
7. Viewer panel on the downloaded MP4 and a contact sheet. Only then cover and copy review with the owner.
