"""Spec: repo-unslop-02 · heydamir/unslop — the re-cut, built to both audits.

What is different from repo-unslop-01 (the scheduled take):
  * template  = "design-review": this tool's own animation language (paper plate, fabricated app screens,
                hard cuts, camera punch-in). Not the channel's dark stage. See
                graphics/templates/design-review/template.json.
  * script    = user register per SCRIPT-AUDIT.md: you-as-actor, consequences ("so you can…"), one copyable
                action, the limit inside the pitch (not a "problem" section), 145 words, comment CTA kept
                (owner, 2026-11-07), claim-accurate but not README-verbatim (owner: "do not invent" != "quote").
  * beats     = 8 scenes / ~20 visual events (3 hard cuts in the hook, 4 audit marks, 3 direction lines,
                3 pass states, a typed command + 5 stack chips, a dragged before/after, 3 boundary rows).
"""

REPO = "https://github.com/heydamir/unslop"

# Voice: 215 wpm is allowed (owner, 2026-11-07). Base read is ~184 wpm, so tempo 1.15 lands ~212.
BRIEF_EXTRA = {"voice_tempo": 1.15, "copyable_action": "/unslop this dashboard"}

PLAN = {
    # this tool's animation language (graphics/templates/<name>/); also says "no capture pack"
    "template": "design-review",
    "id": "repo-unslop-02",
    "tool": "unslop",
    "question": "You've seen this screen. Why does every AI-built app look the same?",
    # The plan's own visual metadata (the brief's flow scenes). The animation itself is authored in BEATS,
    # which is where this tool's template and its artifacts live.
    "hook_visual": {
        "kind": "steps",
        "intent": "three fabricated app screens that are the same screen with different words",
        "steps": ["purple gradient", "glow behind the card", "emoji labels"],
    },
    "points": [
        {
            "n": 1,
            "claim": "unslop is a skill for Claude Code and Codex that finds the slop in a screen and names it, with where it lives, before it edits anything.",
            "spoken": "unslop is a skill for Claude Code or Codex, and it starts by naming the slop out loud, and where it lives.",
            "source": REPO,
            "source_note": "README: 'unslop is a skill for Claude Code and Codex that turns vibecoded, AI-looking UI into a designed interface' + 'Audit. Lists every sign of slop with where it lives.'",
            "visual": {"kind": "steps", "intent": "the slop named where it lives, on the screen itself", "steps": ["purple gradient", "glow", "emoji labels"]},
            "rows": ["purple gradient", "glow", "emoji labels", "shouty copy"],
            "title": "FIRST, IT NAMES THE SLOP",
            "sub": "It says where each sign lives.",
            "steps": ["purple gradient", "glow", "emoji labels", "shouty copy"],
        },
        {
            "n": 2,
            "claim": "It proposes a direction taken from the product — character, the moment that carries the colour, a signature detail — and you steer it before it edits anything.",
            "spoken": "Then it asks what your product actually is. Your answer becomes the direction: the character, the one moment that carries the colour, the signature detail.",
            "source": REPO,
            "source_note": "README: 'It audits the screen and proposes a direction before it edits anything, so you can steer it early.' + 'Direction. Character, world, the one or two moments that carry the color, and a signature detail, all taken from your product.'",
            "visual": {"kind": "steps", "intent": "the direction typed from your answer: character, one moment, a detail", "steps": ["the character", "the one moment with colour", "one signature detail"]},
            "title": "YOUR ANSWER IS THE DIRECTION",
            "sub": "It is proposed, not applied.",
            "steps": ["the character", "the one moment with colour", "one signature detail"],
        },
        {
            "n": 3,
            "claim": "It then fixes the screen in nine passes — spacing, color, icons, copy, type, layout, details, visuals, motion — in that order, on the same screen.",
            "spoken": "Then it redraws the same screen in nine passes, so what you get back still looks like your product, just designed.",
            "source": REPO,
            "source_note": "README: 'Passes. Spacing, color, icons, copy, type, layout, details, visuals and motion, in that order.'",
            "visual": {"kind": "steps", "intent": "the same screen changing pass by pass", "steps": ["Spacing", "Colour", "Type", "Layout", "Motion"]},
            "title": "NINE PASSES, ONE SCREEN",
            "sub": "Spacing first, motion last.",
            "steps": ["Spacing", "Colour", "Type", "Layout", "Motion"],
        },
        {
            "n": 4,
            "claim": "You run it by typing /unslop with your screen or a live link, and it works in whatever the screen is built with.",
            "spoken": "Type slash unslop, then your screen or a live link. It runs in Next.js, React, Vue, Svelte or plain CSS.",
            "source": REPO,
            "source_note": "README: 'In Claude Code, type `/unslop` with what you want.' + 'It works in whatever your screen is built with, like Next.js, React, Vue, Svelte, Tailwind or plain HTML and CSS … even on a live site when all you have is a link.'",
            "visual": {"kind": "steps", "intent": "typing the slash command, then the stacks it runs in", "steps": ["Next.js", "React", "Vue", "Svelte"]},
            "chips": ["Next.js", "React", "Vue", "Svelte", "plain CSS"],
            "title": "TYPE SLASH UNSLOP",
            "sub": "A screen, or a live link.",
            "steps": ["Next.js", "React", "Vue", "Svelte", "plain CSS"],
        },
        {
            "n": 5,
            "claim": "The result keeps the layout and the words of the screen it was given; what changes is the product it now looks like.",
            "spoken": "Same layout, same words, different product. That is the whole point.",
            "source": REPO,
            "source_note": "README: 'shows your product instead of a glossy blob' + 'fixes the screen pass by pass like a designer doing a redline review' — the screen is fixed, not replaced.",
            "visual": {"kind": "steps", "intent": "a dragged before/after of the same layout and words", "steps": ["Same layout", "Same words", "Different product"]},
            "title": "SAME WORDS, DIFFERENT PRODUCT",
            "sub": "Fixed, not replaced.",
            "steps": ["Same layout", "Same words", "Different product"],
        },
    ],
    "catch": "If your screen is already good it says so; it asks before any paid image; and it needs Claude Code or Codex to run.",
    "catch_sub": "An agent skill: it works where your agent works.",
    "catch_title": "What to expect",
    "catch_visual": {
        "kind": "steps",
        "intent": "what to expect: it says so when the screen is already good, it asks before any paid image",
        "steps": ["says so when already good", "asks before paid images", "needs Claude Code or Codex"],
    },
    "brand_line": "unslop · a design skill",
    "cover": {
        "text": "EVERY AI APP LOOKS SAME",
        "visual": "one vibecoded screen on the left, the same screen redesigned on the right, divider dragged between them",
        "concepts": [
            {
                "id": "c1", "layout": "split", "text": "EVERY AI APP LOOKS SAME",
                "media": {"kind": "designed", "file": "cover-c1.png",
                          "design": "Paper plate split down the middle: the same fabricated app screen twice — violet gradient with a glow and emoji badges on the left, the redesigned paper version on the right — with the headline sitting across the divider."},
            },
            {
                "id": "c2", "layout": "window", "text": "SAME SCREEN, BUT DESIGNED",
                "media": {"kind": "designed", "file": "cover-c2.png",
                          "design": "A fabricated browser window on the paper plate, half slop and half redesigned, with the audit labels (gradient, glow, emoji) pinned to the slop half and a single violet accent on the clean half."},
            },
            {
                "id": "c3", "layout": "bleed", "text": "NINE PASSES ON ONE SCREEN",
                "media": {"kind": "designed", "file": "cover-c3.png",
                          "design": "Full-bleed paper with the nine pass chips (spacing, colour, icons, copy, type, layout, details, visuals, motion) stacked as a vertical rail, the last three lit violet, and a small before/after screen in the corner."},
            },
        ],
    },
    "cta": "Comment UNSLOP and I'll pin the repo.",
    "cta_keyword": "UNSLOP",
    "seo": {
        "onscreen_first3s": "UNSLOP: EVERY AI SCREEN",
        "keyword": "AI UI design",
        "aliases": ["AI slop design", "fix vibecoded UI", "unslop skill"],
        "youtube": {
            "title": "Why every AI-built app looks the same (and the skill that fixes it)",
            "description": (
                "AI UI design has a look: the purple gradient, the glow behind the card, the emoji in the buttons. "
                "unslop is a skill for Claude Code or Codex that names the slop with where it lives, sets a direction "
                "from your product, then redraws the same screen in nine passes — spacing, color, icons, copy, type, "
                "layout, details, visuals, motion. It runs in Next.js, React, Vue, Svelte or plain CSS, and on a live "
                "site when a link is all you have. Repo: https://github.com/heydamir/unslop "
                "#Shorts #AIUIDesign #ClaudeCode #WebDesign #AISkills"
            ),
            "tags": ["AI UI design", "AI slop design", "fix vibecoded UI", "unslop skill", "Claude Code skill",
                     "design review agent", "AI UI redesign"],
            "hashtags": ["#Shorts", "#AIUIDesign", "#ClaudeCode", "#WebDesign", "#AISkills"],
        },
        "tiktok": {
            "caption": "AI UI design, fixed instead of replaced: unslop names the slop, takes a direction from your product, then redraws the same screen in nine passes. Comment UNSLOP for the repo.",
            "hashtags": ["#AIUIDesign", "#ClaudeCode", "#WebDesign", "#AISkills", "#AIAgents"],
        },
        "instagram": {
            "caption": "Same layout, same words, different product: unslop audits an AI-looking screen and redraws it pass by pass inside Claude Code or Codex. Comment UNSLOP for the repo.",
            "hashtags": ["#AIUIDesign", "#ClaudeCode", "#WebDesign", "#BuildInPublic", "#AISkills"],
        },
        "facebook": {
            "caption": "Every AI-built screen has the same look. unslop is a skill for Claude Code or Codex that names the slop, takes a direction from your product and redraws the screen in nine passes. Comment UNSLOP for the repo.",
            "hashtags": ["#AIUIDesign", "#ClaudeCode", "#WebDesign", "#AISkills", "#BuildInPublic"],
        },
        "x": {
            "text": "AI UI design: unslop names the slop in a vibecoded screen, takes a direction from your product, then redraws the same screen in nine passes.",
            "hashtags": ["#AIUIDesign", "#ClaudeCode"],
        },
    },
    "brief_meta": {
        "title": "unslop: the skill that redraws AI-looking UI",
        "niche": "AI tools",
        "keywords": ["AI UI design", "AI slop design", "Claude Code skill", "AI UI redesign"],
        "idea": "unslop names the slop in an AI-looking screen, takes a direction from the product, and redraws the same screen in nine passes.",
        "viewer": {
            "who": "builders who shipped a vibecoded app that works but looks like every other AI app",
            "problem": "the screen reads generic and unfinished, and they do not want to redesign it from scratch",
            "job": "decide whether a design skill inside their agent can fix the screen they already have",
        },
    },
}

