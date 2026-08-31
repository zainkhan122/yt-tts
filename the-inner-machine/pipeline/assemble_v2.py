#!/usr/bin/env python3
"""Retention assembler v2 (16:9 long-form) for The Inner Machine.

NO sentence subtitles. Only IMPORTANT WORDS (the shot's `overlay`) appear, as kinetic
text at the TOP of the screen on a SINGLE line, synced to that sentence's TTS duration.
Every shot = one image with its own zoom/pan (changes every 3-6s), dip 0.2s at boundaries.

scenes/shots.json: [{img, motion, text(sentence->TTS), overlay?(KEY WORDS)}, ...]
Usage: python3 assemble_v2.py shots.json out.mp4 [--voice bm_george]
"""
import subprocess, sys, os, json, argparse
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)

def _bootstrap():
    for mod,pkg in [("imageio_ffmpeg","imageio-ffmpeg"),("kokoro_onnx","kokoro-onnx"),
                    ("soundfile","soundfile"),("PIL","pillow")]:
        try: __import__(mod)
        except Exception:
            subprocess.run([sys.executable,"-m","pip","install","--quiet",pkg],capture_output=True)
_bootstrap()
import tts, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
FF=subprocess.check_output([sys.executable,"-c","import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W,H,FPS=1920,1080,24
COPPER=(224,164,88); INK=(16,18,46)

def run(a):
    r=subprocess.run(a,capture_output=True,text=True)
    if r.returncode!=0:
        print("CMD FAILED"," ".join(map(str,a[:5]))); print(r.stderr[-900:]); sys.exit(1)
    return r

def motion_fc(mot,nf):
    name,zs,ze,x0,y0,x1,y1=mot
    z=f"{ze}+({zs}-{ze})*sqrt(max(0,1-on/{nf}))" if name=="settle" else f"{zs}+({ze}-{zs})*on/{nf}"
    x=f"(iw-iw/zoom)*({x0}+({x1}-{x0})*on/{nf})"; y=f"(ih-ih/zoom)*({y0}+({y1}-{y0})*on/{nf})"
    return z,x,y

def words_png(text,path,color,yfrac=0.10):
    """Single-line kinetic words at TOP; font shrinks to fit one line."""
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img)
    size=120
    f=ImageFont.truetype(FONT,size)
    while d.textlength(text,font=f)>W*0.9 and size>40:
        size-=6; f=ImageFont.truetype(FONT,size)
    w=d.textlength(text,font=f); x=(W-w)/2; y=int(H*yfrac)
    for ox in(-4,0,4):
        for oy in(-4,0,4): d.text((x+ox,y+oy),text,font=f,fill=INK+(235,))
    d.text((x,y),text,font=f,fill=color+(255,))
    img.save(path)

def scene(sc,i,work):
    a,sr=tts.synth(sc["text"],voice=VOICE); dur=len(a)/sr
    sf.write(f"{work}/s{i}.wav",a,sr)
    nf=max(int(round(dur*FPS)),1); z,x,y=motion_fc(sc["motion"],nf)
    inputs=["-loop","1","-framerate",str(FPS),"-t",f"{dur:.3f}","-i",sc["img"]]
    fc=(f"[0:v]scale={int(W*1.2)}:{int(H*1.2)}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={int(W*1.2)}:{int(H*1.2)},"
        f"zoompan=z='{z}':x='{x}':y='{y}':d={nf}:s={W}x{H}:fps={FPS},setsar=1,"
        f"eq=saturation=1.05,vignette=PI/5,format=yuv420p,fade=t=in:st=0:d=0.2,"
        f"fade=t=out:st={max(dur-0.2,0):.2f}:d=0.2[bg]")
    last="[bg]"
    if sc.get("overlay"):
        words_png(sc["overlay"],f"{work}/p{i}.png",COPPER,0.10)
        inputs+=["-loop","1","-framerate",str(FPS),"-t",f"{dur:.3f}","-i",f"{work}/p{i}.png"]
        fc+=";[1:v]format=rgba,fade=t=in:st=0.2:d=0.2:alpha=1[pp];[bg][pp]overlay=0:0[v1]"
        last="[v1]"
    fc+=f";{last}format=yuv420p[v]"
    run([FF,"-y"]+inputs+["-filter_complex",fc,"-map","[v]","-c:v","libx264","-preset","veryfast","-crf","24",
         "-maxrate","5000k","-bufsize","10000k","-r",str(FPS),"-t",f"{dur:.3f}","-an",f"{work}/v{i}.mp4"])
    run([FF,"-y","-i",f"{work}/v{i}.mp4","-i",f"{work}/s{i}.wav",
         "-filter_complex",f"[1:a]apad=whole_dur={dur:.3f},loudnorm=I=-16:TP=-1.5[a]",
         "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","160k","-shortest",f"{work}/av{i}.mp4"])
    return dur

def main():
    global VOICE
    ap=argparse.ArgumentParser(); ap.add_argument("shots"); ap.add_argument("out"); ap.add_argument("--voice",default="bm_george")
    a=ap.parse_args(); VOICE=a.voice
    scs=json.load(open(a.shots)); work=a.out+".work"; os.makedirs(work,exist_ok=True)
    parts=[]
    for i,sc in enumerate(scs):
        d=scene(sc,i,work); parts.append(os.path.abspath(f"{work}/av{i}.mp4")); print(f"scene {i}: {d:.1f}s",flush=True)
    lf=f"{work}/list.txt"
    with open(lf,"w") as f:
        for p in parts: f.write(f"file '{p}'\n")
    run([FF,"-y","-f","concat","-safe","0","-i",lf,"-c","copy",a.out])
    print("ASSEMBLED:",a.out)

if __name__=="__main__": main()
