# Reference playbook — what the studied reference shorts teach, and where each principle is enforced

Source analyses live in `research/reference-study/` (house reference channels) and
`research/critiques/instagram-adilet.fndr-2026-11-10.md` (external creator teardown, VLM frame
forensics). These are the distilled, transferable principles. Rule (owner, 2026-11-11): a
principle is ADOPTED only once it is mapped to a gate below — otherwise it is a note, not a rule.
Reference = lead, never copy: we take anatomy, never assets.

| # | Principle observed in reference shorts | Where it is enforced now |
|---|---|---|
| R1 | Never a static hold: reference cuts land every ~2–7 frames of motion; our bar: a visual change at least every 4.5 s. | `tools/motion/focus_check.py` hold limit via `preflight.check_motion`; viewer panel "motion" bar |
| R2 | Signature move is text that animates WITH the voice: words reveal/pop on the spoken word; key words in the accent colour. | House caption band — `velocity-black`/`musike` `.cw.pk` grammar (registered in `graphics/tests/test_house_style.py`); `payload.accent_words` pin the pink words per scene |
| R3 | The product/interface carries the demo — a device or app mockup is on screen the whole time; bare text-on-background cards never carry a scene. | `tools/viewer_panel.py` bars ("media >= 60% of scenes; cards support, never carry"); musike template puts every scene INSIDE the player window |
| R4 | Interfaces respect safe areas and the frame edge — nothing the viewer should read is clipped. | `graphics/render.py::audit_overflow` (lesson 25) |
| R5 | Restrained grade: dark ground, ONE accent, white text; subtle grain/halftone surface treatment — not flat renders. | Palette per `template.json`; shared postfx grain/halftone/vignette in `graphics/templates/shared.css` (applied to every graphics render) |
| R6 | Structure beats freeform: numbered/step content inside the device frame, one idea per scene, hook claim in sentence one. | `graphics/beats.py` lints (B1 one scene per phrase, B4 depicts-overlap, max_text caps); viewer panel clause "hook claim in sentence one" |
| R7 | End with the account, not an ad: profile card, Follow affordance with a cursor press, a COMMENT keyword the viewer can act on. | House endcard (`D.brand` + `ev.press`-synced cursor); enforced by `test_house_style.py` endcard checks |
| R8 | Trust beat before the CTA: reference shorts state a plain catch/risk before asking for anything. | Beat plan keeps an honesty scene (`honesty_card`) before `endcard`; feature-sheet evidence pinned by `lint_feature_sheet` (F6 verbatim-quote rule) |
| R9 | Muted-legibility: the whole pitch must work sound-off — first frame sells the benefit, giant captions from word one. | Viewer panel bars; caption band font size is a registered grammar property (lesson 24 gate) |
| R10 | Motion churn, not theme churn. Every beat earns a VISUAL MOMENT (state change, tap, progress, swap-in), but the teardowns on file (adilet 2026-11-10, gittrend.io 2026-10-24) show the references keep ONE visual system — mostly plain cuts/fades, minimal kinetic type, a single accent — and vary the choreography, never the colors/type/shapes. Per-beat style churn burns brand memory and breaks muted-legibility. Corrected per owner question 2026-11-11: "each beat = powerful animation, different style/colors/shapes" is half right — the motion bar is non-negotiable; the style-churn bar is not what the references do. | Motion floor: `tools/motion/focus_check.py` + viewer-panel "motion" bar; ONE system: `test_house_style.py` (registered grammars, `D.brand` endcard); beats choreography per scene: `beats.py` lints B1/B4 |

Process: when a new reference analysis lands (`research/critiques/`), extract principles into this
table in the same commit; a principle stays "note, not rule" until the right-hand column names a
real gate. Rows R2–R4 were promoted to code on 2026-11-11 during the musike v3/v3.1 cycle.
