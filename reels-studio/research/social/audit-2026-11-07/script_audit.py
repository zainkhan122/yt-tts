#!/usr/bin/env python3
"""Script register audit: is the voice talking to a user, or reading a README?

Reads the transcripts already stored in measurements.json (same ASR pass as the visual audit, so the
comparison is like-for-like) and scores each script on the devices the reference accounts actually use:

  address      second person you/your, imperatives, "we/our"
  stake        numbers, money, time, consequence clauses ("so you can", "before you", "without")
  readme       spec-sheet verbs (provides / supports / allows / comes with / built on) and jargon nouns
  shape        opening move, enumeration, catch/concession, closing move (comment-ask / save-ask / none)
  copyable     does the script give the viewer a prompt or command they can paste

Usage: python3 script_audit.py [measurements.json]
"""
import json
import re
import sys
from pathlib import Path

RE_VERB_IMPERATIVE = set("""start type ask tell give install open add make use save check copy run connect try
comment stop let set paste drop build create pick take send keep avoid point write put switch turn name share""".split())

README_VERBS = ["provide", "provides", "support", "supports", "allow", "allows", "enable", "enables",
               "consists", "consist", "comes with", "built on", "written in", "designed for", "based on",
               "includes", "offers", "is a", "it is a", "package", "framework", "implements"]

JARGON = ["api", "sdk", "cli", "config", "module", "library", "repo", "node", "git", "runtime", "wrapper",
          "mcp", "css", "python", "gpu", "shader", "bpy", "urdf", "glb", "stl", "obj", "schema", "parameter",
          "flag", "version", "npm", "win", "gmail", "playwright", "ffmpeg", "claude code", "codex", "query",
          "vulkan", "metal", "android", "llm", "tokens", "edge", "mesh", "joints"]

BENEFIT = ["so you can", "so you get", "so it", "so they", "that way", "instead of", "without", "before you",
           "no need", "you don't have to", "you still", "for free", "free", "in one place", "all in one"]

CATCH = ["the catch", "of course", "not a guarantee", "by default", "only for now", "for now", "still"]

STATUS_GAP = ["top 1%", "no one", "nobody", "everyone", "most people", "actually", "just dropped",
              "blowing up", "someone just", "people are now", "you wouldn't know", "stop "]

NUMWORD = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
           "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "twenty": 20, "hundred": 100,
           "thousand": 1000, "million": 1000000}


def words_of(segs):
    if not segs:
        return ""
    if isinstance(segs, dict):
        segs = list(segs.values())
    if isinstance(segs[0], str):
        return " ".join(segs)
    return " ".join(s.get("text", "") for s in segs)


def sentences(text):
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    return parts or [text]


def per100(n, total):
    return round(100.0 * n / max(1, total), 1)


