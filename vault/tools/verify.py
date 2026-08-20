#!/usr/bin/env python3
"""verify.py — enforce MASTER_RULES R9 (double-verify). Usage:
  python3 tools/verify.py /home/user/videos/video_006 storyboard   # pre-render checks
  python3 tools/verify.py /home/user/videos/video_006 tts          # post-tts checks
  python3 tools/verify.py /home/user/videos/video_006 chunk 0      # post-render chunk check
  python3 tools/verify.py /home/user/videos/video_006 assemble     # part A/V sync check
Exit 0 = ALL PASS, exit 1 = failures (list them).
"""
import json, os, sys, re

VID = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else "storyboard"
SB = os.path.join(VID, "storyboard.json")
AS = os.path.join(VID, "assets.json")
CFG = os.path.join(VID, "storyboard_config.json")
CHUNK = 26
fails = []

def ok(cond, msg):
    if not cond:
        fails.append(msg)

beats = json.load(open(SB))
assets = json.load(open(AS))
cfg = json.load(open(CFG))
MAX_USES = cfg.get("max_uses", 2)
N = len(beats)

if MODE == "storyboard":
    # (a) caption anchors exist in their sentence
    for i, b in enumerate(beats):
        if b.get("caption"):
            anchor, disp, style = b["caption"]
            if anchor.lower() not in b["sentence"].lower():
                ok(False, f"beat {i}: anchor {anchor!r} NOT in sentence {b['sentence'][:50]!r}")
    # (b) no duplicate captions
    from collections import Counter
    caps = [b["caption"][1] for b in beats if b.get("caption")]
    d = Counter(caps)
    for k, v in d.items():
        if v > 1:
            ok(False, f"duplicate caption {k!r} x{v}")
    # (c) no asset > max_uses
    usage = Counter(b["asset"] for b in beats)
    for a, n in usage.items():
        if n > MAX_USES:
            ok(False, f"asset {a} used {n}x (> {MAX_USES})")
    # (d) no two consecutive beats share an asset
    for i in range(1, N):
        if beats[i]["asset"] == beats[i-1]["asset"]:
            ok(False, f"beats {i-1},{i} share asset {beats[i]['asset']}")
    # (e) every asset file exists
    for b in beats:
        p = assets[b["asset"]][0]
        if not os.path.exists(p):
            ok(False, f"asset {b['asset']} file missing: {p}")
    # (f) no asset reused more than once WITHIN a chunk
    for k in range((N + CHUNK - 1)//CHUNK):
        a, z = k*CHUNK, min((k+1)*CHUNK, N)
        cc = Counter(beats[i]["asset"] for i in range(a, z))
        for asset, n in cc.items():
            if n > 1:
                ok(False, f"chunk {k}: asset {asset} used {n}x within chunk")
    # (g) distinct-asset coverage
    print(f"  beats={N} distinct_assets={len(usage)} captions={len(caps)} assets_total={len(assets)}")
    # (h) R14 asset-variety: all assets used (when pool <= beats), reuse distance spread
    from collections import defaultdict
    pos = defaultdict(list)
    for i, b in enumerate(beats):
        pos[b["asset"]].append(i)
    unused = [a for a in assets if a not in pos]
    if unused and len(assets) <= N:
        ok(False, f"{len(unused)} assets NEVER used: {unused[:8]}")
    dists = [p[1]-p[0] for p in pos.values() if len(p) > 1]
    if dists:
        print(f"  reuse: min_distance={min(dists)} beats, avg={sum(dists)/len(dists):.0f}")
        if min(dists) < 26:
            ok(False, f"min reuse distance {min(dists)} beats < 26 (pattern risk)")

elif MODE == "tts":
    missing = [i for i, b in enumerate(beats) if b.get("caption") and "cap_start" not in b]
    for i in missing:
        ok(False, f"beat {i}: caption has no cap_start")
    # mid-sentence keywords should have cap_start > 0 (first word = 0 is ok)
    for i, b in enumerate(beats):
        if b.get("caption") and "cap_start" in b:
            anchor = b["caption"][0]
            if anchor.lower() not in b["sentence"].lower():
                ok(False, f"beat {i}: anchor still missing")
            else:
                at = b["sentence"].lower().find(anchor.lower())
                cs = b["cap_start"]
                if at > 0 and cs <= 0:
                    ok(False, f"beat {i}: mid-sentence keyword but cap_start=0")

elif MODE == "chunk":
    k = int(sys.argv[3])
    a, z = k*CHUNK, min((k+1)*CHUNK, N)
    import subprocess, urllib.request, zipfile, io, time
    FF = subprocess.check_output(["python3","-c","import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()
    # pull the chunk zip from the repo (vbeats are deleted locally after push)
    name = os.path.basename(VID.rstrip("/"))
    tok_path = os.path.expanduser("~/secrets/github_pat.txt")
    tok = open(tok_path).read().strip() if os.path.exists(tok_path) else ""
    def api(url, tries=6):
        for at in range(tries):
            try:
                req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'User-Agent':'vault'})
                return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
            except Exception:
                if at == tries-1: raise
                time.sleep(6*(at+1))
    head = api(f'https://api.github.com/repos/zainkhan122/yt-tts/git/refs/heads/main')['object']['sha']
    zp = f'/tmp/verify_{name}_{k:02d}.zip'
    url = f'https://raw.githubusercontent.com/zainkhan122/yt-tts/{head}/vault/{name}/video_chunk_{k:02d}.zip'
    for at in range(6):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
            urllib.request.urlretrieve(url, zp)
            break
        except Exception:
            if at == 5: raise
            time.sleep(6*(at+1))
    ex = f'/tmp/verify_{name}_{k:02d}'
    with zipfile.ZipFile(zp) as zf:
        zf.extractall(ex)
    def info(p):
        r = subprocess.run([FF,"-i",p],capture_output=True,text=True)
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
        f = re.search(r"(\d+) fps", r.stderr)
        s = re.search(r"SAR (\d+:\d+)", r.stderr)
        h,mi,se=m.groups(); d=int(h)*3600+int(mi)*60+float(se)
        return d, (f.group(1) if f else None), (s.group(1) if s else None)
    for i in range(a, z):
        p = os.path.join(ex, f"vbeat_{i:03d}.mp4")
        if not os.path.exists(p):
            ok(False, f"beat {i}: vbeat missing from repo zip"); continue
        d, fps, sar = info(p)
        bl = beats[i].get("beat_len", beats[i].get("beat_dur", 0))
        ok(fps == "30", f"beat {i}: fps={fps} (want 30)")
        ok(sar == "1:1", f"beat {i}: SAR={sar} (want 1:1)")
        ok(abs(d - bl) < 0.05, f"beat {i}: dur={d:.3f} vs beat_len={bl:.3f}")
    # cleanup
    if os.path.exists(zp): os.remove(zp)
    import shutil
    if os.path.exists(ex): shutil.rmtree(ex, ignore_errors=True)

elif MODE == "assemble":
    import subprocess
    FF = subprocess.check_output(["python3","-c","import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()
    def dur(p):
        r = subprocess.run([FF,"-i",p],capture_output=True,text=True)
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
        h,mi,s=m.groups(); return int(h)*3600+int(mi)*60+float(s)
    nparts = (N + CHUNK - 1)//CHUNK
    for k in range(nparts):
        pv = os.path.join(VID, f"part_{k:02d}.mp4")
        pa = os.path.join(VID, f"part_{k:02d}.wav")
        if not (os.path.exists(pv) and os.path.exists(pa)):
            ok(False, f"part {k}: missing file"); continue
        dv, da = dur(pv), dur(pa)
        ok(abs(dv-da) < 0.1, f"part {k}: video={dv:.2f} audio={da:.2f} diff={dv-da:+.2f}")

if fails:
    print(f"❌ {len(fails)} FAILURES:")
    for f in fails:
        print("   -", f)
    sys.exit(1)
else:
    print("✅ ALL CHECKS PASS")
