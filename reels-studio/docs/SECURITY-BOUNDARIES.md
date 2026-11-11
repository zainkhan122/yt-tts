# Hypeless security and authority boundaries

## Model authority is deliberately narrow

The optional producer has registered public-source read tools and a schema-bound draft submission tool. The critic has reporting tools, not publishing tools. Neither may execute model-generated code, choose arbitrary filesystem paths, fetch localhost/cloud metadata, change the voice configuration, access credential files, or change a production queue.

OpenRouter authorization is held by the trusted HTTP client, never injected into prompts. Exact free model/provider/version and pricing are checked first; free key credit cap, local call caps, bounded retries and receipts prevent silent paid/model fallback. The owner explicitly permits the selected free providers to retain/train on PUBLIC source material and owned test drafts only. That is not permission to upload private account/customer data.

## Cloud separation

- Research preparation receives a short-lived read-only repository token only where needed to read pinned artifacts.
- Browser capture has no model or social keys and does not authenticate to private websites.
- Model steps receive only `OPENROUTER_API_KEY`, not Buffer/Google publishing credentials.
- Shadow render jobs receive none of those keys and have read-only repository permission. Checkout credentials are not persisted.
- The comparison job receives the model key only for criticism; it has no social-publication route.
- No optional-agent workflow cron, release upload, Pages deployment, production queue mutation or activation command exists.

The production publisher remains independent and uses its existing durable reservations/receipts. Hash checks detect accidental local production-state changes inside a pilot; they are one guard, not a claim that arbitrary hostile code would be safe to execute. Only trusted controller code executes.

## Secret locations

Encrypted Actions secrets are the cloud authority. Local recovery copies live outside git in `~/.config/reels-studio` with restrictive permissions. Logs/reports expose only public resource IDs, hashes, statuses, quota/cost summaries and dates. Never include full environment dumps, raw OAuth responses, bearer headers, source credential files or unencrypted upload-session URLs.

The source scanner checks known available credential values and token patterns. It cannot prove that an unknown secret was never leaked anywhere; use least privilege, scoped credentials, provider-side limits and rotation when warranted. Do not print a secret in order to 'verify' it.

## Operational recovery

Use `RESUME.md`, `CURRENT_STATE.md`, versioned prompts/schemas, immutable asset references, Actions artifacts and provider journals. Preserve uncertain states instead of treating an interrupted request as failure and repeating it. Resume source/state from GitHub; do not depend on recollecting chat messages.

A complete blank-session restore does not magically recover private login authority. Existing cloud secrets keep cloud jobs operating, while local writes still require an authorized GitHub connection. Never create a public credential recovery endpoint or commit an encrypted vault whose decryption key is stored next to it.
