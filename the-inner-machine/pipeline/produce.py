#!/usr/bin/env python3
"""Robust config-driven producer for the animated channel.
Reads a project config (json) and emits, under output/<Title>/:
  <Title>.mp4 · <Title>.metadata.md · <Title> cover.jpg ·
  shorts/<Title> hook.mp4 + payoff.mp4 (+ .metadata.md) · state.json
Self-bootstraps deps (survives sandbox resets), idempotent (state.json),
verifies every output (dims/fps/audio/duration) and never ships on failure.
Voice: Kokoro, locked via config["voice"] (default bm_george).
Usage: python3 produce.py CONFIG [--only long|shorts|cover|meta]
"""
import subprocess, sys, os, json, math, argparse, shutil, re
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
def bootstrap():
    failed = []
    for mod, pkg in [("kokoro_onnx","kokoro-onnx"),("soundfile","soundfile"),
                     ("imageio_ffmpeg","imageio-ffmpeg"),("PIL","pillow")]:
        try:
            __import__(mod); continue
        except Exception:
            pass
        subprocess.run([sys.executable,"-m","pip","install","--quiet",pkg],capture_output=True)
        try:
            __import__(mod)
        except Exception:
            failed.append(pkg)
    if failed:
        sys.exit(f"[produce] FATAL: could not install required packages: {', '.join(failed)}")
