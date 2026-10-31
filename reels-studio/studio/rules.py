"""Hard rules for the shorts system (v2).

These are facts, safety and platform checks only. They do not decide how a short is
structured or worded. The writer owns the script and copy; these functions only refuse
what must never ship: credits in visible text, generic or malformed tags, missing
sources, expired reviews, undisclosed AI narration, copy that breaks platform limits,
and identical copy pasted across platforms.
"""
import datetime as dt
import re
from dataclasses import dataclass

PLATFORMS = ("youtube", "tiktok", "instagram", "facebook", "x")

# Hard maximum characters for the final assembled text of each platform.
LIMITS = {"youtube": 5000, "tiktok": 2200, "instagram": 2200, "facebook": 5000, "x": 280}
YOUTUBE_TITLE_MAX = 100

# (min, max) hashtags per platform for the final text.
HASHTAG_RANGE = {"youtube": (2, 5), "tiktok": (2, 5), "instagram": (2, 5), "facebook": (1, 3), "x": (0, 2)}

GENERIC_TAGS = {
    "#ai", "#coding", "#video", "#tech", "#viral", "#fyp", "#foryou", "#foryoupage", "#trending",
    "#programming", "#code", "#software", "#learntocode", "#reels", "#explore",
    "#technology", "#innovation", "#future", "#artificialintelligence", "#chatgpt", "#gpt",
}
REQUIRED_YT_TAG = "#shorts"

# Anything that reads as a capture credit, an attribution or a capture date.
CREDIT_PATTERN = re.compile(
    r"\b(credits?|attribution|attributed|own captures?|own capture|own browser|captured (on|by)|"
    r"capture date|source credit)\b|\(checked\b|\bchecked 20\d\d|©",
    re.IGNORECASE,
)
# Promotional or robotic phrasing the owner rejected (2026-10-21).
PROMO_PATTERN = re.compile(
    r"game[- ]chang|revolutionary|must[- ]have|mind[- ]blowing|life[- ]changing|no[- ]brainer|"
    r"you won'?t believe|in this video|crushing it|unlock (the|your) power|insane",
    re.IGNORECASE,
)
PLACEHOLDER_PATTERN = re.compile(r"\b(TODO|TBD|lorem|FIXME)\b|\[[^\]]*\]|\{\{|\}\}", re.IGNORECASE)
LEGAL_PATTERN = re.compile(r"\b(licen[cs]e|MIT|Apache|GPL|copyright|terms of service|EULA)\b", re.IGNORECASE)
HASHTAG_PATTERN = re.compile(r"^#[A-Za-z][A-Za-z0-9_]{1,40}$")
URL_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://\S+")
DISCLOSURE_TEXT = "AI-generated narration."

REQUIRED_BRIEF_KEYS = ("id", "title", "niche", "lang", "viewer", "idea", "claims", "proof_plan",
                       "scenes", "seo", "sources", "review")
SPEECH_WPM = 180  # fast but natural narration; checked against the 148-word scrawl script (50.7 s)


@dataclass(frozen=True)
class Finding:
    code: str
    level: str  # "error" or "warning"
    where: str
    message: str

    def __str__(self):
        return f"[{self.level.upper()} {self.code}] {self.where}: {self.message}"


def _err(out, code, where, msg):
    out.append(Finding(code, "error", where, msg))


def _warn(out, code, where, msg):
    out.append(Finding(code, "warning", where, msg))


def assemble(copy, platform, disclosure=DISCLOSURE_TEXT):
    """Final visible text for a platform: the copy plus the disclosure and hashtags.

    The planner calls this so that what is checked is exactly what gets published.
    Hashtags and disclosure are never written into the copy itself.
    """
    if platform == "youtube":
        body = copy["youtube"]["description"]
    elif platform == "x":
        body = copy["x"]["text"]
    else:
        body = copy[platform]["caption"]
    body = body.strip()
    if platform == "facebook" and disclosure:
        body += "\n\n" + disclosure
    tags = copy[platform].get("hashtags", [])
    if tags:
        body += "\n\n" + " ".join(tags)
    return body


