#!/usr/bin/env python3
"""Short QA: the measured gates from FINDINGS section 3A and HOOKS section 5.

Two modes, one threshold file (config/qa-thresholds.json):

  plan   Before render (called by preflight.preflight). Estimates timing from the brief's script at the
         plan speech rate and checks the structure: hook anchor, first phrase, frame-0 media, call to action
         in the last 15%, visual change on speech scenes, static share, static scene length.
  video  After render (called by make_shorts fetch). Reads the render's own kit manifest.json (exact word
         timings) and measures the MP4 (frame change per 0.25 s bin, via ffmpeg).

Numbers are decided here, from config. The vision read is advisory and is not wired into any gate.
Any gate that cannot be measured is BLOCK (fail closed), never a silent pass.

  python3 tools/short_qa.py plan <brief-id> [--json]
  python3 tools/short_qa.py video <render.mp4> --kit <kit.zip | manifest.json> [--json]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS_PATH = ROOT / "config" / "qa-thresholds.json"
PUNCT_END = re.compile(r"[.!?,]$")


class MeasureError(RuntimeError):
    """A measurement could not run (missing ffmpeg, unreadable kit). Always reported as BLOCK."""


def load_thresholds(path: Path = THRESHOLDS_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def gates_apply(brief: dict) -> bool:
    """Owner decision 4 Nov 2026: the gates apply to new batches only. brief_from_plan sets qa_gates: true on every
    brief it writes; briefs without the flag (all earlier ones) are not gated and are not re-measured in the pipeline."""
    return brief.get("qa_gates") is True


def _r(gate: str, status: str, value, limit, detail: str, fix: str = "") -> dict:
    return {"gate": gate, "status": status, "value": value, "limit": limit, "detail": detail, "fix": fix}


def _words(text) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'\u2019\-]*", str(text or ""))


def _in_range(v: float, rng) -> bool:
    return rng[0] <= v <= rng[1]


# ------------------------------------------------------------------ plan (pre-render)
def is_motion_scene(scene: dict, th: dict) -> bool:
    kind = scene.get("type")
    if kind == "image":
        return bool(scene.get("focus")) or not th["image_motion_requires_focus"]
    return kind in th["motion_scene_types"]


def scene_seconds(scene: dict, th: dict) -> float:
    words = _words(scene.get("say"))
    if words:
        return len(words) * 60.0 / th["speech_wpm_plan_estimate"]
    hold = scene.get("hold")
    return float(hold) if isinstance(hold, (int, float)) and not isinstance(hold, bool) else 1.0


def _tool_names(brief: dict) -> list[str]:
    names = []
    title = str(brief.get("title") or "")
    if ":" in title:
        names.append(title.split(":", 1)[0].strip())
    parts = str(brief.get("id") or "").split("-")
    if len(parts) >= 3 and parts[0] == "repo":
        names.append("-".join(parts[1:-1]))  # repo-agent-desktop-01 -> agent-desktop
    names += [str(k) for k in (brief.get("keywords") or [])]
    seo = brief.get("seo") or {}
    if seo.get("keyword"):
        names.append(str(seo["keyword"]))
    return [n for n in names if n and len(n) >= 3]


def plan_results(brief: dict, th: dict | None = None) -> list[dict]:
    th = th or load_thresholds()
    scenes = brief.get("scenes") or []
    if not scenes:
        return [_r("scenes", "BLOCK", 0, ">=1", "brief declares no scenes", "write the scene list")]
    out = []
    secs = [scene_seconds(s, th) for s in scenes]
    total = sum(secs)
    speech_s = sum(d for s, d in zip(scenes, secs) if _words(s.get("say")))
    lo, hi = th["duration_s"]
    out.append(_r("duration_est", "PASS" if _in_range(total, th["duration_s"]) else "BLOCK",
                  round(total, 1), f"{lo}-{hi}s",
                  f"script estimates {total:.1f}s at {th['speech_wpm_plan_estimate']} wpm",
                  "trim or extend the script to 29-55 s of speech"))

    hook = scenes[0]
    onscreen = f"{hook.get('heading') or ''} {hook.get('sub') or ''}"
    has_num = bool(re.search(r"\d", onscreen))
    kw_hit = next((n for n in _tool_names(brief) if n.lower() in onscreen.lower()), None)
    anchored = has_num or bool(kw_hit)
    out.append(_r("hook_anchor", "PASS" if anchored else "BLOCK", bool(anchored),
                  f"number or tool name in on-screen text, first {th['hook_anchor_window_s']}s",
                  f"on-screen hook text: {onscreen.strip() or '(none)'!r}",
                  "put a number or the tool's name in the hook heading or sub"))

    first_sentence = re.split(r"(?<=[.!?])\s", str(hook.get("say") or "").strip(), maxsplit=1)[0]
    n_first = len(_words(first_sentence))
    out.append(_r("hook_phrase", "PASS" if 0 < n_first <= th["hook_first_phrase_words_max"] else "BLOCK",
                  n_first, f"<= {th['hook_first_phrase_words_max']} words",
                  "first sentence of the hook line", "shorten the first sentence of the hook"))

    frame0_ok = hook.get("type") in th["media_scene_types"] and (hook.get("type") != "image" or bool(hook.get("image")))
    out.append(_r("frame0_media", "PASS" if frame0_ok else "BLOCK", hook.get("type"),
                  "tool media (clip, page, scroll, steps or image file)",
                  "frame 0 must show the tool, not a text card", "open the hook on the tool's own media"))

    all_words = [w for s in scenes for w in _words(s.get("say"))]
    n_all = len(all_words)
    tail_start = math.ceil(n_all * (1 - th["cta_last_share"]))
    tail = " ".join(all_words[tail_start:]).lower()
    cta = next((c for c in th["cta_words"] if re.search(rf"\b{re.escape(c)}\b", tail)), None)
    out.append(_r("cta_last_15pct", "PASS" if cta else "BLOCK", cta or "",
                  f"a call word in the last {round(th['cta_last_share'] * 100)}% of the script",
                  f"{n_all} spoken words; tail of {n_all - tail_start} words",
                  "add one spoken call (follow, comment, save...) near the end"))

    # FINDINGS 3B: a graphic card lasts at most card_max_s, then a tool screen or a zoom follows.
    card_types = set(th.get("card_scene_types", []))
    long_cards = [s.get("id", f"#{i}") for i, (s, d) in enumerate(zip(scenes, secs))
                  if s.get("type") in card_types and d > th.get("card_max_s", 2.0)]
    out.append(_r("card_max_2s", "PASS" if not long_cards else "BLOCK", long_cards,
                  f"card scene <= {th.get('card_max_s', 2.0)}s ({', '.join(sorted(card_types))})",
                  "cards running too long: " + (", ".join(map(str, long_cards)) or "none"),
                  "cut the card to 2 s, then show a tool screen or zoom into one"))

    # HOOKS section 5.6 (warning): the hook names a familiar anchor the viewer already knows.
    anchors = th.get("hook_familiar_anchors", [])
    first_hook_sentence = re.split(r"(?<=[.!?])\s", str(hook.get("say") or "").strip(), maxsplit=1)[0]
    anchor_hit = next((a for a in anchors if re.search(rf"\b{re.escape(a)}\b", first_hook_sentence, re.I)), None)
    out.append(_r("hook_familiar_anchor", "PASS" if anchor_hit else "WARN", anchor_hit or "",
                  "familiar name in the first hook sentence (warning only)",
                  f"first hook sentence: {first_hook_sentence[:80]!r}",
                  "consider naming a product or platform the viewer already knows"))

    motion = [is_motion_scene(s, th) for s in scenes]
    speech_motion = sum(d for s, d, m in zip(scenes, secs, motion) if m and _words(s.get("say")))
    share = (speech_motion / speech_s) if speech_s else 0.0
    out.append(_r("visual_change_speech", "PASS" if speech_s and share >= th["visual_change_speech_share_min"] else "BLOCK",
                  round(share, 3), f">= {th['visual_change_speech_share_min']}",
                  "share of speech time on a moving scene (camera, focus, reveal or cut)",
                  "give every spoken scene a camera move, highlight or cut"))

    static_share = sum(d for d, m in zip(secs, motion) if not m) / total if total else 1.0
    out.append(_r("graphic_only_share", "PASS" if static_share <= th["graphic_only_share_max"] else "BLOCK",
                  round(static_share, 3), f"<= {th['graphic_only_share_max']}",
                  "share of runtime on static scenes", "replace static cards with tool screens or zooms"))

    too_long = [s.get("id", f"#{i}") for i, (s, d, m) in enumerate(zip(scenes, secs, motion))
                if not m and d > th["static_scene_max_s"]]
    out.append(_r("static_scene_len", "PASS" if not too_long else "BLOCK", too_long,
                  f"static scene <= {th['static_scene_max_s']}s",
                  "static scenes that run too long: " + (", ".join(map(str, too_long)) or "none"),
                  "shorten the card or add a zoom into a tool screen"))

    run = worst = 0.0
    for d, m in zip(secs, motion):
        run = 0.0 if m else run + d
        worst = max(worst, run)
    out.append(_r("motion_gap", "PASS" if worst <= th["motion_gap_max_s"] else "BLOCK", round(worst, 2),
                  f"<= {th['motion_gap_max_s']}s", "longest run without a move",
                  "add a camera move, highlight or cut inside the static stretch"))
    return out


def plan_verdict(results: list[dict]) -> str:
    return "BLOCK" if any(r["status"] == "BLOCK" for r in results) else "PASS"


# ------------------------------------------------------------------ video (post-render)
def ffmpeg_exe() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg  # bundled binary, optional
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # noqa: BLE001 - any failure means no decoder
        raise MeasureError(f"ffmpeg not found ({exc}); install ffmpeg or imageio-ffmpeg") from exc


def sample_gray_frames(mp4: Path, fps: float, w: int = 96, h: int = 54):
    """Decode the MP4 to small grayscale frames at a fixed rate. Returns a numpy array (n, h, w)."""
    import numpy as np
    cmd = [ffmpeg_exe(), "-v", "error", "-i", str(mp4), "-vf", f"fps={fps},scale={w}:{h},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    proc = subprocess.run(cmd, capture_output=True, check=False)
    if proc.returncode != 0 or not proc.stdout:
        raise MeasureError(f"ffmpeg could not decode {mp4.name}: {proc.stderr[-200:].decode(errors='replace')}")
    arr = np.frombuffer(proc.stdout, dtype=np.uint8)
    n = arr.size // (w * h)
    return arr[: n * w * h].reshape(n, h, w).astype(np.float32)


def change_bins(frames, fps: float, bin_s: float, threshold: float) -> list[bool]:
    """True where the picture changes in a bin. A change is the mean absolute pixel difference between
    consecutive sampled frames; sample k (time k/fps) is assigned to the bin that contains it."""
    import numpy as np
    if len(frames) < 2:
        return []
    diffs = np.abs(frames[1:] - frames[:-1]).mean(axis=(1, 2))
    total_bins = math.ceil(len(frames) / fps / bin_s)
    flags = [False] * total_bins
    for k, d in enumerate(diffs, start=1):
        b = min(total_bins - 1, int(k / fps / bin_s + 1e-9))
        if d >= threshold:
            flags[b] = True
    return flags


def _speech_bin_mask(words: list, n_bins: int, bin_s: float) -> list[bool]:
    mask = [False] * n_bins
    for _, start, end in words:
        b0 = max(0, int(start / bin_s))
        b1 = min(n_bins - 1, int(max(start, end - 1e-6) / bin_s))
        for b in range(b0, b1 + 1):
            mask[b] = True
    return mask


def timing_results(words: list, duration: float, th: dict) -> list[dict]:
    """Gates that only need the render's own word timings (kit manifest)."""
    if not words:
        return [_r("speech_timing", "BLOCK", 0, "word timings present", "kit manifest has no word timings",
                   "rebuild the kit with word timings")]
    words = sorted(words, key=lambda w: w[1])
    out = []
    wpm = len(words) / duration * 60.0 if duration else 0.0
    out.append(_r("speech_wpm", "PASS" if _in_range(wpm, th["speech_wpm"]) else "BLOCK", round(wpm, 1),
                  f"{th['speech_wpm'][0]}-{th['speech_wpm'][1]} wpm", f"{len(words)} words over {duration:.1f}s",
                  "adjust the script length or the voice pace"))
    gaps = [max(0.0, words[i + 1][1] - words[i][2]) for i in range(len(words) - 1)]
    longest = max(gaps) if gaps else 0.0
    out.append(_r("longest_pause", "PASS" if longest <= th["longest_pause_s"] else "BLOCK", round(longest, 2),
                  f"<= {th['longest_pause_s']}s", "longest silence between words",
                  "cut the dead air between phrases"))
    first = words[0][1]
    out.append(_r("hook_speech_start", "PASS" if first <= th["hook_speech_start_max_s"] else "BLOCK", round(first, 2),
                  f"<= {th['hook_speech_start_max_s']}s", "time of the first spoken word",
                  "remove intro silence before the first word"))
    # HOOKS section 1 and 5 (measured, info only): first-3-second pace and phrase structure. Not gates.
    first3 = [w for w in words if w[1] < 3.0]
    pause_s = th.get("phrase_pause_s", 0.35)
    phrases, cur = [], 0
    for i, w in enumerate(words):
        cur += 1
        if i + 1 == len(words) or words[i + 1][1] - w[2] >= pause_s:
            phrases.append(cur); cur = 0
    n_pauses = sum(1 for i in range(len(words) - 1) if words[i + 1][1] - words[i][2] >= pause_s)
    out.append(_r("measure_first3s_wpm", "INFO", round(len(first3) / 3.0 * 60.0, 1),
                  f"reference {th.get('hook_first3s_wpm_target', 220)} wpm (measured, not gated)",
                  f"{len(first3)} words in the first 3 s", "none"))
    out.append(_r("measure_phrases", "INFO", len(phrases),
                  f"reference {th.get('phrases_per_video_ref', [5, 14])} phrases with >= {pause_s}s pause (measured)",
                  f"{n_pauses} pauses >= {pause_s}s; mean {round(sum(phrases) / len(phrases), 1) if phrases else 0} words per phrase",
                  "none"))
    head = words[:12]
    end_idx = next((i for i, w in enumerate(head) if PUNCT_END.search(w[0])), len(head) - 1)
    phrase_end = head[end_idx][2]
    out.append(_r("hook_first_phrase_end", "PASS" if phrase_end <= th["hook_first_phrase_end_max_s"] else "BLOCK",
                  round(phrase_end, 2), f"<= {th['hook_first_phrase_end_max_s']}s", "end of the first phrase",
                  "make the first phrase shorter"))
    return out


