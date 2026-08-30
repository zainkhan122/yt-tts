# the-inner-machine/ — "The Inner Machine"

A standalone animated explainer channel about **how the mind works** (psychology, behavior,
consciousness). Start with **`brand/setup.md`** — the authoritative identity, strategy & SOP.

> ## ⚠️ SEPARATE from the reference channel
> The reference channel ("The Deeper Mind", in this repo's `vault/`) is consulted for
> **production technique only**. This channel has its **own name, brand, voice, strategy, and
> SOP** and does not follow the reference. Never merge the two.

## Layout
- `brand/` — logo.png, logo_800x800.png, banner.jpg, **setup.md** (strategy/SOP), make_brand.py.
- `pipeline/` — produce.py, tts.py, sample_voices.py, repo_push.py (the toolchain).
- `plan/video-NN-<slug>/` — per-video source (project.json + keyframes).
- `output/<Title>/` — deliverables (long-form + 2 Shorts + metadata + cover + state.json).
- `handoff/HANDOFF.md` — operational resume.

## Produce a video
```bash
python3 pipeline/produce.py plan/video-01-where-do-dreams-come-from/project.json
# -> output/<Title>/  (auto-verified: dims/fps/audio/duration; state.json = ok)
```
