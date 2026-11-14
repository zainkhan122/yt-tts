#!/usr/bin/env python3
"""SEO data generator: write the search copy for every platform, then let the rulebook judge it.

The pipeline used to require an agent to hand-write `brief["seo"]` for five platforms every time.
That is where the pipeline broke: a short could render and even pass the visual QA with no search
copy at all, or with copy that failed the platform rules at the scheduling hour.

This tool closes that gap. It generates the SEO block from what the brief already knows (title,
keywords, the spoken scenes, the claims, the viewer, the CTA), writes it into the brief, and then
runs the SAME checker the shipping gate uses (tools/seo_pack.py). If the generated copy breaks a
rule, the tool says so instead of shipping it.

  python3 tools/seo_generate.py briefs/<id>.json            # print the generated block
  python3 tools/seo_generate.py briefs/<id>.json --write    # write it into the brief
  python3 tools/seo_generate.py briefs/<id>.json --write --check
  python3 tools/seo_generate.py briefs/<id>.json --only youtube,instagram,facebook

Platforms connected to Buffer (config/publishing.json -> buffer.channels, enabled) are listed in
the output: those are the social networks the shorts are actually scheduled on. TikTok and X are
generated too, because the SEO rulebook requires every platform block to exist and validate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

GENERIC_TAGS = {"#ai", "#coding", "#video", "#tech", "#technology", "#viral", "#fyp", "#foryou",
                "#foryoupage", "#trending", "#programming"}
CREDIT = re.compile(r"\bcredits?\b|own (browser )?captures?|\(checked \d{4}|checked 20\d\d-", re.I)
LEGAL = re.compile(r"\b(licen[cs]e[ds]?|mit|apache|gpl|agpl|lgpl|bsd|mpl)\b", re.I)
SENT = re.compile(r"(?<=[.!?])\s+")
# Words that leave a sentence hanging when a cut lands right after them.
DANGLING = {"a", "an", "the", "and", "or", "but", "so", "if", "then", "than", "to", "of", "for", "with",
            "in", "on", "at", "by", "as", "is", "are", "was", "were", "be", "been", "being", "do", "does",
            "did", "have", "has", "had", "will", "would", "can", "could", "should", "may", "might", "must",
            "not", "no", "yes", "you", "your", "my", "it", "its", "that", "this", "these", "those", "up",
            "out", "over", "under", "from", "into", "about", "after", "before", "when", "while", "how",
            "what", "why", "who", "which", "because", "just", "very", "more", "most", "than", "each", "every"}


# ---------------------------------------------------------------- small helpers

def clean(text: str) -> str:
    """One line, no credit note, no stray whitespace."""
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    t = CREDIT.sub("", t)
    return t.strip(" ,;:-")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENT.split(clean(text)) if s.strip()]


def trim_dangling(text: str) -> str:
    """Drop the trailing function words a cut leaves behind ('...that you can' -> '...Veo 3')."""
    words = str(text or "").split()
    while words and words[-1].lower().strip(".,;:!?") in DANGLING:
        words.pop()
    return " ".join(words).rstrip(" ,;:-")


def shorten(text: str, limit: int) -> str:
    """Cut at a sentence, then a clause, then a word — never mid-phrase.

    A caption that ends "…trust only the independent" is worse than no caption, so the cut always
    lands on a boundary a reader would have paused at.
    """
    t = clean(text)
    if len(t) <= limit:
        return t
    for s in sentences(t):          # a whole sentence that fits
        if len(s) <= limit:
            return s
    cut = t[:limit]
    for sep in ("; ", " — ", ", ", " - ", " and "):   # a clause boundary
        idx = cut.rfind(sep)
        if idx > limit * 0.45:
            return trim_dangling(cut[:idx].rstrip(" ,;:-"))
    return trim_dangling(cut.rsplit(" ", 1)[0].rstrip(" ,;:-"))


def end_sentence(part: str) -> str:
    """A part of a paragraph must end like a sentence, or the paragraph runs together."""
    p = clean(part)
    if p and p[-1] not in ".!?":
        p += "."
    return p


def tag(phrase: str) -> str:
    """'seedance 2.0' -> '#Seedance20' (alphanumerics only, CamelCase)."""
    words = re.findall(r"[A-Za-z0-9]+", str(phrase or ""))
    if not words:
        return ""
    body = "".join(w[:1].upper() + w[1:] for w in words)
    if not re.match(r"[A-Za-z]", body):       # a tag must start with a letter
        body = "T" + body
    return "#" + body


def cap(text: str) -> str:
    t = clean(text)
    return t[:1].upper() + t[1:] if t else t


def keyword_of(brief: dict) -> str:
    seo = brief.get("seo") or {}
    kw = clean(seo.get("keyword") or "")
    if kw:
        return kw
    kws = brief.get("keywords") or []
    if kws:
        return clean(kws[0])
    title = clean(brief.get("title") or "")
    return title.split(":")[0].strip() or "this tool"


def aliases_of(brief: dict, keyword: str) -> list[str]:
    seo = brief.get("seo") or {}
    out = [clean(a) for a in (seo.get("aliases") or []) if clean(a)]
    for k in brief.get("keywords") or []:
        k = clean(k)
        if k and k.lower() != keyword.lower() and k not in out:
            out.append(k)
    return out[:4]


def parts_of(brief: dict) -> dict:
    """The brief's own material, split into the pieces the copy needs."""
    scenes = brief.get("scenes") or []
    hook = ""
    points, catch, cta = [], "", ""
    for s in scenes:
        say = clean(s.get("say") or "")
        sid = str(s.get("id") or "").lower()
        heading = clean(s.get("heading") or "")
        if sid == "catch" or "catch" in heading.lower():
            catch = say or catch
            continue
        if sid == "cta" or s is scenes[-1] and not cta:
            cta = say or cta
            continue
        if not hook:
            hook = say
        elif say:
            points.append(say)
    claims = [clean(c.get("text") or "") for c in (brief.get("claims") or []) if clean(c.get("text") or "")]
    if not hook and claims:
        hook = claims[0]
    return {"hook": hook, "points": points, "catch": catch, "cta": cta,
            "claims": claims, "viewer": brief.get("viewer") or {}, "niche": clean(brief.get("niche") or "")}


