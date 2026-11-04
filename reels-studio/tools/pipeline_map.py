#!/usr/bin/env python3
"""Generate docs/pipeline-stages.html from the code: stages, the tools each stage runs, preflight checks and the gates.

Nothing here is hand-written except the layout. Stage order comes from make_shorts.STAGES (read with ast), each
stage's description from its docstring, the tools it runs from the tools/*.py paths in its body, the preflight
checks from preflight.py, and the gates with their numbers from config/qa-thresholds.json and short_qa.

  python3 tools/pipeline_map.py            # writes docs/pipeline-stages.html
  python3 tools/pipeline_map.py --check    # exit 1 if the committed file is stale
"""
from __future__ import annotations

import argparse
import ast
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "pipeline-stages.html"
sys.path.insert(0, str(ROOT / "tools"))


def _module(name: str) -> ast.Module:
    return ast.parse((ROOT / "tools" / name).read_text(encoding="utf-8"))


def stage_order() -> list[str]:
    for node in _module("make_shorts.py").body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "STAGES" for t in node.targets):
            return [e.value for e in node.value.elts]
    raise SystemExit("STAGES not found in make_shorts.py")


def stage_functions() -> dict[str, ast.FunctionDef]:
    funcs = {}
    for node in _module("make_shorts.py").body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("stage_"):
            funcs[node.name[len("stage_"):]] = node
    return funcs


def tools_called(fn: ast.FunctionDef) -> list[str]:
    found = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for m in re.findall(r"tools/[A-Za-z0-9_./-]+\.py", node.value):
                if m not in found:
                    found.append(m)
    return found


def preflight_checks() -> list[str]:
    names = []
    for node in _module("preflight.py").body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("check_"):
            names.append(node.name[len("check_"):])
    return names


def preflight_phases() -> tuple[str, ...]:
    for node in _module("preflight.py").body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "PHASES" for t in node.targets):
            return tuple(e.value for e in node.value.elts)
    return ()


def gate_rows() -> list[dict]:
    import short_qa
    th = short_qa.load_thresholds()
    rows = []
    sample_brief = {"scenes": [{"id": "hook", "type": "image", "image": "x.jpg", "heading": "N 1",
                                "say": "One two three."}]}
    for r in short_qa.plan_results(sample_brief, th):
        rows.append({"stage": "plan (preflight)", "gate": r["gate"]})
    dummy = [("a", 0.1, 0.2)]
    for r in short_qa.timing_results(dummy, 40.0, th):
        rows.append({"stage": "video (fetch)", "gate": r["gate"]})
    for r in short_qa.picture_results([True], [True], float(th["frame_bin_s"]), th):
        rows.append({"stage": "video (fetch)", "gate": r["gate"]})
    limits = {
        "duration_est": f"{th['duration_s'][0]}-{th['duration_s'][1]} s",
        "duration": f"{th['duration_s'][0]}-{th['duration_s'][1]} s",
        "hook_anchor": "number or tool name, first 2 s",
        "hook_phrase": f"<= {th['hook_first_phrase_words_max']} words",
        "frame0_media": "tool media, not a text card",
        "cta_last_15pct": f"call word in last {round(th['cta_last_share'] * 100)}%",
        "visual_change_speech": f">= {round(th['visual_change_speech_share_min'] * 100)}% of speech time",
        "graphic_only_share": f"<= {round(th['graphic_only_share_max'] * 100)}% still",
        "static_scene_len": f"<= {th['static_scene_max_s']} s per static scene",
        "motion_gap": f"<= {th['motion_gap_max_s']} s still",
        "speech_wpm": f"{th['speech_wpm'][0]}-{th['speech_wpm'][1]} wpm",
        "longest_pause": f"<= {th['longest_pause_s']} s",
        "hook_speech_start": f"<= {th['hook_speech_start_max_s']} s",
        "hook_first_phrase_end": f"<= {th['hook_first_phrase_end_max_s']} s",
    }
    for row in rows:
        row["limit"] = limits.get(row["gate"], "")
    return rows


