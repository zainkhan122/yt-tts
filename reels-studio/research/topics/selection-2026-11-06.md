# Topic shortlist — decision record

Discovery: third-party GitHub trend report generated **Nov 5, 2026, 10:14 PM New York**: https://github.com/yaojiejia/agents-radar/issues/424 and https://github.com/HuggerHustle/ai-radar/issues/159. It is not an exhaustive scan of all registered TikTok/YouTube sources or proof of a strict rolling 24-hour ranking.

First-party analytics: only snapshots taken no later than **Nov 5, 2026, 2:00 PM New York**, a conservative cutoff because the system clock and the supplied local date disagree. YouTube 24–48h cohort, one observation per video nearest 36h: n=13, median 34 views. Agent-workflow analogs n=3, median 51; creative-media analogs n=3, median 34. Their samples are very small and ages vary: directional proxies, not estimates of performance for a new topic. No impressions/CTR were available.

Selection: third-party reported star growth strength (0–3: 3 >= 1,000; 2 >= 500; 1 < 500 or reported without a daily figure) + editorial utility/visual demonstrability (0–3) + bounded first-party analytics adjustment. Adj. = clamp(log2((cohort-median+1)/(baseline+1)), -1.5, +1.5); unknown cohorts neutral. The 12 examined candidates below are ordered by score; the top 10 are proposals, not new approvals. Star deltas are third-party estimates, not audited GitHub API history.

| Rank | Topic | Trend | Editorial fit | Analytics adj. | Total | Visual proof idea |
|---:|---|---:|---:|---:|---:|---|
| 1 | [vercel-labs/agent-desktop](https://github.com/vercel-labs/agent-desktop) | 3 | 3 | +0.57 | 6.57 | A robot opens and operates a desktop app |
| 2 | [max-sixty/worktrunk](https://github.com/max-sixty/worktrunk) | 2 | 3 | +0.57 | 5.57 | One repository branches into isolated agent workspaces |
| 3 | [NVIDIA/auto-ontology](https://github.com/NVIDIA/auto-ontology) | 3 | 2 | +0.57 | 5.57 | Tables form a graph before an agent asks a question |
| 4 | [scenario-labs/skills](https://github.com/scenario-labs/skills) | 2 | 3 | +0.00 | 5.00 | A single brief splits into image, video and 3D outputs |
| 5 | [career-ops-hq/career-ops](https://github.com/career-ops-hq/career-ops) | 1 | 3 | +0.57 | 4.57 | A CV and job posts flow into a scored shortlist |
| 6 | [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) | 1 | 3 | +0.57 | 4.57 | An agent reads a page and fills a form |
| 7 | [garrytan/gstack](https://github.com/garrytan/gstack) | 2 | 2 | +0.57 | 4.57 | A coding task flows through designer, reviewer and QA |
| 8 | [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) | 3 | 1 | +0.57 | 4.57 | Web pages are collected and transformed into structured data |
| 9 | [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 1 | 3 | +0.00 | 4.00 | A topic flows into script, footage, captions and video |
| 10 | [microsoft/VibeVoice](https://github.com/microsoft/VibeVoice) | 1 | 3 | +0.00 | 4.00 | Text becomes a voice waveform with multiple speakers |
| 11 | [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | 1 | 2 | +0.57 | 3.57 | An agent retrieves information from multiple sources |
| 12 | [google/skills](https://github.com/google/skills) | 1 | 1 | +0.57 | 2.57 | An agent chooses a skill and interacts with a Google service |

## Analytics comparison evidence

- Agent workflows: Co-op Anything 336 views at 35.78h; Gemini Agent 51 at 32.53h; WhatsApp MCP 34 at 30.78h. Median 51 vs 34 baseline.
- Creative-media: Higgsfield 34 views at 26.49h; Mosa 45 at 26.21h; Pomelli 14 at 24.87h. Median 34 vs 34 baseline.
- The 24–48h band still mixes ages; dates, topic, distribution, and content differ. Medians are descriptive, not causal.
- No comparable-specific group is available for every possible future topic. The score then makes no analytics adjustment and says so; editorial research and user approval remain mandatory.

## Caveats

- Repository descriptions were checked against commits existing before the analytics cutoff; live READMEs and current star totals can change. Demonstrations, pricing, hardware and access should be verified before scripting.
- Scenario needs an MCP connection and may incur costs; VibeVoice original TTS code has restrictions/removal history; review model access and consent.
- The previously approved NVIDIA SkillEvaluator remains the next approved production topic; this list does not change that.
- A fresh complete scan of registered social sources was not established for this decision. Topic-dedup checked current local covered registry; confirm semantic duplicates and remote queue before producing.
