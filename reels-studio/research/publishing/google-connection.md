# Connect YouTube — stable sign-in, no sandbox server required

## Your client JSON is already received

The Google Web OAuth client is secured outside git. Its registered callback is correct. **Do not recreate the client or resend its secret.** Channel consent was completed and verified on 2026-10-10. The instructions below now serve for renewal.

The old `e2b.app/setup/...` link expired when its sandbox disappeared. It has been replaced by a direct Google sign-in link and the existing, permanent GitHub Pages callback.

## Current status

YouTube is connected, its encrypted Actions secret is installed, and the first Shorts tags/playlists update was verified. Google supplied a seven-day refresh grant expiring 2026-10-17 at 18:42 Pakistan time. Check the app's publishing status; if still Testing, move it to In production and then obtain a fresh consent link from the agent. The original client JSON does not need to be recreated.

## How to authorize or renew

1. Open the **fresh Google sign-in link supplied by the agent**. Sign in on Google and choose **Hypeless Ai**, granting the requested YouTube permission.
2. Google returns you to:

   ```text
   https://zainkhan122.github.io/yt-tts/oauth/callback/
   ```

   Click **Download connection response**.
3. **Immediately attach `hypeless-youtube-connection.json` in your private conversation with the agent.** Google authorization codes expire quickly. Do not upload this file to GitHub or paste it publicly.

The agent will exchange the one-time code, verify the exact channel and store the refresh credentials as encrypted GitHub Actions secret `YOUTUBE_OAUTH_JSON`. No passwords, installations or command-line work are needed from you.

If the response code has expired, ask for a fresh Google link. You do **not** need a new OAuth client. The sign-in request link lasts up to 24 hours; the code Google issues after consent is much shorter-lived, so return the response immediately.

## Why this survives a reset

- Google redirects only to the registered HTTPS GitHub Pages callback, not to a temporary sandbox.
- The page has no analytics, external scripts, cookies, token exchange or network requests. It removes the authorization code/state from the visible URL and lets you download the response locally.
- The client secret, PKCE verifier and state-signing key never appear in the page, response file or repository.
- PKCE and signed state are saved privately with mode 600 and survive a workspace restoration. The agent validates both before exchanging the code over Google's HTTPS token endpoint.
- This is the regular Web-application OAuth flow with a real registered HTTPS callback, **not** Google's deprecated out-of-band redirect URI flow.
- The connection is not complete until the agent verifies the returned account. Only channel **UCcWh9OdX3rbfHOtDZ6neyrA** is accepted.

## What it enables

- YouTube backend tags and category/format playlists for Shorts already sent through Buffer.
- The separate long-form uploader, after its own media approvals and live pilot. Consent alone does not upload or publish a video.

Buffer publishing already works independently. Its existing posts/schedules and duplicate locks are not changed by this OAuth repair. The configured YouTube cron stays inactive without OAuth, then uses enrichment-only mode until the long-form pilot passes.

## If creating a client in future

- Enable **YouTube Data API v3** in your Google Cloud project.
- Use an OAuth **Web application** client, not Desktop, API key or service account.
- Keep the exact callback URL above, including its trailing slash.
- A normal Gmail project generally uses External audience. For unattended operation, avoid leaving the OAuth app in Testing: refresh tokens with this scope generally expire after seven days in Testing. “In production” is an app setting, not video publication. [4](https://developers.google.com/identity/protocols/oauth2)
- Only approve a personal unverified app you created and understand. If Google/account policy blocks it, resolve those requirements rather than bypassing the account's restrictions.
- Custom thumbnail eligibility is a separate YouTube channel feature. OAuth does not automatically enable it.

## Agent operations

```bash
python3 -m pip install -r tools/youtube/requirements.txt
python3 tools/youtube/oauth_handoff.py start
# Read the private youtube_authorization_url file to give the owner the direct Google link.
# Do not commit the link or pending state; never echo the client secret.
python3 tools/youtube/oauth_handoff.py finish /home/user/uploads/hypeless-youtube-connection.json
# If token exchange succeeded but GitHub secret storage failed:
python3 tools/youtube/oauth_handoff.py retry-secret-upload
```

Private state: `~/.config/reels-studio/youtube_oauth_pending.json`.
Client config: `~/.config/reels-studio/google_client.json`.
Completed refresh credentials: `~/.config/reels-studio/youtube_oauth.json`.
Do not use an expired sandbox hostname again.
