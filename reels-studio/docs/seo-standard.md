# SEO standard for Shorts copy (owner 31 Oct)

Enforced by `tools/seo_pack.py`. Every error blocks the brief. Warnings are reported.

## Keyword
- One primary search phrase per video (`seo.keyword`), plus 2-3 aliases people actually type (`seo.aliases`).
- The primary phrase is spoken in the first 10 s (SP010, warning) and shown on screen in the first 3 s (SP011).

## YouTube Shorts
| Field | Rule | Code |
|---|---|---|
| Title | Contains the primary phrase within the first 4 words; a search phrase, not a slogan | SP060, SP100 |
| Description | Line 1 is a full sentence of 60+ chars that names the keyword; keyword within the first 150 chars | SP102, SP071 |
| Description | Exactly one link (the tool page). The only link allowed anywhere | SP103 |
| Description | Ends with `#shorts` and 3-4 niche hashtags, one built from the keyword | SP070, SP104 |
| Tags | 4-10 backend tags, including the keyword and at least two aliases; under 500 chars | SP101, SP072 |

## Instagram, Facebook, TikTok
| Field | Rule | Code |
|---|---|---|
| Caption | Keyword within the first 10 words (8 for TikTok) | SP060 |
| Caption | No link | SP103 |
| Hashtags | 3-4 niche hashtags, one built from the keyword | SP040/041, SP104 |

## X
- Keyword within the first 12 words; no link; at most 2 hashtags.

## Always
- Niche tags name the audience or the task. Generic tags (#AI, #viral, #fyp) are banned (SP090, SP051).
- Plain, accurate claims from the tool's own page or README. No numbers the source does not state.
- No credits, licences or legal text in visible copy (SP091, SP080, SP081).
