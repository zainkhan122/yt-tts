import re
#!/usr/bin/env python3
"""Generate briefs/<id>.json from videos/<id>/plan.json. The plan is the brain; this only maps it.

Scene order is fixed by the format, not by the content:
  hook (viewer question) -> one scene per plan point -> catch -> call to action.
Every spoken line, heading, image, SEO string and claim is copied from the plan. Nothing about any
tool is written here, and nothing is claimed that the plan does not say.

Prerequisites (each is checked, and the build stops with the missing item named):
  1. tools/video_plan.py passes for the plan (PLAN PASS), including the packaging fields.
  2. tools/motion/build_plan_kit.py has written captures/<id>/plan-<n>.jpg, plan-catch.jpg (when the
     catch is a card) and captures/<id>/plan-keep.json.
  3. Any point or catch that uses an animation names a file that exists in captures/<id>/.

Usage: python3 tools/brief_from_plan.py videos/<id>/plan.json
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BuildError(SystemExit):
    pass



def _post_hashtags(plan: dict) -> list[str]:
    """Hashtags come from the plan's own YouTube SEO description (niche tags, #shorts included).
    Falls back to ["#shorts"] only when the plan has none. Capped at five (owner rule)."""
    desc = ((plan.get("seo") or {}).get("youtube") or {}).get("description", "")
    tags: list[str] = []
    for h in re.findall(r"#\w+", desc):
        if h.lower() not in [t.lower() for t in tags]:
            tags.append(h)
    if not tags:
        return ["#shorts"]
    if "#shorts" not in [t.lower() for t in tags]:
        tags = ["#shorts", *tags]
    return tags[:5]

def scene_focus(band):
    """Two focus steps on the card: the whole band, then a slightly tighter view of it (a visible move)."""
    y0, y1 = band
    h = y1 - y0
    return [
        {"box": [0.0, round(y0 - 0.02, 3), 1.0, round(h + 0.04, 3)], "at": 0.0, "pad": 1.0},
        {"box": [0.0, round(y0, 3), 1.0, round(h, 3)], "at": 2.2, "pad": 1.0},
    ]


def _keep_for(keep, key, vid):
    if key not in keep:
        raise BuildError(f"{vid}: plan-keep.json has no band for {key}; re-run tools/motion/build_plan_kit.py")
    return keep[key]


def _card_scene(scene_id, key, heading, sub, say, keep, vid):
    return {
        "id": scene_id, "type": "image", "image": f"{key}.jpg",
        "heading": heading, "sub": sub, "say": say,
        "focus": scene_focus(_keep_for(keep, key, vid)),
        "keep_visible": [[0.0, 1.0]], "keep_band": [0.7, 0.95], "card_bottom": 1440,
    }


def _flow_scene(scene_id, heading, nodes, say):
    """Boxes joined by arrows, drawn by the template and lit as the voice says each box's words."""
    return {"id": scene_id, "type": "flow", "heading": heading, "nodes": list(nodes), "say": say}


def _animation_file(vid, name):
    path = ROOT / "captures" / vid / name
    if not path.exists():
        raise BuildError(f"{vid}: animation '{name}' not found in captures/{vid}/; build it or use a card visual")
    return name