def picture_results(changed: list[bool], speech: list[bool], bin_s: float, th: dict) -> list[dict]:
    """Gates from frame change: visual change during speech, graphic-only share, longest still stretch."""
    out = []
    n_speech = sum(speech)
    if n_speech == 0:
        out.append(_r("visual_change_speech", "BLOCK", None, f">= {th['visual_change_speech_share_min']}",
                      "no speech bins were measured", "check the kit word timings"))
    else:
        share = sum(1 for c, s in zip(changed, speech) if c and s) / n_speech
        out.append(_r("visual_change_speech", "PASS" if share >= th["visual_change_speech_share_min"] else "BLOCK",
                      round(share, 3), f">= {th['visual_change_speech_share_min']}",
                      "share of speech time with a visible change (threshold frame_change_min)",
                      "add camera moves, highlights or cuts on the spoken scenes"))
    still = (sum(1 for c in changed if not c) / len(changed)) if changed else 1.0
    out.append(_r("graphic_only_share", "PASS" if still <= th["graphic_only_share_max"] else "BLOCK", round(still, 3),
                  f"<= {th['graphic_only_share_max']}", "share of the video with no visible change",
                  "replace still stretches with tool screens or zooms"))
    run = worst = 0
    for c in changed:
        run = 0 if c else run + 1
        worst = max(worst, run)
    worst_s = worst * bin_s
    out.append(_r("motion_gap", "PASS" if worst_s <= th["motion_gap_max_s"] else "BLOCK", round(worst_s, 2),
                  f"<= {th['motion_gap_max_s']}s", "longest stretch with no visible change",
                  "add a move inside the still stretch"))
    return out


