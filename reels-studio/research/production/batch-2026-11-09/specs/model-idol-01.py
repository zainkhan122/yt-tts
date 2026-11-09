"""Spec: model-idol-01 · idol — one photo in, a 3D Gaussian splat out (owner-approved rewrite 2026-11-08).

Rewrite approved by the owner: user-first register from SCRIPT-AUDIT (situation hook, you-as-subject,
consequence clauses, one boundary as a sentence inside the payoff, one spoken copyable action, comment CTA).
Both beats the owner fixed by hand — the photo↔3D split view, and the background-cut → .ply → Blender flow —
are built as NEW archetypes of this tool's own template (split_view, blender_handoff), proved by motion.

Claims: only what the model card / lab table states; the benchmark is attributed to the lab on screen.
The spoken script never names where the topic was found.
"""

MODEL = "https://huggingface.co/speridlabs/idol"

BRIEF_EXXXTRA = {"voice_tempo": 1.15, "copyable_action": "python -m idol.sample --image photo.jpg --mode real", "tail": 2.0}

PLAN = {
    "template": "photo-to-3d",
    "id": "model-idol-01",
    "tool": "idol",
    "question": "You shoot one photo for the product page — but can your buyer turn it around?",
    "hook_visual": {
        "kind": "steps",
        "intent": "flat product photos the buyer can only see from one angle, cut into a spinnable object",
        "steps": ["one flat photo", "and then it spins"],
    },
    "points": [
        {
            "n": 1,
            "claim": "idol turns a single picture of an object into a full three-D Gaussian splat, including the sides the picture never showed, in about two seconds.",
            "spoken": "Drop one photo into idol — you pull out a full three-D model you can turn with your mouse. Even the sides your camera never saw are drawn in. In about two seconds.",
            "source": MODEL,
            "source_note": "Model card: 'Idol turns one picture of an object into a 3D Gaussian splat… including the sides the picture never showed' + 'can run in under 2 seconds'.",
            "visual": {"kind": "steps", "intent": "photo beside its live 3D, cursor drags it around", "steps": ["photo in", "3D out", "drag with the mouse"]},
            "rows": ["one photo in", "sides the camera missed", "about two seconds"],
            "title": "PHOTO IN, 3D OUT",
            "sub": "Turn it with a mouse.",
            "steps": ["photo in", "3D out", "turn with mouse"],
        },
        {
            "n": 2,
            "claim": "The pipeline removes the background, frames the object, and writes a standard 3DGS .ply that opens in Blender — no studio or turntable.",
            "spoken": "No studio, no turntable. It cuts the background, frames the object, and hands you a file that opens in Blender — so you drag it straight onto the product page or into a game.",
            "source": MODEL,
            "source_note": "Model card: 'it removes the background, frames the object and generates up to 1,048,576 Gaussians, written as a standard 3DGS .ply' — .ply opens in any Gaussian-splat viewer (Blender reads .ply).",
            "visual": {"kind": "steps", "intent": "background stripped off the same object, .ply into a Blender window", "steps": ["background cut", "open in Blender", "drag into your page"]},
            "title": "STRAIGHT INTO BLENDER",
            "sub": "No studio, no turntable.",
            "steps": ["background cut", "open in Blender", "drag into your page"],
        },
        {
            "n": 3,
            "claim": "It runs on your own consumer GPU — 7.2 GB VRAM — with no cloud call or waitlist.",
            "spoken": "Your own graphics card runs it — about seven gigabytes. No cloud call, no waitlist.",
            "source": MODEL,
            "source_note": "Model card: 'It runs on consumer GPUs, using 7.2 GB of VRAM and can run in under 2 seconds.' Cloud-free reading: it's a local SDK run.",
            "visual": {"kind": "steps", "intent": "gauge on your card, no cloud chips", "steps": ["your GPU", "no cloud", "no waitlist"]},
            "title": "YOUR GPU, NOT THE CLOUD",
            "sub": "About seven gigabytes.",
            "steps": ["your GPU", "no cloud", "no waitlist"],
        },
        {
            "n": 4,
            "claim": "Try it free in the browser demo, or run one command on your own machine.",
            "spoken": "Or type one command on your own machine — python idol sample, photo.jpg — and your first model is a file you already have.",
            "source": MODEL,
            "source_note": "Model card demo badge -> huggingface.co/spaces/speridlabs/idol; SDK: pip install -e . + python -m idol.sample --image photo.jpg --mode real.",
            "visual": {"kind": "steps", "intent": "the free demo door, then the command typing itself", "steps": ["browser demo", "one command"]},
            "chips": ["free browser demo", "python -m idol.sample"],
            "title": "ONE COMMAND",
            "sub": "Demo first, or your machine.",
            "steps": ["browser demo", "one command"],
        },
        {
            "n": 5,
            "claim": "On the lab's own benchmark it edges TripoSplat and TRELLIS on every visual column, and it was the number-one trending model on Hugging Face today.",
            "spoken": "On the lab's own tests it beat both big image-to-three-D tools on every visual score — and it was the top trending model today.",
            "source": MODEL,
            "source_note": "Benchmark table: Idol bold in SSIM, LPIPS, IoU, DINOv2, CLIP, sharpness distance vs TripoSplat/TRELLIS. HF trending #1, score ~765 on 2026-11-08.",
            "visual": {"kind": "steps", "intent": "bars with idol on top, trending badge", "steps": ["every visual score", "top trending"]},
            "title": "PROOF ON ITS OWN TESTS",
            "sub": "Visual scores: idol on top.",
            "steps": ["every visual score", "top trending"],
        },
    ],
    "catch": "One boundary: it makes single objects — your sneaker, your mug, your product — not whole rooms. Everything your photo shows, you still get.",
    "catch_sub": "One object per picture.",
    "catch_title": "One boundary",
    "catch_visual": {
        "kind": "steps",
        "intent": "single objects only, stated plainly",
        "steps": ["single objects, not rooms", "you keep every angle you shot"],
    },
    "brand_line": "idol · one photo to 3D",
    "cover": {
        "text": "PHOTO IN, 3D OUT",
        "visual": "a plain product photo on the left, the same object as a spun Gaussian splat on the right",
        "concepts": [
            {
                "id": "c1", "layout": "split", "text": "PHOTO IN, 3D OUT",
                "media": {"kind": "designed", "file": "cover-c1.png",
                          "design": "Paper plate split down the middle: left a flat fabricated product photo of a sneaker, right the same sneaker as a violet Gaussian-splat object with orbit ticks, headline across the divider."},
            },
            {
                "id": "c2", "layout": "window", "text": "PHOTO IN, SPLAT OUT",
                "media": {"kind": "designed", "file": "cover-c2.png",
                          "design": "A fabricated demo-page window: photo chip on the left rail, violet 3D blob with rotation arrows in the middle, .ply file card on the right, headline along the top."},
            },
            {
                "id": "c3", "layout": "bleed", "text": "PHOTO TO 3D, FAST",
                "media": {"kind": "designed", "file": "cover-c3.png",
                          "design": "Full-bleed paper with a giant '2s' chip, a VRAM bar at 7.2 GB, and a small violet splat orbiting in the corner."},
            },
        ],
    },
    "cta": "So skip the reshoot. Comment IDOL and I'll pin the link.",
    "cta_keyword": "IDOL",
    "seo": {
        "onscreen_first3s": "ONE PHOTO, NOW 3D",
        "keyword": "image to 3D",
        "aliases": ["photo to 3D model", "Gaussian splat", "idol model", "3D from one image"],
        "youtube": {
            "title": "Image to 3D in 2 seconds: idol turns one photo into a spinnable model",
            "description": (
                "Drop one product photo into idol and you get a full 3D Gaussian splat you can turn around with your "
                "mouse — even the sides the camera never saw. Background cut, standard 3DGS .ply that opens in Blender "
                "or any splat viewer, on your own GPU (7.2 GB VRAM, under 2 s): "
                "python -m idol.sample --image photo.jpg --mode real. Model: "
                "https://huggingface.co/speridlabs/idol #Shorts #ImageTo3D #GaussianSplat #3DAI"
            ),
            "tags": ["image to 3D", "photo to 3D model", "Gaussian splat", "idol model", "3D AI",
                     "single image 3D", "Hugging Face"],
            "hashtags": ["#Shorts", "#ImageTo3D", "#GaussianSplat", "#AI3D", "#Blender"],
        },
        "tiktok": {
            "caption": "Image to 3D — one product photo becomes a spinnable 3D model: background cut, .ply out, your own GPU. Comment IDOL for the link.",
            "hashtags": ["#ImageTo3D", "#GaussianSplat", "#AI3D", "#Blender", "#AITools"],
        },
        "instagram": {
            "caption": "Image to 3D with idol: one photo becomes a model you can spin with the mouse — even the sides the camera never saw. Comment IDOL for the link.",
            "hashtags": ["#ImageTo3D", "#GaussianSplat", "#Blender", "#AI3D", "#AITools"],
        },
        "facebook": {
            "caption": "Image to 3D: one product photo in, a spinnable model out — on your own GPU, about two seconds. Comment IDOL for the link.",
            "hashtags": ["#ImageTo3D", "#GaussianSplat", "#AI3D", "#Blender", "#Sneakerheads"],
        },
        "x": {
            "text": "Image to 3D from one photo: idol turns a single product shot into a model your buyers can spin — about 2 seconds on your own GPU.",
            "hashtags": ["#ImageTo3D", "#GaussianSplat"],
        },
    },
    "brief_meta": {
        "title": "idol: one photo becomes a 3D model",
        "niche": "AI tools",
        "keywords": ["image to 3D", "photo to 3D model", "Gaussian splat", "idol model"],
        "idea": "Drop one product photo into idol and you pull out a spinnable 3D model — no studio, your own GPU, one command.",
        "viewer": {
            "who": "shop owners, makers, 3D-curious builders with a flat product photo",
            "problem": "a buyer can't see the object from behind — and a 3D version usually means a scanner or a modeller",
            "job": "believe one photo can give a spinnable model, and know exactly what to click tonight",
        },
    },
}

