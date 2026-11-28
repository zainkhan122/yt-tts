"""Fail-closed compatibility assessment; no claim that an adapter exists."""
from pathlib import Path
from .assets import AssetError,inspect_media
from .blueprint import digest

class CompatibilityError(ValueError):pass

def to_render_instructions(execution,records,*,renderer):
    """Resolve assets and validate against explicit renderer contract.

    `renderer` declares formats, operations, animation types, transitions and
    camera instructions implemented by the actual renderer adapter. This does
    not itself implement or invoke any compositor.
    """
    required={'formats','operations','animation_types','transitions','camera'}
    if set(renderer)!=required:raise CompatibilityError('Incomplete renderer capability contract')
    by_key={(r['beat_id'],r['event_id'],r['asset_id']):r for r in records};out=[]
    for j in execution['jobs']:
        label=j['beat_id']+'/'+j['event_id'];r=by_key.get((j['beat_id'],j['event_id'],j['asset_id']))
        if not r:raise CompatibilityError(label+': asset missing')
        if r.get('operation')!=j['operation'] or r.get('provider')!=j['provider'] or r.get('model')!=j['model'] or r.get('generation_status') not in {'complete','reused'}:raise CompatibilityError(label+': asset provenance does not match execution')
        fmt={'image/png':'png','image/jpeg':'jpg','video/mp4':'mp4'}.get(r['media_type'])
        if fmt not in renderer['formats'] or j['operation'] not in renderer['operations'] or j['animation_type'] not in renderer['animation_types'] or j['transition'] not in renderer['transitions'] or j['camera'] not in renderer['camera']:raise CompatibilityError(label+': renderer does not implement requested media/effect')
        path=Path(r['file_path'])
        try:
            if digest(path)!=r['content_hash']:raise AssetError('Asset digest changed')
            inspect_media(path,fmt,j['width'],j['height'],j['duration'] if fmt=='mp4' else None)
        except (OSError,AssetError) as e:raise CompatibilityError(label+': '+str(e)) from e
        out.append({'beat_id':j['beat_id'],'event_id':j['event_id'],'asset_id':j['asset_id'],'file_path':str(path),'content_hash':r['content_hash'],'start':j['start'],'duration':j['duration'],'animation_type':j['animation_type'],'camera':j['camera'],'transition':j['transition']})
    return out

# Existing prototype takes hard-coded shapes, not asset clips or general semantic actions.
LEGACY_RENDERER={'formats':set(),'operations':set(),'animation_types':set(),'transitions':set(),'camera':set()}
