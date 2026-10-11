# Context protocol — keep the session small, keep the work resumable

> **Why this file exists.** On 2026-10-10 a Hypeless work session ended with
> *"The conversation is too long for the model."* Nothing was lost — the repo is the
> memory — but re-entry was expensive: catching a fresh session up by reading the doc
> set + state files costs **~153 KB ≈ 43,700 tokens** (measured 2026-10-11). That cost
> compounds every time a session restarts, and it is what eventually overflows the
> chat. This protocol cuts the fixed re-entry cost by **~97%** and bounds everything
> a session emits afterwards.

## Rule 0 — think in code

Never pull raw data into the conversation to reason over it. Write a small script that
reads, filters, counts and prints only the answer. One script replaces ten tool calls.
Every audit, measurement and verification in
`docs/2026-10-11-session-resume-audit.md` was produced this way — no 1,300-line file
was ever pasted into the chat.

## The three tools (`tools/context/`)

| Tool | What it does | Bound |
|---|---|---|
| `ctxpack.py` | Builds `.context/PACK.md`: one always-fresh handoff page generated from `tools/maintenance/resume_status.py` (single state source, cannot drift) | 8 KiB default (~2.2k tokens); real pack today: 3.8 KiB |
| `ctxgrep.py` | Answers questions from docs/state/logs as ranked `file:line` snippets | 2.5 KiB default per query |
| `quiet.py` | Runs any command; full output goes to `.context/logs/`, the transcript gets exit code + duration + bounded tail | 12 tail lines default |

### Session start — the four lines that replace a re-read

```bash
cd ~/yt-tts/reels-studio
python3 tools/context/ctxpack.py --write   # regenerate (cheap, always fresh)
cat .context/PACK.md                       # read THIS, not the doc set
python3 tools/context/ctxpack.py --check   # FRESH, or STALE + reasons (exit 1)
```

Then work from the pack's *Reading index*. Open a file in full **only** when:

1. you are about to **edit** it (reading-to-edit is correct);
2. the pack marks it `always`/required for the task at hand, or it is < 4 KB;
3. `ctxgrep.py` proved the file is genuinely the right source and its remaining
   section is the answer.

`tracker/*.json` and `queue/*.json` are **retrieval-only** — never open them whole.
They are receipts: query them (`ctxgrep.py "news-claude-free-01"`) and let the snippet
answer. The same goes for any file over ~10 KB.

### Retrieval instead of reading

```bash
python3 tools/context/ctxgrep.py "youtube refresh grant expiry"     # ~0.5 KB answer
python3 tools/context/ctxgrep.py "held" --path queue/publish.json   # 17.7 KB file → snippet
python3 tools/context/ctxgrep.py "<term>" --path .context/logs      # into bounded logs
```

### Command output, bounded

```bash
python3 tools/context/quiet.py -- python3 -m pytest tests -v
# exit=0 · output=21564B → transcript gets 4 tail lines + log path
# full result stays greppable: ctxgrep.py "FAILED" --path .context/logs
```

Exit codes are propagated (124 on timeout), so agents can still branch on results.

### Write-back — the repo is the memory, not the transcript

At every phase boundary (and before starting a new chat): save receipts/state to
`git` (journals, `research/maintenance/*.json`), then `ctxpack.py --write`. A new
chat then restarts from 3.8 KB instead of 43k tokens. This is not theory: the
2026-10-11 resumed session reconstructed its entire operational state from git + one
pack in a single turn — exactly because the previous session had written state down.

## How this relates to `mksglu/context-mode`

[context-mode](https://github.com/mksglu/context-mode) is an MCP server + hooks that
does this for hook-capable coding clients (Claude Code, Cursor, VS Code, Copilot, …).
Its four mechanisms and the equivalents in force here:

| context-mode mechanism | Their implementation | Here (Arena) | Notes |
|---|---|---|---|
| Sandboxed tool output (~98% reduction) | `ctx_execute`, `ctx_batch_execute`, MCP interception | `quiet.py` + Rule 0 | Same effect, enforced by protocol instead of hooks |
| Persistent searchable session memory | SQLite + FTS5, BM25 `ctx_search` | git journals/receipts + `ctxgrep.py` scoring | The repo already *was* the memory; grep makes it cheap |
| Routing enforcement | PreToolUse/PostToolUse/SessionStart hooks; routing block in `AGENTS.md`/rules files | this document, referenced from `RESUME.md`/`README.md`; `ctxpack.py --check` as the tripwire | Arena exposes no hooks or MCP — enforcement is convention + a checkable freshness exit code |
| Think in code | mandated on 17 platforms | Rule 0 above | Identical discipline |

**Boundaries, stated honestly:**

- Arena cannot install MCP servers or hooks, so the real context-mode plugin cannot
  run *inside this chat*. If you use Claude Code / Cursor / VS Code / Copilot on this
  repo locally, install it per its README — that gets you enforced routing, FTS5
  memory and `ctx stats` for those clients, on top of this repo's tooling.
- This protocol deliberately does **not** enforce brevity/prose style. Per
  context-mode's own README, aggressive brevity degrades reasoning; what matters is
  *where data goes*, not how the model talks.
- No blocking layer exists here (unlike their hook interception). The guardrail is
  `ctxpack.py --check` (exit 1 + reasons when the pack no longer matches HEAD/state)
  and the rule that oversized reads are not how answers are produced.

## Measured effect (2026-10-11)

| Path | Without | With | Reduction |
|---|---|---|---|
| Session re-entry (docs + state) | 153.5 KB ≈ 43.7k tokens | 3.8 KB ≈ 1.1k tokens | **97.5%** |
| One receipt question (`news-claude-free-01`) | open 17.7 KB `publications.json` | ~0.7 KB ranked snippets | ~96% |
| Verbose test suite | 21.6 KB transcript | 0.6 KB summary + greppable log | ~97% |

## Maintenance

- `.context/` is git-ignored and regenerable: pack at will; logs auto-prune to the
  newest 200. Verify tooling with `python3 -m pytest tests/test_context.py -q`.
- If the pack reports STALE: regenerate (`--write`). If it reports OVER-BUDGET:
  trim this doc's index in `ctxpack.py` (`ENTRY_DOCS`).
- Nothing in this protocol changes publishing, rendering, credentials or the owner
  pause — it only changes what enters the conversation window.
