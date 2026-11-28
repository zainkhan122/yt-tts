"""Translate scheduled semantic events into explicit provider jobs, not pixels.

Selection uses declared capabilities only; callers must configure policy. A
fallback is never implicit and never converts object movement into a still.
"""
from __future__ import annotations
import math

class ExecutionError(ValueError):pass

OPERATIONS={'image','video','image_to_video','programmatic_motion','composite'}
MOTION={'video','image_to_video','programmatic_motion','composite'}

def build_execution(blueprint,registry,policy,*,width,height,allow_deviation=False):
    if not isinstance(blueprint,dict) or not isinstance(blueprint.get('beats'),list) or not blueprint['beats']:raise ExecutionError('Scheduled beats required')
    if type(width)!=int or type(height)!=int or width<1 or height<1:raise ExecutionError('Invalid dimensions')
    result=[]; known_assets={}; seen_events=set()
    for beat in blueprint['beats']:
        try:
            bid=beat['id']; treatment=beat['treatment']; start=beat['start'];end=beat['end'];assets={a['id']:a for a in beat['assets']}
            if not isinstance(bid,str) or not bid or not isinstance(start,(float,int)) or not isinstance(end,(float,int)) or not math.isfinite(start) or not math.isfinite(end) or not start<end:raise ValueError('invalid beat')
            for event in beat['events']:
                eid=event['id'];aid=event['asset_id'];at=event['audio_time']; dur=event['duration']
                if eid in seen_events or aid not in assets or not isinstance(at,(float,int)) or not isinstance(dur,(float,int)) or not math.isfinite(at) or not math.isfinite(dur) or dur<=0 or at<start or at+dur>end+1e-9:raise ValueError('invalid event timing, id or asset')
                seen_events.add(eid);spec=assets[aid];reference=spec.get('reuse_of')
                if reference and reference not in known_assets:raise ValueError('asset reuse target not previously planned')
                choices=policy.get(treatment,[]);chosen=None;reasons=[]
                for option in choices:
                    operation=option['operation']; name=option['provider'];alternative=bool(option.get('deviation'))
                    if operation not in OPERATIONS:reasons.append(name+': unknown operation');continue
                    if alternative and not allow_deviation:reasons.append(name+': deviation requires approval');continue
                    try:p=registry.get(name,operation)
                    except ValueError as exc:reasons.append(str(exc));continue
                    cap=p.capabilities
                    if treatment not in cap.treatments and not alternative:reasons.append(name+': unsupported treatment');continue
                    if event['camera'] not in cap.camera_motion:reasons.append(name+': unsupported camera instruction');continue
                    if operation=='image_to_video' and not cap.image_to_video:reasons.append(name+': image-to-video not supported');continue
                    if width>cap.max_width or height>cap.max_height or (operation in MOTION and (cap.max_duration is None or dur>cap.max_duration)):reasons.append(name+': media limits');continue
                    if reference and not cap.reference_images:reasons.append(name+': cannot use reference');continue
                    # Non-still requested animation can never be silently reduced to a moving still.
                    needs_object=event['animation_type'] not in {'still','camera_only'}
                    if needs_object and (operation not in MOTION or not cap.object_motion):reasons.append(name+': no object animation');continue
                    chosen=(p,operation,option);break
                if chosen is None:raise ExecutionError(f'{bid}/{eid}: no supported executable strategy; '+ '; '.join(reasons))
                p,op,opt=chosen
                result.append({'beat_id':bid,'event_id':eid,'asset_id':aid,'provider':p.capabilities.identity,'model':p.capabilities.model,'operation':op,'treatment':treatment,'subject':beat['subject'],'objects':beat['objects'],'description':spec['description'],'action':event['action'],'animation_type':event['animation_type'],'camera':event['camera'],'transition':event['transition'],'start':at,'duration':dur,'width':width,'height':height,'reference_asset':reference,'deviation':opt.get('deviation') or None})
                known_assets[aid]=True
        except ExecutionError:raise
        except (KeyError,TypeError,ValueError) as exc:raise ExecutionError(f'{beat.get("id","unknown")}: malformed scheduled event: {exc}') from exc
    return {'schema':1,'audio_sha256':blueprint.get('audio_sha256'),'jobs':result}
