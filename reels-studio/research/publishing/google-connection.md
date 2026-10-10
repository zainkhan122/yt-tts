# One-time YouTube connection — no installation needed

The Buffer key cannot grant direct YouTube access. This connection enables:

- Long-form uploads, custom thumbnails and scheduled publishing.
- Backend tags and category/format playlists for YouTube Shorts already posted through Buffer.

**You never give the agent your Google password.** Sign-in/consent happens on Google.

## What you do once

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create/select a project, for example **Hypeless Publishing**. Enable **YouTube Data API v3** in its API Library.
2. Open **Google Auth Platform** (or APIs & Services → OAuth consent screen). Set the app name and your support/contact email. Use **External** audience for a normal Gmail account. While testing, add your Google account as a test user. For ongoing unattended access, move the OAuth app to **In production** before the final connection; Testing-mode refresh tokens generally expire after seven days. This app setting does **not** publish any videos. [4](https://developers.google.com/identity/protocols/oauth2)
3. Create an OAuth client of type **Web application**, not Desktop, service account or API key. Add this exact **Authorized redirect URI**, including the trailing slash:

   ```text
   https://zainkhan122.github.io/yt-tts/oauth/callback/
   ```

4. Download that client's JSON. Tell the agent it is ready. The agent will open the private **YouTube connection** page; upload the JSON there, then click Google consent and select the **Hypeless Ai** channel. Do not paste the secret into public chat, a GitHub issue or a source file.

If Google shows an unverified-app warning, only proceed for the personal app you created and understand. If your account policy blocks it, stop and resolve Google's verification requirements rather than bypassing account restrictions.

Before the first long episode, also check YouTube Studio → Settings → Channel → Feature eligibility for custom thumbnails. OAuth does not itself enable channel features. If YouTube refuses a thumbnail, the worker keeps the video private and reports the problem.

## What the agent/system does

- Runs the connector on an HTTPS live-preview host (no localhost connection from your browser).
- Uses OAuth state validation, a 30-minute session and PKCE.
- Requests the `youtube.force-ssl` scope needed for uploading, metadata and playlists. Google's consent wording is broader than our actual operations; this integration does not use deletion/comment endpoints.
- Verifies the authorized channel is exactly **UCcWh9OdX3rbfHOtDZ6neyrA** before saving credentials.
- Stores the refresh token/client secret as encrypted GitHub Actions secret **YOUTUBE_OAUTH_JSON**. No credentials are committed.
- Keeps private recovery files outside git, mode 600. The separate upload-session encryption key is already provisioned as **YOUTUBE_STATE_KEY**.
- Leaves publishing disabled after connection. First run a private pilot, check the actual video/thumbnail/metadata, then explicitly approve a public pilot.

## Important distinctions

- **OAuth app production** ≠ **video publication**.
- **Uploading successfully** ≠ **processing successfully** ≠ **publicly published**.
- Current `videos.insert` documentation says unverified API projects are not restricted to private viewing, while a generated summary on the video-resource page still repeats the older audit warning. We will verify the actual project's public-publishing behavior with a pilot, not promise access from documentation alone. The uploader holds and reports permission/privacy failures rather than retrying new uploads. [1](https://developers.google.com/youtube/v3/docs/videos/insert)
- Google access tokens are short-lived and refreshed automatically. Revoked/expired refresh tokens produce a reconnect alert, not endless retries.
- “Private-first” means private on YouTube. This repository/its existing Release archive are public; do not use this storage design for confidential embargoed media without changing the storage backend first.

## Agent commands (not user installation steps)

```bash
python3 -m pip install -r tools/youtube/requirements.txt
# Start with the start_process tool, not a blocking bash call:
python3 -u tools/youtube/oauth_connect.py --port 8765
```

Open the private `/setup/<one-time-key>` path printed by the connector on its HTTPS preview host. The stable Pages callback routes only to a valid HTTPS `.e2b.app` session; the connector independently checks signed state and PKCE before exchanging the code. Stop the connector after successful setup.
