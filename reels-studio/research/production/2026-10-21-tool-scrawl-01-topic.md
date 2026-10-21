# Topic selection — 2026-10-21

**Video:** `tool-scrawl-01` · **archetype:** workflow (new for the channel: the last three were
quest, myth-bust and demo-first)

## Why this one

- **Fresh, verifiable, and demoable in one sentence.** Scrawl is a macOS menu-bar capture tool
  (release v0.3.11 published 2026-10-21T02:51Z): press ⌥⇧S, talk and draw over the screen, and it
  packs a contact sheet, keyframes, a time-aligned transcript and a manifest into a bundle you paste
  into an agent.
- **The viewer job is concrete:** stop writing paragraphs describing a UI bug; show the agent.
- **It has real media on the product page** — a live Mac window mock, the iPhone-mirror cards, the
  "How it works" strip and the Install block — so the film can show the product instead of cards.
- **The catch is honest and useful:** Apple silicon + macOS 26 only, the Windows build is an
  unsigned preview that does not self-update, and it asks for screen-recording, microphone and
  accessibility permissions.

## Facts, checked today (2026-10-21)

| fact | value | source |
|---|---|---|
| repository | `kitlangton/scrawl` | own capture |
| stars / forks | 588 / 54 | GitHub API, 2026-10-21 |
| licence | MIT | GitHub API |
| created | 2026-10-14 | GitHub API |
| latest release | v0.3.11, 2026-10-21T02:51:34Z (`Scrawl-0.3.11-arm64.dmg`, `Scrawl-0.3.11-windows-x64.zip`) | GitHub Releases API |
| platforms | Apple silicon Mac, macOS 26+; Windows 10 2004+ x64, unsigned preview, no self-update; Linux "coming soon" | project README + page |
| hotkey | ⌥⇧S starts and finishes a capture; ⇧ hold-drag draws; ⇧click drops a pin; ⌘Z undo; ⌥⇧V pastes the latest capture | page "Controls" |
| output bundle | `contact-sheet.png`, `frames/frame-XX.png`, `summary.md` (transcript + interaction timeline), `scrawl.json` | project README |
| capture rule | a frame only when something happens (draw, click, say "look"/"now", screen change); speech transcribed on the computer | page "How it works" |
| install | `brew install --cask kitlangton/tap/scrawl` · agent skill: `bunx skills add kitlangton/scrawl` | page "Install" + README |

## Licence position (once, as a trust badge, never in the hook or the title)

MIT. No paid tier is claimed anywhere in the film; it is a free, open-source app, so the licence is
one line in the end card only.

## Claim that the video is built on

> Show the agent the problem instead of describing it: one hotkey records screen, voice and marks,
> and hands the agent a contact sheet plus a transcript it can actually read.

Everything else in the film supports that claim or qualifies it.
