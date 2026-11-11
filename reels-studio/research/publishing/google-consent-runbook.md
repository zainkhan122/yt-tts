# Google consent runbook — renewing and making it last for years

> **Status 2026-10-11: COMPLETED.** The app is In production and an indefinite grant is live-verified. Keep this file for the revocation/lost-credential recovery path (§2) and the guardrails (§4).

**Why the connection expires every 7 days:** our OAuth app is (or was) in **Testing**
publishing status. Google expires refresh tokens of Testing-status apps after exactly
7 days *regardless of how often they are used* — a fixed clock, not inactivity. Renewing
while still Testing only buys another 7 days. The permanent fix is one console setting:
publish the app **In production**. The 7-day cap then disappears; the grant is
effectively indefinite subject to the guardrails in §4.

Deadline history: grant issued 2026-10-10, recorded expiry **2026-10-17T13:42Z**
(18:42 Pakistan). Miss it and only YouTube *enrichment* (tags/playlists/covers) and
long-form uploads pause — Buffer publishing and already-scheduled posts are unaffected.

## 1. Permanent fix — owner does this in a browser (~3 minutes)

Console: **https://console.cloud.google.com/auth/audience** (or classic path:
APIs & Services → OAuth consent screen; the 2026 UI calls it **Google Auth Platform**).
Select the yt-tts project, open the **Audience** tab.

1. Check **Publishing status**.
   - Already **In production** → skip to §2.
   - **Testing** → continue.
2. Complete any missing required fields on the **Branding** tab: app name, user support
   email, developer contact email. Homepage + privacy policy are only *required* for full
   verification (§5); if the console asks for them at publish time, the repo homepage
   (`https://github.com/zainkhan122/yt-tts`) is acceptable scaffolding, or add a
   `/privacy/` page to the Pages site (media.py build) — decide then, not now.
3. On **Audience**, click **PUBLISH APP** → confirm. Status becomes **In production**.
4. Google will nag about verification — **ignore it.** For a personal, single-user app
   the unverified-production state is fine: consent shows a "Google hasn't verified this
   app" warning (bypass with *Advanced → Go to Hypeless Ai (unsafe)*) and a 100-user cap
   that we will never approach. Verification is optional (see §5) and does not change
   token lifetime.
5. **Do NOT** recreate the OAuth client, reset its secret, or delete the Cloud project.
   Publishing status is a free setting; it has no billing effect.

Footnote: a Google **Workspace** account could use an "Internal" app, which never has the
7-day cap at all. Not applicable to a personal channel; noted only for completeness.

## 2. Re-consent once (agent + owner, ~5 minutes)

After §1, obtain ONE fresh consent — this is what mints the long-lived token. The flow is
the repo's durable handoff (no sandbox server):

```bash
python3 tools/youtube/oauth_handoff.py start          # agent → private link (valid 24 h)
# owner: open link → sign in as the Hypeless channel → approve (warning screen is expected)
#        → stable Pages callback → "Download connection response"
python3 tools/youtube/oauth_handoff.py finish <response-file>   # exchange + verify + store
```

- The client JSON must exist locally for `start` (`~/.config/reels-studio/google_client.json`).
  A fresh sandbox does NOT have it; re-attach the same client JSON privately, or run from
  the main workspace. Never create a second client.
- The code Google issues is short-lived — attach the response file immediately.
- `finish` verifies the exact channel (`UCcWh9OdX3rbfHOtDZ6neyrA`) and re-uploads the
  encrypted `YOUTUBE_OAUTH_JSON` Actions secret.

## 3. How we verify it actually worked

Google returns `refresh_token_expires_in` **only for time-limited (Testing) grants**.
`oauth_connect.complete()` records `refresh_token_expires_at` only when present:

- Testing grant → bundle has `refresh_token_expires_at` → reports warn (today's state).
- Production grant → **field absent** → `resume_status` / YouTube delivery reports stop
  showing an expiry. That absence *is* the confirmation.
- Optional live check: dispatch `youtube.yml` mode=enrich; report shows
  `oauth_connected: true`. Covers/tags/playlists then apply automatically on the crons.

## 4. Guardrails — what can still kill a production token

1. **6 months of inactivity** — not a risk: the crons use the token several times a day.
2. **50 refresh tokens per client/user** — every consent creates a new one and the oldest
   is silently dropped past 50. Don't re-consent recreationally; one is enough. We are far
   below the cap.
3. **Owner revokes access** (Google Account → Security → Third-party access) — re-consent
   per §2 if deliberate.
4. **Account password change** — only affects Gmail/mail-type scopes; our YouTube scopes
   are unaffected.
5. **Deleting the Cloud project or OAuth client** — that destroys every token instantly.
   Never do it; if the client is lost, that is the one true re-setup scenario.

If it ever breaks (`invalid_grant`): §2 again, 5 minutes. There is no other maintenance.

## 5. Optional: remove the "unverified app" warning (not required)

Sensitive-scope verification (YouTube scopes are sensitive, not restricted — no CASA
security assessment needed) requires: organization/domain ownership verification
(Search Console), a privacy-policy URL on a domain you can verify, scope justification,
and a demo video of the OAuth flow. Review takes days to weeks. It removes the warning
screen and the 100-user cap; it changes nothing about token lifetime. Skip unless the
warning bothers you or the app is ever shared beyond its owner.

## 6. Sources checked (2026-10-11)

- Google OAuth 2.0 documentation (updated 2026-05-26): Testing-status external apps
  expire refresh tokens in 7 days; production status removes the cap.
- Google SDM authorization docs: 7-day expiry ties to client-ID production approval;
  the unverified-app screen "can be bypassed for personal use".
- Community-confirmed practice (2026): publishing to production without completing
  verification yields non-expiring tokens for personal use (100-user cap irrelevant).