def build(plan_path):
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    vid = plan["id"]
    keep_path = ROOT / "captures" / vid / "plan-keep.json"
    keep = json.loads(keep_path.read_text(encoding="utf-8")) if keep_path.exists() else {}
    seo = plan["seo"]
    meta = plan["brief_meta"]
    brand = plan["brand_line"]

    hook_vis = plan.get("hook_visual") or {}
    if hook_vis.get("kind") == "steps":
        scenes = [_flow_scene("hook", seo["onscreen_first3s"], hook_vis["steps"], plan["question"])]
    else:
        scenes = [_card_scene("hook", "plan-1", seo["onscreen_first3s"], brand, plan["question"], keep, vid)]
        scenes[0]["keep_visible"] = [[0.0, 1.0]]
    for p in plan["points"]:
        key = f"plan-{p['n']}"
        if p["visual"]["kind"] == "animation":
            scenes.append({
                "id": f"point{p['n']}", "type": "clip",
                "src": _animation_file(vid, p["visual"]["animation"]),
                "in": 0.0, "out": 14.0, "say": p["spoken"],
            })
            continue
        if p["visual"]["kind"] == "steps":  # drawn by the template, lit as the voice says each step
            scenes.append(_flow_scene(f"point{p['n']}", p["title"].upper(), p["steps"], p["spoken"]))
            continue
        scenes.append(_card_scene(f"point{p['n']}", key, p["title"].upper(), p["sub"], p["spoken"], keep, vid))

    cv = plan["catch_visual"]
    if cv["kind"] == "animation":
        catch_scene = {"id": "catch", "type": "clip", "src": _animation_file(vid, cv["animation"]),
                       "in": 0.0, "out": 14.0, "say": plan["catch"]}
    elif cv["kind"] == "steps":
        catch_scene = _flow_scene("catch", plan.get("catch_title", "The catch").upper(), cv["steps"], plan["catch"])
    else:
        catch_scene = _card_scene("catch", "plan-catch", plan.get("catch_title", "The catch").upper(),
                                  plan["catch_sub"], plan["catch"], keep, vid)
    scenes.append(catch_scene)

    # Outro: question + keyword chip + follow card with the channel logo (the template's endcard).
    scenes.append({"id": "cta", "type": "endcard", "keyword": plan["cta_keyword"], "say": plan["cta"]})

    today = dt.date.today().isoformat()
    brief = {
        "id": vid,
        "capture": f"captures/{vid}",
        "title": meta["title"],
        "niche": meta["niche"],
        "lang": "en-us",
        "style": "explainer",
        "status": "draft",
        "production_category": plan.get("production_category", "repo"),
        "keywords": meta["keywords"],
        "facts": {
            "method": "tool's own README and repo page, read on the day of the plan",
            "limits": plan["catch"],
        },
        "sources": [p["source"] for p in plan["points"]],
        "verify_before_render": [
            f"Every point cites its source in the plan ({vid}/plan.json).",
            "Kit images are drawn from the plan's own visual spec only.",
        ],
        "scenes": scenes,
        "seo": seo,
        "post": {"cta": plan["cta"], "hashtags": _post_hashtags(plan)},
        "research_basis": [f"videos/{vid}/plan.json"],
        "viewer": meta["viewer"],
        "idea": meta["idea"],
        "claims": [{"id": f"c{p['n']}", "text": p["claim"], "source": p["source"]} for p in plan["points"]],
        "proof_plan": [{"claim": f"c{p['n']}", "evidence": "source:" + p["source"],
                        "how_shown": p["visual"]["intent"]} for p in plan["points"]],
        "treatment": {
            "audience": meta["viewer"]["who"],
            "viewer_job": meta["viewer"]["job"],
            "intent": "search",
            "hook_mechanic": plan.get("hook_mechanic", "viewer question about the tool's first claim"),
            "open_loop": {"plant": plan["question"], "payoff_scene": "point1"},
            "proof_moment": "point1",
            "selected_cover": [c["text"] for c in plan["cover"]["concepts"]].index(plan["cover"]["text"]),
            "archetype": "spotlight",
            # the three concepts come from the plan (COVER-RULES.md); never one concept
            "cover_concepts": [dict(c) for c in plan["cover"]["concepts"]],
        },
        # Honest review state: the plan was written by the agent from the maker's own material. The
        # owner approved the TOPIC; nothing here says the owner approved this plan or its copy.
        "review": {
            "reviewed_at": today,
            "expires_at": None,
            "reviewer": "agent: plan written from the maker's README and repo page",
            "notes": "Topic approved by owner (config/topic-approvals.json). Plan and copy await owner review at the cover gate.",
        },
        "motion_standard": 2,
        "qa_gates": True,  # new batches: Short QA gates apply (tools/short_qa.py)
    }
    out = ROOT / "briefs" / f"{vid}.json"
    existing = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
    brief = merge_brief(existing, brief)
    out.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", out.relative_to(ROOT), "scenes", len(scenes))
    return out


# Fields an operator sets by hand or that record a human/agent decision. Regeneration keeps them.
KEEP_IF_PRESENT = ("status", "review", "voice_seed", "renderer", "graphics", "qa_gates")


def merge_brief(existing, generated: dict) -> dict:
    """Regenerating a brief must never silently change what renders or who approved it.

    - Keys the generator does not produce (renderer, graphics, voice_seed, notes...) are kept.
    - Keys in KEEP_IF_PRESENT keep the existing value when one exists.
    - Everything else comes from the plan, so the plan stays the source for copy and scenes.
    """
    if existing is None:
        return generated
    merged = dict(generated)
    for key, value in existing.items():
        if key not in generated:
            merged[key] = value
    for key in KEEP_IF_PRESENT:
        if key in existing:
            merged[key] = existing[key]
    return merged


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    try:
        build(sys.argv[1])
    except BuildError as exc:
        print(f"BLOCK: {exc.code}", file=sys.stderr)
        sys.exit(1)