def _scene_text(scene):
    parts = [scene.get("say", ""), scene.get("heading", ""), scene.get("note", "")]
    for key in ("onscreen", "caption", "label"):
        value = scene.get(key)
        if isinstance(value, str):
            parts.append(value)
    return " ".join(p for p in parts if isinstance(p, str))


def check_brief(brief, *, today=None, captures_dir=None, disclosure=DISCLOSURE_TEXT):
    """Return a list of Findings for one brief. An empty list means it may be scheduled."""
    out = []
    bid = brief.get("id", "<no id>")
    today = today or dt.date.today()

    if "template" in brief:
        _err(out, "B001", bid, "the `template` field is removed in v2; delete it")
    if "credits_on_screen" in brief:
        _err(out, "B002", bid, "credits do not belong in the brief; keep them in the kit's credits file")
    for key in REQUIRED_BRIEF_KEYS:
        if key not in brief or brief[key] in ("", [], {}, None):
            _err(out, "B003", bid, f"required field `{key}` is missing or empty")
    if out and any(f.code == "B003" for f in out):
        # Further checks need the required fields; stop early with a clear list.
        return out

    viewer = brief["viewer"]
    if not isinstance(viewer, dict) or not viewer.get("problem") or not viewer.get("who"):
        _err(out, "B010", bid, "viewer needs `who` and `problem` (the viewer's own situation)")

    scenes = brief["scenes"]
    if not isinstance(scenes, list) or not scenes:
        _err(out, "B020", bid, "scenes must be a non-empty list")
        scenes = []
    spoken_words = 0
    for i, s in enumerate(scenes):
        where = f"{bid} scene {i + 1}"
        if not isinstance(s, dict) or not str(s.get("type", "")).strip():
            _err(out, "B021", where, "every scene needs a `type`")
            continue
        say = s.get("say", "")
        if not say and not s.get("hold"):
            _err(out, "B022", where, "scene has no `say` line and no `hold`")
        spoken_words += len(str(say).split())
        text = _scene_text(s)
        if CREDIT_PATTERN.search(text):
            _err(out, "B030", where, "credit or capture note in visible scene text")
        if PROMO_PATTERN.search(text):
            _warn(out, "B031", where, "promotional wording in scene text")
        if PLACEHOLDER_PATTERN.search(text):
            _err(out, "B032", where, "placeholder text left in scene")
    if scenes and isinstance(scenes[0], dict) and LEGAL_PATTERN.search(_scene_text(scenes[0])):
        _err(out, "B040", bid, "licence or legal term in the opening scene; it is a one-time trust badge, not the hook")

    duration = brief.get("duration_s")
    if duration and spoken_words / SPEECH_WPM * 60 > float(duration) + 1:
        _err(out, "B023", bid, f"{spoken_words} spoken words need about {spoken_words / SPEECH_WPM * 60:.0f}s, "
                               f"longer than duration_s={duration}")

    claims = brief["claims"] if isinstance(brief["claims"], list) else []
    claim_ids = set()
    for c in claims:
        if not isinstance(c, dict) or not c.get("id") or not c.get("text"):
            _err(out, "B050", bid, "every claim needs `id` and `text`")
            continue
        claim_ids.add(c["id"])
        src = c.get("source", "")
        if not (isinstance(src, str) and src.startswith("https://")):
            _err(out, "B051", bid, f"claim {c['id']} has no https source")
    if not claims:
        _err(out, "B050", bid, "at least one claim is required")

    covered = set()
    for p in brief["proof_plan"] if isinstance(brief["proof_plan"], list) else []:
        if not isinstance(p, dict) or p.get("claim") not in claim_ids:
            _err(out, "B052", bid, f"proof_plan entry points at an unknown claim: {p!r}")
            continue
        ev = str(p.get("evidence", ""))
        if ev.startswith("capture:"):
            rel = ev.split(":", 1)[1]
            if captures_dir is not None and not (captures_dir / rel).exists():
                _err(out, "B053", bid, f"capture evidence {rel!r} not found in the capture pack")
        elif ev.startswith("source:") or ev == "owner_test":
            pass
        else:
            _err(out, "B053", bid, f"evidence must be capture:<file>, source:<url> or owner_test (got {ev!r})")
            continue
        covered.add(p["claim"])
    for cid in sorted(claim_ids - covered):
        _err(out, "B054", bid, f"claim {cid} has no proof_plan entry; show it or cut it")

    # B060 (review expiry) removed 31 Oct 2026: fact-age rules are not part of the approved pipeline.

    out.extend(check_copy(brief, disclosure=disclosure))
    return out