FEATURES = {
    "tool": {"name": "idol", "repo": MODEL},
    "features": [
        {"id": "f1", "title": "One picture to a 3D Gaussian splat",
         "what": "A render, a generated image or a photo becomes a 3D Gaussian splat.",
         "evidence_quote": "Idol turns one picture of an object into a 3D Gaussian splat."},
        {"id": "f2", "title": "Even the hidden sides",
         "what": "Up to 1,048,576 Gaussians, including sides the picture never showed.",
         "evidence_quote": "generates up to 1,048,576 Gaussians, written as a standard 3DGS `.ply`"},
        {"id": "f3", "title": "Background cut, object framed",
         "what": "The pipeline isolates the object before reconstructing it.",
         "evidence_quote": "it removes the background, frames the object"},
        {"id": "f4", "title": "Runs on consumer GPUs",
         "what": "7.2 GB of VRAM; can run in under 2 seconds.",
         "evidence_quote": "It runs on consumer GPUs, using 7.2 GB of VRAM and can run in under 2 seconds."},
        {"id": "f5", "title": "Standard .ply out",
         "what": "The file opens in any Gaussian-splat viewer or Blender.",
         "evidence_quote": "written as a standard 3DGS `.ply`"},
        {"id": "f6", "title": "Free Space demo + open SDK",
         "what": "A Hugging Face Space demo, and `pip install -e .` for the SDK with one Python call.",
         "evidence_quote": "`pip install -e .`"},
        {"id": "f7", "title": "Photo mode and render mode",
         "what": "`--mode real` for photographs, `--mode synthetic` for renders of a single object.",
         "evidence_quote": "`--mode real` for photographs"},
        {"id": "f8", "title": "Benchmark edges TripoSplat and TRELLIS",
         "what": "Bold in SSIM, LPIPS, IoU, DINOv2, CLIP and sharpness distance on the lab's table.",
         "evidence_quote": "TripoSplat and TRELLIS lose every visual column"},
        {"id": "f9", "title": "Exact command you can copy",
         "what": "One line turns a photo into a .ply on your own machine.",
         "evidence_quote": "python -m idol.sample --image photo.jpg --mode real"},
        {"id": "f10", "title": "Two encoders are gated", "risk": True,
         "what": "Accept terms once on DINOv3 and FLUXXX.2 before the SDK will run.",
         "evidence_quote": "it reads input through two gated models"},
    ],
    "risks": [{"id": "r1", "text": "Your own runs need an NVIDIA GPU with CUDA (the free Space demo needs no GPU)."},
              {"id": "r2", "text": "Built for single objects — it frames one object per picture, not scenes."}],
    "source_urls": [MODEL, "https://huggingface.co/spaces/speridlabs/idol"],
}

