#!/usr/bin/env python3
"""Sample local mp4s into C:/ ext frames.json for frame_critique --external."""
import json, os, re, subprocess, sys

OUT = "/tmp/ext"
FF = subprocess.run(["python3", "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"],
                    capture_output=True, text=True).stdout.strip()

def main():
    src_dir = sys.argv[sys.argv.index("--dir") + 1]
    vids = sorted(f for f in os.listdir(src_dir) if f.endswith(".mp4"))
    pack = []
    for i, v in enumerate(vids[:5], 1):
        src = os.path.join(src_dir, v)
        p = subprocess.run([FF, "-i", src], capture_output=True, text=True)
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr)
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        d = f"{OUT}/frames-{i}"
        os.makedirs(d, exist_ok=True)
        for j, t in enumerate([0.3, dur * .45, dur * .88]):
            subprocess.run([FF, "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", src,
                            "-frames:v", "1", "-vf", "scale=512:-1", "-q:v", "4", f"{d}/f{j+1}.jpg"], check=True)
        pack.append({"name": v[:-4], "caption": "",
                     "frames": sorted(os.path.join(d, f) for f in os.listdir(d))})
        print(f"{v}: {dur:.1f}s, 3 frames", flush=True)
    json.dump(pack, open(f"{OUT}/frames.json", "w"))

if __name__ == "__main__":
    main()
