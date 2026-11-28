# Source scanning and audit

Install the extractor in the environment that will run the scan: `python3 -m pip install yt-dlp`. The tool is read-only with respect to the source registry, post history and publication schedule. It writes the specified JSON output; do not point it at an existing valuable file.

Run a scan and report. For a user-specified day, use that date explicitly; otherwise derive yesterday from the actual clock in the requested timezone after checking it. Never reuse an old example date as the current date:

```sh
# Example: yesterday in Pakistan time. Verify the machine clock before using it.
python3 tools/recent_social_scan.py --date yesterday --timezone Asia/Karachi --hours 500 --limit 200 --workers 20 --output research/topics/source-audit-yesterday-pkt.json
python3 tools/source_scan_report.py research/topics/source-audit-yesterday-pkt.json --output research/topics/source-audit-yesterday-pkt.md
```

If the user specifies a target date, pass `--date YYYY-MM-DD` instead. Before any relative-date scan, run `python3 tools/date_context.py` and use its live today/yesterday for the timezone in question; never copy a date from an old shortlist, handoff or example command. To resolve `--date today` or `--date yesterday` from a user-provided reference date when clocks conflict, pass `--reference-date YYYY-MM-DD`; the JSON labels that reference `user_supplied`, not independently verified. With no date or reference the scanner uses the host clock in the specified timezone (default America/New_York). A project utility cannot change an assistant platform's injected system date; if the injected date, the user's stated date and the host clock disagree, report the disagreement and use the user-confirmed reference rather than silently treating any clock as verified. `--hours` marks the rolling window and does not change the explicit calendar-day classification. A target-day match is not proof that a post had appeared by the actual current instant when the clock is wrong. Always check the host observed timestamp in the JSON.

The output lists every active registered TikTok and YouTube source and includes all extracted entries and available metadata. YouTube Atom usually covers only its newest 15 videos, and flat listings often omit timestamps; supplying a `YOUTUBE_API_KEY` enables batch timestamp lookup. `--details` attempts individual lookups for unknowns, but can be slow and still fail. Unknowns are not silently treated as outside the target day. A limit-hit means the listing may be incomplete; increase `--limit` where practical. Extracted view/engagement counts reflect observation time, not target-day performance. Platforms may omit fields or block access. Exit 2 indicates incomplete coverage, not an empty result. Review duplicate topics against the authoritative publication trackers before recommending them. This script does not automatically run, deploy, or guarantee completeness.
