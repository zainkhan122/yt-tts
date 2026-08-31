#!/usr/bin/env python3
"""Auto-continuing, resumable orchestrator for one video (The Inner Machine).

Ordered steps: images -> long(chunked) -> thumbnail -> metadata -> shorts(separate).
Progress persists in <vdir>/run_state.json, so EVERY session resumes automatically at the
next incomplete step. It NEVER asks to proceed — it just does the next chunk/step and saves.

One task per session: within the "long" session, call this repeatedly; each call renders ONE
chunk (default 8 shots). Other steps complete in a single call.

Usage: python3 run.py [vdir] [--chunk N]
Exit codes: 0 = did work / advanced; 3 = AGENT_ACTION needed (generate missing images).
"""
import os, sys, json, subprocess, argparse
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import assemble_v2 as A
from PIL import Image, ImageDraw, ImageFont
FF=A.FF
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ORDER=["images","long","thumbnail","metadata","shorts"]

def load(vdir):
    shots=json.load(open(f"{vdir}/shots.json"))
    title=json.load(open(f"{vdir}/project.json"))["title"]
    st=f"{vdir}/run_state.json"
    state=json.load(open(st)) if os.path.exists(st) else {"step":"images","chunk":0}
    return shots,title,state,st

def save(state,st): json.dump(state,open(st,"w"),indent=1)

def step_images(vdir,shots,state,st):
    missing=sorted({s["img"] for s in shots if not os.path.exists(os.path.join(vdir,s["img"]))})
    if missing:
        print("AGENT_ACTION: generate_images", len(missing)); [print("  -",m) for m in missing]
        sys.exit(3)
    print("images: all", len({s['img'] for s in shots}), "base images present")
    state["step"]="long"; save(state,st)

def step_long(vdir,shots,title,state,st,chunk):
    A.VOICE="bm_george"
    work=f"{vdir}/long.work"; os.makedirs(work,exist_ok=True)
    i0=state["chunk"]; i1=min(i0+chunk,len(shots))
    for i in range(i0,i1):
        d=A.scene(shots[i],i,work); print(f"  shot {i}/{len(shots)}: {d:.1f}s",flush=True)
    state["chunk"]=i1
    if i1>=len(shots):
        lf=f"{work}/list.txt"
        with open(lf,"w") as f:
            for i in range(len(shots)): f.write(f"file '{os.path.abspath(work)}/av{i}.mp4'\n")
        out=f"{vdir}/{title}.mp4"
        A.run([FF,"-y","-f","concat","-safe","0","-i",lf,"-c","copy",out])
        import shutil; shutil.rmtree(work,ignore_errors=True)
        print("LONG DONE:",out)
        state["step"]="thumbnail"; state["chunk"]=0
    save(state,st)

def step_thumbnail(vdir,title,state,st):
    src=os.path.join(vdir,"img/b01.jpg")
    im=Image.open(src).convert("RGB"); Wd,Hd=1280,720
    im=im.resize((int(im.width*Hd/im.height),Hd)) if im.width/im.height>Wd/Hd else im.resize((Wd,int(im.height*Wd/im.width)))
    l=(im.width-Wd)//2; t=(im.height-Hd)//2; im=im.crop((l,t,l+Wd,t+Hd))
    d=ImageDraw.Draw(im,"RGBA"); d.rectangle([0,0,Wd,Hd],fill=(10,12,30,130))
    f=ImageFont.truetype(FONT,68); words=title.split(); a=[];cur=""
    for w in words:
        if d.textlength(cur+" "+w,font=f)>Wd*0.9 and cur: a.append(cur);cur=w
        else: cur=(cur+" "+w).strip()
    a.append(cur); a=a[:2]; y=Hd-60-68*1.2*len(a)
    for L in a:
        w=d.textlength(L,font=f); x=(Wd-w)/2
        for ox in(-4,0,4):
            for oy in(-4,0,4): d.text((x+ox,y+oy),L,font=f,fill=(10,12,30,235))
        d.text((x,y),L,font=f,fill=(244,239,230,255)); y+=68*1.2
    im.save(f"{vdir}/cover.jpg",quality=90); print("THUMBNAIL:",f"{vdir}/cover.jpg")
    state["step"]="metadata"; save(state,st)

def step_metadata(vdir,title,state,st):
    md=f"""# {title}
**Format:** 1920x1080 @ 24fps · Voice: bm_george (Kokoro)

## Description
{title} Every night it happens and almost nobody asks why. We follow the real mechanism —
from the first random spark to the story your mind tells you — and what it's actually for.
Watch to the end for the part that changes how you see sleeping.

#psychology #neuroscience #mind #brain #theinnermachine

## Tags
psychology, neuroscience, dreams, how your brain works, animated explainer, mind, sleep
"""
    open(f"{vdir}/metadata.md","w").write(md); print("METADATA:",f"{vdir}/metadata.md")
    state["step"]="shorts"; save(state,st)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("vdir",nargs="?",default=None); ap.add_argument("--chunk",type=int,default=8)
    a=ap.parse_args()
    vdir=a.vdir or os.path.join(os.path.dirname(HERE),"plan","video-01-where-do-dreams-come-from")
    shots,title,state,st=load(vdir)
    step=state["step"]
    print(f"[run] video='{title}' step={step} chunk={state['chunk']}/{len(shots)}")
    if step=="images": step_images(vdir,shots,state,st)
    elif step=="long": step_long(vdir,shots,title,state,st,a.chunk)
    elif step=="thumbnail": step_thumbnail(vdir,title,state,st)
    elif step=="metadata": step_metadata(vdir,title,state,st)
    elif step=="shorts": print("SHORTS: separate session — build 9:16 hook/payoff from the long video.")
    nxt=state["step"]
    print(f"[run] next step: {nxt}")

if __name__=="__main__": main()
