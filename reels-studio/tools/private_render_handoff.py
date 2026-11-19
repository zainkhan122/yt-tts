#!/usr/bin/env python3
"""Restore a temporary encrypted draft pack inside a production runner, not a public release."""
import os, subprocess, sys, tarfile, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = 'repo-moneyprinterturbo-01'

def main():
    if len(sys.argv) not in (2, 3) or sys.argv[1] != BRIEF or (len(sys.argv) == 3 and sys.argv[2] != '--verify'):
        raise SystemExit('private handoff only supports the explicitly selected draft')
    if not os.environ.get('DRAFT_HANDOFF_KEY'):
        raise SystemExit('private handoff key missing')
    encrypted = ROOT / 'research/production/private-handoff/moneyprinterturbo.tar.gz.enc'
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / 'pack.tar.gz'
        subprocess.run(['openssl','enc','-d','-aes-256-cbc','-pbkdf2','-iter','200000',
                        '-in',str(encrypted),'-out',str(archive),'-pass','env:DRAFT_HANDOFF_KEY'],check=True)
        with tarfile.open(archive, 'r:gz') as tar:
            allowed = {f'captures/{BRIEF}/manifest.json', f'captures/{BRIEF}/webui-en.jpg',
                       f'captures/{BRIEF}/webui-en-crop.jpg', f'covers/{BRIEF}/selection.json',
                       f'covers/{BRIEF}/cover-selected.jpg'}
            members=tar.getmembers()
            if {m.name for m in members} != allowed or any(not m.isfile() for m in members):
                raise SystemExit('unexpected private handoff contents')
            if len(sys.argv) == 3:
                import hashlib
                for member in members:
                    local = ROOT / member.name
                    if not local.is_file() or hashlib.sha256(tar.extractfile(member).read()).digest() != hashlib.sha256(local.read_bytes()).digest():
                        raise SystemExit('private handoff differs from local reviewed assets: ' + member.name)
            else:
                tar.extractall(ROOT,filter='data')
    print('Private handoff assets verified.' if len(sys.argv) == 3 else 'Temporary draft assets restored inside runner; receipt hashes still required.')

if __name__ == '__main__': main()