def tool_name(brief: dict, keyword: str) -> str:
    title = clean(brief.get("title") or "")
    if ":" in title:
        head = title.split(":")[0].strip()
        if head:
            return head
    return keyword


# ---------------------------------------------------------------- copy builders

def build_title(brief: dict, kw: str, p: dict) -> str:
    """Search phrase first, then the benefit. <= 100 chars hard, <= 60 recommended."""
    benefit = ""
    title = clean(brief.get("title") or "")
    if ":" in title:
        benefit = title.split(":", 1)[1].strip()
    if not benefit:
        claim = p["claims"][0] if p["claims"] else p["hook"]
        benefit = shorten(claim, 44)
    benefit = shorten(benefit, 44).rstrip(" ,;:-")
    out = f"{cap(kw)}: {benefit}" if benefit else cap(kw)
    if len(out) > 60:
        out = trim_dangling(shorten(out, 60).rstrip(" ,;:-"))
    if len(out) > 100:
        out = shorten(out, 100)
    return out


def build_description(brief: dict, kw: str, p: dict, link: str) -> str:
    """One paragraph, keyword in the first 150 chars, one link at most, 263-569 chars."""
    parts = [end_sentence(lead_of(brief, kw, p))]
    for claim in p["claims"][:2]:
        s = shorten(claim, 150)
        if s:
            parts.append(end_sentence(s))
    if p["catch"]:
        parts.append(end_sentence(shorten(p["catch"], 160)))
    if p["cta"]:
        parts.append(shorten(p["cta"], 110))
    body = " ".join(parts)
    if link:
        body += " " + link
    body = re.sub(r"\s+", " ", body).strip()
    if len(body) < 263:
        # too short for the reference band: add the viewer job, never filler
        job = clean((p["viewer"] or {}).get("job") or "")
        if job:
            body += " " + shorten(job, 120)
    if len(body) > 569:
        body = shorten(body, 569)
    return body


