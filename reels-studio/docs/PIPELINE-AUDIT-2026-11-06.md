# Pipeline audit — 6 November 2026

Scope: local repository pipeline from production inputs and render idempotency through
queue approval and Buffer delivery. The dated handoff is historical, not approval. No
render, queue, social, release, receipt, or cover state was changed by this audit.

## Corrected

- Approval used two disagreeing panel readers; the older one accepted substring-matched,
  dated records. Approval now uses the ship guard's exact canonical panel, pinned at
  approval. Reviewers must use `viewer-panel-<id>.md`.
- Approval checked old platforms before applying `--platforms`. The ship guard now
  checks the proposed platforms, including the YouTube cover requirement. Legacy
  entries cannot be re-approved by this route.
- Delivery previously relied on CI and the earlier approval; the live posting path now
  checks selected entries and live release digests immediately before new posts. A
  missing tag or inaccessible release fails closed. Historical legacy exemptions remain.
- A cover approval fetched the live cover but did not compare it with the preview the
  reviewer saw. Mismatched bytes now require another extract and review.
- Render attempt fingerprints now reject missing, escaping or symlinked graphics input
  directories/files instead of silently omitting them; changes to those inputs are hashed.
- Release digest pins require actual lowercase hexadecimal SHA-256. The queue fingerprint
  now calls the same brief identity function as receipts and the ship guard. Malformed
  cover layouts report a rule violation rather than raising a sorting TypeError.

## Remaining limitations / decisions

- This is not proof of a complete cloud E2E run: no Actions render, voice reuse, release
  download, Buffer post, or YouTube mutation was attempted. Those require credentials,
  external services and owner authorization. The handoff's cover FAIL remains binding;
  do not enqueue or approve the Short without the owner's decision.
- Existing legacy items are deliberately exempt from the ship guard. They can still be
  selected by delivery; removing their grandfathering requires a migration/owner decision.
- Ship checks receipt brief identity, not a complete end-to-end binding of receipt,
  graphics, render manifest, panel, cover and release kit. Graphics are in the attempt
  fingerprint, but a receipt predating changed graphics cannot prove the render used the
  intended approved graphics. Define and migrate a versioned provenance contract before
  claiming that guarantee. The panel video pin is a human assertion, not proof of viewing.
- Cover approvals and panel assertions are repository records; their authorship and
  owner sign-off are not cryptographically verified. The pending cover decision cannot
  be resolved automatically. `covers/` and capture packs are ignored local inputs, so a
  fresh checkout may not have the media needed to validate authored plans.
- The three existing held queue items still have no pinning receipt. No receipts were
  fabricated or repaired. See `tools/ship.py status`.
- CI on main currently checks approved state; it cannot itself prevent direct commits
  bypassing process or detect mutations after CI and before an external service fetches
  media. Delivery now performs its own live check, but no cross-service transaction exists.
- The full local test suite is not clean. Besides environment-dependent ffmpeg, Python
  tar filter support, browser/space, yt-dlp and missing ignored media, it includes stale
  cover fixtures and a reference-report assertion. See the test run summary in the
  session response; do not interpret targeted passing tests as a full E2E certification.
