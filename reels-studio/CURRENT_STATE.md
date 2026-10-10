# Hypeless — current operational state

Generated: 2026-10-10T21:52:42.054369+00:00 · source commit: `3c60ea51ef00`

| System | Actual state |
|---|---|
| Buffer delivery | enabled=True; verified pilot=True; 3/day in America/New_York |
| Buffer queue | {'approved': 3, 'held': 8} |
| Platform receipts | {'scheduled': 6, 'sent': 3, 'published_manual': 3} |
| YouTube metadata | enabled=True; completed receipts=1 |
| Long-form uploads | pilot passed=False; queued=0 |
| OPTIONAL producer/critic | production=False; publishing=False; qualification=unqualified |

## Optional pilot model lock

- producer: `nvidia/nemotron-3-ultra-550b-a55b:free`
- critic: `google/gemma-4-31b-it:free`
- audio_critic: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`

**Recorded Google grant expiry:** 2026-10-17T13:42:00+00:00

## Resume rules
- A missing local OpenRouter key is expected when it is stored ONLY in Actions Secrets; do not ask for it again without checking secret metadata.
- Never re-upload a video with an existing platform receipt/reservation.
- The optional producer/critic cannot publish or activate itself. Model scores are not parity certification.
- A fresh conversation can restore operational state from git, not private chat reasoning. A completely new workspace still needs authorized GitHub access for writes; existing cloud jobs keep their encrypted secrets.

## Start here
1. Read `RESUME.md` and `agent/ACCEPTANCE.md`.
2. Read the latest pilot report; inspect existing Actions runs before starting another.
3. Read `tracker/publications.json` and `tracker/youtube-publications.json` before any provider operation.
4. Never infer missing results. Preserve unknown/uncertain receipts and resolve them first.

## Latest optional-lab verdict / exact continuation
- **OFF / UNQUALIFIED**, no candidate cleared all pre-render gates. Read `research/pilots/PILOT_REPORT.md`.
- Five matched topics attempted; content weaknesses found. Fixed critic repeatedly 429; audio specialist requires a minimum balance not authorized by this free-only pilot. No paid route, identity spoofing, gate waiver or automatic model fallback.
- Latest critic-only run `38087458049`; latest audio diagnostic `38088477850`. No model requests need replaying blindly.
- Final credential-free cloud regression `38089170017`: 194 tests passed; production files unchanged.
- Full checkpoint restore tested: 156/156 files byte-identical. Reference `research/pilots/free-p5/full-checkpoint-archive.json`; continuation supports `checkpoint_source=archived-free-p5`.
- Existing Buffer/YouTube publishing state is independent; pilot workflows cannot activate or publish.
