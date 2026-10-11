#!/usr/bin/env python3
"""Run a command with bounded transcript output; keep the full log out of context.

    python3 tools/context/quiet.py -- python3 -m pytest tests -q
    python3 tools/context/quiet.py --label audit -- git log --stat -20

Prints: exit code, duration, byte counts, log path, then only --tail (or --head)
lines of merged stdout+stderr. The complete output lands in
`.context/logs/<utc>-<label>.log`; follow up with ctxgrep.py --path .context/logs.
Exit code mirrors the child (124 on timeout) so CI/agents can branch on it.
"""
import argparse
import datetime as dt
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / '.context' / 'logs'
KEEP_LOGS = 200


def _prune(max_logs=KEEP_LOGS):
    """Keep the log directory bounded; oldest transcripts are scratch, not receipts."""
    try:
        logs = sorted(LOG_DIR.glob('*.log'))
        for old in logs[:-max_logs]:
            old.unlink()
    except OSError:
        pass


def run(cmd, tail=12, head=0, timeout=900, label=None):
    """Execute cmd from ROOT. Returns (exit_code, log_path, summary_text)."""
    slug = re.sub(r'[^a-z0-9]+', '-', (label or ' '.join(cmd[:2])).lower()).strip('-')[:40] or 'cmd'
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = LOG_DIR / f'{stamp}-{slug}.log'
    started = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors='replace', timeout=timeout)
        out, code = (proc.stdout or '') + (proc.stderr or ''), proc.returncode
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b'').decode(errors='replace') if isinstance(e.stdout, bytes) else (e.stdout or '')) + \
              ((e.stderr or b'').decode(errors='replace') if isinstance(e.stderr, bytes) else (e.stderr or ''))
        code, timed_out = 124, True
    except FileNotFoundError as e:
        out, code = f'command not found: {e}', 127
    duration = time.monotonic() - started
    log.write_text(f'$ {" ".join(cmd)}\nexit={code} duration={duration:.2f}s bytes={len(out.encode())}\n\n{out}')
    _prune()
    try:
        display = log.relative_to(ROOT)
    except ValueError:
        display = log
    lines = out.splitlines()
    shown, omitted = [], 0
    if head:
        shown += lines[:head]
    remainder = lines[len(shown):]
    if tail and len(remainder) > tail:
        omitted = len(remainder) - tail
        shown.append(f'... ({omitted} lines omitted) ...')
        shown += remainder[-tail:]
    elif tail:
        shown += remainder
    elif remainder:
        omitted = len(remainder)
        shown.append(f'... ({omitted} lines omitted) ...')
    summary = [
        f"$ {' '.join(cmd)}",
        f"exit={code}{' (TIMEOUT)' if timed_out else ''} duration={duration:.2f}s output={len(out.encode())}B log={display}",
    ]
    if shown:
        summary.append('--- output (bounded) ---')
        summary += shown
        if omitted:
            summary.append(f"(full log: {display}; retrieve lines with: python3 tools/context/ctxgrep.py \"<term>\" --path .context/logs)")
    return code, log, '\n'.join(summary)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tail', type=int, default=12, help='trailing lines to show (default 12)')
    ap.add_argument('--head', type=int, default=0, help='leading lines to show in addition (default 0)')
    ap.add_argument('--timeout', type=int, default=900, help='seconds before the command is killed (default 900)')
    ap.add_argument('--label', default=None, help='log filename label')
    ap.add_argument('cmd', nargs=argparse.REMAINDER, help='command after --')
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == '--' else a.cmd
    if not cmd:
        ap.error('no command given; usage: quiet.py -- <command>')
    code, log, summary = run(cmd, tail=a.tail, head=a.head, timeout=a.timeout, label=a.label)
    print(summary)
    sys.exit(code)


if __name__ == '__main__':
    main()
