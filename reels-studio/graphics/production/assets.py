"""Single-host asset orchestration; provider adapters write to a supplied path.

No external provider is registered here. Only explicitly retryable adapter errors
are retried; uncertain remote submissions must not be repeated automatically.
"""
from __future__ import annotations
import fcntl, hashlib, json, os, re, subprocess, tempfile, time
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from graphics.media import ffmpeg_exe,clip_duration
from .blueprint import digest

class AssetError(RuntimeError):pass
class RetryableAssetError(AssetError):pass

_FORMATS={'png':('image/png','PNG'), 'jpg':('image/jpeg','JPEG'), 'mp4':('video/mp4',None)}

def inspect_media(path,fmt,width,height,duration=None,max_bytes=100_000_000):
    p=Path(path)
    if fmt not in _FORMATS or not p.is_file() or p.is_symlink() or not 0<p.stat().st_size<=max_bytes:raise AssetError('Missing, oversized or unsupported asset')
    if fmt in {'png','jpg'}:
        try:
            with Image.open(p) as im:
                if im.format!=_FORMATS[fmt][1] or im.size!=(width,height):raise AssetError('Image format or dimensions mismatch')
                im.verify()
        except (OSError,UnidentifiedImageError,Image.DecompressionBombError) as e:raise AssetError('Invalid image') from e
        return {'media_type':_FORMATS[fmt][0], 'width':width,'height':height,'duration':None}
    # Decode entire video for integrity; FFmpeg output is discarded, not loaded into RAM.
    try:
        probe=subprocess.run([ffmpeg_exe(),'-hide_banner','-i',str(p)],capture_output=True,text=True,timeout=30)
        stream=re.search(r'Stream #.*Video:.*?\b(\d{2,5})x(\d{2,5})\b',probe.stderr)
        d=clip_duration(p)
        if not stream or (int(stream[1]),int(stream[2]))!=(width,height) or d<=0 or duration is None or abs(d-duration)>.15:raise AssetError('Video metadata mismatch')
        checked=subprocess.run([ffmpeg_exe(),'-v','error','-xerror','-i',str(p),'-map','0:v:0','-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=120)
        if checked.returncode:raise AssetError('Video failed full decode')
    except subprocess.TimeoutExpired as e:raise AssetError('Video validation timed out') from e
    return {'media_type':'video/mp4','width':width,'height':height,'duration':d}

def _hash_obj(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

class AssetStore:
    def __init__(self,root,registry,*,max_bytes=100_000_000,retries=1):
        if type(retries)!=int or not 0<=retries<=3:raise ValueError('Retry limit must be 0..3')
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True);self.registry=registry;self.max_bytes=max_bytes;self.retries=retries
    def reuse(self,job,record):
        if job.get('reference_asset')!=record.get('asset_id'):raise AssetError('Reuse target mismatch')
        path=Path(record['file_path'])
        if not path.is_file() or digest(path)!=record['content_hash']:raise AssetError('Reuse asset missing or changed')
        fmt={'image/png':'png','image/jpeg':'jpg','video/mp4':'mp4'}.get(record['media_type'])
        inspect_media(path,fmt,job['width'],job['height'],job['duration'] if fmt=='mp4' else None,self.max_bytes)
        return {**record,'asset_id':job['asset_id'],'beat_id':job['beat_id'],'event_id':job['event_id'],'generation_status':'reused','reused_from':record['asset_id']}
    def generate(self,job,*,prompt,fmt,reference_records=(),continuity=None,force=False):
        try:p=self.registry.get(job['provider'],job['operation'])
        except (KeyError,ValueError) as e:raise AssetError(str(e)) from e
        cap=p.capabilities
        if job['model']!=cap.model or fmt not in cap.output_formats or fmt not in _FORMATS:raise AssetError('Provider model/format mismatch')
        if job['operation'] in {'video','image_to_video','programmatic_motion','composite'} and fmt!='mp4':raise AssetError('Motion assets must be actual video, not still images')
        if job['operation']=='image' and fmt not in {'png','jpg'}:raise AssetError('Image operation requires an image format')
        if job['width']>cap.max_width or job['height']>cap.max_height:raise AssetError('Provider dimension limit')
        if job['operation'] in {'video','image_to_video','programmatic_motion','composite'} and (cap.max_duration is None or job['duration']>cap.max_duration):raise AssetError('Provider duration limit')
        refs=[]
        for ref in reference_records:
            if not cap.reference_images:raise AssetError('Provider does not support reference images')
            path=Path(ref['file_path']).resolve()
            if not path.is_file() or digest(path)!=ref['content_hash']:raise AssetError('Reference asset missing or changed')
            if ref['media_type'] not in {'image/png','image/jpeg'}:raise AssetError('Reference must be an image')
            ref_fmt='png' if ref['media_type']=='image/png' else 'jpg'
            inspect_media(path,ref_fmt,ref['width'],ref['height'],max_bytes=self.max_bytes)
            if ref_fmt not in cap.input_formats:raise AssetError('Unsupported reference format')
            refs.append({'asset_id':ref['asset_id'],'path':str(path),'content_hash':ref['content_hash']})
        if job.get('reference_asset') and not any(r['asset_id']==job['reference_asset'] for r in refs):raise AssetError('Required reference missing')
        if not isinstance(prompt,str) or not prompt.strip():raise AssetError('Prompt required')
        request={'provider':cap.identity,'model':cap.model,'operation':job['operation'],'prompt':prompt,'format':fmt,'width':job['width'],'height':job['height'],'duration':job['duration'] if fmt=='mp4' else None,'references':refs,'continuity':continuity or {}}
        # Reference path is not semantically significant; hash is.
        key_request={**request,'references':[{'asset_id':r['asset_id'],'content_hash':r['content_hash']} for r in refs]};key=_hash_obj(key_request)
        dst=self.root/(key+'.'+fmt);meta=self.root/(key+'.json');lock=self.root/(key+'.lock')
        with lock.open('a+b') as lk:
            fcntl.flock(lk,fcntl.LOCK_EX)
            data=None
            if not force and meta.is_file() and dst.is_file():
                try:
                    data=json.loads(meta.read_text());props=inspect_media(dst,fmt,job['width'],job['height'],request['duration'],self.max_bytes)
                    if data['content_hash']!=digest(dst) or data['request_hash']!=key:data=None
                except (OSError,ValueError,KeyError,AssetError):data=None
            if data is None:
                with tempfile.TemporaryDirectory(prefix='asset-',dir=self.root) as tmp:
                    output=Path(tmp)/('generated.'+fmt)
                    for attempt in range(self.retries+1):
                        output.unlink(missing_ok=True)
                        try:
                            p.adapter.generate(request,output)
                            props=inspect_media(output,fmt,job['width'],job['height'],request['duration'],self.max_bytes)
                            break
                        except RetryableAssetError:
                            if attempt==self.retries:raise
                            time.sleep(min(.1*2**attempt,1))
                    content=digest(output);os.replace(output,dst)
                    data={'request_hash':key,'content_hash':content,'file_path':str(dst),**props}
                    m=Path(tmp)/'meta.json';m.write_text(json.dumps(data,indent=2));os.replace(m,meta)
            return {**data,'asset_id':job['asset_id'],'beat_id':job['beat_id'],'event_id':job['event_id'],'provider':cap.identity,'model':cap.model,'generation_prompt':prompt,'reference_assets':[{'asset_id':r['asset_id'],'content_hash':r['content_hash']} for r in refs],'generation_status':'complete','continuity':continuity or {},'operation':job['operation']}
