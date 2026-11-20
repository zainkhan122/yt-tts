"""User-approved replacement covers, independent of immutable render kits."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def effective_item(item):
    manifest = ROOT / 'approved-thumbnails' / 'manifest.json'
    if not manifest.exists():
        return item
    entry = json.loads(manifest.read_text()).get(item['video_id'])
    if not entry:
        return item
    expected = item['video_id'] + '.png'
    if entry.get('file') != expected:
        raise ValueError('Invalid approved cover filename')
    return {**item, 'cover_sha256': entry['sha256'],
            'cover_reviewed_at': entry.get('reviewed_at', 'user-approved'),
            'preserve_existing_custom': entry.get('preserve_existing_custom', False),
            'manual_cover_eligible': entry.get('manual_cover_eligible', False),
            'approved_replacement_file': expected}
