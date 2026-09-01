#!/usr/bin/env python3
"""Word-synced keyword captions. No legal copy.
Usage: python3 tools/stamp_caps.py IN.mp4 AUDIO captions.json OUT.mp4
captions.json: [{"text": "MOVIEPASS", "need": ["moviepass", "movie pass"]}, ...]
"""
from __future__ import annotations
import json, os, subprocess, sys, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

LEGAL = (
    "advice", "investment", "disclaimer", "not financial", "education only",
)
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
VOSK = Path(os.environ.get("VOSK_MODEL", "/home/user/.cache/vosk-model-small-en-us-0.15"))


def ffprobe_dur(p):
    err = subprocess.run([FF, "-i", str(p)], capture_output=True, text=True).stderr
    for line in err.splitlines():
        if "Duration" in line and "N/A" not in line:
            hms = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def words_vosk(audio: Path):
    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)
    wav = Path("/tmp/vosk16.wav")
    subprocess.run(
        [FF, "-y", "-i", str(audio), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)],
        capture_output=True, check=True,
    )
    wf = wave.open(str(wav), "rb")
    rec = KaldiRecognizer(Model(str(VOSK)), wf.getframerate())
    rec.SetWords(True)
    out = []
    while True:
        data = wf.readframes(4000)
        if not data:
            break
        if rec.AcceptWaveform(data):
            r = json.loads(rec.Result())
            out.extend(r.get("result") or [])
    r = json.loads(rec.FinalResult())
    out.extend(r.get("result") or [])
    wf.close()
    wav.unlink(missing_ok=True)
    return out


def find_time(words, needles):
    joined = [(w.get("word", "").lower(), float(w.get("start", 0))) for w in words]
    for needle in needles:
        parts = needle.lower().split()
        if len(parts) == 1:
            for tok, t in joined:
                if tok == parts[0] or parts[0] in tok:
                    return t
        else:
            for i in range(len(joined) - len(parts) + 1):
                window = [joined[i + j][0] for j in range(len(parts))]
                if window == parts:
                    return joined[i][1]
                if all(p in window[k] or window[k] in p for k, p in enumerate(parts)):
                    return joined[i][1]
    return None


def make_cap(text, path, W, H, portrait=False):
    size = 52 if portrait else 44
    fnt = ImageFont.truetype(FONT, size)
    im = Image.new("RGBA", (W, 130 if portrait else 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tw = d.textlength(text, font=fnt)
    x = max(8, (W - tw) / 2)
    y = 36 if portrait else 28
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, 3)):
        d.text((x + dx, y + dy), text, font=fnt, fill=(0, 0, 0, 255))
    d.text((x, y), text, font=fnt, fill=(244, 193, 93, 255))
    im.save(path)


def holds(caps, default=2.6):
    out = []
    for i, (disp, t) in enumerate(caps):
        hold = default
        if i + 1 < len(caps):
            gap = caps[i + 1][1] - t
            if gap < default + 0.15:
                hold = max(1.15, gap - 0.15)
        out.append((disp, t, round(hold, 3)))
    return out


def main():
    IN, AUDIO, CAPS, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
    spec = json.loads(CAPS.read_text())
    for item in spec:
        t = item["text"].lower()
        if any(x in t for x in LEGAL):
            sys.exit(f"L1: caption {item['text']!r} contains legal copy")
    print("aligning...", flush=True)
    words = words_vosk(AUDIO)
    (Path("/tmp") / "vosk_words.json").write_text(json.dumps(words))
    print("vosk words", len(words), flush=True)
    preview = " ".join(w.get("word", "") for w in words[:40])
    print("head:", preview, flush=True)
    timed = []
    used = set()
    for item in spec:
        t = find_time(words, item.get("need") or [item["text"]])
        if t is None:
            print("  MISS", item["text"], flush=True)
            continue
        key = round(t, 2)
        if key in used:
            # skip duplicate timestamp
            continue
        used.add(key)
        timed.append((item["text"], t))
        print(f"  {t:7.2f}  {item['text']}", flush=True)
    timed.sort(key=lambda x: x[1])
    if not timed:
        sys.exit("no captions aligned")
    # probe size
    err = subprocess.run([FF, "-i", str(IN)], capture_output=True, text=True).stderr
    W, H = 1280, 720
    for line in err.splitlines():
        if "Video:" in line and "x" in line:
            import re
            m = re.search(r"(\d{3,4})x(\d{3,4})", line)
            if m:
                W, H = int(m.group(1)), int(m.group(2))
            break
    portrait = H > W
    T = ffprobe_dur(IN)
    WORK = Path("/tmp/stamp_caps")
    WORK.mkdir(exist_ok=True)
    for p in WORK.glob("c*.png"):
        p.unlink()
    pngs = []
    for i, (disp, t, h) in enumerate(holds(timed)):
        p = WORK / f"c{i:02d}.png"
        make_cap(disp, p, W, H, portrait=portrait)
        pngs.append((p, t, h))
    cur = IN
    BATCH = 5
    for bi in range(0, len(pngs), BATCH):
        group = pngs[bi:bi + BATCH]
        args = [FF, "-y", "-i", str(cur)]
        for p, t, h in group:
            args += ["-itsoffset", f"{t:.3f}", "-loop", "1", "-framerate", "24",
                     "-t", f"{h:.2f}", "-i", str(p)]
        parts = []
        last = "0:v"
        y = "H-h-48" if portrait else "H-h-18"
        for j, _ in enumerate(group):
            parts.append(f"[{j+1}:v]format=rgba[c{j}]")
            parts.append(f"[{last}][c{j}]overlay=x=(W-w)/2:y={y}:eof_action=pass[o{j}]")
            last = f"o{j}"
        out = WORK / f"ov_{bi:02d}.mp4"
        if bi + BATCH >= len(pngs):
            out = OUT
        args += ["-filter_complex", ";".join(parts),
                 "-map", f"[{last}]", "-map", "0:a:0?",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                 "-pix_fmt", "yuv420p", "-r", "24", "-c:a", "copy",
                 "-t", f"{T:.3f}", "-movflags", "+faststart", str(out)]
        print("batch", bi, "->", out, flush=True)
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(r.stderr[-1200:])
        if cur != IN and cur.exists() and cur != out:
            cur.unlink()
        cur = out
    print("WROTE", OUT, round(OUT.stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