def build_html() -> str:
    th = json.loads((ROOT / "config" / "qa-thresholds.json").read_text(encoding="utf-8"))
    stages = stage_order()
    funcs = stage_functions()
    gates = gate_rows()
    checks = preflight_checks()
    phases = preflight_phases()
    cards = []
    for i, name in enumerate(stages, start=1):
        fn = funcs.get(name)
        doc = (ast.get_docstring(fn) or "").strip() if fn else ""
        tools = tools_called(fn) if fn else []
        tool_html = "".join(f"<li><code>{html.escape(t)}</code></li>" for t in tools) or "<li class=dim>no tool call</li>"
        cards.append(f"""
<div class="stage"><div class="num">{i}</div><div class="name">{html.escape(name)}</div>
<p>{html.escape(doc) or '<span class=dim>(no description)</span>'}</p><ul>{tool_html}</ul></div>""")
    arrows = "<div class='arrow'>&#8594;</div>".join(cards)
    gate_rows_html = "".join(
        f"<tr><td>{html.escape(g['stage'])}</td><td><code>{html.escape(g['gate'])}</code></td>"
        f"<td>{html.escape(g['limit'])}</td></tr>" for g in gates)
    check_html = "".join(f"<span class=chip>{html.escape(c)}</span>" for c in checks)
    phase_html = " &middot; ".join(html.escape(p) for p in phases)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Shorts pipeline: stages generated from code</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{font:15px/1.5 system-ui,sans-serif;margin:0;background:#0b1020;color:#e8ecf7}}
header{{padding:28px 32px 8px}} h1{{margin:0 0 4px;font-size:24px}} h2{{font-size:18px;margin:32px 32px 8px}}
.sub{{color:#9aa6c7}} .flow{{display:flex;flex-wrap:wrap;gap:6px;padding:12px 32px;align-items:stretch}}
.stage{{background:#151d33;border:1px solid #2c3a63;border-radius:12px;padding:14px;width:200px;min-height:210px}}
.num{{display:inline-block;background:#ff6b3d;color:#0b1020;border-radius:99px;width:24px;height:24px;text-align:center;font-weight:700;line-height:24px}}
.name{{font-weight:700;font-size:17px;margin:6px 0}} .stage p{{font-size:13px;color:#c4cde6;margin:4px 0 8px}}
.stage ul{{margin:0;padding-left:16px;font-size:12px}} .stage code{{color:#9fd3ff;word-break:break-all}}
.arrow{{align-self:center;font-size:22px;color:#ff6b3d;padding:0 2px}}
.dim{{color:#6f7aa0}} table{{border-collapse:collapse;margin:0 32px;width:calc(100% - 64px)}}
td,th{{border-bottom:1px solid #2c3a63;padding:6px 10px;text-align:left;font-size:13px}} th{{color:#9aa6c7}}
code{{font-family:ui-monospace,monospace}} .chip{{display:inline-block;background:#1d2a4d;border-radius:99px;padding:3px 10px;margin:3px;font-size:12px}}
.box{{margin:0 32px;background:#151d33;border-radius:12px;padding:14px 18px;color:#c4cde6;font-size:14px}}
footer{{padding:24px 32px;color:#6f7aa0;font-size:12px}}
</style></head><body>
<header><h1>Shorts pipeline: stages generated from code</h1>
<div class="sub">Generated by <code>tools/pipeline_map.py</code> from the code. Thresholds from <code>config/qa-thresholds.json</code>.
Gates apply to new batches only (brief flag <code>qa_gates</code>).</div></header>

<h2>Stages (make_shorts.py, in run order)</h2>
<div class="flow">{arrows}</div>

<h2>Preflight</h2>
<div class="box">Phases: {phase_html}<br>Checks: {check_html}</div>

<h2>Gates (numbers from config)</h2>
<table><tr><th>where</th><th>gate</th><th>limit</th></tr>{gate_rows_html}</table>

<h2>Config</h2>
<div class="box"><code>hashtags_per_platform</code> = {th['hashtags_per_platform']} &middot;
<code>frame_change_min</code> = {th['frame_change_min']} (uncalibrated: caveat 1 is open) &middot;
<code>cta_last_share</code> = {th['cta_last_share']}</div>

<footer>Re-generate after changing stages, checks or thresholds: <code>python3 tools/pipeline_map.py</code>.
Check for staleness: <code>python3 tools/pipeline_map.py --check</code>.</footer>
</body></html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if docs/pipeline-stages.html is out of date")
    args = ap.parse_args(argv)
    text = build_html()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("docs/pipeline-stages.html is stale: run python3 tools/pipeline_map.py")
            return 1
        print("docs/pipeline-stages.html is up to date")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
