# Cloud render + Buffer dispatch with a GitHub PAT

**Short answer: yes.** With a GitHub PAT that carries the right permissions, the whole chain
(brief → cloud render → QA → queue → Buffer scheduling) can be driven end to end, without a
browser. This file is the exact contract: what the PAT must be able to do, what I run with it,
what it still cannot do, and where each step fails closed.

Repository: `zainkhan122/yt-tts`

---

## 1. What the PAT must be able to do

| Step | Needs | Classic PAT scope | Fine-grained PAT permission |
|---|---|---|---|
| Push briefs / queue to `main` | write repo contents | `repo` | Contents: **Read and write** |
| Dispatch `render.yml` / `post.yml` | start a workflow run | `workflow` | Actions: **Read and write** |
| Read run status, job logs, artifacts | read runs/artifacts | `repo` | Actions: **Read and write** |
| Create the public Release | write a release | `repo` | Contents: **Read and write** |
| Install `BUFFER_API_KEY` as an Actions secret | write repo secrets | `repo` (+ admin on the repo) | Secrets: **Read and write** |

Minimum classic PAT: **`repo` + `workflow`**, with the owner account as a repo admin.
If you prefer a fine-grained PAT: **Contents R/W + Actions R/W + Secrets R/W** on
`zainkhan122/yt-tts` only, no org-wide access.

The PAT is used two ways, both supported by the repo as it stands:
- **Environment** — `GH_TOKEN` (read by `lib/secrets.py`), or saved once at
  `~/.config/reels-studio/gh_token` (chmod 600) so every command finds it.
- **Git push** — `reels.py cloud` and `make_shorts.py` push with the same token.

Nothing is ever printed or committed: `lib/secrets.py` redacts the token from every log line.

---

## 2. What I run, in order

### 2.1 Cloud render (GitHub Actions, `render.yml`)

```bash
# one runner per brief, up to 10 in parallel
python3 reels-studio/reels.py cloud tool-<id> [...] --receipt reels-studio/research/production/receipts/<batch>.json
# or drive the workflow directly:
python3 reels-studio/tools/gh_actions.py dispatch render.yml -i briefs=tool-<id> -i publish_release=false
python3 reels-studio/tools/gh_actions.py wait <run_id> --timeout 2400
```

The workflow is: `plan` → `voice` → `render` → `publish` (Release) → `finalize-attempt`.
- **plan** — validates the briefs, pulls the capture packs, reserves input fingerprints
  (a repeat dispatch of the same brief inside 6 h is refused).
- **voice** — TTS + alignment QA; a bad voice fails here, before any video minutes are spent.
  Also runs the "UI proof" gate (no text-on-grid shorts). The VLM half of that gate needs
  `NVIDIA_KEY`; without it the gate warns and skips the VLM step only.
- **render** — the video, with QA gates (`tools/short_qa.py`: duration, WPM, hook, visual
  change, motion gap) and the SEO pack gate.
- **publish** — one verified public Release per batch (opt-in via `publish_release=true`);
  the temporary Actions artifacts are deleted afterwards.
- `renderer: "graphics"` (the house engine) is supported on the runner: the workflow
  sparse-checks out `/reels-studio/graphics/`, and `cloud/setup-render.sh` installs the
  Playwright Chromium the engine needs.

### 2.2 Buffer scheduling (`post.yml`)

The delivery workflow is three passes, and the third one is the only one that mutates Buffer:

```bash
python3 reels-studio/tools/gh_actions.py dispatch post.yml -i mode=dry-run    -i video_ids=<id>
python3 reels-studio/tools/gh_actions.py dispatch post.yml -i mode=verify     -i video_ids=<id>
python3 reels-studio/tools/gh_actions.py dispatch post.yml -i mode=schedule   -i video_ids=<id>
```

`tools/make_shorts.py` does exactly this sequence (dry-run → verify → schedule) and stops on
the first failure. The video itself is hosted as a stable GitHub Pages URL and handed to Buffer
as a link — no upload to Buffer's storage.

Buffer writes are gated three ways, all fail-closed:
- `config/publishing.json` → `buffer.enabled: true` and `live_pilot_passed: true`
- the workflow sets `ALLOW_BUFFER_MUTATIONS=true` **only** when the mode is `schedule`
- the publisher refuses live runs outside GitHub Actions

Connected channels (Buffer): **Facebook `6ac8fe8d6a5c39ccb6623485`**, **Instagram
`6ac8fe316a5c39ccb66231cb`**, **YouTube `6ac904af6a5c39ccb662a01f`**. TikTok and X have brand
profiles but are **not** connected to Buffer, so nothing is scheduled there.

### 2.3 Installing the Buffer key as an Actions secret

The Buffer API key is **not** in the repo and must not be pasted into a chat. With the PAT:

```bash
# from a local file or an env var — the value is never printed
python3 reels-studio/tools/gh_secret.py set BUFFER_API_KEY --from-file C:\secure\buffer.txt
python3 reels-studio/tools/gh_secret.py list      # names + timestamps only
```

The tool fetches the repository's public encryption key, seals the value with it (libsodium
sealed box) and uploads the ciphertext — the same mechanism the YouTube OAuth connector uses.

---

## 3. What a PAT still cannot do (the honest limits)

1. **The PAT is not a Buffer credential.** Buffer still needs its own API key
   (`BUFFER_API_KEY`). Either save it locally (`~/.config/reels-studio/buffer_token`) or hand me
   the file path and let `gh_secret.py` install it. Without it, `post.yml` can only do
   dry-run / verify / inventory — no scheduling.
2. **Actions secrets are write-only.** After `gh_secret.py set`, nobody (including me) can read
   the value back from GitHub. That is the point, but it means a lost key must be re-issued.
3. **GitHub Actions minutes/billing.** The render job is 4 vCPU / 16 GB, up to 10 briefs in
   parallel, 80-minute timeout. A private repo burns paid minutes; a public repo uses the free
   tier. Cost control: `max-parallel` and the 6-hour duplicate-dispatch guard.
4. **A local checkout with git remotes is required.** `reels.py cloud` refuses to dispatch
   unless the working tree matches `origin/main` (it pulls `--rebase` first). A code-only
   archive with no `.git` can write briefs and plans but cannot dispatch until it is a real
   checkout with `origin` pointing at `zainkhan122/yt-tts`.
5. **The voice stack is local to the runner** (Kokoro / Chatterbox weights, no API key), but
   `NVIDIA_KEY` is optional and only affects the VLM half of the UI-proof gate.
6. **Buffer's own limits apply** — rate limits, per-channel queues and the daily cap in
   `config/publishing.json`. The publisher paces posts and stops rather than double-posting.

---

## 4. The full daily loop, one screen

```bash
python3 reels-studio/tools/get_topics.py                      # every source, last 24 h, deduped
python3 reels-studio/tools/topics_covered.py check <topic>    # prove it is not already covered
# ... write the brief + plan + beats (the agent's part) ...
python3 reels-studio/reels.py cloud <brief-id> --receipt <receipt>.json   # render in the cloud
python3 reels-studio/tools/make_shorts.py "make 1 short today"   # queue + Buffer (scheduling is part of the request)
python3 reels-studio/tools/make_shorts.py "make 1 short today" --no-schedule   # rehearsal: read-only Buffer checks only
```

Every stage refuses to do the wrong thing on its own: the topic sheet filters covered topics,
`studio/select.py` blocks a covered subject, `tools/make_shorts.py` refuses to render a topic
another video already covers, and the Buffer publisher schedules only queue entries that were
reviewed and approved.
