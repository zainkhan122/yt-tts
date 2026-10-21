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
GENERIC_TAGS = {"#ai", "#coding", "#video", "#tech", "#technology", "#viral", "#fyp", "#foryou", "#foryoupage", "#trending", "#programming"}
CREDIT_TEXT = re.compile(r"\bcredits?\b|own (browser )?captures?|\(checked \d{4}|checked 20\d\d-", re.I)
URL_X = 23  # X counts every link as 23 chars

# Stable rule IDs: code -> (severity, one-line meaning). The receipt stores code + exact message.
RULE_IDS = {
    "SP001": ("error", "seo.keyword present"),
    "SP010": ("warning", "keyword spoken in the first ~10 s"),
    "SP011": ("warning", "keyword in the on-screen text of the first 3 s"),
    "SP020": ("error", "platform block present"),
    "SP030": ("error", "field within the platform hard character limit"),
    "SP031": ("warning", "field within the recommended character limit"),
    "SP040": ("error", "hashtag count within the platform maximum"),
    "SP041": ("warning", "hashtag count within the recommended range"),
    "SP050": ("error", "hashtags are well formed"),
    "SP051": ("warning", "no generic tags (#fyp/#viral)"),
    "SP060": ("warning", "keyword within the first N words of the field"),
    "SP070": ("error", "youtube: #Shorts in the description hashtags"),
    "SP090": ("error", "no generic hashtags (#AI, #Coding, #Video, #Tech, #Viral...) — niche tags only"),
    "SP091": ("error", "no credits/attribution/capture-note text in visible copy (credits live in the kit)"),
    "SP071": ("warning", "youtube: keyword in the first 150 chars of the description"),
    "SP072": ("error", "youtube: backend tags within 500 chars"),
    "SP080": ("warning", "no licence/legal term in a title or first line (benefit-first copy)"),
    "SP081": ("warning", "no licence/legal term in the first 150 chars of the youtube description"),
}

# Viewer-benefit first (owner rule 2026-10-18, PLAYBOOK §9): legal detail goes below the fold.
LEGAL = re.compile(r"\b(licen[cs]e[ds]?|mit|apache|gpl|agpl|lgpl|bsd|mpl|openrail)\b", re.I)


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


def check(brief_path_or_text):
    """Validate one brief's seo block.

    -> (brief id, error strings, warning strings, findings). Strings carry a leading "[SPxxx] ";
    findings is the structured form [{"id", "severity", "message"}] that receipts persist.
    Reads a path (str/Path) or a raw JSON text (str starting with "{").
    """
    text = str(brief_path_or_text)
    b = json.loads(text) if text.lstrip().startswith("{") else json.loads(Path(text).read_text())
    bid = b.get("id") or "?"
    seo = b.get("seo") or {}
    kws = [seo.get("keyword", "")] + seo.get("aliases", [])
    kws = [k for k in kws if k]
    errors, warns, findings, blocks = [], [], [], []

    def add(code, message):
        severity = RULE_IDS[code][0]
        (errors if severity == "error" else warns).append(f"[{code}] {message}")
        findings.append({"id": code, "severity": severity, "message": message})

    if not kws:
        add("SP001", "seo.keyword missing")
    # spoken + on-screen alignment from the script
    scenes = b.get("scenes") or []
    spoken5 = " ".join(s.get("say", "") for s in scenes[:1])  # hook line ≈ first 4-5 s at ~170 wpm
    onscreen = seo.get("onscreen_first3s") or (scenes[0].get("headline", "") + " " + scenes[0].get("sub", "") if scenes else "")
    if kws and not has_kw(spoken5 + " " + " ".join(s.get("say", "") for s in scenes[1:3]), kws):
        add("SP010", "keyword not spoken in the first ~10 s: TikTok/YouTube index speech (say it in the hook if natural)")
    if kws and not has_kw(onscreen, kws + [w for k in kws for w in k.split() if len(w) > 3]):
        add("SP011", f"keyword not in on-screen text of the first 3 s ('{onscreen.strip()}')")
    for plat, (field, hard, soft, hmin, hmax, firstn) in RULES.items():
        p = seo.get(plat)
        if not p:
            add("SP020", f"{plat}: missing block")
            continue
        text = p.get(field, "")
        tags = p.get("hashtags", [])
        n = x_len(text + " " + " ".join(tags)) if plat == "x" else len(text)
        if n > hard:
            add("SP030", f"{plat}: {field} {n} chars > hard limit {hard}")
        elif n > soft:
            add("SP031", f"{plat}: {field} {n} chars > recommended {soft}")
        if not (hmin <= len(tags) <= hmax):
            add("SP040" if plat in ("instagram", "x") and len(tags) > hmax else "SP041", f"{plat}: {len(tags)} hashtags (want {hmin}-{hmax})")
        if any(not re.fullmatch(r"#\w+", t) for t in tags):
            add("SP050", f"{plat}: malformed hashtag in {tags}")
        if any(t.lower() in GENERIC_TAGS for t in tags if not (plat == "youtube" and t.lower() == "#shorts")):
            add("SP090", f"{plat}: generic hashtag(s) {[t for t in tags if t.lower() in GENERIC_TAGS]} — use niche tags that name the tool's audience or task")
        if CREDIT_TEXT.search(text or "") or CREDIT_TEXT.search(p.get("description", "") or ""):
            add("SP091", f"{plat}: credits/capture note in visible copy — move it to the kit, keep only a plain source link")
        if any(t.lower() in ("#fyp", "#foryou", "#foryoupage", "#viral") for t in tags):
            add("SP051", f"{plat}: generic tags (#fyp/#viral) carry no signal in 2026")
        if kws and not has_kw(text, kws, firstn):
            add("SP060", f"{plat}: keyword not within the first {firstn} words of the {field}")
        first_line = (text or "").split("\n")[0]
        if LEGAL.search(first_line):
            add("SP080", f"{plat}: licence/legal term in the {field} first line — open with who "
                         f"it's for and what it does for them; legal detail goes at the bottom")
        if plat == "youtube":
            if "#shorts" not in [t.lower() for t in tags]:
                add("SP070", "youtube: #Shorts missing from description hashtags")
            desc = p.get("description", "")
            if kws and not has_kw(desc[:150], kws):
                add("SP071", "youtube: keyword not in the first 150 chars of the description")
            if len(",".join(p.get("tags", []))) > 500:
                add("SP072", "youtube: backend tags exceed 500 chars")
        blocks.append((plat, p, text, tags))
    return bid, errors, warns, findings, b, seo, blocks, spoken5, onscreen


