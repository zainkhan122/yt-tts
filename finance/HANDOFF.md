# 🔄 HANDOFF — THRESHOLD (finance YouTube)
*Update this file FIRST at the start of every session (F25), then work.*
*If this file and VIDEO_QUEUE.md disagree, VIDEO_QUEUE.md wins on progress.*

## How to use
1. Read this whole file.
2. Refresh CURRENT STATE + NEXT ACTIONS to match reality. Push.
3. If building: `python3 tools/bootstrap.py`
4. If workspace is empty: `python3 tools/repo_sync.py pull` (needs PAT). Never full-clone the psychology vault.
5. Continue from NEXT ACTIONS.

## The project in one paragraph
**THRESHOLD** — faceless finance explainer. The face of the channel is the graphics (charts, diagrams, branded stills), not a person. English, US/UK-weighted, 25–40, “I feel behind.” Fence: sourced money mechanisms and milestones. Never stock tips, crypto, Pexels-as-look, or The Deeper Mind’s voice/tools-as-is. Psychology repo `zainkhan122/yt-tts` holds this project in folder **`finance/`**. Workspace `/home/user/finance-yt` is scratch.

## CURRENT STATE (2026-08-27, session start → end of this turn)
- User committed: 12 months, graphics-as-face, real motion kit. Go/no-go accepted.
- Psychology clone **removed from workspace** (~1.5GB). Rules extracted into MASTER_RULES.md (F1–F30).
- Tools written (bootstrap, motion_kit, qa_pack, render_thumb, preview_server, repo_sync, check_script, verify).
- Month-1 slate + metadata packs written (8 long-form + 12 Shorts).
- Secrets saved locally (gitignored): GitHub PAT + Pexels key. Pexels is **not** the look (F29); key kept only for rare object stills.
- Demo pipeline in progress this session (silent motion + 3 TTS auditions). Voice still unlocked.
- Repo `finance/` push this session if PAT works.

## NEXT ACTIONS (in order)
1. User pastes GitHub PAT → `secrets/github_pat.txt` (never commit it). Then `python3 tools/repo_sync.py push`.
2. User confirms Month-1 slate in `month1/PLAN.md` (or marks cuts).
3. Voice audition (add_voice) — lock F5. Do not reuse af_heart.
4. Video 01 step (a): sources.md + script + qa_pack. One step per turn (F16).
5. Do not generate a full video this session.

## SECRETS (do NOT push)
- `/home/user/finance-yt/secrets/github_pat.txt`  (also `~/secrets/github_pat.txt` if bootstrap looks there)
- No Pexels key. We do not use Pexels.

## KEY PATHS
- Workspace: `/home/user/finance-yt/`
- Repo folder: `finance/` on `zainkhan122/yt-tts` (main)
- Rules: `MASTER_RULES.md`
- Queue: `VIDEO_QUEUE.md`
- Month 1: `month1/PLAN.md` + `month1/vNN/metadata.md`
- Preview: `python3 tools/preview_server.py` then open the live preview
- Research (advisory only): `research/FINANCE_YT_NICHE_RESEARCH.md`, `research/GO_NO_GO.md`

## OPERATIONAL FACTS
- Do **not** `git clone` yt-tts fully (history ~6.8GB). Use `repo_sync.py`.
- `/tmp` is 993MB tmpfs and wipes often. Render motion scenes to `output/` then push.
- Snapshot cap ~128MB. Keep workspace slim: tools + current video + rules.
- Image gen cap 10/turn if we use it for illustrated stills.
- YPP plan: assume 8,000 watch hours (bar from 1 Feb 2027 for new applicants).
- 2026 inauthentic-content policy: original scripts + original charts are the defense.