def lead_of(brief: dict, kw: str, p: dict) -> str:
    """The first clause of the copy: the search phrase, then the promise."""
    benefit = ""
    title = clean(brief.get("title") or "")
    if ":" in title:
        benefit = title.split(":", 1)[1].strip()
    if not benefit:
        fact = p["claims"][0] if p["claims"] else p["hook"]
        benefit = shorten(fact, 60)
    benefit = shorten(benefit, 60).rstrip(" ,;:-")
    return f"{cap(kw)}: {benefit}" if benefit else cap(kw)


def build_caption(brief: dict, kw: str, p: dict, platform: str) -> str:
    """Keyword first, one sourced fact, the honest catch, the ask. No links, <= platform limit."""
    bits = [end_sentence(lead_of(brief, kw, p))]
    fact = p["claims"][0] if p["claims"] else (p["points"][0] if p["points"] else "")
    if fact:
        bits.append(end_sentence(shorten(fact, 160)))
    if p["catch"]:
        bits.append(end_sentence(shorten(p["catch"], 120)))
    if p["cta"]:
        bits.append(shorten(p["cta"], 90))
    text = " ".join(b for b in bits if b)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    limit = {"tiktok": 300, "instagram": 400, "facebook": 400}[platform]
    if len(text) > limit:
        text = shorten(text, limit)
    return text


def build_x(kw: str, p: dict) -> str:
    bits = [cap(kw)]
    if p["claims"]:
        bits.append(end_sentence(shorten(p["claims"][0], 110)))
    if p["catch"]:
        bits.append(end_sentence(shorten(p["catch"], 100)))
    text = re.sub(r"https?://\S+", " ", " ".join(b for b in bits if b))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 220:
        text = shorten(text, 220)
    return text


def build_tags(kw: str, aliases: list[str], name: str, niche: str) -> list[str]:
    """YouTube backend tags: the keyword, at least two aliases, the tool and the niche."""
    out = [kw]
    out += [a for a in aliases if a.lower() != kw.lower()][:3]
    if name and name.lower() != kw.lower():
        out.append(name)
    if niche:
        out.append(niche)
    out.append(f"{kw} tutorial")
    out.append(f"{kw} alternative")
    seen, tags = set(), []
    for t in out:
        t = clean(t)
        k = t.lower()
        if not t or k in seen:
            continue
        seen.add(k)
        tags.append(t)
    return tags[:10]


TECH = re.compile(r"\b(?:[A-Z]{2,}[A-Za-z0-9]*|[A-Z][a-z]+[A-Z][A-Za-z0-9]*)\b")
TECH_SKIP = {"the", "and", "ai", "api", "web", "app", "its", "it"}


def tech_terms(texts) -> list[str]:
    """The technical nouns in the copy (CDP, REPL, SVG, CapCut) — the niche hashtags people search."""
    out: list[str] = []
    for t in texts:
        for m in TECH.finditer(str(t or "")):
            w = m.group(0)
            if w.lower() in TECH_SKIP or len(w) < 3 or w in out:
                continue
            out.append(w)
    return out


def build_hashtags(kw: str, aliases: list[str], name: str, niche: str, platform: str,
                   tech: list[str] | None = None) -> list[str]:
    """Exactly the owner's count (5), one built from the keyword, no generic tags."""
    out = []
    if platform == "youtube":
        out.append("#Shorts")
    out.append(tag(kw))
    for a in aliases:
        out.append(tag(a))
    if name:
        out.append(tag(name))
    if niche:
        out.append(tag(niche))
    for t in tech or []:
        out.append(tag(t))
    seen, tags = set(), []
    for t in out:
        if not t or t.lower() in seen or t.lower() in GENERIC_TAGS:
            continue
        seen.add(t.lower())
        tags.append(t)
    return tags[:5]


