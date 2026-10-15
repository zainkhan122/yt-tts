# RESEARCH — Indra OCR (repo-indra-01)

**Checked:** 2026-10-15, 08:00–08:05 UTC. **Owner topic approval:** 2026-10-15. **Planned output:** one English, artifact-only short video; no Release or Buffer action.

## Selection score (80/100; PIPELINE §2)

| Criterion | Points | Evidence / judgment |
|---|---:|---|
| Trend velocity | 19/25 | GitHub API: 282 stars; created 2026-10-13 11:07:11Z. At the 2026-10-15 08:05:11Z refresh, age was 44.97 h, or about **150.5 stars/day**. The raw radar displays 282/day because `trend_radar.py` divides by whole integer days; do not use that uncorrected rate. |
| Demo-ability | 20/20 | Ran the published `indra-ocr==0.3.2` package in OCR-only mode on a self-generated, image-only one-page invoice. It returned the line items and total correctly; the local viewer/CLI are documented. This is our own test, not the project's speed benchmark. |
| Audience breadth | 12/15 | Useful to people processing printed PDFs and images; document work is broad, though less universal than a general chatbot. |
| Social proof + gap | 6/15 | No direct Indra creator post appeared in today's 32-channel feed. Buffer history supports hands-on open-source demos generally, not Indra specifically. |
| Free / saves-money value | 8/10 | Local CPU workflow and no per-call service charge; code is Apache-2.0, but the model weights have a separate modified OpenRAIL-M license with use restrictions. |
| Freshness of angle | 15/15 | No Indra brief/publication appears in the repository's current records. The proposed synthetic-document test and explicit scan/script limitations are not a repeat of the last three videos. |

## Source-checked claims and caveats

1. **GitHub repository and live metadata** — https://github.com/datalab-to/indra and https://api.github.com/repos/datalab-to/indra (API refreshed 2026-10-15 08:01:29Z): 282 stars, 24 forks, created 2026-10-13, Apache-2.0 repository code, pushed 2026-10-15. The README documents a local CLI and viewer, PDF/image input, Markdown/plain-text/JSON output, and about 18 MB of model files.
2. **CPU speed** — the repository README's throughput table: on the authors' same x86 AMD EPYC/no-GPU machine and 300 OmniParseBench pages, OCR mode reached 7.3 pages/s on 4 cores and 49.4 pages/s on 32 cores. State the condition; do not imply every laptop gets 49 pages/s. The benchmark is the project's result, not an independent test.
3. **Model details and model license** — https://huggingface.co/datalab-to/indra-ocr and https://huggingface.co/datalab-to/indra-ocr/blob/main/LICENSE (model metadata refreshed 2026-10-15 08:01:29Z; model-card/license revision `ed345c7`). The main recognizer is described as about 1M parameters. The card distinguishes Apache-2.0 code from model weights under a modified OpenRAIL-M license; the repo says the weight terms allow research/personal use and eligible startups, but prohibit use competitively with Datalab's API. Do not call the whole project Apache-2.0 or unrestricted commercial use.
4. **Limitations** — https://github.com/datalab-to/indra#limitations: optimized for clean print; handwriting is unsupported; degraded/old scans score poorly. OCR on scans is limited to the listed scripts; Arabic/Urdu are not supported for scanned images, while digital PDFs with an existing searchable text layer can retain any script. Simple tables are more reliable than merged/nested or unruled tables.
5. **Local demo proof** — `captures/repo-indra-01/sample-scan.pdf` is a self-generated, image-only synthetic invoice with no real customer data. The command used `--mode ocr`, so it did not read an embedded text layer. The saved output recovered the two item rows and PKR 1,360 total. The observed 437 ms is one sandbox run and is not used as a performance promise.

## Editorial and asset decisions

- Lead with the before/after: a clean synthetic document becomes usable Markdown without a GPU; show the actual OCR output.
- Attribute benchmark numbers to the project's published test and state core count. Keep the scan/script limitations visible and distinguish code license from weight license.
- All demo inputs and composite visuals are generated for this video; no personal documents, third-party creator clips, or copied demo media. No on-screen credit captions; source/credit links go in the post kit and description.
- Buffer Insights snapshot: `reels-studio/tracker/buffer-insights.json`, fetched 2026-10-15 07:49:07Z, complete and coverage-valid: 69 shared video records, 65 expected tracked sent posts, and three Instagram records awaiting metric refresh (all 69 have sent timestamps). Internal YouTube top posts were DeepSeek local inference (972 views), Qwen3.8 local (807), and Papermorph (608); Instagram's Open Code Review post had 266 views. These support a practical open-source demo angle, not an Indra-specific viral claim.