def video_results(mp4: Path, kit_manifest: dict, th: dict | None = None) -> tuple[list[dict], dict]:
    """Measure the MP4 and the kit's word timings. Returns (results, measured)."""
    th = th or load_thresholds()
    fps, bin_s = float(th["frame_sample_fps"]), float(th["frame_bin_s"])
    try:
        frames = sample_gray_frames(Path(mp4), fps)
    except MeasureError as exc:
        return [_r("measure", "BLOCK", None, "frames decoded", str(exc), "install ffmpeg, then re-run fetch")], {}
    duration = len(frames) / fps
    lo, hi = th["duration_s"]
    results = [_r("duration", "PASS" if _in_range(duration, th["duration_s"]) else "BLOCK", round(duration, 2),
                  f"{lo}-{hi}s", "measured length of the MP4", "trim or extend the script")]
    words = []
    for scene in kit_manifest.get("scenes") or []:
        for w in scene.get("words") or []:
            if isinstance(w, (list, tuple)) and len(w) >= 3:
                words.append((str(w[0]), float(w[1]), float(w[2])))
    results += timing_results(words, duration, th)
    changed = change_bins(frames, fps, bin_s, float(th["frame_change_min"]))
    n_bins = len(changed)
    speech = _speech_bin_mask(words, n_bins, bin_s) if words else [False] * n_bins
    results += picture_results(changed, speech, bin_s, th)
    measured = {"duration_s": round(duration, 2), "frames_sampled": int(len(frames)), "bins": n_bins,
                "frame_change_min": th["frame_change_min"], "words": len(words)}
    return results, measured


