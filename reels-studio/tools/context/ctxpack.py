#!/usr/bin/env python3
"""Build the session context pack: one small, always-fresh handoff artifact.

Read `.context/PACK.md` (default budget 8 KiB) at session start instead of the
whole doc set. The pack reuses `tools/maintenance/resume_status.py` as the single
state source, so it cannot drift from the operational snapshot.

Modes:
  (default)  print the pack to stdout
  --write    write .context/PACK.md + .context/pack.json (machine manifest)
  --check    verify freshness/budget of an existing pack; non-zero if stale
  --json     print the manifest instead of markdown
  --full     do not trim sections to the budget (still prints a size note)
"""
import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.maintenance.resume_status import snapshot  # noqa: E402

PACK_DIR = Path('.context')
PACK_MD = PACK_DIR / 'PACK.md'
PACK_JSON = PACK_DIR / 'pack.json'
DEFAULT_BUDGET = 8192
MAX_FULL_BUDGET = 32768
CHARS_PER_TOKEN = 3.6
MAX_AGE_HOURS = 24

# artifact -> (read policy, guidance). Policy: always | on-demand | retrieval-only | regenerated
ENTRY_DOCS = [
    ['.context/PACK.md', 'always', 'this file'],
    ['RESUME.md', 'on-demand', 'authority + guardrails; the pack embeds the non-negotiables'],
    ['CURRENT_STATE.md', 'regenerated', 'regenerate with resume_status.py --write; the pack is newer'],
    ['README.md', 'on-demand', 'project overview'],
    ['PLAYBOOK.md', 'on-demand', 'strategy questions only'],
    ['PIPELINE.md', 'on-demand', 'end-to-end mechanics'],
    ['PHASES.md', 'on-demand', 'phase history'],
    ['research/pilots/PILOT_REPORT.md', 'on-demand', 'only if pilot history is investigated'],
    ['research/pilots/STATUS.md', 'on-demand', 'optional-agent state'],
    ['agent/ACCEPTANCE.md', 'on-demand', 'before any pilot/qualification work'],
    ['docs/SECURITY-BOUNDARIES.md', 'on-demand', 'before credential-touching work'],
    ['tracker/publications.json', 'retrieval-only', 'never open in full; use ctxgrep.py'],
    ['queue/publish.json', 'retrieval-only', 'queue_ctl.py / ctxgrep.py'],
    ['config/publishing.json', 'retrieval-only', 'ctxgrep.py for keys'],
    ['config/agent-pilot.json', 'retrieval-only', 'lifecycle_status via ctxgrep.py'],
]
STATE_SOURCES = [
    'config/publishing.json', 'config/youtube.json', 'config/agent-pilot.json',
    'config/operating-policy.json', 'queue/publish.json', 'queue/youtube-long.json',
    'tracker/publications.json', 'tracker/youtube-publications.json',
    'tracker/system-status.json', 'research/pilots/STATUS.md',
]


def _head(root):
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return 'unknown'


def _dirty_count(root):
    try:
        out = subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True, stderr=subprocess.DEVNULL)
        return len([l for l in out.splitlines() if l.strip()])
    except Exception:
        return -1


def _sha(root, rel):
    p = root / rel
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else None


def _kb(n):
    return f"{n / 1024:.1f}K"


def _tok(n):
    return int(n / CHARS_PER_TOKEN)


def _days_left(iso):
    try:
        end = dt.datetime.fromisoformat(iso.replace('Z', '+00:00'))
        return (end - dt.datetime.now(dt.timezone.utc)).days
    except Exception:
        return None


def _state_row(info):
    b, y, a = info['buffer'], info['youtube'], info['optional_agent']
    q = b['queue_approvals']
    return {
        'buffer': f"enabled={b['enabled']} pilot={b['pilot_passed']} {b['daily_target']}/day {b['timezone']}",
        'queue': f"approved={q.get('approved', 0)} held={q.get('held', 0)}",
        'receipts': str(b['platform_receipt_states']),
        'youtube': f"enabled={y['enabled']} metadata_done={y['metadata_completed']} long_pilot={y['long_pilot_passed']} long_queued={y['long_queue_count']}",
        'optional_agent': f"{a['qualification']} / {a.get('lifecycle_status')} (production={a['production_enabled']})",
    }


def _grant_expiry(root, info):
    iso = info['youtube'].get('recorded_refresh_grant_expiry_utc')
    source = 'live-vault'
    if not iso:
        p = root / 'tracker/system-status.json'
        if p.exists():
            try:
                iso = json.loads(p.read_text())['youtube'].get('recorded_refresh_grant_expiry_utc')
                source = 'tracker/system-status.json (recorded)'
            except Exception:
                iso = None
    return iso, source


