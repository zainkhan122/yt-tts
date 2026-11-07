"""Spec: repo-sand3d-01 · Sandflow-ai/sand3d (topic #7, radar 2026-11-07)."""

REPO = "https://github.com/Sandflow-ai/sand3d"

# Voice pace/lead: measured wpm and hook-start gates (short_qa video) — every Short must PASS.
BRIEF_EXTRA = {"speed": 1.28, "lead_in": 0.06}

PLAN = {
    "id": "repo-sand3d-01",
    "tool": "sand3d",
    "question": "Can an LLM do 3D modeling?",
    "hook_visual": {
        "kind": "steps",
        "intent": "a prompt becoming short code, and that code becoming a printable object",
        "steps": ["Ask for a part", "Code builds it"],
    },
    "points": [
        {
            "n": 1,
            "claim": "sand3d is a Python library for writing 3D objects as short programs over Blender's bpy module.",
            "spoken": "It's a Python library that writes three-dimensional objects as short programs on top of Blender.",
            "source": REPO,
            "source_note": "README: 'sand3d is a Python library for writing 3D objects as short programs: profiles, solids, edits, frames, joints and assemblies, over Blender's bpy.'",
            "visual": {"kind": "steps", "intent": "python lines building a named part in Blender"},
            "title": "Parts as programs",
            "sub": "Short Python, built on Blender.",
            "steps": ["import sand3d", "Name the part", "Export the mesh"],
        },
        {
            "n": 2,
            "claim": "A part takes two to six times fewer tokens than in Blender Python or CadQuery, and the whole API fits in a prompt.",
            "spoken": "A part takes two to six times fewer tokens than the same part in Blender Python or CadQuery, and the whole API fits in a prompt.",
            "source": REPO,
            "source_note": "README: 'Short. A part takes 2 to 6× fewer tokens than the same part in Blender Python, CadQuery or FeatureScript'; 'The whole API fits in a prompt, about 3,600 tokens'.",
            "visual": {"kind": "steps", "intent": "the token count falling and the API fitting in one prompt"},
            "title": "Small enough for a prompt",
            "sub": "Fewer tokens than Blender Python.",
            "steps": ["Two to six times fewer", "API in about 3,600 tokens", "Named parts, not coordinates"],
        },
        {
            "n": 3,
            "claim": "Parts, edges and faces are reached by name, and the same program builds the same mesh every time.",
            "spoken": "Every part, edge and face is reached by name, and the same program builds the same mesh every time.",
            "source": REPO,
            "source_note": "README: 'Named, not computed. Parts, edges and faces are reached by name, never by hand-computed coordinates.'; 'Deterministic. The same program builds the same mesh, bit for bit.'",
            "visual": {"kind": "steps", "intent": "named parts and a repeatable build"},
            "title": "Named, and repeatable",
            "sub": "Same program, same mesh.",
            "steps": ["Parts reached by name", "Edges and faces by name", "Same mesh every time"],
        },
        {
            "n": 4,
            "claim": "One call exports GLB, URDF, USD, OBJ or STL, and the washing machine example is 38 lines with four joints.",
            "spoken": "It exports GLB, URDF, USD, OBJ or STL, and a washing machine example is thirty-eight lines with four joints.",
            "source": REPO,
            "source_note": "README: 'Export: GLB, URDF, USD, OBJ, STL'; 'A front-loading washing machine in 38 lines of code'; 'four joints that say how they move'.",
            "visual": {"kind": "steps", "intent": "the export formats and the jointed washing machine example"},
            "title": "Straight to a file",
            "sub": "GLB, URDF, USD, OBJ or STL.",
            "steps": ["GLB for the web", "URDF for robots", "STL for printing"],
        },
    ],
    "catch": "The catch: it needs Blender's bpy module, which only ships for certain Python versions, so check yours first.",
    "catch_sub": "bpy has no wheel for every Python or Intel Mac.",
    "catch_title": "The catch",
    "catch_visual": {
        "kind": "steps",
        "intent": "the Python versions bpy supports and the Intel Mac exception",
        "steps": ["Needs Blender's bpy", "Python 3.13 or 3.11", "Intel Macs use 3.11"],
    },
    "brand_line": "sand3d · code-first CAD",
    "cover": {
        "text": "A MODEL FROM CODE",
        "visual": "designed graphic of Python lines turning into an isometric part with named faces",
        "concepts": [
            {
                "id": "c1", "layout": "bleed", "text": "A MODEL FROM CODE",
                "media": {"kind": "designed", "file": "cover-c1.png",
                          "design": "Full-bleed isometric plate drawing of a bracket with two holes, its faces tagged with name labels, and code lines running behind the headline."},
            },
            {
                "id": "c2", "layout": "window", "text": "LLM WRITES THE PART",
                "media": {"kind": "designed", "file": "cover-c2.png",
                          "design": "Framed code window with the bracket program and its export line, and the rendered part sitting beside the window."},
            },
            {
                "id": "c3", "layout": "split", "text": "PRINT WHAT IT BUILDS",
                "media": {"kind": "designed", "file": "cover-c3.png",
                          "design": "Split plate: a jointed washing-machine silhouette made of named blocks on top, and the export format chips underneath."},
            },
        ],
    },
    "cta": "What would you model first? Comment MESH and I'll pin it.",
    "cta_keyword": "MESH",
    "seo": {
        "onscreen_first3s": "3D MODELING FOR LLMS",
        "keyword": "3D modeling",
        "aliases": ["Python 3D modeling", "LLM 3D modeling", "code CAD for Blender"],
        "youtube": {
            "title": "3D modeling: sand3d writes parts as Python code",
            "description": (
                "Python 3D modeling that fits in a prompt: sand3d writes solids as short programs over Blender, with parts, "
                "edges and faces reached by name instead of computed coordinates, and the same program always building the "
                "same mesh. One call exports GLB, URDF, USD, OBJ or STL, and the repo's washing machine example is thirty-eight "
                "lines with four joints. Repo: https://github.com/Sandflow-ai/sand3d "
                "#Shorts #Python3DModeling #Blender #CAD #AIAgents"
            ),
            "tags": ["3D modeling", "Python 3D modeling", "LLM 3D modeling",
                     "code CAD for Blender", "sand3d", "procedural modeling"],
            "hashtags": ["#Shorts", "#Python3DModeling", "#Blender", "#CAD", "#AIAgents"],
        },
        "tiktok": {
            "caption": "3D modeling for LLMs: sand3d writes a part as a short program, names every face, and exports GLB or STL. Comment MESH for the repo.",
            "hashtags": ["#Python3DModeling", "#Blender", "#CAD", "#AIAgents", "#Maker"],
        },
        "instagram": {
            "caption": "3D modeling on top of Blender: sand3d takes short programs instead of coordinate math, names every part, and exports GLB, URDF or STL. Comment MESH for the repo.",
            "hashtags": ["#Python3DModeling", "#Blender", "#CAD", "#AIAgents", "#Maker"],
        },
        "facebook": {
            "caption": "3D modeling built for LLMs: sand3d writes parts as short programs over Blender, reaches faces by name, and exports GLB, URDF or STL. Comment MESH for the repo link.",
            "hashtags": ["#Python3DModeling", "#Blender", "#CAD", "#AIAgents", "#Maker"],
        },
        "x": {
            "text": "3D modeling for LLMs: sand3d writes a part as a short program over Blender, names every face, and exports GLB, URDF or STL.",
            "hashtags": ["#Python3DModeling", "#Blender"],
        },
    },
    "brief_meta": {
        "title": "sand3d: 3D parts written as short Python programs",
        "niche": "AI tools",
        "keywords": ["3D modeling", "code CAD", "Blender automation", "LLM CAD"],
        "idea": "sand3d lets an LLM write 3D objects as short Python programs that export to GLB, URDF, USD, OBJ or STL.",
        "viewer": {
            "who": "makers and engineers who want an LLM to produce real 3D parts",
            "problem": "Blender scripts are long and coordinate-heavy for a model to write",
            "job": "decide whether program-first CAD is a workable path to a printable part",
        },
    },
}

