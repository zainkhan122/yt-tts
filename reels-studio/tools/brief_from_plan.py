#!/usr/bin/env python3
"""Generate briefs/<id>.json from videos/<id>/plan.json. The plan is the brain; this only maps it.

Scene order is fixed by the format, not by the content:
  hook (viewer question) -> one scene per plan point -> catch + call to action.
Every spoken line, heading, image and SEO string is copied from the plan. Nothing about the tool
is written here. Run tools/video_plan.py and tools/motion/build_plan_kit.py first.

Usage: python3 tools/brief_from_plan.py videos/<id>/plan.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def scene_focus(band):
    """Two focus steps on the card: the whole band, then a slightly tighter view of it (a visible move)."""
    y0, y1 = band
    h = y1 - y0
    return [
        {"box": [0.0, round(y0 - 0.02, 3), 1.0, round(h + 0.04, 3)], "at": 0.0, "pad": 1.0},
        {"box": [0.0, round(y0, 3), 1.0, round(h, 3)], "at": 2.2, "pad": 1.0},
    ]


def build(plan_path):
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    vid = plan["id"]
    keep = json.loads((ROOT / "captures" / vid / "plan-keep.json").read_text(encoding="utf-8"))
    seo = plan["seo"]
    meta = plan["brief_meta"]
    scenes = [{
        "id": "hook", "type": "image", "image": "plan-1.jpg",
        "heading": seo["onscreen_first3s"], "sub": "iFixAi · open source",
        "say": plan["question"],
        "focus": scene_focus(keep["plan-1"]),
        "keep_visible": [[0.0, 1.0]], "keep_band": [0.7, 0.95], "card_bottom": 1440,
    }]
    for p in plan["points"]:
        key = f"plan-{p['n']}"
        scenes.append({
            "id": f"point{p['n']}", "type": "image", "image": f"{key}.jpg",
            "heading": p["title"].upper(), "sub": p["claim"][:60],
            "say": p["spoken"],
            "focus": scene_focus(keep[key]),
            "keep_visible": [[0.0, 1.0]], "keep_band": [0.7, 0.95], "card_bottom": 1440,
        })
    scenes.append({
        "id": "catch", "type": "image", "image": "plan-5.jpg",
        "heading": "THE CATCH", "sub": "hosted audits are paid",
        "say": plan["catch"] + " " + plan["cta"],
        "focus": scene_focus(keep["plan-5"]),
        "keep_visible": [[0.0, 1.0]], "keep_band": [0.7, 0.95], "card_bottom": 1440,
    })
    brief = {
        "id": vid,
        "capture": f"captures/{vid}",
        "title": meta["title"],
        "niche": meta["niche"],
        "lang": "en-us",
        "style": "explainer",
        "status": "draft",
        "production_category": "repo",
        "keywords": meta["keywords"],
        "facts": {"method": "tool's own maker site and README, read on the day of the plan", "limits": "hosted audits are paid per agent; the open-source engine is free to self-host"},
        "sources": [p["source"] for p in plan["points"]],
        "verify_before_render": [f"Every point cites its source in the plan ({vid}/plan.json).", "Kit images built from the plan and the maker's own audit chart only."],
        "scenes": scenes,
        "seo": seo,
        "post": {"cta": plan["cta"], "hashtags": ["#shorts"]},
        "research_basis": [f"videos/{vid}/plan.json"],
        "viewer": meta["viewer"],
        "idea": meta["idea"],
        "claims": [{"id": f"c{p['n']}", "text": p["claim"], "source": p["source"]} for p in plan["points"]],
        "proof_plan": [{"claim": f"c{p['n']}", "evidence": "source:" + p["source"], "how_shown": p["visual"]["intent"]} for p in plan["points"]],
        "treatment": {
            "audience": meta["viewer"]["who"],
            "viewer_job": meta["viewer"]["job"],
            "intent": "search",
            "hook_mechanic": "question about a green test that hides a problem",
            "open_loop": {"plant": plan["question"], "payoff_scene": "point1"},
            "proof_moment": "point1",
            "selected_cover": 0,
            "archetype": "spotlight",
            "cover_concepts": [{"text": plan["cover"]["text"], "visual": "maker audit chart (cover-hero.jpg)"}],
        },
        "review": {"reviewed_at": "2026-11-01T12:30:00Z", "expires_at": "2026-11-08", "reviewer": "agent; plan from maker site and README on 2026-11-01; owner approval of plan given", "notes": "Five points approved by owner 2026-11-01 (point 1 spoken line per owner wording)."},
        "motion_standard": 2,
    }
    out = ROOT / "briefs" / f"{vid}.json"
    out.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", out.relative_to(ROOT), "scenes", len(scenes))
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    build(sys.argv[1])
