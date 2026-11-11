# Solid Glass — fact sheet (checked 2026-10-15)

Primary sources: GitHub repo `deeplethe/solid-glass` README + GitHub API (checked 2026-10-15T10:31Z).

- GitHub API: 904 stars, 12 forks, created 2026-10-12T09:19Z, MIT license, pushed 2026-10-15. "Nine hundred stars in three days" is accurate at check time.
- What it is: a design system for AI applications — one stylesheet (`src/solid-glass.css`) that restyles existing shadcn/ui components via their `data-slot`/classes; components need no changes. Requires a shadcn/ui project (React 19, Tailwind CSS 4).
- Positioning: between flat design and liquid glass; only an outline shows through so text stays readable (the video's hook claim, from README).
- Registry: 13 items (README badge). Own agent-focused components include status-glyph, tool-steps, ask-card, context-ring, diff-view, composer, reasoning. Install: `npx shadcn@latest add deeplethe/solid-glass/solid-glass`.
- Catches (mandatory): needs the shadcn/React/Tailwind stack; project is days old so expect breaking changes.
- Demo visuals are our own recreation/cards made for this video (no copied repo screenshots).