# ---------------------------------------------------------------- the generator

def generate(brief: dict) -> tuple[dict, list[str]]:
    """-> (seo block, notes about which platforms Buffer will publish)"""
    kw = keyword_of(brief)
    aliases = aliases_of(brief, kw)
    p = parts_of(brief)
    name = tool_name(brief, kw)
    niche = p["niche"]
    sources = [s for s in (brief.get("sources") or []) if str(s).startswith("https://")]
    tech = tech_terms([p["hook"]] + p["claims"] + p["points"])

    seo = {
        "keyword": kw,
        "aliases": aliases,
        "onscreen_first3s": clean((brief.get("seo") or {}).get("onscreen_first3s") or "") or
                            clean((brief.get("scenes") or [{}])[0].get("heading") or ""),
        "youtube": {
            "title": build_title(brief, kw, p),
            "description": build_description(brief, kw, p, sources[0] if sources else ""),
            "hashtags": build_hashtags(kw, aliases, name, niche, "youtube", tech),
            "tags": build_tags(kw, aliases, name, niche),
        },
        "tiktok": {"caption": build_caption(brief, kw, p, "tiktok"),
                   "hashtags": build_hashtags(kw, aliases, name, niche, "tiktok", tech)},
        "instagram": {"caption": build_caption(brief, kw, p, "instagram"),
                      "hashtags": build_hashtags(kw, aliases, name, niche, "instagram", tech)},
        "facebook": {"caption": build_caption(brief, kw, p, "facebook"),
                     "hashtags": build_hashtags(kw, aliases, name, niche, "facebook", tech)},
        "x": {"text": build_x(kw, p), "hashtags": build_hashtags(kw, aliases, name, niche, "x", tech)[:2]},
    }
    notes = []
    try:
        cfg = json.loads((ROOT / "config" / "publishing.json").read_text(encoding="utf-8"))
        channels = cfg.get("buffer", {}).get("channels", {})
        connected = [p_ for p_, c in channels.items() if c.get("enabled")]
        notes.append("buffer-connected: " + ", ".join(connected))
    except Exception:
        notes.append("buffer-connected: (publishing.json unreadable)")
    return seo, notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brief", type=Path)
    ap.add_argument("--write", action="store_true", help="write the block into the brief")
    ap.add_argument("--check", action="store_true", help="run tools/seo_pack.py on the result")
    ap.add_argument("--only", help="comma list of platforms to keep from an existing block")
    a = ap.parse_args(argv)

    brief = json.loads(a.brief.read_text(encoding="utf-8"))
    seo, notes = generate(brief)
    if a.only:
        keep = {x.strip() for x in a.only.split(",") if x.strip()}
        old = brief.get("seo") or {}
        merged = {k: v for k, v in old.items() if k in keep}
        merged.update({k: v for k, v in seo.items() if k in keep})
        seo = merged

    if a.write:
        brief["seo"] = seo
        a.brief.write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"seo written -> {a.brief}")
    else:
        print(json.dumps(seo, indent=2, ensure_ascii=False))
    for n in notes:
        print(n)

    if a.check:
        import seo_pack
        # check the GENERATED block, not the old one in the file
        probe = dict(brief)
        probe["seo"] = seo
        bid, errors, warns, findings, b, seo2, blocks, spoken5, onscreen = seo_pack.check(json.dumps(probe, ensure_ascii=False))
        for e in errors:
            print("  ERROR", e)
        for w in warns:
            print("  WARN ", w)
        print(f"seo_pack: {len(errors)} error(s), {len(warns)} warning(s)")
        return 1 if errors else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