def load_kit_manifest(kit: Path) -> dict:
    kit = Path(kit)
    if kit.suffix == ".json":
        return json.loads(kit.read_text(encoding="utf-8"))
    if kit.suffix == ".zip":
        with zipfile.ZipFile(kit) as zf:
            names = sorted((n for n in zf.namelist() if n.endswith("manifest.json")), key=len)
            if not names:
                raise MeasureError(f"{kit.name}: no manifest.json inside the kit")
            return json.loads(zf.read(names[0]).decode("utf-8"))
    raise MeasureError(f"{kit.name}: expected a kit .zip or manifest .json")


def run_video_qa(mp4: Path, kit: Path, th: dict | None = None) -> dict:
    """Full post-render QA record (never raises for a failed measurement; that is a BLOCK)."""
    th = th or load_thresholds()
    try:
        manifest = load_kit_manifest(kit)
    except (MeasureError, OSError, ValueError, zipfile.BadZipFile) as exc:
        results, measured = [_r("kit", "BLOCK", None, "readable kit manifest", str(exc),
                                "rebuild the kit")], {}
    else:
        results, measured = video_results(Path(mp4), manifest, th)
    verdict = plan_verdict(results)
    return {"file": Path(mp4).name, "verdict": verdict, "measured": measured, "results": results,
            "thresholds": {k: th[k] for k in ("duration_s", "speech_wpm", "longest_pause_s", "graphic_only_share_max",
                                              "visual_change_speech_share_min", "motion_gap_max_s", "frame_change_min")}}