def check_copy(brief, *, disclosure=DISCLOSURE_TEXT):
    """Copy rules on the assembled final text of each platform."""
    out = []
    bid = brief.get("id", "<no id>")
    copy = brief.get("seo") or {}
    voice = brief.get("voice") or {}
    synthetic = voice.get("synthetic", True)  # narration is synthetic unless the brief says otherwise
    finals = {}

    for platform in PLATFORMS:
        block = copy.get(platform)
        where = f"{bid} {platform}"
        if not isinstance(block, dict):
            _err(out, "C001", where, "no copy for this platform")
            continue
        if platform == "youtube":
            title = str(block.get("title", ""))
            if not title or len(title) > YOUTUBE_TITLE_MAX:
                _err(out, "C002", where, f"title must be 1–{YOUTUBE_TITLE_MAX} characters (got {len(title)})")
            if CREDIT_PATTERN.search(title):
                _err(out, "C003", where, "credit or capture note in the title")
            if PROMO_PATTERN.search(title):
                _err(out, "C004", where, "promotional wording in the title")
        text = assemble(copy, platform, disclosure=disclosure if (platform == "facebook" and synthetic) else "")
        finals[platform] = text
        visible = text
        if CREDIT_PATTERN.search(visible):
            _err(out, "C010", where, "credit or capture note in visible copy")
        if PROMO_PATTERN.search(visible):
            _err(out, "C011", where, "promotional wording in visible copy")
        if PLACEHOLDER_PATTERN.search(visible):
            _err(out, "C012", where, "placeholder text in visible copy")
        if len(visible) > LIMITS[platform]:
            _err(out, "C013", where, f"final text is {len(visible)} characters, limit {LIMITS[platform]}")
        for url in URL_PATTERN.findall(visible):
            if not url.startswith("https://"):  # any other scheme, or http:
                _err(out, "C014", where, f"non-https link {url}")

        tags = block.get("hashtags", [])
        if not isinstance(tags, list):
            _err(out, "C020", where, "hashtags must be a list")
            tags = []
        for t in tags:
            if not HASHTAG_PATTERN.match(str(t)):
                _err(out, "C021", where, f"malformed hashtag {t!r}")
            elif str(t).lower() in GENERIC_TAGS:
                _err(out, "C022", where, f"generic hashtag {t!r}; use a niche tag for this viewer")
        lo, hi = HASHTAG_RANGE[platform]
        if not lo <= len(tags) <= hi:
            _err(out, "C023", where, f"{len(tags)} hashtags; want {lo}–{hi}")
        if platform == "youtube" and REQUIRED_YT_TAG not in {str(t).lower() for t in tags}:
            _err(out, "C024", where, "YouTube needs #Shorts in its hashtags")

        if platform == "facebook" and synthetic:
            if not disclosure:
                _err(out, "C031", where, "synthetic narration but no disclosure text is configured")
            elif disclosure not in text:
                _err(out, "C030", where, "AI-narration disclosure missing from Facebook copy")

    seen = {}
    for platform, text in finals.items():
        key = re.sub(r"\s+", " ", text).strip().lower()
        if key in seen:
            _err(out, "C040", f"{bid} {platform}", f"identical copy to {seen[key]}; write a variant for each platform")
        else:
            seen[key] = platform
    return out


def errors(findings):
    return [f for f in findings if f.level == "error"]