FEATURES = {
    "tool": {"name": "unslop", "repo": REPO},
    "features": [
        {"id": "f1", "title": "A skill for Claude Code and Codex",
         "what": "It runs where the agent runs, as a skill folder.",
         "evidence_quote": "unslop is a skill for Claude Code and Codex that turns vibecoded, AI-looking UI into a designed interface with its own character."},
        {"id": "f2", "title": "It finds the slop first",
         "what": "Purple gradients, glows, emoji labels, shouty copy and uneven spacing, named.",
         "items": ["purple gradient", "glow", "emoji labels", "shouty copy"],
         "evidence_quote": "It finds the slop first, the purple gradients, glows, emoji labels, shouty copy and uneven spacing"},
        {"id": "f3", "title": "Audit, with where it lives",
         "what": "Every sign of slop is listed with its location.",
         "evidence_quote": "**Audit.** Lists every sign of slop with where it lives."},
        {"id": "f4", "title": "A direction from the product",
         "what": "Character, the moments that carry the colour, and a signature detail.",
         "evidence_quote": "**Direction.** Character, world, the one or two moments that carry the color, and a signature detail, all taken from your product."},
        {"id": "f5", "title": "Nine passes, in order",
         "what": "Spacing, color, icons, copy, type, layout, details, visuals and motion.",
         "evidence_quote": "**Passes.** Spacing, color, icons, copy, type, layout, details, visuals and motion, in that order."},
        {"id": "f6", "title": "Works in the viewer's stack",
         "what": "Any framework the screen is built with, and a live site from a link.",
         "evidence_quote": "It works in whatever your screen is built with, like Next.js, React, Vue, Svelte, Tailwind or plain HTML and CSS"},
        {"id": "f7", "title": "It says so when the screen is already good",
         "what": "It suggests small refinements instead of a redesign.",
         "evidence_quote": "If the screen is already good, it tells you so and suggests a few small refinements instead of redesigning it."},
        {"id": "f8", "title": "It asks before a paid generation",
         "what": "The prompt is shown and the paid call waits for a yes.",
         "evidence_quote": "it shows the prompt and asks before every paid generation"},
        {"id": "f9", "title": "The exact thing you type",
         "what": "A slash command with your screen, your page or a live link.",
         "evidence_quote": "In Claude Code, type `/unslop` with what you want."},
        {"id": "f10", "title": "Story video needs two more tools", "risk": True,
         "what": "Playwright and ffmpeg, for the square story video.",
         "evidence_quote": "Story videos also require ffmpeg installed and available on your PATH."},
    ],
    "risks": [{"id": "r1", "text": "It is an agent skill: it needs Claude Code or Codex to run."},
              {"id": "r2", "text": "A paid hero image is optional, and it asks before every generation."}],
    "source_urls": [REPO],
}

