"""Spec: model-idol-01 · speridlabs/idol — one photo in, a 3D Gaussian splat out.

Source of the day: HF trending #1 (2026-11-08, trend ~765, 1,291 likes), read from the model card and
the benchmark table on the day of the plan. Positions on the channel: image-to-3D is a fresh frame for us —
no covered key matches 'idol' (ledger-checked 2026-11-08).

Base: repo-unslop-02's proven cut (owner-approved rhythm) — but with idol's OWN template
  (owner ruling 2026-11-08: every Tool gets its own template with its own colors, animations, graphics;
  never reuse another tool's visual language).
  * template  = "photo-to-3d" (graphics/templates/photo-to-3d/): a dark 3D-viewer canvas — fabricated
                photo chips, a violet Gaussian-splat point cloud with orbit rings, scanlines, a VRAM
                gauge, a bench leaderboard. Not the unslop paper plate, not the channel dark stage.
  * script    = user-first register: you-as-actor, outcomes first ("Take one photo of your product. Now spin
                it."), the limit inside the pitch without a "problem" section, comment CTA kept.
  * claims    = only what the model card states (per-card benchmark attributed to the lab).
"""

MODEL = "https://huggingface.co/speridlabs/idol"

BRIEF_EXTRA = {"voice_tempo": 1.15, "copyable_action": "python -m idol.sample --image photo.jpg --mode real", "tail": 2.0}

