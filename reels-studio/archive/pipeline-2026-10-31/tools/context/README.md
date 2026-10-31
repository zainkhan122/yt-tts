# tools/context — bounded-context session tooling

Keeps the agent's conversation small: one compact pack instead of whole-document
reads, capped retrieval instead of file dumps, bounded command output instead of raw
logs. Read `CONTEXT-PROTOCOL.md` (repo root) for the routing rules; this file is the
tool reference. Stdlib only; no network, no credentials, no publishing capability.

## ctxpack.py — session entry point

```bash
python3 tools/context/ctxpack.py            # print the pack (markdown)
python3 tools/context/ctxpack.py --write    # write .context/PACK.md + .context/pack.json
python3 tools/context/ctxpack.py --check    # FRESH (exit 0) | STALE + reasons (exit 1)
python3 tools/context/ctxpack.py --json     # machine manifest (commit, hashes, budget)
python3 tools/context/ctxpack.py --full     # no budget trimming (still size-noted)
```

The pack is generated from `tools/maintenance/resume_status.py` — the same source as
`CURRENT_STATE.md` — so it cannot drift from recorded operational state. Freshness
means: same HEAD, unchanged `tracker/`+`queue/`+`config/` state hashes, < 24 h old,
within budget.

## ctxgrep.py — retrieval, never a dump

```bash
python3 tools/context/ctxgrep.py "gemini agent"                  # top 6 files, ≤2.56 KB
python3 tools/context/ctxgrep.py "quota" --path research/receipts.json
python3 tools/context/ctxgrep.py "FAILED" --path .context/logs --top 3
python3 tools/context/ctxgrep.py "cron" --ext .yml --json
```

Scores by matched terms (all terms tracked, any may match), repeats, and filename
bonus; prints `file:line` + trimmed snippets; stops at `--max-bytes`
(default 2560). Exit 1 when nothing matched. Files >256 KB are skipped and counted,
never read. Default scope is markdown/JSON/YAML/TXT/LOG under the repo, excluding
`.git/.context/captures/renders/raw/batches` (an explicit `--path .context/...`
reaches them deliberately).

## quiet.py — bounded command output

```bash
python3 tools/context/quiet.py -- python3 -m pytest tests -q
python3 tools/context/quiet.py --tail 20 --label deploy -- git push
python3 tools/context/quiet.py --head 5 --tail 5 --timeout 300 -- ./long_job.sh
```

Prints exit code, duration, byte count, log path and a bounded window of the merged
output; the full transcript lands in `.context/logs/<utc>-<label>.log` (auto-pruned
to the newest 200). Exit code mirrors the child (124 on timeout, 127 not found), so
CI/agents branch on it. Retrieve follow-ups with
`ctxgrep.py "<term>" --path .context/logs`.

## Tests

```bash
python3 -m pytest tests/test_context.py -q     # 13 tests: budget, freshness, caps, exit codes
```
