# Single source of state (Shorts pipeline)

Owner rule (5 Nov 2026): the GitHub repo is the single source of truth. Nothing outside the repo decides anything.

## The one state

`queue/publish.json`, one item per Short, is the only state. Every other file is an input that the item pins by hash.

| Stage | Who writes it | What the item records |
|---|---|---|
| enqueued (`approval: held`) | `tools/post/queue_ctl.py enqueue` | release tag, asset digest, brief canonical hash, cover |
| pinned (automatic) | `queue_ctl enqueue` and `ship.py pin-held` | `review`: MP4 sha256 taken from the release asset digest, so the bytes are identified without a manual step |
| panel (human) | the viewer-panel file | states `Video sha256: <hex>` (the exact file reviewed) and `Panel result: PASS|FAIL` |
| approved (`approval: approved`) | `tools/post/queue_ctl.py approve` (runs `ship.check` first) | `approved_panel_sha` and `approved_cover_sha` (pinned so later changes are drift) |
| scheduled | `post.yml` | Buffer ids in `tracker/publications.json` (derived log, never read for decisions) |

## One brief identity

`tools/brief_identity.py` defines it once: sha256 of the brief's canonical JSON. Receipts write it as `brief_identity_sha256`, the queue stores it as `brief_sha256`, and the guard checks both. Receipts without it are drift. Formatting does not change it. Content does.

Regenerating a brief (`tools/brief_from_plan.py`) keeps operator fields: renderer, graphics, voice_seed, qa_gates, status, review, and any key the generator does not produce.

## Inputs pinned by the item

- `briefs/<id>.json`: pinned two ways. Receipts pin raw file bytes. The queue pins canonical JSON (`common.fingerprint`). Each link is compared with its own definition.
- `research/production/receipts/*.json`: the latest receipt that pins the brief governs.
- `research/production/viewer-panel-<id>.md`: verdict comes only from its `Panel result: PASS|FAIL` line. Changing the file after approval is drift.
- Cover: pinned at approval. A later change to the queued cover is drift.
- Live release: `check-all --live` compares the queued digest with the digest GitHub reports now. A replaced asset is drift. CI runs this on every push.

## Rules

1. Nothing is approved unless `ship.check` passes. `queue_ctl approve` enforces this.
2. The scheduled file must be the reviewed file. Its SHA-256 must equal the release asset digest.
3. Items approved before the guard carry `ship_legacy: true` and a reason. They are listed, not checked. New items are never legacy.
4. CI (`.github/workflows/ship-state.yml`) installs the declared requirements, runs the ship and publishing tests, and runs `ship.py check-all --live` on every push to `main`.
5. Gates are code. Vision and human notes are advisory.

## Where to look

- `python3 tools/ship.py next <id>`: the single next action for a Short.
- `python3 tools/ship.py status` (`--write` regenerates `STATUS.md`; `--check` fails if stale).

## Commands

- `python3 tools/ship.py review <id> --mp4 <released-asset.mp4> --run <run_id> [--cover <file>]` (optional: re-verify a downloaded file against the pin)
- `python3 tools/ship.py pin-held` (pins held items enqueued before automatic pinning)
- `python3 tools/ship.py check <id>`
- `python3 tools/ship.py check-all [--live]`
- Tests: `python3 -m pytest -q tests/test_ship.py`

## Not done (honest)

- Voice fast-fail (built, not yet cloud-verified): `render.yml` has a `voice` job before `render`. It runs `make --voice-out`, which does TTS and the alignment QA once, and uploads `vo.wav` and `voice.json` (timing, order, duration, engine, sha256). The `render` job downloads them and runs `make --voice-in`, so the audio that passed QA is the audio that renders. A changed `vo.wav` is refused. Rebuilds skip the voice job. Needs one cloud run to prove it end to end.

## Not in the state (on purpose)

- Local copies of the repo. Work happens in a fresh clone, which is deleted afterward.
- Workspace copies of briefs, receipts or queue data.
- Chat or memory notes. They are not state.