BEATS = {
    "tool": "idol",
    "template": "photo-to-3d",
    "handle": "@hypeless",
    "scenes": [
        {"scene_id": "hook", "phrase": 0, "archetype": "photo_splat", "headline": "ONE PHOTO ISN'T ENOUGH",
         "feature_id": "f1", "depicts": "flat product photos, then the object spinning",
         "payload": {
             "eyebrow": "IMAGE TO 3D",
             "accent_word": "FLAT",
             "label": "ONE PHOTO \u2192 3D",
             "photos": [
                 {"name": "sneaker.jpg", "tag": "PRODUCT PHOTO", "caption": "front view \u00b7 flat", "shape": "sneaker"},
                 {"name": "mug.jpg", "tag": "PRODUCT PHOTO", "caption": "one angle only", "shape": "mug"},
             ],
             "splat": {"name": "sneaker.ply", "count": "1,048,576 GAUSSIANS",
                       "caption": "every side \u00b7 opens anywhere", "badge": "FULL 3D", "seed": 9102, "shape": "sneaker"},
             "cue_phrases": ["one photo", "product page", "from behind"],
         }},
        {"scene_id": "point1", "phrase": 1, "archetype": "split_view", "headline": "PHOTO \u21c4 SPIN",
         "feature_id": "f1", "depicts": "photo beside its live 3D; a cursor drags it around",
         "payload": {
             "eyebrow": "PHOTO IN, 3D OUT",
             "accent_word": "MOUSE",
             "photo": {"name": "sneaker.jpg", "tag": "ONE PHOTO", "caption": "flat", "shape": "sneaker"},
             "splat": {"name": "sneaker.ply", "count": "made from it",
                       "caption": "drag it with the mouse", "badge": "\u2248 2 S", "seed": 4211, "shape": "sneaker"},
             "chips": ["turn with your mouse", "sides drawn in", "about two seconds"],
             "cue_phrases": ["drop that photo", "turn around with your mouse", "never saw", "two seconds"],
         }},
        {"scene_id": "point2", "phrase": 2, "archetype": "blender_handoff", "headline": "STRAIGHT INTO BLENDER",
         "feature_id": "f5", "depicts": "same object, background stripped; .ply lands in a Blender window",
         "payload": {
             "eyebrow": "NO STUDIO",
             "accent_word": "BLENDER",
             "photo": {"name": "sneaker.jpg", "tag": "THE SAME PHOTO", "caption": "cut, framed", "shape": "sneaker"},
             "file": {"name": "sneaker.ply", "kind": "3DGS"},
             "app": {"name": "Blender", "title": "Blender \u00b7 layout"},
             "steps": ["cut the background", "file opens in Blender", "use it in a page or game"],
             "cue_phrases": ["no studio", "cuts the background", "blender", "product page"],
         }},
        {"scene_id": "point3", "phrase": 3, "archetype": "gpu_gauge", "headline": "YOUR GPU, NOT THE CLOUD",
         "feature_id": "f4", "depicts": "the VRAM gauge fills; no-cloud chips",
         "payload": {
             "eyebrow": "ON YOUR MACHINE",
             "accent_word": "YOURS",
             "vram": 7.2, "gauge_cap": 24,
             "chips": ["your card runs it", "no cloud call", "no waitlist", "\u2248 7 GB"],
             "chip_subs": ["consumer cards run it", "the file is yours", "no queue, no account", "VRAM peak, per the lab"],
             "cue_phrases": ["graphics card", "seven gigabytes", "no cloud", "waitlist"],
         }},
        {"scene_id": "point4", "phrase": 4, "archetype": "two_doors", "headline": "ONE COMMAND",
         "feature_id": "f9", "depicts": "free demo door, then the command typing itself",
         "payload": {
             "eyebrow": "TRY IT",
             "accent_word": "ONE",
             "doors": [
                 {"title": "Free demo first", "sub": "Drop a photo in the browser, get the model.",
                  "line": "drop photo \u2192 get .ply"},
                 {"title": "On your machine", "sub": "One command turns a photo into a file.",
                  "line": "python -m idol.sample --image photo.jpg"},
             ],
             "cue_phrases": ["one command", "own machine", "a file you already have"],
         }},
        {"scene_id": "point5", "phrase": 5, "archetype": "leaderboard", "headline": "PROOF ON ITS OWN TESTS",
         "feature_id": None, "depicts": "idol's row wins every visual score, trending badge",
         "payload": {
             "eyebrow": "PROOF",
             "accent_word": "every",
             "badge": "TOP TRENDING TODAY",
             "rows": [
                 {"name": "idol", "score": 0.97, "val": "0.726 SSIM", "win": True},
                 {"name": "TRELLIS", "score": 0.72, "val": "0.716 SSIM"},
                 {"name": "TripoSplat", "score": 0.68, "val": "0.712 SSIM"},
                 {"name": "LGM", "score": 0.60, "val": "0.722 SSIM"},
             ],
             "cue_phrases": ["own tests", "every visual score", "top trending"],
         }},
        {"scene_id": "catch", "phrase": 6, "archetype": "expect_rows", "headline": "ONE BOUNDARY",
         "feature_id": "f10", "depicts": "single objects only, one honest row",
         "payload": {
             "eyebrow": "ONE BOUNDARY",
             "rows": [
                 {"kind": "tag", "t": "Single objects, not rooms", "s": "a sneaker, a mug, a product"},
                 {"kind": "ok", "t": "Every angle your photo shows is yours", "s": "plus the sides it never saw"},
             ],
             "cue_phrases": ["single objects", "still get"],
         }},
        {"scene_id": "cta", "phrase": 7, "archetype": "endcard", "headline": "SKIP THE RESHOOT",
         "feature_id": None, "depicts": "comment keyword, follow press",
         "payload": {"keyword": "IDOL", "keyword_chip": False, "follow": "Follow",
                     "cue_phrases": ["comment idol", "pin the link"]},
         "cue_word": "idol"},
    ],
}