def score(text):
    low = text.lower()
    toks = re.findall(r"[a-z0-9']+", low)
    total = len(toks)
    sents = sentences(text)
    words = [w for w in toks]
    you = sum(1 for w in toks if w in ("you", "your", "yours", "you're"))
    we = sum(1 for w in toks if w in ("we", "our", "us"))
    it = sum(1 for w in toks if w in ("it", "its", "it's"))
    nums = sum(1 for w in toks if w.isdigit()) + sum(1 for w in toks if w in NUMWORD)
    jarg = sum(1 for j in JARGON if j in low)
    readme = sum(low.count(v) for v in README_VERBS)
    benefit = sum(low.count(b) for b in BENEFIT)
    catch = [c for c in CATCH if c in low]
    gap = [g for g in STATUS_GAP if g in low]
    imper = 0
    for s in sents:
        first = re.findall(r"[a-z']+", s.lower())
        if first and first[0] in RE_VERB_IMPERATIVE:
            imper += 1
    enum = bool(re.search(r"\b(three|3|five|5|four|4|number one|first,|number 1)\b", low))
    first_person_sing = bool(re.search(r"\bi\b", low))
    q_open = sents[0].strip().endswith("?")
    closing = sents[-1].lower()
    if "comment" in closing:
        cta = "comment-ask"
    elif "save" in closing:
        cta = "save-ask"
    elif closing.startswith(("ask", "type", "just use", "give it", "start", "try")):
        cta = "action-ask"
    elif "follow" in closing:
        cta = "follow-ask"
    else:
        cta = "none"
    copyable = bool(re.search(r"(ask (claude|it|the agent)|tell it,|type /|just type|slash |give it (a|that|this)|"
                              r"install it in|start with the)", low))
    # consequence clauses: the sentence tells the viewer what they get / avoid
    consequence = len(re.findall(r"\bso (you|it|they|now|that)|that way|instead of|before you|without|"
                                 r"no need|doesn't need|don't need|you still|for free\b", low))
    # "you get / you can / you don't have to" promises
    promise = len(re.findall(r"\byou (can|get|don't|don't have|still|just|need|want|have|steer|answer|"
                             r"approve|authorize|give|ask|type|tell)\b|you'll|you're", low))
    # definition chain: naming the product as a category
    definition = len(re.findall(r"\bit'?s (called )?[a-z]+|\bis (a|an) [a-z]+|\bcalled [a-z]+", low))
    # list dumping: longest comma run inside one sentence
    comma_run = max((len(re.findall(r",", s)) for s in sents), default=0)
    # shortest / longest sentence
    slen = [len(re.findall(r"[a-z0-9']+", x.lower())) for x in sents]
    # hook classification
    first = sents[0].strip().lower()
    if first.endswith("?"):
        hook = "question"
    elif re.search(r"\b(if|when) you", first):
        hook = "situation"
    elif re.search(r"\b(everyone|most people|the top|nobody|no one|someone just|people are now)", first):
        hook = "status-gap"
    elif re.search(r"\bit'?s (dsh|called|a |an )|^\w+ is a", first):
        hook = "definition"
    else:
        hook = "statement"
    return {
        "words": total,
        "sentences": len(sents),
        "w_per_sentence": round(total / max(1, len(sents)), 1),
        "you_per_100": per100(you, total),
        "we_per_100": per100(we, total),
        "it_per_100": per100(it, total),
        "numbers_per_100": per100(nums, total),
        "imperatives": imper,
        "imperative_per_sentence": round(imper / max(1, len(sents)), 2),
        "benefit_clauses": benefit,
        "benefit_per_100": per100(benefit, total),
        "readme_verbs": readme,
        "readme_per_100": per100(readme, total),
        "jargon_terms": jarg,
        "jargon_per_100": per100(jarg, total),
        "catch_present": bool(catch),
        "status_gap_markers": gap,
        "enumeration": enum,
        "opening_question": q_open,
        "first_person_singular": first_person_sing,
        "closing_cta": cta,
        "copyable_prompt": copyable,
        "consequence_clauses": consequence,
        "consequence_per_100": per100(consequence, total),
        "you_promises": promise,
        "promise_per_100": per100(promise, total),
        "definition_chain": definition,
        "max_comma_run": comma_run,
        "longest_sentence_words": max(slen),
        "mean_sentence_words": round(sum(slen) / max(1, len(slen)), 1),
        "hook_type": hook,
        "opening": sents[0].strip(),
        "closing": sents[-1].strip(),
    }


def main(path="measurements.json"):
    m = json.loads(Path(path).read_text())
    out = {}
    for group, blob in m["groups"].items():
        if "Instagram" in group:
            continue  # ASR of Roman-Urdu is not reliable enough for a word-level register score
        tr = blob.get("transcripts") or {}
        out[group] = {f: score(words_of(segs)) for f, segs in tr.items()}
    # group medians on the comparable keys
    keys = [k for k in next(iter(next(iter(out.values())).values())) if isinstance(
        next(iter(next(iter(out.values())).values()))[k], (int, float))]
    med = {}
    for g, rows in out.items():
        vals = {k: sorted(r[k] for r in rows.values()) for k in keys}
        med[g] = {k: vals[k][len(vals[k]) // 2] for k in keys}
        n = len(rows)
        med[g]["n"] = n
        med[g]["share_comment_ask"] = round(sum(r["closing_cta"] == "comment-ask" for r in rows.values()) / n, 2)
        med[g]["share_copyable_prompt"] = round(sum(r["copyable_prompt"] for r in rows.values()) / n, 2)
        med[g]["share_catch"] = round(sum(r["catch_present"] for r in rows.values()) / n, 2)
        med[g]["share_enumeration"] = round(sum(r["enumeration"] for r in rows.values()) / n, 2)
        med[g]["share_opening_question"] = round(sum(r["opening_question"] for r in rows.values()) / n, 2)
    return {"per_video": out, "group_median": med}


if __name__ == "__main__":
    res = main(sys.argv[1] if len(sys.argv) > 1 else "measurements.json")
    print(json.dumps(res["group_median"], indent=1))
    dst = Path("script_metrics.json")
    dst.write_text(json.dumps(res, indent=1))
    print("->", dst)