def build_pack(root, state=None, budget=DEFAULT_BUDGET, full=False):
    """Return (markdown, manifest). Pure/side-effect-free apart from reading files."""
    root = Path(root)
    info = state if state is not None else snapshot()
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    head = _head(root)
    dirty = _dirty_count(root)

    doc_rows = []
    for rel, policy, guidance in ENTRY_DOCS:
        p = root / rel
        size = p.stat().st_size if p.exists() else None
        doc_rows.append({'path': rel, 'bytes': size, 'tokens': _tok(size) if size else None,
                         'policy': policy, 'guidance': guidance})
    doc_rows.sort(key=lambda r: -(r['bytes'] or 0))
    readable = [r for r in doc_rows if r['bytes'] and r['policy'] in ('on-demand', 'always', 'regenerated')]
    total_doc_bytes = sum(r['bytes'] or 0 for r in readable)
    state_bytes = sum((root / r).stat().st_size for r in STATE_SOURCES if (root / r).exists())

    expiry, expiry_src = _grant_expiry(root, info)
    days = _days_left(expiry) if expiry else None

    sections = []
    sections.append(('header', '\n'.join([
        '# Session context pack',
        f"Generated {now} · commit `{head[:12]}` · tree_dirty={dirty if dirty >= 0 else 'unknown'}",
        f"Budget {_kb(budget)} · this pack replaces reading {_kb(total_doc_bytes)} of docs + {_kb(state_bytes)} of state (~{_tok(total_doc_bytes + state_bytes)} tokens naive).",
        'Protocol: CONTEXT-PROTOCOL.md · deeper answers: `python3 tools/context/ctxgrep.py "<query>"`',
    ])))

    guard = ['## Guardrails (owner decisions in force)',
             f"- Optional producer/critic: **{info['optional_agent'].get('lifecycle_status')}**, {info['optional_agent']['qualification']}; do not restart or activate without a new explicit owner request.",
             '- Interactive Arena agent leads research, scripts, assets, editing and QA.',
             '- Never re-upload a video that has a platform receipt/reservation; receipts are journal state, not fresh provider verification.',
             '- Never echo or commit credentials; expect local OpenRouter key to be absent (Actions secret only).',
             '- Model self-scores are not qualification; scheduled is not sent; OAuth configured is not verified.']
    sections.append(('guardrails', '\n'.join(guard)))

    st = _state_row(info)
    sections.append(('state', '\n'.join([
        '## System state (recorded journals)',
        '| System | State |', '|---|---|',
        f"| Buffer delivery | {st['buffer']} |",
        f"| Queue | {st['queue']} |",
        f"| Receipts | {st['receipts']} |",
        f"| YouTube | {st['youtube']} |",
        f"| Optional agent | {st['optional_agent']} |",
    ])))

    watch = ['## Watch items']
    if expiry:
        watch.append(f"- Google refresh grant recorded expiry **{expiry}** ({expiry_src}); {days} days left — owner must re-check Audience publishing status before any YouTube write." if days is not None else f"- Google refresh grant recorded expiry **{expiry}**.")
    else:
        watch.append('- Google refresh grant expiry not recorded here (vault/tracker absent in this workspace); check tracker/system-status.json in the main workspace.')
    watch.append('- Five Oct-10 videos held in queue by design; publish as the next batch, no same-day dump.')
    watch.append('- Long-form upload pilot has not passed; nothing in queue/youtube-long.json.')
    sections.append(('watch', '\n'.join(watch)))

    budget_lines = ['## Reading index (open only what you need)',
                    f"`PACK.md` is the entry point. Naive read of the listed docs+state = {_kb(total_doc_bytes + state_bytes)} (~{_tok(total_doc_bytes + state_bytes)} tokens); most answers live in the rows below.",
                    '| Artifact | Size | Policy | Retrieval hint |', '|---|---|---|---|']
    for r in doc_rows:
        if r['bytes'] is None:
            continue
        budget_lines.append(f"| `{r['path']}` | {_kb(r['bytes'])} | {r['policy']} | {r['guidance']} |")
    budget_lines.append('| `tracker/*`, `queue/*` | ' + _kb(state_bytes) + ' | retrieval-only | `ctxgrep.py "<term>"` |')
    actions = ['## Next safe actions',
               '1. Regenerate this pack at session start: `python3 tools/context/ctxpack.py --write`.',
               f"2. Leave the optional agent paused; latest recorded decision is in `config/operating-policy.json` ({info['operating_policy'].get('decided_on', 'n/a')}).",
               '3. Before any provider write: `python3 tools/maintenance/resume_status.py` and `ctxgrep.py` the relevant tracker/queue receipts first.',
               '4. Run long commands through `tools/context/quiet.py`; keep full output in `.context/logs/`.']
    sections.append(('actions', '\n'.join(actions)))
    sections.append(('reading-index', '\n'.join(budget_lines)))

    receipts = sorted((root / 'research/maintenance').glob('*.json')) if (root / 'research/maintenance').exists() else []
    tail = ['## Latest maintenance receipts']
    tail += [f"- `{p.relative_to(root)}`" for p in receipts[-5:]] or ['- none found']
    sections.append(('receipts', '\n'.join(tail)))

    marker = f"_pack_v1_{now}_{head[:12]}_"
    kept, truncated = [], False
    limit = MAX_FULL_BUDGET if full else budget
    for name, text in sections:
        candidate = '\n\n'.join([t for _, t in kept] + [text])
        if not full and len(candidate.encode()) + 96 > limit:
            truncated = True
            continue
        kept.append((name, text))
    body = '\n\n'.join(t for _, t in kept)
    note = f"\n\n_[pack trimmed to budget {_kb(limit)}: {len(sections) - len(kept)} section(s) omitted; run with --full or use ctxgrep.py]_" if truncated else ''
    md = f'<!-- {marker} -->\n' + body + note + '\n'

    manifest = {
        'schema_version': 1, 'marker': marker, 'generated_at': now, 'source_commit': head, 'tree_dirty': dirty,
        'budget_bytes': limit, 'pack_bytes': len(md.encode()), 'pack_tokens_est': _tok(len(md.encode())),
        'naive_docs_bytes': total_doc_bytes, 'naive_state_bytes': state_bytes,
        'naive_tokens_est': _tok(total_doc_bytes + state_bytes),
        'truncated': truncated, 'sections': [n for n, _ in kept],
        'entry_docs': [{'path': r['path'], 'bytes': r['bytes'], 'policy': r['policy']} for r in doc_rows if r['bytes']],
        'doc_hashes': {r: _sha(root, r) for r in STATE_SOURCES if _sha(root, r)},
    }
    return md, manifest