FEATURES = {
    "tool": {"name": "sand3d", "repo": REPO},
    "features": [
        {"id": "f1", "title": "3D objects as short programs",
         "what": "Parts, solids, edits and assemblies are written as Python over bpy.",
         "evidence_quote": "sand3d is a Python library for writing 3D objects as short programs: profiles, solids, edits, frames, joints and assemblies, over Blender's bpy."},
        {"id": "f2", "title": "Few tokens per part",
         "what": "A part costs two to six times fewer tokens than in Blender Python or CadQuery.",
         "metric": {"value": 6, "unit": "x fewer tokens"},
         "evidence_quote": "Short. A part takes 2 to 6× fewer tokens than the same part in Blender Python, CadQuery or FeatureScript"},
        {"id": "f3", "title": "Named, not computed",
         "what": "Parts, edges and faces are addressed by name, never by coordinates.",
         "evidence_quote": "Named, not computed. Parts, edges and faces are reached by name, never by hand-computed coordinates."},
        {"id": "f4", "title": "Deterministic builds",
         "what": "The same program produces the same mesh, bit for bit.",
         "evidence_quote": "Deterministic. The same program builds the same mesh, bit for bit."},
        {"id": "f5", "title": "Exports real formats",
         "what": "One call writes GLB, URDF, USD, OBJ or STL named by the file extension.",
         "evidence_quote": "One call; the file's extension names the format; lengths in metres."},
        {"id": "f6", "title": "Whole API in a prompt",
         "what": "The documented API fits in a prompt at about 3,600 tokens.",
         "metric": {"value": 3600, "unit": "tokens"},
         "evidence_quote": "The whole API fits in a prompt, about 3,600 tokens"},
        {"id": "f7", "title": "bpy version limits", "risk": True,
         "what": "Blender's bpy module only ships for some Python versions and some Macs.",
         "evidence_quote": "bpy has no wheel for Python 3.12, nor for Intel Macs from 5.2 on: there, use Python 3.11."},
    ],
    "risks": [{"id": "r1", "text": "It depends on Blender's bpy module, so the Python version and the machine both matter."},
              {"id": "r2", "text": "There are no category verbs: a chair or a table is a program you write in sand3d."}],
    "source_urls": [REPO],
}

