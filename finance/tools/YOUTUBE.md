# YouTube publish (gated)

Never uploads unless every lock is true. Default visibility is **private**. Public is refused. This tool never asks for a Gmail password.

## One-time setup

1. Google Cloud Console → enable **YouTube Data API v3**.
2. Credentials → **OAuth client ID** → type **Desktop app**. Download the JSON.
3. Save it **outside git**:

```
~/.config/the-public-record/youtube/client_secret.json
```

(or `secrets/youtube_client_secret.json`, which is gitignored)

4. Paste each channel’s **Channel ID** (`UC…`) into `youtube_channels.json`. Studio → Settings → Channel → Advanced. Empty ids are not allow-listed. Upload is blocked until they are real `UC` ids.

5. Sign in once per channel (the Google account that **owns** that brand channel):

```
python3 tools/youtube_publish.py --auth --channel UC…your…id
```

The token is written to `~/.config/the-public-record/youtube/tokens/UC….json` (`0600`). Not the repo. If the login’s channel id does not match `--channel`, auth is refused.

```
pip install google-auth google-auth-oauthlib google-api-python-client pillow
```

## After a film is cut

```
python3 tools/youtube_publish.py --pack "episodes/NAME" --channel UC… -o approval.json
python3 tools/youtube_publish.py approval.json --dry-run
```

Dry-run prints channel, title, visibility, video path, thumbnail path. It does **not** upload.

If that is the right package: set `"approved": true` (JSON boolean, not the string `"true"`). Visibility stays `"private"` unless you set `"unlisted"`.

```
python3 tools/youtube_publish.py approval.json --upload
```

`--upload` is required. No flag → refuse. `--dry-run` and `--upload` together → refuse.

The tool then:

- checks `approved === true`
- checks channel id against `youtube_channels.json`
- checks video + thumbnail exist
- checks metadata (title length, Shorts `#Shorts`, longs have the disclaimer)
- checks the OAuth token belongs to **that** channel
- uploads private/unlisted
- sets the thumbnail
- posts the pinned-comment text (YouTube Data API cannot pin; pin in Studio)
- writes a report with `youtu.be` URLs under `~/.config/the-public-record/youtube/reports/`

## Locks (upload will not start if any fail)

| Lock | Rule |
|---|---|
| approved | JSON `true` only |
| channel | `UC` + 22 chars **and** in `youtube_channels.json` |
| video | existing non-empty `.mp4` |
| thumbnail | existing jpg/png, ≥640×360, ≤2MB |
| metadata | title + description; longs ≤60; Shorts ≤50 + `#Shorts` |
| OAuth | token for **this** channel id, outside the repo |
| command | `--upload` |
| visibility | `private` or `unlisted` only |

## What it will not do

- Public uploads
- Upload without `--upload`
- Upload with `"approved": "true"`
- Use a token from a different brand account
- Store tokens in git
- Ask for a password