def check_pack(root, state=None, budget=DEFAULT_BUDGET):
    """Return (ok, [problems]). Fresh = same commit, same state hashes, within age and budget."""
    root = Path(root)
    p = root / PACK_JSON
    if not p.exists():
        return False, ['no pack found; run: python3 tools/context/ctxpack.py --write']
    try:
        saved = json.loads(p.read_text())
    except Exception as e:
        return False, [f'pack manifest unreadable: {e}']
    problems = []
    head = _head(root)
    if saved.get('source_commit') != head:
        problems.append(f"stale commit: pack {str(saved.get('source_commit'))[:12]} != HEAD {head[:12]}")
    changed = [r for r, h in saved.get('doc_hashes', {}).items() if _sha(root, r) != h]
    if changed:
        problems.append('state changed since pack: ' + ', '.join(changed[:6]))
    try:
        age_h = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(saved['generated_at'])).total_seconds() / 3600
        if age_h > MAX_AGE_HOURS:
            problems.append(f'pack is {age_h:.1f}h old (limit {MAX_AGE_HOURS}h)')
    except Exception:
        problems.append('pack has no readable timestamp')
    if saved.get('pack_bytes', 0) > budget:
        problems.append(f"pack {saved.get('pack_bytes')}B exceeds budget {budget}B")
    return (not problems), problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--write', action='store_true', help='write .context/PACK.md and .context/pack.json')
    ap.add_argument('--check', action='store_true', help='verify the existing pack is fresh and within budget')
    ap.add_argument('--json', action='store_true', help='print the machine manifest instead of markdown')
    ap.add_argument('--full', action='store_true', help='do not trim sections to the budget')
    ap.add_argument('--budget', type=int, default=DEFAULT_BUDGET, help=f'markdown budget in bytes (default {DEFAULT_BUDGET})')
    a = ap.parse_args()
    root = ROOT
    if a.check:
        ok, problems = check_pack(root, budget=a.budget)
        print('FRESH' if ok else 'STALE')
        for x in problems:
            print('- ' + x)
        sys.exit(0 if ok else 1)
    md, manifest = build_pack(root, budget=a.budget, full=a.full)
    if a.write:
        (root / PACK_DIR).mkdir(parents=True, exist_ok=True)
        (root / PACK_MD).write_text(md)
        (root / PACK_JSON).write_text(json.dumps(manifest, indent=2) + '\n')
        print(f"wrote {PACK_MD} ({manifest['pack_bytes']}B, ~{manifest['pack_tokens_est']} tokens; naive baseline ~{manifest['naive_tokens_est']} tokens)")
    if a.json:
        print(json.dumps(manifest, indent=2))
    elif not a.write:
        print(md, end='')


if __name__ == '__main__':
    main()
