#!/usr/bin/env python3
"""Bounded retrieval over repo docs/state: top snippets, capped bytes — never a full dump.

Instead of opening `tracker/publications.json` (18 KB) to answer one question:
    python3 tools/context/ctxgrep.py "news-claude-free-01 youtube"
prints ranked hits (`file:line` + the matching line, trimmed) and stops at
--max-bytes. Exit code 0 if anything matched, 1 if nothing did.

Search scope defaults to markdown + JSON under the operational dirs; large or
binary files are skipped and counted, never read whole into output.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {'.git', '.context', 'captures', 'renders', '__pycache__', 'node_modules', 'raw', 'batches'}
TEXT_EXT = {'.md', '.json', '.txt', '.yml', '.yaml', '.log'}
MAX_FILE_BYTES = 262144
SNIPPET_CHARS = 220


def _iter_files(root, exts, subdir=None):
    base = root / subdir if subdir else root
    candidates = [base] if base.is_file() else sorted(base.rglob('*'))
    for p in candidates:
        if p.is_dir():
            continue
        try:
            rel = p.relative_to(base if base.is_dir() else base.parent)
        except ValueError:
            rel = p
        if subdir is None and any(part in SKIP_DIRS for part in rel.parts):
            continue
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if exts and p.suffix.lower() not in exts:
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                yield p, 'too-large'
                continue
        except OSError:
            continue
        yield p, None


def search(root, query, top=6, max_bytes=2560, subdir=None, exts=None):
    """Return (hits, skipped_large, total_scanned). hits sorted by relevance."""
    root = Path(root)
    terms = [t for t in re.split(r'\s+', query.strip().lower()) if t]
    if not terms:
        return [], 0, 0
    exts = set(exts) if exts else TEXT_EXT
    hits, skipped, scanned = [], 0, 0
    for p, why in _iter_files(root, exts, subdir):
        if why == 'too-large':
            skipped += 1
            continue
        scanned += 1
        try:
            lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
        except OSError:
            continue
        matched_terms, count, best = set(), 0, []
        for i, line in enumerate(lines, 1):
            low = line.lower()
            for t in terms:
                if t in low:
                    count += low.count(t)
                    matched_terms.add(t)
                    if len(best) < 3:
                        best.append((i, line.strip()[:SNIPPET_CHARS]))
        if not matched_terms:
            continue
        name_bonus = 1.5 * sum(1 for t in terms if t in p.name.lower())
        score = count + 10 * (len(matched_terms) / len(terms)) + name_bonus
        hits.append({'file': str(p.relative_to(root)), 'score': round(score, 2),
                     'terms_matched': f"{len(matched_terms)}/{len(terms)}", 'hits': count,
                     'snippets': [{'line': i, 'text': t} for i, t in best]})
    hits.sort(key=lambda h: -h['score'])
    return hits[:top], skipped, scanned


def render(hits, skipped, scanned, max_bytes):
    out, used = [], 0
    for n, h in enumerate(hits, 1):
        block = [f"{n}. {h['file']}  (terms {h['terms_matched']}, {h['hits']} hits)"]
        for s in h['snippets']:
            block.append(f"   L{s['line']}: {s['text']}")
        text = '\n'.join(block)
        if used + len(text.encode()) + 140 > max_bytes:
            out.append(f"... output capped at {max_bytes} bytes ({len(hits) - n + 1} more hit(s) withheld; raise --max-bytes)")
            break
        out.append(text)
        used += len(text.encode())
    if not hits:
        out.append(f'no hits ({scanned} file(s) scanned, {skipped} large file(s) skipped)')
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('query', help='space-separated terms; ALL terms are tracked, any term may match')
    ap.add_argument('--top', type=int, default=6, help='max files in output (default 6)')
    ap.add_argument('--max-bytes', type=int, default=2560, help='output cap (default 2560)')
    ap.add_argument('--path', default=None, help='limit to a subdirectory, e.g. tracker or .context/logs')
    ap.add_argument('--ext', action='append', default=None, help='limit extensions, e.g. --ext .json')
    ap.add_argument('--json', action='store_true', help='machine-readable output')
    a = ap.parse_args()
    sub = a.path if a.path and (ROOT / str(a.path)).exists() else None
    hits, skipped, scanned = search(ROOT, a.query, top=a.top, max_bytes=a.max_bytes, subdir=sub, exts=a.ext)
    if a.json:
        print(json.dumps({'query': a.query, 'scanned': scanned, 'skipped_large': skipped, 'hits': hits}, indent=2))
    else:
        print(render(hits, skipped, scanned, a.max_bytes))
    sys.exit(0 if hits else 1)


if __name__ == '__main__':
    main()