bootstrap()
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont
import tts
FF = subprocess.check_output([sys.executable,"-c",
     "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

LOGF = None
def log(msg):
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    if LOGF:
        try:
            with open(LOGF, "a") as f: f.write(line + "\n")
        except Exception: pass

def preflight(cfg, base):
    """Fail fast with a clear message before any rendering, so a bad config or a
    missing asset never turns into a cryptic ffmpeg error mid-run."""
    errs = []
    for k in ("title", "format", "beats"):
        if k not in cfg: errs.append(f"config missing '{k}'")
    fmt = cfg.get("format", {})
    for k in ("w", "h", "fps"):
        if k not in fmt: errs.append(f"format missing '{k}'")
    if not cfg.get("beats"): errs.append("no beats defined")
    for i, b in enumerate(cfg.get("beats", [])):
        for k in ("kf", "narration", "caption", "motion"):
            if k not in b: errs.append(f"beat {i} missing '{k}'")
        if not os.path.exists(os.path.join(base, b.get("kf", ""))):
            errs.append(f"beat {i} keyframe NOT FOUND: {b.get('kf')}")
    if not os.path.exists(FF): errs.append(f"ffmpeg not found: {FF}")
    if not os.path.exists(FONT): errs.append(f"font not found: {FONT}")
    free = shutil.disk_usage(ROOT).free
    if free < 500 * 1024 * 1024: errs.append(f"low disk space: {free//1024//1024}MB free")
    if errs:
        log("PREFLIGHT FAILED:")
        for e in errs: log("  - " + e)
        raise RuntimeError("preflight: " + "; ".join(errs))
    log(f"PREFLIGHT OK ({len(cfg['beats'])} beats, {free//1024//1024}MB free)")

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print("CMD FAILED:", " ".join(str(a) for a in args[:6])); print(r.stderr[-1200:]); sys.exit(1)
    return r
def dur(p):
    r = subprocess.run([FF,"-i",p],capture_output=True,text=True)
    for l in r.stderr.splitlines():
        if "Duration" in l:
            h,m,s = l.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(h)*3600+float(m)*60+float(s)
    raise RuntimeError("no dur "+p)

# ---------- captions / motion / render (orientation-aware) ----------
def caption_png(text,path,W,H):
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img); size=62
    font=ImageFont.truetype(FONT,size); lines=text.split("\n")
    while True:
        ws=[d.textlength(l,font=font) for l in lines]
        if max(ws)<=W*0.92 or size<=40: break
        size-=4; font=ImageFont.truetype(FONT,size)
    lh=size*1.28; y=int(H*0.16)-lh*len(lines)/2
    for l in lines:
        w=d.textlength(l,font=font); x=(W-w)/2
        for ox in(-3,0,3):
            for oy in(-3,0,3): d.text((x+ox,y+oy),l,font=font,fill=(16,18,46,235))
        d.text((x,y),l,font=font,fill=(255,246,224,255)); y+=lh
    img.save(path)
def motion_fc(mot,nf):
    name,zs,ze,x0,y0,x1,y1=mot
    z=f"{ze}+({zs}-{ze})*sqrt(max(0,1-on/{nf}))" if name=="settle" else f"{zs}+({ze}-{zs})*on/{nf}"
    x=f"(iw-iw/zoom)*({x0}+({x1}-{x0})*on/{nf})"; y=f"(ih-ih/zoom)*({y0}+({y1}-{y0})*on/{nf})"
    return z,x,y
def render_beat(kf,cap,mot,dur_s,out,W,H,FPS,last=False,narration=None,pause_s=0.15,overlay_text=None,overlay_start_frac=0.0,overlay_end_frac=1.0,font_size=62):
    nf=int(round(dur_s*FPS)); z,x,y=motion_fc(mot,nf)
    fout=f",fade=t=out:st={dur_s-0.45:.2f}:d=0.45" if last else ""
    text=overlay_text or narration or cap; words=re.findall(r"[A-Za-z0-9][A-Za-z0-9’'-]*[.,!?;:]?",text)
    speech=max(0.1,dur_s-pause_s); weights=[max(1,len(re.sub(r'[^A-Za-z0-9]','',w)))+(0.35 if re.search(r'[.,!?;:]',w) else 0) for w in words]; total=sum(weights) or 1
    srt=f"{out}.srt"
    def st(t):
        h=int(t//3600); m=int((t%3600)//60); sec=t%60; return f'{h:02d}:{m:02d}:{sec:06.3f}'.replace('.',',')
    with open(srt,'w') as sf:
        for n,i in enumerate(range(0,len(words),2),1):
            j=min(i+2,len(words)); a=speech*(overlay_start_frac+(overlay_end_frac-overlay_start_frac)*sum(weights[:i])/total); b=speech*(overlay_start_frac+(overlay_end_frac-overlay_start_frac)*sum(weights[:j])/total)
            sf.write(f'{n}\n{st(a)} --> {st(b)}\n{" ".join(words[i:j])}\n\n')
    # SRT/libass burn-in is used instead of a separate overlay stream: it is deterministic and visible in the encoded pixels.
    srt_filter=srt.replace('\\','/')
    fc=f"[0:v]scale={int(W*1.2)}:{int(H*1.2)}:force_original_aspect_ratio=increase:flags=lanczos,crop={int(W*1.2)}:{int(H*1.2)},zoompan=z='{z}':x='{x}':y='{y}':d={nf}:s={W}x{H}:fps={FPS},setsar=1,eq=saturation=1.05,vignette=PI/5,format=yuv420p,fade=t=in:st=0:d=0.3{fout},subtitles='{srt_filter}':force_style='FontName=DejaVu Sans,FontSize={font_size},PrimaryColour=&H00E0F6FF,OutlineColour=&H002E1210,BorderStyle=1,Outline=4,Alignment=8,MarginV=170'[v]"
    run([FF,"-y","-i",kf,"-filter_complex",fc,"-map","[v]","-c:v","libx264","-preset","ultrafast","-crf","21","-r",str(FPS),"-t",f"{dur_s:.3f}","-an",out])
    os.remove(srt)

def concat(parts,out,W,H,FPS):
    lf=out+".txt"
    with open(lf,"w") as f:
        for p in parts: f.write(f"file '{p}'\n")
    run([FF,"-y","-f","concat","-safe","0","-i",lf,"-c:v","libx264","-preset","fast",
         "-crf","21","-pix_fmt","yuv420p","-r",str(FPS),out]); os.remove(lf)

# ---------- builders ----------
def build_long(cfg,base,outdir,title,work):
    W,H,FPS=cfg["format"]["w"],cfg["format"]["h"],cfg["format"]["fps"]; GAP=cfg.get("gap",0.45)
    os.makedirs(work,exist_ok=True); vos=[]; durs=[]
    for i,b in enumerate(cfg["beats"]):
        v=f"{work}/vo_{i}.wav"
        if not os.path.exists(v): tts.synth(b["narration"],voice=cfg.get("voice","bm_george"),out=v)
        vos.append(v); durs.append(round(dur(v)+GAP,3))
    total=round(sum(durs),3)
    parts=[]
    for i,b in enumerate(cfg["beats"]):
        o=f"{work}/beat_{i}.mp4"
        render_beat(os.path.join(base,b["kf"]),b["caption"],b["motion"],durs[i],o,W,H,FPS,last=(i==len(cfg["beats"])-1))
        parts.append(o)
    concat(parts,f"{work}/video.mp4",W,H,FPS)
    # narration
    pads=[]
    for i,v in enumerate(vos):
        p=f"{work}/nap_{i}.wav"; run([FF,"-y","-i",v,"-af",f"apad=whole_dur={durs[i]:.3f}","-ar","48000","-ac","2",p]); pads.append(p)
    nl=f"{work}/na.txt"
    with open(nl,"w") as f:
        for p in pads: f.write(f"file '{p}'\n")
    run([FF,"-y","-f","concat","-safe","0","-i",nl,"-c:a","pcm_s16le",f"{work}/narr.wav"])
    run([FF,"-y","-f","lavfi","-i",f"sine=frequency=110:duration={total}",
         "-f","lavfi","-i",f"sine=frequency=164.8:duration={total}",
         "-f","lavfi","-i",f"sine=frequency=220:duration={total}","-filter_complex",
         "[0:a]volume=0.5[a0];[1:a]volume=0.3[a1];[2:a]volume=0.2[a2];"
         f"[a0][a1][a2]amix=inputs=3:normalize=0,lowpass=f=520,afade=t=in:st=0:d=3,afade=t=out:st={total-4:.2f}:d=4,volume=0.35[pad]",
         "-map","[pad]","-ar","48000","-ac","2",f"{work}/pad.wav"])
    final=f"{outdir}/{title}.mp4"
    run([FF,"-y","-i",f"{work}/video.mp4","-i",f"{work}/narr.wav","-i",f"{work}/pad.wav",
         "-filter_complex","[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[n];[n]asplit=2[n1][n2];"
         "[2:a][n2]sidechaincompress=threshold=0.03:ratio=4:attack=15:release=400[pd];"
         "[n1][pd]amix=inputs=2:normalize=0[a]",
         "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","160k","-shortest",final])
    info=subprocess.run([FF,"-i",final],capture_output=True,text=True).stderr
    d=dur(final)
    ok={"dims":f"{W}x{H}" in info,"fps":f"{FPS} fps" in info,"aud":"Audio: aac" in info,"dur":abs(d-total)<1.5}
    json.dump({"total":total,"durs":durs},open(f"{outdir}/timings.json","w"))
    print("LONG VERIFY:",ok); return ok,total,durs

def build_cover(cfg,base,outdir,title):
    W,H=1280,720
    im=Image.open(os.path.join(base,cfg["beats"][0]["kf"])).convert("RGB")
    im=im.resize((int(im.width*H/im.height),H)) if im.width/im.height>W/H else im.resize((W,int(im.height*W/im.width)))
    l=(im.width-W)//2; t=(im.height-H)//2; im=im.crop((l,t,l+W,t+H))
    d=ImageDraw.Draw(im,"RGBA"); d.rectangle([0,0,W,H],fill=(10,12,30,120))
    f=ImageFont.truetype(FONT,72); lines=title.split(" ")
    # wrap to <=2 lines
    a=[];cur=""
    for w in lines:
        if d.textlength(cur+" "+w,font=f)>W*0.9 and cur: a.append(cur);cur=w
        else: cur=(cur+" "+w).strip()
    a.append(cur); a=a[:2]
    y=H-60-72*1.2*len(a)
    for L in a:
        w=d.textlength(L,font=f); x=(W-w)/2
        for ox in(-4,0,4):
            for oy in(-4,0,4): d.text((x+ox,y+oy),L,font=f,fill=(10,12,30,235))
        d.text((x,y),L,font=f,fill=(255,246,224,255)); y+=72*1.2
    im.save(f"{outdir}/{title} cover.jpg",quality=90)

def build_meta(cfg,outdir,title,total,durs):
    kw=title.lower()
    chap=[];t=0
    for i,b in enumerate(cfg["beats"]):
        chap.append(f"{int(t//60):02d}:{int(t%60):02d} — {b['caption'].replace(chr(10),' ')}"); t+=durs[i]
    md=f"""# {title}
**Format:** {cfg['format']['w']}x{cfg['format']['h']} @ {cfg['format']['fps']}fps · {total:.1f}s · Voice: {cfg.get('voice','bm_george')} (Kokoro)

## Description
{title}? Every night it happens, and almost nobody asks why. In this video we follow the science and the meaning of it — from the first spark to the story your mind tells you. Watch until the end for the part that changes how you see it.

#psychology #neuroscience #mind

## Chapters
""" + "\n".join(chap) + f"""

## Tags
psychology, neuroscience, {kw}, dreams, mind, explained, animation
"""
    open(f"{outdir}/{title}.metadata.md","w").write(md)

def build_short(cfg,base,outdir,title,kind,beats_sel,work):
    W,H,FPS=1080,1920,30; GAP=0.4
    os.makedirs(f"{outdir}/shorts",exist_ok=True); os.makedirs(work,exist_ok=True)
    sel=[cfg["beats"][i] for i in beats_sel]
    vos=[];durs=[]
    for i,b in enumerate(sel):
        v=f"{work}/s_{kind}_{i}.wav"
        if not os.path.exists(v): tts.synth(b["narration"],voice=cfg.get("voice","bm_george"),out=v)
        vos.append(v); durs.append(round(dur(v)+GAP,3))
    parts=[]
    for i,b in enumerate(sel):
        o=f"{work}/s_{kind}_beat_{i}.mp4"
        render_beat(os.path.join(base,b["kf"]),b["caption"],b["motion"],durs[i],o,W,H,FPS,last=(i==len(sel)-1))
        parts.append(o)
    concat(parts,f"{work}/s_{kind}_v.mp4",W,H,FPS)
    pads=[]
    for i,v in enumerate(vos):
        p=f"{work}/s_{kind}_n_{i}.wav"; run([FF,"-y","-i",v,"-af",f"apad=whole_dur={durs[i]:.3f}","-ar","48000","-ac","2",p]); pads.append(p)
    nl=f"{work}/s_{kind}_na.txt"
    with open(nl,"w") as f:
        for p in pads: f.write(f"file '{p}'\n")
    run([FF,"-y","-f","concat","-safe","0","-i",nl,"-c:a","pcm_s16le",f"{work}/s_{kind}_narr.wav"])
    out=f"{outdir}/shorts/{title} {kind}.mp4"
    run([FF,"-y","-i",f"{work}/s_{kind}_v.mp4","-i",f"{work}/s_{kind}_narr.wav",
         "-filter_complex","[1:a]loudnorm=I=-16:TP=-1.5[a]","-map","0:v","-map","[a]",
         "-c:v","copy","-c:a","aac","-b:a","128k","-shortest",out])
    info=subprocess.run([FF,"-i",out],capture_output=True,text=True).stderr
    ok=("1080x1920" in info) and ("Audio: aac" in info)
    open(f"{outdir}/shorts/{title} {kind}.metadata.md","w").write(
        f"# {title} — {kind} Short\n9:16 vertical · Voice {cfg.get('voice','bm_george')}\n\n## Description\n{title}? #Shorts #psychology #mind\n")
    print(f"SHORT {kind} VERIFY:",ok); return ok

def main():
    global LOGF
    ap=argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("--only")
    a=ap.parse_args()
    cfg=json.load(open(a.config)); base=os.path.dirname(os.path.abspath(a.config))
    title=cfg["title"]; outdir=os.path.join(ROOT,"output",title)
    os.makedirs(outdir,exist_ok=True); work=f"{outdir}/.work"; os.makedirs(work,exist_ok=True)
    LOGF=os.path.join(outdir,"produce.log"); state=f"{outdir}/state.json"
    only=a.only
    try:
        # Fail closed before any dependency download or render. The validator enforces
        # channel-level invariants that ffmpeg cannot know (orientation, beat schema,
        # asset reuse and missing keyframes).
        validator=os.path.join(ROOT,"tools","validate_project.py")
        vr=subprocess.run([sys.executable,validator,a.config],capture_output=True,text=True)
        print(vr.stdout, end="")
        if vr.returncode:
            print(vr.stderr, end="")
            raise RuntimeError("project validation failed; no render started")
        preflight(cfg,base)
        total=None; durs=None; tf=f"{outdir}/timings.json"
        # SOP ORDER (enforced): 1 long video -> 2 thumbnail(cover) -> 3 metadata -> 4 shorts LAST
        if only in (None,"long"):
            ok,total,durs=build_long(cfg,base,outdir,title,work)
            if not all(ok.values()): raise RuntimeError(f"long verify failed: {ok}")
        if only in (None,"cover"): build_cover(cfg,base,outdir,title)
        if only in (None,"meta"):
            if total is None and os.path.exists(tf):
                td=json.load(open(tf)); total,durs=td["total"],td["durs"]
            if total is None: raise RuntimeError("no timings - run --only long first")
            build_meta(cfg,outdir,title,total,durs)
        if only in (None,"shorts"):
            n=len(cfg["beats"])
            h=build_short(cfg,base,outdir,title,"hook",list(range(min(2,n))),work)
            p=build_short(cfg,base,outdir,title,"payoff",list(range(max(0,n-2),n)),work)
            if not (h and p): raise RuntimeError("shorts verify failed")
        json.dump({"title":title,"status":"ok","voice":cfg.get("voice","bm_george"),
                   "ts":f"{datetime.now():%Y-%m-%d %H:%M:%S}"},open(state,"w"),indent=1)
        log("PRODUCED: "+outdir)
    except SystemExit:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        json.dump({"title":title,"status":"failed","error":str(e),
                   "voice":cfg.get("voice","bm_george"),
                   "ts":f"{datetime.now():%Y-%m-%d %H:%M:%S}"},open(state,"w"),indent=1)
        log("FAILED: "+str(e)); sys.exit(2)

if __name__=="__main__":
    main()
