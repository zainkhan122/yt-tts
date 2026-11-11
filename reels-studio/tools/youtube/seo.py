"""Shared YouTube copy contract. Titles/hooks matter more than backend tags.

Never stuff a tag list into a description. Hashtags and backend tags are different.
The hidden correlation tag is for retry reconciliation, not a search-growth claim.
"""
import hashlib
import re


def tag_cost(tags):
    return sum(len(t) + (2 if " " in t else 0) for t in tags) + max(0, len(tags)-1)


def tracking_tag(item):
    return "hypeless-ref-" + hashlib.sha256((item["video_id"] + "\0" + item["asset_digest"]).encode()).hexdigest()[:20]


def keyword_hit(keyword, text, window=20):
    """Does the primary keyword appear *naturally* in this copy?

    Verbatim first (punctuation- and case-insensitive). Otherwise every keyword
    token must appear, in order, inside a window of `window` words - so
    "fx0 design agent" is satisfied by "fx0 is an open-source design agent" but
    not by the words scattered across a paragraph. The old verbatim-only rule
    rejected five of five live Shorts whose copy reads fine (run 39476928857:
    "A specific primary keyword must appear naturally in title/opening
    description") and blocked the YouTube enrichment worker entirely.
    """
    def stem(word):
        """Just enough stemming for copy: generators/generator, rewrites/rewriter, engineering/engineer.

        Applied repeatedly so both sides of a pair land on the same form
        (engineering -> engineer -> engine, engineer -> engine).
        """
        for _ in range(3):
            if len(word) <= 4:
                break
            for suffix in ("ies", "ing", "es", "ed", "er", "s", "e"):
                if word.endswith(suffix) and len(word) - len(suffix) >= 4:
                    word = word[:-len(suffix)] + ("y" if suffix == "ies" else "")
                    break
            else:
                break
        return word

    def words(value):
        return [stem(w) for w in re.findall(r"[a-z0-9]+", (value or "").casefold())]

    kw = words(keyword)
    text_words = words(text)
    if not kw or not text_words:
        return False
    for start in range(len(text_words)):
        chunk = text_words[start:start + len(kw) + window]
        pos = 0
        for word in chunk:
            if pos < len(kw) and word == kw[pos]:
                pos += 1
                if pos == len(kw):
                    return True
    return False


def validate(brief, kind="long", marker=None):
    youtube = brief.get("seo", {}).get("youtube", {})
    title = youtube.get("title", "").strip()
    description = youtube.get("description", "").strip()
    keyword = brief.get("seo", {}).get("keyword", "").strip()
    if not title or len(title) > 100:
        raise ValueError("YouTube title must be 1–100 characters")
    if not keyword or not keyword_hit(keyword, title + " " + description[:250]):
        raise ValueError("A specific primary keyword must appear naturally in title/opening description")
    tags = list(dict.fromkeys(t.strip() for t in youtube.get("tags", []) if isinstance(t, str) and t.strip()))
    if not tags:
        raise ValueError("Backend SEO tags are required (do not put this list in the description)")
    if marker and marker not in tags:
        tags.append(marker)
    if tag_cost(tags) > 500:
        raise ValueError("YouTube backend tags exceed 500 characters including separators/quotes")
    hashtags = youtube.get("hashtags", [])
    if not 1 <= len(hashtags) <= 5 or any(not re.fullmatch(r"#\w+", h) for h in hashtags):
        raise ValueError("Use 1–5 relevant, valid hashtags")
    if kind == "short" and "#shorts" not in [h.lower() for h in hashtags]:
        raise ValueError("Shorts metadata needs #Shorts")
    if kind == "long" and "#shorts" in [h.lower() for h in hashtags]:
        raise ValueError("Long videos must not be tagged #Shorts")
    chapters = brief.get("chapters", [])
    if kind == "long":
        if len(chapters) < 3 or chapters[0].get("start_seconds") != 0:
            raise ValueError("Long video needs at least three real chapters beginning at 0:00")
        previous = -10
        lines = []
        duration = brief.get("duration_seconds")
        for chapter in chapters:
            seconds = chapter["start_seconds"]
            if not isinstance(seconds, int) or seconds - previous < 10 or not chapter.get("title"):
                raise ValueError("Chapters need increasing timestamps and at least ten seconds per chapter")
            if duration and seconds >= duration:
                raise ValueError("Chapter lies outside the video")
            previous = seconds
            clock = (f"{seconds//3600}:{seconds//60%60:02}:{seconds%60:02}" if seconds >= 3600 else f"{seconds//60}:{seconds%60:02}")
            lines.append(clock + " " + chapter["title"])
        if duration and duration - previous < 10:
            raise ValueError("Final chapter must be at least ten seconds long")
        description += "\n\nCHAPTERS\n" + "\n".join(lines)
    sources = brief.get("sources", [])
    if not sources:
        raise ValueError("Source links are required for factual AI coverage")
    missing = [s for s in sources if isinstance(s, str) and s not in description]
    if missing:
        description += "\n\nSOURCES\n" + "\n".join(missing)
    # Credits never go in visible copy (owner rule 2026-10-21); they live in the kit's credits file.
    if kind == "long":
        description += "\n\nAI-generated narration. AI tools, minus the hype."
    description += "\n\n" + " ".join(hashtags)
    if len(description.encode("utf-8")) > 5000:
        raise ValueError("YouTube description exceeds 5,000 UTF-8 bytes after chapters, credits and hashtags")
    return {"title": title, "description": description, "tags": tags,
            "categoryId": "28", "defaultLanguage": "en", "defaultAudioLanguage": "en"}


def merge_tags_preserving_copy(video, tags):
    """videos.update replaces mutable parts: preserve existing snippet properties.
    Never include `status`, so tags enrichment cannot change privacy/scheduling.
    """
    source = video["snippet"]
    fields = ("title", "description", "categoryId", "defaultLanguage", "defaultAudioLanguage")
    snippet = {k: source[k] for k in fields if k in source}
    if not snippet.get("title") or not snippet.get("categoryId"):
        raise ValueError("Existing YouTube snippet lacks required fields")
    merged = list(dict.fromkeys(source.get("tags", []) + tags))
    if tag_cost(merged) > 500:
        raise ValueError("Merging existing and SEO tags exceeds limit; review without deleting owner metadata")
    snippet["tags"] = merged
    return {"id": video["id"], "snippet": snippet}
