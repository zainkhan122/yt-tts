# Tooling reviews — 2026-10-12 (owner-requested)

Two repos the owner asked to check: `lightpanda-io/browser` (candidate Chrome replacement for the
capture lanes) and `darkzOGx/youtube-automation-agent` (lessons for our own pipeline). Both were read
at source today; Lightpanda was additionally exercised live in this sandbox (nightly binary
`1.1.0-nightly.10455+44e378d61`, 75 MB) because the decision hinges on capabilities, not marketing.

---

## 1. lightpanda-io/browser — verdict: NOT a Chrome replacement for us (empirically unusable for both pixel lanes)

**What it is.** A headless browser written from scratch in Zig (not a Chromium/WebKit fork). Web
loader via libcurl + html5ever parser + V8 for JS. CDP **and** WebDriver BiDi servers,
`puppeteer.connect({browserWSEndpoint})` support, cookies, custom headers, proxy, network
interception, adblocker, `--obey-robots`, an MCP server, and an "agent mode" that records
deterministic **PandaScript** replays (prototype with an LLM, ship a token-free script). Prebuilt
nightly binaries for linux/macOS (x86_64 + aarch64), Homebrew/Arch/Docker. Vendor benchmark:
123 MB vs 2 GB peak memory and 5 s vs 46 s for 100 pages (~16x lighter, ~9x faster than headless
Chrome). Telemetry is **on** by default (`LIGHTPANDA_DISABLE_TELEMETRY=true` to disable). License
**AGPL-3.0** (commit "add AGPL license"); nightly-only releases.

**What our lanes need.** Both capture paths are pixel-dependent:
- `tools/capture.py` / `tools/capture_extra.cjs` harvest *regions* from live geometry
  (`getBoundingClientRect`) to place camera moves and crops;
- the video pipeline screenshots real styled pages (hero images, CSS, fonts) into scene footage.

**Empirical results in this sandbox (today).**

| Probe | Chrome expectation | Lightpanda result |
| :-- | :-- | :-- |
| `h1` (40px font) rect | ≈ 0,40,~300,46 | `0,40,5,5` |
| `.card` (300px wide, padding 16, margin-left 48) | ≈ 68,~108,332,~52 | `5,55,300,20` |
| inline-block button | ≈ 68,~208,~120,~44 | `305,70,5,5` |
| `position:absolute; left:120; top:600` | `120,600,…` | `310,85,5,5` (flows, offsets ignored) |
| `document.documentElement.scrollHeight` | full page height | `1080` (viewport only) |
| `--dump png` of that styled 1080-tall page | full-colour 1920×1080 render | **1920×137 text strip**, 46 colours |

So: JS and the DOM execute, flex/`gap` roughly move, but the **CSS box model is not honoured**
(padding, margins, font metrics, absolute positioning) and there is **no paint stage** — the PNG dump
is documented and observed as a *text-only* rendering. `getBoundingClientRect` output therefore does
not describe the page any real viewer (or our camera code) sees, and no real screenshot exists.

**Decision.** Keep Chrome as the capture engine; do not route `capture.py`/`capture_extra.cjs` or any
screenshot step through Lightpanda. It stays interesting for **DOM/text-only** work where neither
pixels nor geometry matter — e.g. a pre-dispatch "is this claim still on the source page" fetcher for
briefs, link/robots checks, or JS-rendered text extraction in CI (9x speed / 16x memory would be real
savings there). Not integrated now: we have no lane that needs it today, the builds are nightly-only,
AGPL matters if anything is ever distributed, and telemetry must be explicitly disabled. Revisit if a
text lane appears.

---

## 2. darkzOGx/youtube-automation-agent — lessons worth taking (ideas, not the stack)

