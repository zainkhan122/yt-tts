# STATUS — Video 016 "Why You're Exhausted as a Deep Thinker"

## Step (a) assets + script — DONE (2026-08-24)

### Session context
- FULL workspace wipe 2026-08-24 → recovered docs/tools/reusable from public
  repo (blobless sparse clone). Secrets re-pasted by user. HANDOFF.md rewritten
  (commit ddeb7dd2ce). bootstrap.py green.

### Script (voiceover.txt)
- 200 beats (~7.7–8 min at measured ~2.31s/beat — up from v15's 169/6:30).
- Hook in first 2 sentences; comment-driving question at the end
  ("replaying the past or rehearsing the future?").
- R12 midpoint interrupt at beat 95 (48%): MAYA vignette (story format — v15
  used a pause-question, so the format rotates).
- Mechanism = energy economics: Jung's psychic energy (finite budget) +
  directed thinking vs fantasy thinking + inferior function (sensation) as the
  unused rest-channel. "Five rules" practical section (externalize loops, cap
  rehearsal, feed the inferior, ration depth, build a shutdown).
- Fence-checked (R22/R23): NOT #6 (3AM rumination = anxiety loop; v16 centers
  drain/energy, not worry), NOT #19 (self-criticism), NOT #18 (rest guilt).
  Pain = cognitive drain; mechanism = Ni/Ti energy economics. Not a dup.
- R12.1: no v15 signposts reused (checked programmatically in check_step_a.py).

### Captions + config
- 27 captions (R2 20–28), all anchors verified: attach to intended FIRST
  occurrence, chronological, no dup displays. 15 gold / 12 caption.
- 8 sections, all start-phrases verified present + in order.
- Title formula: V14 Psych → V15 Why → V16 Why (2 in a row — allowed; V17 must
  NOT be "Why…").
- check_step_a.py = pre-storyboard self-checker (mirrors pipeline parsing).
  ALL CHECKS PASS.

### Assets
- 9 AI images so far (ember-dusk palette — R13 distinct from v13 dawn/cool-blue,
  v14 warm interior, v15 storm grey-blue; distinct subjects: face, candle,
  dusk road, desk thinker, hands, clockwork, insomnia bed, train car, burnt
  match). **img08 (underwater depth metaphor) BLOCKED: 1st attempt by the
  image-model safety filter, retry hit the 10-images-per-turn cap → GENERATE
  FIRST THING NEXT TURN, then re-run rebuild_assets.py.** All 9 verified
  1672×941 (16:9) + sane exposure via ImageMagick (no vision available this
  session).
- 160 stock assets in /tmp/stock16 (61 videos + 99 photos, 338MB): 16 video
  queries ×4 + 18 photo queries ×6, Pexels landscape. assets.json + 
  stock_manifest.json built; fetch_assets.py idempotent (API-based);
  rebuild_assets.py rebuilds from manifest with NO API calls (use this one
  after adding img08 — avoids search-result drift).
- Totals: 178 assets (89% of 200 beats); +img08 → 179 (90%, meets R18).

### Cleanup
- Old /tmp/ytrepo clone kept for reference this turn (28M); remove at step (b).
- Workspace: only video_016 sources (videos dir otherwise empty).

## NEXT TURN — step (b) storyboard + verify
1. Generate img08 (underwater depth metaphor — reworded prompt to pass safety:
   no people, "looking up from deep dark water toward distant surface").
2. python3 videos/video_016/rebuild_assets.py  (pulls img08 into assets.json)
3. PIPE_VIDEO=/home/user/videos/video_016 python3 tools/pipeline.py storyboard
4. python3 tools/verify.py /home/user/videos/video_016 storyboard
5. Push storyboard.json + state.json + img08 to repo.

## Repo (video_016) — after this push
- voiceover.txt, storyboard_config.json, images/img01-07+09+10, fetch_assets.py,
  rebuild_assets.py, check_step_a.py, assets.json, stock_manifest.json, STATUS.md.
