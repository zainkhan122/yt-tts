"""Visual language: the rule that a short's look is decided by what the TOOL IS, not by a template.

A beat plan says what each scene shows. This module says what the whole video looks like while it
shows it: the plate (paper / ink / slate / dots / deep), the accent pair, and which archetypes suit
the tool's category. The reference reels do exactly this — a music tool, a CLI tool and a benchmark
tool do not share a colour or a surface.

The tool's category comes from the feature sheet's `tool.category`, which the agent writes when it
reads the repo. One category, one visual language, enforced by the linter (B12).
"""
from __future__ import annotations

# Archetypes that are always available in any language: the script-only beats and the brand beats.
_ALWAYS = {"concept_card", "stamp_card", "quote_block", "endcard", "cta_stack"}

# The registry. Each entry is a complete visual language.
LANGUAGES: dict[str, dict] = {
    "coding": {
        "label": "Coding agents & CLI",
        "plates": ["ink", "paper"],
        "palette": {"accent": "#FE297D", "accent2": "#38BDF8"},
        "allowed": {"stage_board", "chart_bars", "chart_line", "compare_split", "verdict_pair",
                    "app_mock", "steps_path", "spec_strip", "chip_grid", "flow_link", "terminal_type",
                    "toggle_steps", "stat_pop"},
        "props": ["window", "terminal", "panel", "matrix", "cells", "note", "stamp", "bar", "spark"],
        "note": "Black and paper. Pink for the one thing you must look at, cyan for the second.",
    },
    "audio": {
        "label": "Audio, speech & music",
        "plates": ["paper", "slate"],
        "palette": {"accent": "#34C759", "accent2": "#FFD60A"},
        "allowed": {"stage_board", "chart_bars", "chart_line", "chart_donut", "compare_split",
                    "verdict_pair", "app_mock", "steps_path", "spec_strip", "chip_grid", "flow_link",
                    "terminal_type", "toggle_steps", "stat_pop"},
        "props": ["panel", "bar", "spark", "gauge", "note", "stamp", "machine", "window", "cells"],
        "note": "Studio slate. A live green for playback, amber for the warning.",
    },
    "video3d": {
        "label": "3D, video & vision models",
        "plates": ["deep", "ink"],
        "palette": {"accent": "#8B7CFF", "accent2": "#7CD4FC"},
        "allowed": {"stage_board", "chart_bars", "chart_line", "chart_donut", "compare_split",
                    "verdict_pair", "app_mock", "steps_path", "spec_strip", "chip_grid", "flow_link",
                    "terminal_type", "toggle_steps", "stat_pop"},
        "props": ["stack", "gauge", "spark", "panel", "matrix", "note", "stamp", "bar"],
        "note": "Deep space with a violet cast. Depth first: stacked layers, glow, orbit.",
    },
    "design": {
        "label": "Design, UI & frontend tools",
        "plates": ["paper", "dots"],
        "palette": {"accent": "#6C4CF1", "accent2": "#E4572E"},
        "allowed": {"stage_board", "chart_bars", "compare_split", "verdict_pair", "app_mock",
                    "steps_path", "spec_strip", "chip_grid", "flow_link", "terminal_type",
                    "toggle_steps", "stat_pop", "quote_block"},
        "props": ["window", "cells", "note", "stamp", "folder", "panel", "bar", "machine"],
        "note": "Clean paper. Purple for the judgement, tangerine for the change.",
    },
    "data": {
        "label": "Data, leaderboards & benchmarks",
        "plates": ["deep", "paper", "ink"],
        "palette": {"accent": "#FFD60A", "accent2": "#38BDF8"},
        "allowed": {"chart_bars", "chart_line", "chart_donut", "stage_board", "compare_split",
                    "verdict_pair", "app_mock", "steps_path", "spec_strip", "chip_grid", "flow_link",
                    "terminal_type", "toggle_steps", "stat_pop"},
        "props": ["bar", "spark", "matrix", "stack", "gauge", "cells", "note", "stamp", "window"],
        "note": "Grid and glow. The chart IS the scene: lead with numbers, let the picture explain them.",
    },
    "system": {
        "label": "System utilities & privacy",
        "plates": ["ink", "slate"],
        "palette": {"accent": "#F97316", "accent2": "#3B82F6"},
        "allowed": {"stage_board", "chart_bars", "chart_line", "compare_split", "verdict_pair",
                    "app_mock", "steps_path", "spec_strip", "chip_grid", "flow_link", "terminal_type",
                    "toggle_steps", "stat_pop"},
        "props": ["panel", "window", "note", "stamp", "bar", "matrix", "cells"],
        "note": "Obsidian clean. Orange for the alert, blue for the fix.",
    },
    "general": {
        "label": "General AI tooling",
        "plates": ["paper", "ink", "slate"],
        "palette": {"accent": "#D93025", "accent2": "#1F5F8B"},
        "allowed": {"stage_board", "chart_bars", "chart_line", "chart_donut", "compare_split",
                    "verdict_pair", "app_mock", "steps_path", "spec_strip", "chip_grid", "flow_link",
                    "terminal_type", "toggle_steps", "stat_pop"},
        "props": ["card", "window", "panel", "note", "stamp", "cells", "bar", "spark", "matrix",
                  "folder", "machine", "envelope", "scale", "gauge", "stack"],
        "note": "Printed paper with a red accent. Every prop in the library is available.",
    },
}