def write_qa_record(mp4: Path, record: dict) -> Path:
    out = Path(mp4).with_name(Path(mp4).stem + "-qa.json")
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def _print(results: list[dict], verdict: str) -> None:
    print(verdict)
    for r in results:
        tail = f"  -> {r['fix']}" if r["status"] == "BLOCK" and r["fix"] else ""
        print(f"   {r['status']:5} {r['gate']:24} {r['value']!s:>10}  {r['detail']}{tail}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("brief_id")
    p_plan.add_argument("--json", action="store_true")
    p_video = sub.add_parser("video")
    p_video.add_argument("mp4")
    p_video.add_argument("--kit", required=True)
    p_video.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.mode == "plan":
        brief = json.loads((ROOT / "briefs" / f"{args.brief_id}.json").read_text(encoding="utf-8"))
        results = plan_results(brief)
        verdict = plan_verdict(results)
        if args.json:
            print(json.dumps({"id": args.brief_id, "verdict": verdict, "results": results}, indent=2, ensure_ascii=False))
        else:
            _print(results, verdict)
        return 1 if verdict == "BLOCK" else 0
    record = run_video_qa(Path(args.mp4), Path(args.kit))
    out = write_qa_record(Path(args.mp4), record)
    if args.json:
        print(json.dumps(record, indent=2, ensure_ascii=False))
    else:
        _print(record["results"], record["verdict"])
        print(f"record: {out}")
    return 1 if record["verdict"] == "BLOCK" else 0


if __name__ == "__main__":
    sys.exit(main())
