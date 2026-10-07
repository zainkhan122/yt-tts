#!/usr/bin/env python3
"""
SEO pack: turn a brief's `seo` block into ready-to-paste, VALIDATED copy for YouTube Shorts, TikTok, Instagram Reels,
Facebook Reels and X. Copy is written per video (by the agent); this tool enforces 2026 platform rules
(PLAYBOOK.md §9) and the universal "triple keyword alignment":
  keyword in the first words of title/caption  +  on screen in the first 3 s  +  spoken in the first 5 s.

  python3 tools/seo_pack.py briefs/spotlight-universal-modder-01.json          # -> renders/<id>/seo.md (+ exit 1 on errors)

Brief schema:
  "seo": {"keyword": "AI game modding", "aliases": ["mod PC games with AI"],
          "youtube": {"title": "...", "description": "...", "hashtags": ["#Shorts", ...], "tags": ["...", ...]},
          "tiktok": {"caption": "...", "hashtags": [...]}, "instagram": {"caption": "...", "hashtags": [...]},
          "facebook": {"caption": "...", "hashtags": [...]}, "x": {"text": "...", "hashtags": [...]},
          "onscreen_first3s": "AI MODS ANY PC GAME"}   # optional (else the hook scene headline)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = {  # platform: (main field, hard max chars, soft max chars, hashtags min, hashtags max, keyword within first N words)
    "youtube": ("title", 100, 60, 3, 5, 4),
    "tiktok": ("caption", 4000, 300, 3, 5, 8),
    "instagram": ("caption", 2200, 400, 1, 5, 10),
    "facebook": ("caption", 5000, 400, 1, 5, 10),
    "x": ("text", 280, 240, 0, 2, 12),
}
URL_X = 23  # X counts every link as 23 chars


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())


def has_kw(text, kws, first_words=None):
    t = norm(text).split()
    if first_words:
        t = t[:first_words]
    blob = " " + " ".join(t) + " "
    return any((" " + " ".join(norm(k).split()) + " ") in blob for k in kws)


def x_len(text):
    return len(re.sub(r"https?://\S+|\b[\w.-]+\.(com|io|dev|ai|org)/\S*", "x" * URL_X, text))


def main():
    brief_path = Path(sys.argv[1])
    b = json.loads(brief_path.read_text())
    seo = b.get("seo") or {}
    kws = [seo.get("keyword", "")] + seo.get("aliases", [])
    kws = [k for k in kws if k]
    errors, warns, blocks = [], [], []
    if not kws:
        errors.append("seo.keyword missing")
    # spoken + on-screen alignment from the script
    scenes = b.get("scenes") or []
    spoken5 = " ".join(s.get("say", "") for s in scenes[:1])  # hook line ≈ first 4-5 s at ~170 wpm
    onscreen = seo.get("onscreen_first3s") or (scenes[0].get("headline", "") + " " + scenes[0].get("sub", "") if scenes else "")
    if kws and not has_kw(spoken5 + " " + " ".join(s.get("say", "") for s in scenes[1:3]), kws):
        warns.append("keyword not spoken in the first ~10 s: TikTok/YouTube index speech (say it in the hook if natural)")
    if kws and not has_kw(onscreen, kws + [w for k in kws for w in k.split() if len(w) > 3]):
        warns.append(f"keyword not in on-screen text of the first 3 s ('{onscreen.strip()}')")
    for plat, (field, hard, soft, hmin, hmax, firstn) in RULES.items():
        p = seo.get(plat)
        if not p:
            errors.append(f"{plat}: missing block")
            continue
        text = p.get(field, "")
        tags = p.get("hashtags", [])
        n = x_len(text + " " + " ".join(tags)) if plat == "x" else len(text)
        if n > hard:
            errors.append(f"{plat}: {field} {n} chars > hard limit {hard}")
        elif n > soft:
            warns.append(f"{plat}: {field} {n} chars > recommended {soft}")
        if not (hmin <= len(tags) <= hmax):
            (errors if plat in ("instagram", "x") and len(tags) > hmax else warns).append(f"{plat}: {len(tags)} hashtags (want {hmin}-{hmax})")
        if any(not re.fullmatch(r"#\w+", t) for t in tags):
            errors.append(f"{plat}: malformed hashtag in {tags}")
        if any(t.lower() in ("#fyp", "#foryou", "#foryoupage", "#viral") for t in tags):
            warns.append(f"{plat}: generic tags (#fyp/#viral) carry no signal in 2026")
        if kws and not has_kw(text, kws, firstn):
            warns.append(f"{plat}: keyword not within the first {firstn} words of the {field}")
        if plat == "youtube":
            if "#shorts" not in [t.lower() for t in tags]:
                errors.append("youtube: #Shorts missing from description hashtags")
            desc = p.get("description", "")
            if kws and not has_kw(desc[:150], kws):
                warns.append("youtube: keyword not in the first 150 chars of the description")
            if len(",".join(p.get("tags", []))) > 500:
                errors.append("youtube: backend tags exceed 500 chars")
        blocks.append((plat, p, text, tags))
    # render
    out_dir = ROOT / "renders" / b["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    L = [f"# SEO pack: {b['id']}", "", f"**Primary keyword:** `{seo.get('keyword', '')}` · aliases: {', '.join(seo.get('aliases', [])) or '-'}",
         f"**Triple alignment:** spoken hook \"{spoken5[:90]}…\" · on-screen first 3 s \"{onscreen.strip()}\"", ""]
    names = {"youtube": "YouTube Shorts", "tiktok": "TikTok", "instagram": "Instagram Reels", "facebook": "Facebook Reels", "x": "X"}
    for plat, p, text, tags in blocks:
        L += [f"## {names[plat]}", ""]
        if plat == "youtube":
            L += ["**Title**", "```", text, "```", "**Description**", "```", p.get("description", "").strip() + "\n\n" + " ".join(tags), "```",
                  "**Tags (backend)**", "```", ", ".join(p.get("tags", [])), "```", ""]
        else:
            L += ["```", text.strip() + ("\n\n" + " ".join(tags) if tags else ""), "```", ""]
    L += ["## Checks", ""] + [f"- ❌ {e}" for e in errors] + [f"- ⚠ {w}" for w in warns] + (["- ✅ all platform rules pass"] if not errors and not warns else [])
    (out_dir / "seo.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"seo pack -> renders/{b['id']}/seo.md  ({len(errors)} errors, {len(warns)} warnings)")
    for e in errors:
        print("  ❌", e)
    for w in warns:
        print("  ⚠", w)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