A Node/SQLite "AgentTube" system (~72 commits, single branch, built with Claude Code): 7 agents,
local dashboard (`localhost:3456`), providers for text/TTS/image/video, YouTube Data API upload,
autonomous operator. Much larger surface than our pipeline (dashboard + SQLite everywhere), but the
**gate design** is where its value sits — several patterns match what we built today, which is
reassuring, and a few are genuinely new for us.

**Patterns that validate our current design (already equivalent here):**
- *Publishing fail-closed on an uncertain upload* — "if an upload may have reached YouTube but no
  video ID was returned, it requires channel reconciliation before another attempt". That is exactly
  our `Uncertain` state + `reconcile_known`; theirs confirms this is the right shape.
- *Approval gates before autonomous action* — nothing schedules/publishes without explicit operator
  approval; our queue approvals + cover digest gate are the same idea.
- *Evidence provenance* — every factual claim must link a verified source; waivers require a written
  reason. Our receipts + "key facts verified" tables are a lighter version of the same discipline.

**Patterns worth adopting (ranked by value to us):**
1. **Scene-level repair instead of whole re-renders.** Their "Scene Repair Studio" keeps a durable
   scene manifest (narration, visual, timing, provider/task identity, revision history) and can
   regenerate ONE scene, lock scenes that already work, and rebuild only what changed. Today we
   re-rendered two whole videos (clef, higgsfield) for one-line text fixes — hours of runner time per
   typo. A per-scene manifest + targeted rebuild is the single most valuable idea in this repo for us.
2. **Analytics → learning loop (our biggest gap).** They capture 24 h / 7 d snapshots and judge CTR,
   retention, engagement against **the channel's own history** — never a universal view-count target;
   pending recommendations never influence generation, only operator-approved learnings become
   planning constraints; title/thumbnail A/B experiments restore the control before reporting results,
   require a 95% evidence threshold, and explicitly report *inconclusive*; ROI shows missing evidence
   as unavailable rather than zero. This is directly upstream of the owner's "cover so it gets
   clicked" goal: we currently publish and never look at CTR/retention.
3. **Scene-aware retention** — map YouTube's retention curve onto stored scene durations to find the
   exact beat that loses viewers; learnings per scene, not per video. Pairs naturally with (1).
4. **Readiness probe with persisted, expiring results.** Their "Run verified check" does live text +
   narration + channel probes, creates and decodes a temp MP4, validates every queued upload's
   metadata — never uploading — stores results (SQLite) with remediation steps, blocks autonomous
   runs on a recorded failure, and treats results older than 24 h as unverified. We have the pieces
   (`preflight`, `brief_lint`, `seo_pack`) but no persisted, staleness-aware readiness state.
5. **Stable rule IDs for the SEO/content audit** (severity summary + findings persisted; dismissing a
   false positive carries the reason forward to later audits). Our `brief_lint`/`seo_pack` print
   results; they do not survive as a reviewable record. Cheap to adopt.
6. **Paid-probe discipline:** paid checks are separate opt-ins, and it "never silently tries a second
   paid provider" — good phrasing of a rule we should keep for render/TTS providers.
7. **Comments lane (optional):** sync every 4 h, classify themes/sentiment/questions, quarantine
   likely spam, draft replies for approval, never auto-post (needs `youtube.force-ssl`). Out of scope
   now; noted as a possible future lane.
8. **Shorts from long-form with provenance inheritance** and a separate Shorts analytics baseline —
   relevant only once we have long-form at all.

**Not adopting:** the dashboard/SQLite/Express stack (we are CLI + journals + receipts by design),
the multi-provider media generation sprawl, and its naming/provenance ceremony where our receipts
already cover it.

**Suggested next actions (owner's call, none started):** (a) scene manifest + single-scene rebuild in
the renderer; (b) a small analytics lane: fetch 24 h/7 d stats for sent Shorts, store per-video, and
report CTR/retention vs our own history — this is the feedback that tells us whether covers/titles
work; (c) persist preflight/lint results with rule IDs into the receipt instead of printing them.
