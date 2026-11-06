# Creative pipeline: desktop draft and review

This is a draft creative revision, not a review, cover approval, render or publishing
authorization. The previous desktop render, panel and receipt refer to older inputs.
Do not ship or use those as evidence for this revision. Rebuild the production receipt,
render, review the actual frames and voice, and obtain the required cover/owner approval.

## Creative direction

- Lead with the viewer's task, not the repo name: “Want your AI agent to click through
  your desktop apps?” Then name agent-desktop, install it, snapshot an app, click a ref,
  verify with another snapshot, and recover with fresh refs if the old one goes stale.
- Use the README's npm command as concrete proof, identify Node/npm as prerequisites,
  and name the three supported desktop platforms. The agent, not the tool itself, runs
  the observe/act loop. A changed UI **may** produce STALE_REF or AMBIGUOUS_TARGET;
  do not promise every change produces one specific error.
- Close with a task question and the comment keyword DESKTOP. This is an experiment in
  communication, not a guarantee of retention, comments, link clicks or conversion.
- Prefer a task-specific visual and an action/state transition over decorative icon grids.
  The desktop visual is explicitly labelled as an illustration, not a screen recording.
  Validate visuals and claims against the current README before production.

## Try the cover lab locally

```sh
python3 tools/design_desktop_cover.py
python3 tools/cover_lab.py briefs/repo-agent-desktop-01.json
```

This fills in missing source illustrations and renders three 1080×1920 cover previews plus a
contact sheet under the ignored `covers/repo-agent-desktop-01/` directory. It never overwrites
existing source art. The current first concept uses a separately generated illustration; keep
that source file to reproduce the exact pixels. All concepts are drafts, not approved covers. The plan's selected index
is provisional; it is not a panel verdict. Compare at phone size, judge the truth and
curiosity of each headline and whether the visual actually communicates the tool, then
record the real decision through the existing approval process. `--apply` freezes bytes;
it does not confer human approval.

The lab now uses the bundled Inter Black typeface and keeps headline boxes on a solid,
measured, safe-area plate. The three compositions use different treatments and distinct
illustrations. Contrast and geometry checks cannot measure aesthetics, readability at
all crop sizes, or whether the promise is truthful; those remain human review tasks.

## Known validation limits

A temporary Chromium and libraries were used for a 540×960, 15 fps **silent preview**
with estimated narration timing. It has no actual TTS alignment and is not a final video.
The approved Chatterbox voice model is not cached here, and downloading the existing voice
artifact was blocked by the sandbox network. A new script requires fresh, checked voice
and timing artifacts; the prior audio would not match. The protected-main cloud render
also requires a fresh receipt. Fewer ambient effects may affect pixel-motion thresholds;
do not lower those thresholds to pass an unreviewed render. The ignored cover files must
be supplied wherever production expects them.
