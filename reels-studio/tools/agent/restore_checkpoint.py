#!/usr/bin/env python3
"""Restore a digest-pinned operator archive after transient Actions artifacts expire.
Reads public project archives only; no model or social API request is made.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.agent.prepare import safe_unpack_tar
from tools.agent.openrouter_client import PilotBlocked
from tools.post.common import load_json
from tools.post.media import asset_metadata,public_download


def validate_reference(ref):
    import re
    if not ref.get('operator_archive') or not ref.get('not_a_social_publication'):
        raise PilotBlocked('Checkpoint is not an approved operator archive')
    if not isinstance(ref.get('asset_id'),int) or ref['asset_id']<=0:
        raise PilotBlocked('Invalid checkpoint asset ID')
    if not re.fullmatch(r'agent-[a-z0-9-]+\.tar\.gz',ref.get('name','')):
        raise PilotBlocked('Unexpected checkpoint archive name')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',ref.get('sha256','')):
        raise PilotBlocked('Checkpoint digest missing')
    if not 0<ref.get('size_bytes',0)<=100_000_000:
        raise PilotBlocked('Checkpoint download exceeds safety budget')
    return ref


def restore(manifest,dest):
    ref=validate_reference(load_json(manifest));dest=Path(dest)
    if dest.exists() and any(dest.iterdir()):raise PilotBlocked('Refusing to mix a checkpoint with existing work')
    repo=load_json(ROOT/'config/publishing.json');meta=asset_metadata(repo,ref['asset_id'])
    if meta['name']!=ref['name'] or meta['size']!=ref['size_bytes']:
        raise PilotBlocked('Archived checkpoint identity changed')
    with tempfile.TemporaryDirectory(prefix='hypeless-checkpoint-') as temp:
        file=Path(temp)/'checkpoint.tar.gz'
        public_download(meta['browser_download_url'],ref['size_bytes'],ref['sha256'],file)
        safe_unpack_tar(file,dest,'free-p5-checkpoint',max_bytes=160_000_000)
    if not (dest/'inference/calls.json').is_file() or not (dest/'authoring-report.json').is_file():
        raise PilotBlocked('Checkpoint lacks required journal/evidence')
    return {'restored':True,'source_run':ref['source_run'],'asset_id':ref['asset_id'],'sha256':ref['sha256'],'inference_replayed':False,'publishing_performed':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dest',required=True)
    a=ap.parse_args()
    # Fixed registered archive; neither a model nor workflow input can choose an arbitrary URL.
    print(json.dumps(restore(ROOT/'research/pilots/free-p5/full-checkpoint-archive.json',a.dest),indent=2))


if __name__=='__main__':main()
