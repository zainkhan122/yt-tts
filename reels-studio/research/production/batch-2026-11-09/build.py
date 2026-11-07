#!/usr/bin/env python3
"""Build one batch video's authoring artifacts from a spec module.

Writes videos/<id>/plan.json, briefs/graphics/<id>/features.json, makes the brief with
tools/brief_from_plan.py, then writes beats.json bound to the brief's own script fingerprint.
Nothing here invents copy: the spec module holds the authored text.
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from graphics.beats import script_fingerprint, lint_beats, scene_list  # noqa: E402
from graphics.features import lint_feature_sheet  # noqa: E402
from graphics.timing import close_gaps  # noqa: E402

SPECS = Path(__file__).resolve().parent / "specs"


def load_spec(vid):
    spec_path = SPECS / f"{vid}.py"
    spec = importlib.util.spec_from_file_location(f"spec_{vid.replace('-', '_')}", spec_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_plan(vid, plan):
    d = ROOT / "videos" / vid
    d.mkdir(parents=True, exist_ok=True)
    p = d / "plan.json"
    p.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def words_estimate(brief):
    """Even 3 words/second spread per scene, 0.55 s between scenes: authoring-time lint only.

    Returns (words, phrases). Phrases are built one per brief scene, exactly as the cloud voice stage
    does (graphics/stage.py segments_from_timing), so the local lint checks the same 7-scene binding.
    """
    words, phrases, t = [], [], 0.35
    for sc in brief["scenes"]:
        ws = re.findall(r"\S+", sc["say"])
        scene_words = []
        for w in ws:
            dur = 1 / 3.0
            item = [w, round(t, 3), round(t + dur, 3)]
            words.append(item)
            scene_words.append(item)
            t += dur
        phrases.append({"sid": sc["id"], "text": " ".join(ws), "words": scene_words,
                        "t0": round(scene_words[0][1], 3), "t1": round(scene_words[-1][2], 3)})
        t += 0.55
    return words, phrases


def main(vid):
    mod = load_spec(vid)
    plan = mod.PLAN
    plan.setdefault("id", vid)
    plan.setdefault("author", "agent")
    plan_path = write_plan(vid, plan)

    gdir = ROOT / "briefs" / "graphics" / vid
    gdir.mkdir(parents=True, exist_ok=True)
    (gdir / "features.json").write_text(json.dumps(mod.FEATURES, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    r = subprocess.run([sys.executable, str(ROOT / "tools" / "video_plan.py"), str(plan_path)],
                       capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("PLAN BLOCKED")
        return 1

    r = subprocess.run([sys.executable, str(ROOT / "tools" / "brief_from_plan.py"), str(plan_path)],
                       capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        return 1

    bpath = ROOT / "briefs" / f"{vid}.json"
    brief = json.loads(bpath.read_text(encoding="utf-8"))
    brief["renderer"] = "graphics"
    brief["graphics"] = {"dir": f"briefs/graphics/{vid}",
                         "note": "beat plan bound to the brief scenes; lint is fail-closed on script or scene mismatch"}
    for key, value in getattr(mod, "BRIEF_EXTRA", {}).items():
        brief[key] = value
    brief["voice_seed"] = 0
    brief["qa_gates"] = True
    bpath.write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    joined = " ".join(s["say"] for s in brief["scenes"])
    fp = script_fingerprint([[t, 0.0, 0.0] for t in re.findall(r"\S+", joined)])

    beats = dict(mod.BEATS)
    beats["script_sha256"] = fp
    (gdir / "beats.json").write_text(json.dumps(beats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    source = (gdir / "source.md").read_text(encoding="utf-8")
    fv = lint_feature_sheet(mod.FEATURES, source)
    words, phrases = words_estimate(brief)
    (gdir / "words.estimate.json").write_text(json.dumps(words, indent=1) + "\n", encoding="utf-8")
    phrases = close_gaps(phrases, words[-1][2] + 0.3)
    bv = lint_beats(beats, phrases, mod.FEATURES, script_fp=fp)

    print(f"features lint: {'ok' if not fv else [v.as_dict() for v in fv]}")
    print(f"beats lint:    {'ok' if not bv else [v.as_dict() for v in bv]}")
    if fv or bv:
        return 1
    scenes = scene_list(beats, phrases)
    fb = {s["id"]: s.get("fallback", []) for s in scenes if s.get("fallback")}
    print(f"cue fallbacks (script mismatch risk): {fb or 'none'}")
    for s in scenes:
        print(f"  {s['id']:7s} {s['archetype']:14s} {s['t0']:6.2f}-{s['t1']:6.2f} cue={s['cue']} cues={s['cues']}")
    print("brief scenes:", len(brief["scenes"]), "| words:", len(joined.split()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
