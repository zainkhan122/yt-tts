#!/usr/bin/env python3
"""Run tts_one.py per paragraph so RAM resets. Concat with ffmpeg."""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
textfile, out, voice = sys.argv[1], sys.argv[2], sys.argv[3]
raw = Path(textfile).read_text(encoding="utf-8")
# L7: apply speak_map to a copy only (source file unchanged)
import json
sm_path = ROOT / "reusable/speak_map.json"
if sm_path.exists():
    sm = json.loads(sm_path.read_text())
    for r in sm.get("replacements", []):
        raw = raw.replace(r["from"], r["to"])
    print("L7 speak_map applied", [r["from"] for r in sm.get("replacements", [])], flush=True)
def split_para(p, limit=55):
    """Kokoro OOM on long paragraphs on a 2GB box. Split on sentences."""
    words = p.split()
    if len(words) <= limit:
        return [p]
    import re
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]
    chunks, buf = [], ""
    for s in sents:
        trial = (buf + " " + s).strip()
        if buf and len(trial.split()) > limit:
            chunks.append(buf)
            buf = s
        else:
            buf = trial
    if buf:
        chunks.append(buf)
    return chunks or [p]

paras = []
for p in raw.split("\n\n"):
    p = p.strip()
    if p:
        paras.extend(split_para(p))
print("paras", len(paras), flush=True)
work = Path("/tmp/kokoro_parts")
work.mkdir(exist_ok=True)
for p in work.glob("*"):
    p.unlink()
one = ROOT / "tools/tts_one.py"
files = []
for i, para in enumerate(paras):
    tf = work / f"t{i:02d}.txt"
    wf = work / f"p{i:02d}.wav"
    tf.write_text(para)
    r = subprocess.run([sys.executable, str(one), str(tf), str(wf), voice],
                       capture_output=True, text=True)
    print(f"p{i:02d}", r.stdout.strip() or r.stderr[-200:], "code", r.returncode, flush=True)
    if r.returncode != 0:
        sys.exit(1)
    files.append(wf)
    tf.unlink()
lst = work / "list.txt"
lst.write_text("".join(f"file '{p.resolve()}'\n" for p in files))
import imageio_ffmpeg
ff = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                "-c:a", "pcm_s16le", out], check=True)
print("wrote", out, flush=True)