# Words in a repo name/description that map to a category when the agent did not name one.
CATEGORY_HINTS: list[tuple[tuple[str, ...], str]] = [
    (("cli", "terminal", "cli agent", "coding agent", "code agent", "shell", "rust", "golang",
      "linter", "formatter", "compiler", "sdk", "ide", "vim", "neovim", "git", "refactor",
      "build tool", "build agent"), "coding"),
    (("tts", "speech", "voice", "audio", "music", "sound", "whisper", "podcast", "singing",
      "transcri", "cloning", "dj", "mixer"), "audio"),
    (("video", "3d", "splat", "gaussian", "render", "diffusion", "image", "vision", "depth",
      "avatar", "text-to-image", "text-to-video", "model", "llm", "inference"), "video3d"),
    (("design", "ui", "ux", "frontend", "landing", "figma", "css", "tailwind", "component",
      "webpage", "website", "template", "theme"), "design"),
    (("benchmark", "leaderboard", "arena", "elo", "analytics", "dashboard", "chart", "data",
      "metrics", "tracking", "observability", "price", "cost"), "data"),
    (("privacy", "cleaner", "uninstall", "cache", "backup", "system", "firewall", "vpn",
      "antivirus", "storage", "sync"), "system"),
]


def _norm(text: str) -> str:
    return " ".join(str(text or "").lower().replace("_", " ").replace("-", " ").split())


def detect_category(tool: dict | None) -> str:
    """The category of a tool: the one the agent named, or the one its name and summary imply."""
    tool = tool or {}
    named = str(tool.get("category") or "").strip().lower().replace(" ", "")
    for key in LANGUAGES:
        if named == key:
            return key
    for key, lang in LANGUAGES.items():
        if named and named in key or named and named in str(lang.get("label", "")).lower().replace(" ", ""):
            return key
    hay = _norm(" ".join(str(tool.get(k) or "") for k in ("name", "summary", "what", "tagline", "category")))
    for words, cat in CATEGORY_HINTS:
        for w in words:
            if w in hay:
                return cat
    return "general"


def language_for(tool: dict | None) -> dict:
    """The full visual language for a tool: plate, palette, allowed archetypes, prop kinds."""
    cat = detect_category(tool)
    lang = dict(LANGUAGES[cat])
    lang["category"] = cat
    return lang


def palette_for(tool: dict | None) -> dict:
    """The CSS-variable overrides the renderer applies on top of the plate."""
    return dict(language_for(tool).get("palette") or {})


def allowed_archetypes(tool: dict | None) -> set[str] | None:
    """The archetypes this tool's language permits, or None when no category was detected."""
    lang = language_for(tool)
    return set(lang.get("allowed") or set()) | _ALWAYS