PLAN = {
    "template": "photo-to-3d",
    "id": "model-idol-01",
    "tool": "idol",
    "question": "What if your product photo could spin around — in full 3D?",
    "hook_visual": {
        "kind": "steps",
        "intent": "three fabricated product photos that read as spinnable 3D objects",
        "steps": ["one photo", "background cut", "splat spins"],
    },
    "points": [
        {
            "n": 1,
            "claim": "idol turns a single picture of an object into a full three-D Gaussian splat, including the sides the picture never showed.",
            "spoken": "idol turns one single picture into a full three-D Gaussian splat, even the sides your camera never saw.",
            "source": MODEL,
            "source_note": "Model card: 'Idol turns one picture of an object into a 3D Gaussian splat… including the sides the picture never showed.'",
            "visual": {"kind": "steps", "intent": "one photo, then the hidden sides drawn in", "steps": ["one picture", "hidden sides drawn"]},
            "rows": ["one picture in", "up to a million Gaussians", "hidden sides drawn", "standard .ply"],
            "title": "ONE PICTURE, FULL 3D",
            "sub": "Even the sides the camera never saw.",
            "steps": ["one picture", "hidden sides drawn", "a million Gaussians"],
        },
        {
            "n": 2,
            "claim": "The pipeline removes the background, frames the object, and writes a standard 3DGS .ply that opens in any Gaussian splat viewer.",
            "spoken": "It removes the background, frames the object, and writes a standard PLY file, so it opens in any splat viewer or Blender.",
            "source": MODEL,
            "source_note": "Model card: 'it removes the background, frames the object and generates up to 1,048,576 Gaussians, written as a standard 3DGS .ply' + 'open it in any Gaussian splat viewer'.",
            "visual": {"kind": "steps", "intent": "photo splits into cut-out, frame, .ply file", "steps": ["background cut", "object framed", ".ply written"]},
            "title": "BACKGROUND CUT, PLY OUT",
            "sub": "Opens in any splat viewer or Blender.",
            "steps": ["background cut", "object framed", ".ply written"],
        },
        {
            "n": 3,
            "claim": "It runs on consumer GPUs: 7.2 GB of VRAM, and can run in under 2 seconds.",
            "spoken": "And it runs on your own graphics card: seven point two gigabytes of VRAM, and under two seconds on a fast card.",
            "source": MODEL,
            "source_note": "Model card: 'It runs on consumer GPUs, using 7.2 GB of VRAM and can run in under 2 seconds.'",
            "visual": {"kind": "steps", "intent": "a consumer GPU card with the VRAM bar and a 2 s timer", "steps": ["7.2 GB VRAM", "under 2 s"]},
            "title": "RUNS ON YOUR GPU",
            "sub": "7.2 GB VRAM · under two seconds.",
            "steps": ["your GPU", "7.2 GB VRAM", "under 2 s"],
        },
        {
            "n": 4,
            "claim": "You can try it free in the Hugging Face Space, or install the open SDK and call it from Python.",
            "spoken": "Try it free in the browser demo, or install the SDK and call it from one line of Python.",
            "source": MODEL,
            "source_note": "Model card Demo badge -> huggingface.co/spaces/speridlabs/idol + 'pip install -e .' + 'from idol import IdolPipeline'.",
            "visual": {"kind": "steps", "intent": "the free Space demo page, then the Python call", "steps": ["free demo", "pip install", "one Python call"]},
            "chips": ["free Space demo", "pip install -e .", "IdolPipeline"],
            "title": "TRY IT FREE",
            "sub": "The Space demo, or the SDK in Python.",
            "steps": ["free Space demo", "pip install -e .", "IdolPipeline"],
        },
        {
            "n": 5,
            "claim": "On the lab's own benchmark it edges TripoSplat and TRELLIS on every visual column, and it was the number-one trending model on Hugging Face today.",
            "spoken": "On their own benchmark it edges TripoSplat and TRELLIS on every visual score, and it is the top trending model today.",
            "source": MODEL,
            "source_note": "Benchmark table: Idol bold in SSIM, LPIPS, IoU, DINOv2, CLIP, sharpness distance vs TripoSplat/TRELLIS (PSNR and time go to LGM, footnoted). HF trending #1, score ~765 on 2026-11-08.",
            "visual": {"kind": "steps", "intent": "benchmark bars with idol's row on top, then a trending badge", "steps": ["visual scores", "on top", "trending #1"]},
            "title": "TOP OF THE TABLE TODAY",
            "sub": "Benchmark: every visual column. Chart: trending #1.",
            "steps": ["visual scores", "on top", "trending #1"],
        },
    ],
    "catch": "You need an NVIDIA GPU with CUDA for your own runs; two encoder models ask you to accept their terms once; and it is built for single objects, not scenes.",
    "catch_sub": "The free Space demo needs no GPU at all.",
    "catch_title": "What to expect",
    "catch_visual": {
        "kind": "steps",
        "intent": "what to expect: CUDA GPU, accept two encoders once, single objects",
        "steps": ["NVIDIA + CUDA", "accept two encoders once", "single objects, not scenes"],
    },
    "brand_line": "idol · one photo to 3D",
    "cover": {
        "text": "PHOTO IN, 3D OUT",
        "visual": "a plain product photo on the left, the same object as a spun Gaussian splat on the right",
        "concepts": [
            {
                "id": "c1", "layout": "split", "text": "PHOTO IN, 3D OUT",
                "media": {"kind": "designed", "file": "cover-c1.png",
                          "design": "Paper plate split down the middle: left a flat fabricated product photo of a sneaker, right the same sneaker as a violet Gaussian-splat object with orbit tick marks, headline across the divider."},
            },
            {
                "id": "c2", "layout": "window", "text": "PHOTO IN, SPLAT OUT",
                "media": {"kind": "designed", "file": "cover-c2.png",
                          "design": "A fabricated demo-page window on the paper plate: photo chip on the left rail, a violet 3D blob with rotation arrows in the middle, .ply file card on the right, headline along the top."},
            },
            {
                "id": "c3", "layout": "bleed", "text": "PHOTO TO 3D, FAST",
                "media": {"kind": "designed", "file": "cover-c3.png",
                          "design": "Full-bleed paper with a giant '2s' timer chip, a VRAM bar at 7.2 GB, and a small violet splat object orbiting in the corner."},
            },
        ],
    },
    "cta": "Comment IDOL and I'll pin the link.",
    "cta_keyword": "IDOL",
    "seo": {
        "onscreen_first3s": "ONE PHOTO, NOW 3D",
        "keyword": "image to 3D",
        "aliases": ["photo to 3D model", "Gaussian splat", "idol model", "3D from one image"],
        "youtube": {
            "title": "Image to 3D in under two seconds idol turns one photo",
            "description": (
                "idol turns one picture of an object into a full three-D Gaussian splat — up to a million Gaussians, "
                "including the sides your camera never saw. It removes the background, frames the object and writes "
                "a standard 3DGS .ply that opens in any splat viewer or Blender. Runs on consumer GPUs (7.2 GB VRAM, "
                "under 2 seconds), free to try in the Hugging Face demo, or pip install the SDK. Model: "
                "https://huggingface.co/speridlabs/idol #Shorts #ImageTo3D #GaussianSplat #3DAI #HuggingFace"
            ),
            "tags": ["image to 3D", "photo to 3D model", "Gaussian splat", "idol model", "3D AI",
                     "single image 3D", "Hugging Face"],
            "hashtags": ["#Shorts", "#ImageTo3D", "#GaussianSplat", "#AI3D", "#HuggingFace"],
        },
        "tiktok": {
            "caption": "Image to 3D — one photo of your product becomes a spinnable Gaussian splat: background cut, .ply out, runs on your own GPU. Free demo on Hugging Face. Comment IDOL for the link.",
            "hashtags": ["#ImageTo3D", "#GaussianSplat", "#AI3D", "#HuggingFace", "#AI3D"],
        },
        "instagram": {
            "caption": "Image to 3D with idol: one picture becomes a full Gaussian splat — even the sides the camera never saw. Free to try on Hugging Face, or run it on your own GPU. Comment IDOL for the link.",
            "hashtags": ["#ImageTo3D", "#GaussianSplat", "#AIVideo", "#AI3D", "#HuggingFace"],
        },
        "facebook": {
            "caption": "Image to 3D in, a spinnable model out: one photo becomes a Gaussian splat. idol is open on Hugging Face: 7.2 GB VRAM, under two seconds, standard .ply that opens anywhere. Comment IDOL for the link.",
            "hashtags": ["#ImageTo3D", "#GaussianSplat", "#AI3D", "#HuggingFace", "#AI3D"],
        },
        "x": {
            "text": "Image to 3D, one photo: idol turns a single picture into a Gaussian splat you can spin, under 2 seconds on your own GPU.",
            "hashtags": ["#ImageTo3D", "#GaussianSplat"],
        },
    },
    "brief_meta": {
        "title": "idol: one photo becomes a 3D model",
        "niche": "AI tools",
        "keywords": ["image to 3D", "photo to 3D model", "Gaussian splat", "idol model"],
        "idea": "idol turns one picture of an object into a full three-D Gaussian splat — background cut, .ply out — on a consumer GPU and free to try.",
        "viewer": {
            "who": "makers, shop owners and 3D-curious builders with a product or object photo",
            "problem": "getting a 3D version of a real object means modelling skill they don't have — or a scanner they don't own",
            "job": "decide whether one photo can give them a spinnable 3D asset today",
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
         "what": "The file opens in any Gaussian splat viewer.",
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
         "what": "Accept terms once on DINOv3 and FLUX.2 before the SDK will run.",
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
        {"scene_id": "hook", "phrase": 0, "archetype": "photo_splat", "headline": "YOUR PHOTO, NOW FULL 3D",
         "feature_id": "f1", "depicts": "product photos hard-cut into a point cloud that spins",
         "payload": {
             "eyebrow": "IMAGE TO 3D",
             "accent_word": "3D",
             "label": "ONE PICTURE → SPLAT",
             "photos": [
                 {"name": "sneaker.jpg", "tag": "INPUT · ONE PICTURE", "caption": "one picture · flat 2D"},
                 {"name": "mug.jpg", "tag": "INPUT · ONE PICTURE", "caption": "one picture · flat 2D"},
                 {"name": "lamp.jpg", "tag": "INPUT · ONE PICTURE", "caption": "one picture · flat 2D", "handle": False},
             ],
             "splat": {"name": "sneaker.ply", "count": "1,048,576 GAUSSIANS",
                       "caption": "standard 3DGS · opens anywhere", "badge": "FULL 3D", "seed": 9102},
             "cue_phrases": ["product photo", "spin around", "full 3D"],
         }},
        {"scene_id": "point1", "phrase": 1, "archetype": "depth_callouts", "headline": "ONE PICTURE, FULL 3D",
         "feature_id": "f1", "depicts": "the picture card with the sides it never saw called out",
         "payload": {
             "eyebrow": "REBUILD",
             "accent_word": "3D",
             "photo": {"name": "sneaker.jpg", "tag": "INPUT MODE · SYNTHETIC", "caption": "one picture · before"},
             "marks": ["one picture in", "hidden sides drawn", "a million Gaussians", "standard .ply"],
             "score": "FULL 3D \u00d7 4",
             "cue_phrases": ["single picture", "gaussian splat", "never saw"],
         }},
        {"scene_id": "point2", "phrase": 2, "archetype": "splat_pipeline", "headline": "CUT, FRAME, PLY OUT",
         "feature_id": "f3", "depicts": "the background cut, the frame and the ply file as three lit stages",
         "payload": {
             "eyebrow": "PIPELINE",
             "accent_word": "PLY",
             "stages": [
                 {"kind": "photo", "title": "CUT", "sub": "BiRefNet removes the background.", "kicker": "photo in"},
                 {"kind": "cut", "title": "FRAME", "sub": "The object is framed, centered, padded.", "kicker": "object framed"},
                 {"kind": "splat", "title": "WRITE .PLY", "sub": "A standard 3DGS splat comes out."},
             ],
             "cue_phrases": ["removes the background", "standard PLY", "splat viewer"],
         }},
        {"scene_id": "point3", "phrase": 3, "archetype": "gpu_gauge", "headline": "RUNS ON YOUR GPU",
         "feature_id": "f4", "depicts": "the VRAM gauge filling and the two-second speed chip",
         "payload": {
             "eyebrow": "HARDWARE",
             "accent_word": "GPU",
             "vram": 7.2, "gauge_cap": 24,
             "chips": ["under 2 s", "consumer card", "plays with any viewer", "no cloud call"],
             "chip_subs": ["median request time on the lab's bench", "7.2 GB peak, per the card",
                           "a file, not a hosted result", "your GPU does the work"],
             "cue_phrases": ["own graphics card", "seven point two", "under two seconds"],
         }},
        {"scene_id": "point4", "phrase": 4, "archetype": "two_doors", "headline": "TRY IT TONIGHT, FREE",
         "feature_id": "f6", "depicts": "the free Space demo door and the pip install SDK door",
         "payload": {
             "eyebrow": "TRY IT",
             "accent_word": "free",
             "doors": [
                 {"title": "The free demo", "sub": "A Hugging Face Space: drop a picture, get the splat.",
                  "line": "HF Spaces → speridlabs/idol"},
                 {"title": "The SDK", "sub": "On your own GPU, one Python call per picture.",
                  "line": "pip install the SDK"},
             ],
             "cue_phrases": ["try it free", "install the SDK", "python"],
         }},
        {"scene_id": "point5", "phrase": 5, "archetype": "leaderboard", "headline": "TOP OF THE TABLE",
         "feature_id": None, "depicts": "the benchmark bars with idol on the top row and the trending badge",
         "payload": {
             "eyebrow": "PROOF",
             "accent_word": "top",
             "badge": "TOP TRENDING TODAY",
             "rows": [
                 {"name": "idol", "score": 0.97, "val": "0.726 SSIM", "win": True},
                 {"name": "TRELLIS", "score": 0.72, "val": "0.716 SSIM"},
                 {"name": "TripoSplat", "score": 0.68, "val": "0.712 SSIM"},
                 {"name": "LGM", "score": 0.60, "val": "0.722 SSIM"},
             ],
             "cue_phrases": ["benchmark", "every visual score", "top trending"],
         }},
        {"scene_id": "catch", "phrase": 6, "archetype": "expect_rows", "headline": "WHAT TO EXPECT",
         "feature_id": "f10", "depicts": "the CUDA GPU note, the terms once note, the single objects note",
         "payload": {
             "eyebrow": "WHAT TO EXPECT",
             "rows": [{"kind": "tag", "t": "Your own runs need an NVIDIA GPU with CUDA", "s": "the free Space demo needs no GPU"},
                      {"kind": "tag", "t": "Two encoder models are gated", "s": "accept their terms once"},
                      {"kind": "ok", "t": "Built for single objects", "s": "one object per picture, not scenes"}],
             "cue_phrases": ["nvidia", "terms once", "single objects"],
         }},
        {"scene_id": "cta", "phrase": 7, "archetype": "endcard", "headline": "COMMENT IDOL",
         "feature_id": None, "depicts": "the comment keyword and the follow button",
         "payload": {"keyword": "IDOL", "keyword_chip": False, "follow": "Follow",
                     "cue_phrases": ["comment idol", "pin the link"]},
         "cue_word": "idol"},
    ],
}
