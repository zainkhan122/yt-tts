# Long-form production contract

No long video is queued by this example. Uploading is separate from production:
prepare a genuine 16:9 episode with Option 3 narration and reviewed assets first.
A dedicated long-form rendering template is not claimed implemented by the uploader.

**Cadence:** up to three episodes/week: Tuesday repo walkthrough, Friday AI-news
roundup, Sunday tested AI tools. Start with two if three would compromise research
or editing. Target 6–10 minutes; never stretch a 45-second script into a padded video.

**Script:** specific result/hook → show proof → use-case context → 3–5 structured
sections → real limitations/costs → useful conclusion. Flow-style complete sentences,
about 15 words/sentence; approved Option 3 everywhere. Sources rechecked before
publication. No on-screen credit captions; credits belong in the description.

**Thumbnail:** 2–5 words (max 6), 1–3 large bold lines in Anton, one clear focal
visual, Midnight + Yellow + Sky brand palette, no tiny interface screenshot as the
main message. Export 1280×720 plus an actual 250px-wide preview. Shorten the hook
instead of shrinking the type. The agent must inspect the 250px version before
approval; automatic text-height/contrast checks alone are insufficient.

Store an actual production brief at `briefs/long/<id>.json` with:

```json
{
  "id": "long-example-01",
  "format": "long",
  "category": "tool",
  "duration_seconds": 480,
  "contains_synthetic_media": false,
  "chapters": [
    {"start_seconds": 0, "title": "What the tool actually does"},
    {"start_seconds": 40, "title": "The real demo"},
    {"start_seconds": 210, "title": "Where it falls short"},
    {"start_seconds": 390, "title": "Who should use it"}
  ],
  "thumbnail": {"headline": ["TESTED", "NOT HYPED"], "kicker": "AI TOOLS", "highlight_line": 1},
  "seo": {
    "keyword": "specific tool name",
    "youtube": {
      "title": "Specific Tool Name: What Works, What Does Not",
      "description": "A specific, accurate summary, with the result first. Replace all placeholders after actual research.",
      "hashtags": ["#AItools", "#ArtificialIntelligence", "#Hypeless"],
      "tags": ["specific tool name", "specific tool tutorial", "AI tools"]
    }
  },
  "sources": ["https://example.com/replace-with-primary-source"],
  "credits": "Actual media owners and licences; no fabricated credits."
}
```

The example is documentation, NOT an uploadable brief. Chapters must match the
final render, not an approximate draft outline.

Upload these finished artifacts to a GitHub Release (not to git or Pages):

- `<id>.mp4`
- `<id>-manifest.json`
- `<id>-thumbnail.jpg`
- `<id>-thumbnail-report.json`

The manifest must contain `id`, `format: long`, all true `qa.checks` including
`approved_voice`, `stages.voice.engine` containing the exact approved Chatterbox
configuration, and `video` with `sha256`, `width`, `height`, `duration_seconds`,
`video_codec: h264`, `audio_codec: aac`. The MP4's digest binds the QA to the file.

Build/validate the thumbnail with `tools/youtube/thumbnail.py`. Pin the artifacts
with `tools/youtube/queue_ctl.py enqueue`; this leaves the episode held. Approval
requires an expiry, a real mobile thumbnail review, and separate public-release
approval. See `tools/youtube/README.md` for uploader operation and recovery.
