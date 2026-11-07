#!/usr/bin/env python3
"""Aggregate the 20 fps audit: same metrics for the reference account and our batch, plus sameness tests."""
import json
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

FF = imageio_ffmpeg.get_ffmpeg_exe()
META = Path("/var/tmp/audit/meta")


def mean_frame(mp4, size=(48, 85)):
    cap = cv2.VideoCapture(str(mp4))
    acc, n = None, 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(fr, size), cv2.COLOR_BGR2GRAY).astype(np.float32)
        acc = g if acc is None else acc + g
        n += 1
    cap.release()
    return (acc / max(1, n)).ravel()


def soft_scenes(mp4, thr=8.0):
    """Scene changes counted with a low threshold so fades/glides count too."""
    cap = cv2.VideoCapture(str(mp4))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, round(fps / 20))
    prev, diffs, i = None, [], 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % step == 0:
            g = cv2.cvtColor(cv2.resize(fr, (270, 480)), cv2.COLOR_BGR2GRAY).astype(np.float32)
            if prev is not None:
                diffs.append(float(np.mean(np.abs(g - prev))))
            prev = g
        i += 1
    cap.release()
    d = np.array(diffs)
    peaks = int(np.sum((d > thr) & (d > np.roll(d, 1))))
    return peaks, float(np.median(d)), float(np.percentile(d, 95))


def backgrounds(mp4):
    """How many visually distinct 'treatments' (background lightness regimes) a video uses."""
    cap = cv2.VideoCapture(str(mp4))
    lum, i = [], 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, round(fps / 10))
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % step == 0:
            g = cv2.cvtColor(cv2.resize(fr, (64, 114)), cv2.COLOR_BGR2GRAY)
            lum.append(float(np.median(g)))
        i += 1
    cap.release()
    lum = np.array(lum)
    light = float(np.mean(lum > 128))
    dark = float(np.mean(lum <= 128))
    bright = float(np.mean(lum > 190))
    return {"median_luma": round(float(np.median(lum)), 1), "share_light_bg": round(light, 3),
            "share_dark_bg": round(dark, 3), "share_near_white_bg": round(bright, 3),
            "luma_std": round(float(np.std(lum)), 1)}


def main():
    groups = {"reference (TikTok @buildwithai.club)": sorted(Path("/var/tmp/audit/tt").glob("*.mp4")),
              "ours (batch 2026-11-08)": sorted(Path("/var/tmp/audit/ours").glob("*.mp4"))}
    rows = {}
    for g, files in groups.items():
        for f in files:
            m = json.loads((META / (f.stem + ".json")).read_text())
            sc, med, p95 = soft_scenes(f)
            b = backgrounds(f)
            m["soft_scene_changes"] = sc
            m["soft_scene_changes_per_min"] = round(sc / (m["duration_s"] / 60), 1)
            m["frame_diff_median"] = round(med, 2)
            m["frame_diff_p95"] = round(p95, 2)
            m.update(b)
            rows.setdefault(g, []).append(m)
    # sameness: pairwise correlation of mean frames inside each group
    sim = {}
    for g, files in groups.items():
        mats = [mean_frame(f) for f in files]
        cors = []
        for i in range(len(mats)):
            for j in range(i + 1, len(mats)):
                cors.append(float(np.corrcoef(mats[i], mats[j])[0, 1]))
        sim[g] = {"mean_pairwise_frame_corr": round(float(np.mean(cors)), 3),
                  "min": round(float(np.min(cors)), 3), "max": round(float(np.max(cors)), 3),
                  "n_pairs": len(cors)}
    # group medians
    keys = ["duration_s", "cuts_per_min", "mean_shot_s", "soft_scene_changes_per_min", "face_frame_share",
            "face_area_median", "static_share", "motion_energy", "frame_diff_p95", "white_share",
            "edge_density", "palette_max_chroma", "share_light_bg", "share_near_white_bg", "luma_std",
            "median_luma", "wpm", "words_per_video_s", "silence_share", "longest_pause_s",
            "pauses_over_250ms_per_min", "energy_onsets_per_min", "f0_median_hz", "f0_iqr_hz",
            "spectral_centroid_hz", "spectral_flatness", "loud_p90_dbfs", "first_word_at"]
    summary = {}
    for g, rs in rows.items():
        summary[g] = {}
        for k in keys:
            vals = [r.get(k) for r in rs if isinstance(r.get(k), (int, float))]
            if vals:
                summary[g][k] = {"median": round(float(np.median(vals)), 2),
                                 "min": round(float(np.min(vals)), 2), "max": round(float(np.max(vals)), 2)}
        # distinct palettes
        summary[g]["palette_top1"] = [r["palette"][0]["rgb"] for r in rs if r.get("palette")]
        summary[g]["band_white_median"] = [round(float(np.median([r["band_white"][i] for r in rs])), 3) for i in range(5)]
        summary[g]["transcripts"] = {r["file"]: r.get("transcript", []) for r in rs}
    out = {"summary": summary, "sameness": sim, "rows": rows}
    Path("/var/tmp/audit/aggregate.json").write_text(json.dumps(out, indent=1))
    for k in keys:
        a = summary["reference (TikTok @buildwithai.club)"].get(k)
        b = summary["ours (batch 2026-11-08)"].get(k)
        if a and b:
            print(f"{k:32s} ref {a['median']:>8} ({a['min']}-{a['max']})   ours {b['median']:>8} ({b['min']}-{b['max']})")
    print("\nsameness:", json.dumps(sim, indent=1))
    print("band_white ref:", summary["reference (TikTok @buildwithai.club)"]["band_white_median"])
    print("band_white ours:", summary["ours (batch 2026-11-08)"]["band_white_median"])
    print("palette top1 ref:", summary["reference (TikTok @buildwithai.club)"]["palette_top1"])
    print("palette top1 ours:", summary["ours (batch 2026-11-08)"]["palette_top1"])


if __name__ == "__main__":
    main()
