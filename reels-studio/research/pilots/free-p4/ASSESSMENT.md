# Free-p4 — controller/tool-budget failure, no parity result

Run: https://github.com/zainkhan122/yt-tts/actions/runs/38076909677  
Source revision: `57dd830`  
Models: unchanged selection revision 2; only fixed free endpoints.

All five cases fetched/read their registered evidence, then continued requesting exact-passage searches until the five-round tool budget ended. No complete draft was submitted. There were 25 successful inference receipts reporting $0; no candidate was rendered, paired-reviewed or published.

This outcome is primarily a **controller phase-design defect**, not evidence that every model-authored fact would be wrong. The harness offered research tools without reserving a final submission round. Free-p5 explicitly reserves that round after required sources have been read and forces only the existing draft-submission tool. Evidence, word-count, voice, asset and publishing gates are unchanged; unconsulted sources still block submission.

The optional system remains **OFF / unqualified**. Visual/audio parity and autonomous post-render repair have not been demonstrated by this run.
