# 🗄️ STOCK MEDIA + STORAGE STRATEGY (Tested Live)

**Status of what I confirmed today (Aug 15, 2026):**

| Capability | Result |
|---|---|
| Pexels API — photos | ✅ Works without key (occasional 401 = rate limit) |
| Pexels API — **video b-roll** | ✅ Works — downloaded a real 3.4MB HD clip |
| Direct Pexels file download | ✅ Works |
| Openverse (Flickr + more, CC-licensed photos) | ✅ Works, no key, reliable |
| Wikimedia Commons (photos) | ✅ Works, no key |
| Pixabay | ❌ Requires key |
| `git` in workspace | ✅ Available |
| **Clone (READ) your GitHub repo** | ✅ Works (public repo) |
| **PUSH to your GitHub repo** | ❌ **Needs credentials (I don't have them)** |

---

## 1. STOCK MEDIA — YES, I can get it. Here's the plan.

### How to use it (I run this for you):
```bash
python3 tools/stock_fetch.py pexels-video "rain window night" --n 3 --out stock
python3 tools/stock_fetch.py pexels-photo "lonely person fog"  --n 6 --out stock
python3 tools/stock_fetch.py openverse "silhouette crowd"    --n 6 --out stock
```

### Why this changes our videos (big deal):
Real **motion b-roll** (rain, crowds, fog, hands, cityscapes) mixed with our AI images = the "Aperture / BRAINY DOSE" feel. Movement + realism, which is exactly what Video #1 was missing.

### One 2-minute upgrade I recommend (not required):
Pexels without a key works but hits intermittent 401 rate limits. **Get a FREE key** at https://www.pexels.com/api/ (sign up → "New API key") and give it to me once. I'll store it in the workspace as `~/.pexels_key` and it becomes bulletproof + lets me search precisely.

---

## 2. STORAGE ARCHITECTURE (Workspace + GitHub Vault)

### The constraint (honest):
- Workspace snapshot ≈ **128 MB / 10,000 files** cap.
- One finished video ≈ **85 MB** (final.mp4 ~65MB + voiceover ~11MB + images ~10MB).
- → Workspace can only hold **~1 finished video** at a time. It's our *workbench*, not our *archive*.

### The split:

| Location | Role | What lives there |
|---|---|---|
| **Workspace** (`/home/user`) | Active workbench | Current video (script, images, build, final.mp4 awaiting download) + all text assets (plans, prompts, research — tiny) + tools |
| **GitHub repo `zainkhan122/yt-tts`** | Permanent vault | Every finished video, voiceover, brand asset, research archive — organized |

### Proposed repo structure (vault):
```
yt-tts/
├── vault/
│   ├── brand/                    # logo, banner
│   ├── research/                 # pain points, analysis, strategy docs
│   ├── pipeline/                 # build scripts, prompts, tool docs
│   ├── stock/                    # downloaded stock clips we reuse
│   └── videos/
│       ├── 001_people_who_feel_everything/
│       │   ├── final.mp4
│       │   ├── thumbnail.jpg
│       │   ├── voiceover.mp3
│       │   ├── script.md
│       │   └── metadata.md
│       └── 002_...
```

### Workspace hygiene rules (I'll follow automatically):
1. Keep only the **current** video's binaries in the workspace.
2. After you confirm you've downloaded/pushed a video → I delete its `final.mp4` + `voiceover.mp3` from the workspace (they live in your vault).
3. Scripts, images (compressed), and build code stay in workspace (they're small and re-usable).

---

## 3. GITHUB: WHAT I NEED TO PUSH (pick ONE)

I can READ the repo anytime (public). To **push** from my side I need one of:

### Option A — Fine-grained PAT (lets me push directly) — 3 minutes
1. GitHub → Settings → Developer settings → **Personal access tokens** → *Fine-grained tokens* → Generate
2. **Repository access:** Only select repositories → `zainkhan122/yt-tts`
3. **Permissions:** Contents → Read and write (nothing else)
4. **Expiration:** 30 days (renew as needed)
5. Paste it in chat → I save it in the workspace (note: it'll be stored in a file under `/home/user`; never paste it anywhere public)

### Option B — You push, I pull (works TODAY, zero setup)
You already have `sync.bat` in the repo. Flow:
1. I build everything in the workspace → you download the files
2. You drop them into your local `yt-tts/vault/...` → run `sync.bat`
3. When I need an old asset, I clone/pull and fetch it

### Option C — I give you a manifest + script
I generate a `manifest.txt` (list of files to move) + a `sync.bat` that mirrors the vault folder names, so your local push is one double-click.

**My recommendation: Option A** (one token, then the vault is fully automatic — I push finished videos straight to the repo, organized, with zero manual work from you). Option B works immediately if you'd rather not share a token.

---

## 4. WHAT THIS MEANS FOR THE MONTH-AHEAD

1. **I'll fetch a curated stock library** (20-40 clips/photos) into `stock/` for the v2 videos — rain, crowds, fog, silhouettes, city nights, forests, faces.
2. **v2 videos = AI images + real b-roll + kinetic captions** (fixes the "static" problem + adds real motion).
3. **Every finished video → vault repo** so nothing is ever lost and I can rebuild/repurpose anything later.

**Your two micro-actions (when convenient):**
- (Recommended) Pexels free API key → paste here
- (Recommended) GitHub PAT (Option A) → paste here