BEATS = {
    "tool": "sand3d",
    "handle": "@hypeless",
    "scenes": [
        {"scene_id": "hook", "phrase": 0, "archetype": "flow_link", "headline": "3D MODELING FOR LLMS",
         "feature_id": "f1", "depicts": "a model written by an LLM that you can print",
         "payload": {"nodes": ["Ask for a part", "Code builds it"], "edge_label": "print it",
                     "cue_phrases": ["Can an LLM", "do 3D modeling"]},
         "cue_word": "modeling"},
        {"scene_id": "point1", "phrase": 1, "archetype": "terminal_type", "headline": "PARTS AS PROGRAMS",
         "feature_id": "f1", "depicts": "the python lines that build a named part",
         "payload": {"title": "part.py",
                     "lines": ["import sand3d as s3d", "plate = s3d.extrude(...)", "s3d.export(plate, \"b.glb\")"],
                     "cue_phrases": ["It's sand3d", "a Python library", "on top of Blender"]},
         "cue_word": "Python"},
        {"scene_id": "point2", "phrase": 2, "archetype": "chip_grid", "headline": "SMALL ENOUGH FOR A PROMPT",
         "feature_id": "f2", "depicts": "the token count and the whole API fitting in a prompt",
         "payload": {"chips": ["Fewer tokens per part", "API fits in a prompt", "Fewer than CadQuery"], "highlight": 1,
                     "cue_phrases": ["two to six times fewer tokens", "Blender Python or CadQuery", "whole API fits in a prompt"]},
         "cue_word": "tokens"},
        {"scene_id": "point3", "phrase": 3, "archetype": "toggle_steps", "headline": "NAMED, AND REPEATABLE",
         "feature_id": "f3", "depicts": "parts reached by name and the same mesh every time",
         "payload": {"steps": ["Parts reached by name", "Edges and faces by name", "Same mesh every time"], "done": 3,
                     "cue_phrases": ["reached by name", "same program builds", "same mesh every time"]},
         "cue_word": "name"},
        {"scene_id": "point4", "phrase": 4, "archetype": "concept_card", "headline": "ONE CALL TO A FILE",
         "feature_id": None, "depicts": "the export formats and the jointed washing machine",
         "payload": {"big": "GLB, URDF, USD, OBJ, STL", "sub": "A washing machine in thirty-eight lines."},
         "cue_word": "exports"},
        {"scene_id": "catch", "phrase": 5, "archetype": "chip_grid", "headline": "THE CATCH",
         "feature_id": "f7", "depicts": "the bpy module and the Python versions it needs",
         "payload": {"chips": ["Needs Blender's bpy", "Python versions matter", "Intel Macs need an older one"], "highlight": 0,
                     "cue_phrases": ["needs Blender's bpy module", "only ships for certain Python versions", "check yours first"]},
         "cue_word": "catch"},
        {"scene_id": "cta", "phrase": 6, "archetype": "endcard", "headline": "WHAT WOULD YOU MODEL?",
         "feature_id": None, "depicts": "commenting the keyword MESH to get the repo",
         "payload": {"keyword": "MESH", "follow": "Follow"},
         "cue_word": "MESH"},
    ],
}