def render_report(b, seo, blocks, spoken5, onscreen, errors, warns, findings):
    out_dir = ROOT / "renders" / b["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    L = [f"# SEO pack: {b['id']}", "", f"**Primary keyword:** `{seo.get('keyword', '')}` · aliases: {', '.join(seo.get('aliases', [])) or '-'}",
         f"**Triple alignment:** spoken hook \"{spoken5[:90]}…\" · on-screen first 3 s \"{onscreen.strip()}\"", ""]
    names = {"youtube": "YouTube Shorts", "tiktok": "TikTok", "instagram": "Instagram Reels", "facebook": "Facebook Reels", "x": "X"}
    for plat, p, text, tags in blocks:
        L += [f"## {names[plat]}", ""]
        if plat == "youtube":
            desc_txt = p.get("description", "").strip()
            cr = (b.get("credits_on_screen") or "").strip()
            links = re.findall(r"[\w-]+(?:\.[\w-]+)+/[\w./-]+|[\w-]+\.(?:com|ai|org|io|dev|app|video)\b", cr)
            L += ["**Title**", "```", text, "```", "**Description**", "```", desc_txt + "\n\n" + " ".join(tags), "```",
                  "**Tags (backend)**", "```", ", ".join(p.get("tags", [])), "```", ""]
        else:
            L += ["```", text.strip() + ("\n\n" + " ".join(tags) if tags else ""), "```", ""]
    L += ["## Checks", ""] + [f"- ❌ {e}" for e in errors] + [f"- ⚠ {w}" for w in warns] + (["- ✅ all platform rules pass"] if not errors and not warns else [])
    (out_dir / "seo.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return out_dir / "seo.md", findings


def main():
    argv = sys.argv[1:]
    as_json = "--json" in argv
    args = [a for a in argv if a != "--json"]
    if not args:
        print(__doc__)
        return 2
    rc = 0
    report = {}
    for a in args:
        bid, errors, warns, findings, b, seo, blocks, spoken5, onscreen = check(a)
        path, _ = render_report(b, seo, blocks, spoken5, onscreen, errors, warns, findings)
        report[bid] = {"errors": errors, "warnings": warns, "findings": findings}
        if as_json:
            rc = rc or bool(errors)
            continue
        print(f"seo pack -> {path.relative_to(ROOT)}  ({len(errors)} errors, {len(warns)} warnings)")
        for e in errors:
            print("  ❌", e)
        for w in warns:
            print("  ⚠", w)
        rc = rc or bool(errors)
    if as_json:
        print(json.dumps(report, indent=2))
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