# One scene per spoken phrase (B1). Template "design-review" supplies this tool's own archetypes.
BEATS = {
    "tool": "unslop",
    "template": "design-review",
    "handle": "@hypeless",
    "scenes": [
        {"scene_id": "hook", "phrase": 0, "archetype": "ui_screen", "headline": "UNSLOP: EVERY AI SCREEN",
         "feature_id": "f2", "depicts": "three AI-built screens that look the same, purple gradient and glow",
         "payload": {
             "eyebrow": "AI-BUILT UI",
             "accent_word": "unslop",
             "label": "SAME SCREEN \u00d7 3",
             "pages": [
                 {"variant": "slop", "title": "AMPLIFY YOUR WORKFLOW", "sub": "AI-powered invoicing. Ship faster. Scale effortlessly.",
                  "sections": ["Invoices", "Clients", "Payments"], "url": "nimbus.app/dashboard"},
                 {"variant": "slop", "title": "AMPLIFY YOUR INBOX", "sub": "AI-powered replies. Ship faster. Scale effortlessly.",
                  "sections": ["Inbox", "Drafts", "Rules"], "url": "nimbus.app/inbox"},
                 {"variant": "slop", "title": "AMPLIFY YOUR TEAM", "sub": "AI-powered standups. Ship faster. Scale effortlessly.",
                  "sections": ["Projects", "People", "Reports"], "url": "nimbus.app/team"},
             ],
             "cue_phrases": ["seen this screen", "gradient", "glow"],
             "cam": [1.0, 1.05],
         }},
        {"scene_id": "point1", "phrase": 1, "archetype": "audit_marks", "headline": "FIRST, IT NAMES THE SLOP",
         "feature_id": "f3", "depicts": "the slop in a screen, named and located: gradient, glow, emoji labels",
         "payload": {
             "eyebrow": "AUDIT",
             "accent_word": "slop",
             "page": {"variant": "slop", "title": "AMPLIFY YOUR WORKFLOW", "sub": "AI-powered invoicing. Ship faster. Scale effortlessly.",
                      "sections": ["Invoices", "Clients", "Payments"], "url": "nimbus.app/dashboard"},
             "marks": [{"t": "purple gradient", "sel": ".cards"},
                       {"t": "soft glow", "sel": ".cta"},
                       {"t": "emoji label", "sel": ".badges"},
                       {"t": "shouty copy", "sel": ".hero h1"}],
             "cue_phrases": ["naming the slop", "gradient", "glow", "emoji", "shouty"],
         }},
        {"scene_id": "point2", "phrase": 2, "archetype": "direction_card", "headline": "YOUR ANSWER IS THE DIRECTION",
         "feature_id": "f4", "depicts": "the direction: character, the moment with colour, a signature detail",
         "payload": {
             "eyebrow": "DIRECTION",
             "accent_word": "direction",
             "label": "direction",
             "lines": ["character: quiet, editorial",
                       "one moment: the invoice total",
                       "signature detail: hairline rules"],
             "cue_phrases": ["what your product", "character", "signature detail"],
         }},
        {"scene_id": "point3", "phrase": 3, "archetype": "pass_stack", "headline": "NINE PASSES, ONE SCREEN",
         "feature_id": "f5", "depicts": "the same screen redrawn in nine passes, spacing through motion",
         "payload": {
             "eyebrow": "REDRAW",
             "accent_word": "passes",
             "passes": ["Spacing", "Colour", "Icons", "Copy", "Type", "Layout", "Details", "Visuals", "Motion"],
             "pages": [
                 {"variant": "slop", "title": "AMPLIFY YOUR WORKFLOW", "sub": "AI-powered invoicing. Ship faster. Scale effortlessly.",
                  "sections": ["Invoices", "Clients", "Payments"], "url": "nimbus.app/dashboard"},
                 {"variant": "mid", "title": "Send invoices that get paid", "sub": "One screen, your numbers, nothing in the way.",
                  "sections": ["Invoices", "Clients", "Payments"], "url": "nimbus.app/dashboard"},
                 {"variant": "clean", "title": "Send invoices that get paid", "sub": "One screen, your numbers, nothing in the way.",
                  "sections": ["Invoices", "Clients", "Payments"], "url": "nimbus.app/dashboard", "rowMeta": "12 open"},
             ],
             "cue_phrases": ["redraws the same screen", "nine passes", "designed"],
         }},
        {"scene_id": "point4", "phrase": 4, "archetype": "stack_chips", "headline": "TYPE SLASH UNSLOP",
         "feature_id": "f9", "depicts": "typing the slash command, then the stacks it runs in",
         "payload": {
             "eyebrow": "TYPE IT",
             "accent_word": "unslop",
             "command": "/unslop this dashboard",
             "chips": ["Next.js", "React", "Vue", "Svelte", "plain CSS"],
             "cue_phrases": ["type slash unslop", "next", "react", "vue", "svelte"],
         }},
        {"scene_id": "point5", "phrase": 5, "archetype": "split_compare", "headline": "SAME WORDS, DIFFERENT PRODUCT",
         "feature_id": None, "depicts": "the same layout and words, dragged from slop to designed",
         "payload": {
             "eyebrow": "THE RESULT",
             "accent_word": "different",
             "labels": ["BEFORE", "AFTER"],
             "before": {"variant": "slop", "title": "AMPLIFY YOUR WORKFLOW", "sub": "AI-powered invoicing. Ship faster. Scale effortlessly.",
                        "sections": ["Invoices", "Clients", "Payments"], "url": "nimbus.app/dashboard"},
             "after": {"variant": "clean", "title": "Send invoices that get paid", "sub": "One screen, your numbers, nothing in the way.",
                       "sections": ["Invoices", "Clients", "Payments"], "url": "nimbus.app/dashboard", "rowMeta": "12 open"},
             "cue_phrases": ["same layout", "different product"],
         }},
        {"scene_id": "catch", "phrase": 6, "archetype": "boundary_rows", "headline": "WHAT TO EXPECT",
         "feature_id": "f7", "depicts": "what to expect: it says so when the screen is already good",
         "payload": {
             "eyebrow": "WHAT TO EXPECT",
             "rows": [{"kind": "ok", "t": "It says so when the screen is already good", "s": "small refinements, not a redesign"},
                      {"kind": "tag", "t": "It asks before any paid image", "s": "the prompt is shown first"},
                      {"kind": "tag", "t": "You do need Claude Code or Codex", "s": "it runs where your agent runs"}],
             "cue_phrases": ["already good", "paid image", "claude code"],
         }},
        {"scene_id": "cta", "phrase": 7, "archetype": "endcard", "headline": "COMMENT UNSLOP",
         "feature_id": None, "depicts": "the comment keyword and the follow button",
         # owner: no tool name above the Follow button — the headline carries the keyword
         "payload": {"keyword": "UNSLOP", "keyword_chip": False, "follow": "Follow",
                     "cue_phrases": ["comment unslop", "pin the repo"]},
         "cue_word": "unslop"},
    ],
}
