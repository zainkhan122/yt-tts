# GTA6 Clipper — review draft, not publication-ready

User-selected discovery source and primary research: https://gitlab.com/nocodehack.io/gta6-clipper/-/blob/9a96d6f3d71010a94b482eb1cbde1caf9d5d72ce/README.md
Rights and affiliation: https://gitlab.com/nocodehack.io/gta6-clipper/-/blob/9a96d6f3d71010a94b482eb1cbde1caf9d5d72ce/NOTICE.md

The tool is independent and not affiliated with Rockstar or the named platforms. Streamers retain rights in their footage: obtain permission and follow platform rules. The app itself is MIT licensed. It supports no-AI selection based on chat/loudness, with AI selection optional; don't describe every clip as AI-selected. The tool is free; optional AI services, compute and third-party publishing may cost money. Source reports Python 3.9–3.12, FFmpeg and ffprobe, and local installation; GPU optional. No product was installed or run, so no hands-on performance claims. All graphics here are illustrations, not actual app screenshots or gameplay.

## Narration script (to be recorded in approved Chatterbox Option-3 house voice)
1. Turn a long stream into vertical clips, without scrubbing the whole thing. Meet GTA Six Clipper.
2. Give it a stream or video link. It transcribes locally and looks for peaks in chat and loudness.
3. Those signals help pick moments. You can add an AI pass, but you don't have to.
4. It cuts the clip, puts the streamer above the game, and adds a hook and word-by-word captions.
5. Review each short before sharing. You can adjust the edit, and the original stays intact.
6. The tool is free, but optional services may cost money. Get the creator's permission before posting their footage.
7. Want the repo? Comment CLIP and follow Hypeless for more tools, minus the hype.

## Motion and edit direction
- Hook: a horizontal stream feeds into a vertical Short; crop guides move and lock onto the output. Heading: STREAM TO SHORT.
- Detect: waveform and chat bars grow with the narration; highlight one peak. These are explanatory shapes, NOT real metrics; no numbers.
- Pick: highlighted time range is cut out of the source timeline and passes through an optional AI lane or directly to output.
- Assemble: streamer frame moves above gameplay; caption words appear one by one. Synthetic graphics labelled illustration.
- Review: edit endpoint slides back; original timeline remains visible, then approval chip flips.
- Catch: rights card and optional costs appear as independent caution cards, not claims of automatic clearance.
- Outro: house phrase and @hypeless. Final narration and captions must be aligned from actual forced word timings, not estimated.

The accompanying silent animatic is an editorial visualization only; captions are script cues, not synchronized speech. Before publication: approved voice synthesis, genuine word alignment, voice QA, motion QA, crop review, dedicated cover approval, and production preflight remain outstanding. No publishing or scheduling authorized or performed.

## Revised preview after user feedback
The revised `gta6-clipper-repo-media-preview.mp4` uses the repository's animated `docs/img/short-kaicenat.webp` and official app screenshots from the pinned revision above. The repo labels the clip as Kai Cenat and as GTA 6; that description has not been independently authenticated. The creator's footage is not covered by an assumption of permission merely because it appears in the repo. This is a private review draft; obtain rights clearance before distribution, or replace it with licensed media.

The preview uses the actual shared `graphics/templates/shared.js`, `graphics/templates/shared.css`, `graphics/outro.js` and Anton font. The earlier silent preview used a colorful outro backdrop override. The next voiced draft uses the exact shared house outro, as explicitly requested. Captions use deliberately estimated placeholder timing, not narration alignment. The preview has no audio; approved Chatterbox Option-3 synthesis, real word timing and audio/video QA are still required. The earlier synthetic illustration animatic is superseded. The sourced screenshot is not evidence that we personally ran the software. No publication, production render approval, or rights clearance is claimed.

## Voiced review draft
The one-go route was executed end-to-end and then successfully resumed without a second synthesis: Actions run 44733767096. It used the pinned approved Chatterbox Option-3 voice, 0.7 exaggeration, 0.4 CFG and approved reference. Per-chunk Whisper character matches were 100%, 100%, 98.7%; concatenated match 99.6%. Word timestamps come from pinned whisper.cpp and interpolate unmatched words. The renderer uses the exact shared house outro and caption JS/CSS, and downloaded pinned repo media remains local. It has not been independently established that the repo sample actually shows GTA 6. No rights clearance is claimed.

`renders/repo-gta6-clipper-01/gta6-clipper-narrated-review.mp4` is for private review only. Its independent measured video QA reports BLOCK: first phrase 3.68 seconds vs 3.5 max; visual change during speech 66.9% vs 75% min; no-change share 33.1% vs 25% max; longest motion gap 4.5 seconds vs 3 seconds max. Speech pace 178.9 WPM and first-speech 0.03 seconds passed. No production receipt or user-approved cover; no posting or scheduling. The extracted frame zero is a proposed cover only, not approved.

## Motion revision v2
Requested revision adds narration-cued crop guides moving from the repo's stream sample to a portrait output; simulated chat bars and waveform building around an identified peak; a moving cut marker and selection; the actual sample separated into streamer and game panels and assembled into a vertical frame; and an animated edit handle while the original stays visible. The chart is explicitly illustrative, not platform metrics. Audio and word timings are reused unchanged; the shared house caption and exact outro modules remain in place. The retained source footage has not been rights-cleared.

The motion-v2 private review continues to BLOCK the independent video gate: speech visual change 36.9% vs 75% minimum, no-change share 63.1% vs 25% maximum, and first phrase ends at 3.68 seconds vs 3.5 seconds max. Longest motion gap now passes. These measurements are not a claim that motion is absent; they prevent a publication-ready claim. No production or scheduling was performed.
