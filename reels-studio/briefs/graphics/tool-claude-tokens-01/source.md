# Claude Code token limit — research note

Headroom compresses tool output, logs, files and RAG chunks before the agent reads them, and
reports 60 to 95 percent fewer tokens for JSON, 15 to 20 percent for coding agents.

Ponytail makes the agent write less code: its own benchmark reports 54 percent less code and
20 percent cheaper runs.

OmniRoute routes around the limit to third-party free tiers, claiming about 1.47 billion free
tokens a month across 352 providers.

Graphify maps a codebase once, locally, so the agent stops re-reading the same files.

Honest limit: these are third party plugins, none of them is made by Anthropic, and the numbers
are vendor reported, so measure your own repo.
