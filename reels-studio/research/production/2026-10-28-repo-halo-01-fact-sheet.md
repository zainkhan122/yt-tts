# Fact sheet — repo-halo-01 (halo-overlay)

Checked 2026-10-28 (GitHub API + README). Refresh `stars` at render time.

| Claim | Source | Checked |
|---|---|---|
| Minimal AI assistant that floats over your screen, listens to the conversation, sees the screen, gives short suggestions | README intro, github.com/stormydayy/halo-overlay | 2026-10-28 |
| 516 stars, 36 forks, GPL-3.0, created 2026-10-25 | GitHub API | 2026-10-28 13:56 UTC (manifest) |
| From-scratch rewrite of sohzm/cheating-daddy: one OpenAI-compatible client (Gemini, Groq, OpenAI, OpenRouter, Ollama, LM Studio), ~3,100 lines, 0 runtime deps, 27 unit tests, contextIsolation + sandbox + strict CSP, OS-encrypted keys | README "What's new" table | 2026-10-28 |
| Rewind (v2.1): Ctrl+Shift+Enter → last 30 s–5 min transcript + keyframes → "what happened / what they need / what to say" | README "New: Rewind" | 2026-10-28 |
| Two audio channels labelled Them/You; mic suppressed while system speech plays; auto-answer when a question is detected | README "Everything else" | 2026-10-28 |
| Profiles: interview, meeting, sales, negotiation, presentation, study | README "Everything else" | 2026-10-28 |
| Fully local option: Ollama + vision model; any whisper-compatible local server for speech; localhost needs no key | README "Fully local" | 2026-10-28 |
| Keys encrypted with OS safeStorage (DPAPI/Keychain/libsecret), never sent to UI; data only to configured providers; screen recording off by default | README "Privacy" | 2026-10-28 |
| Disclaimer: rules vary; many interviews, exams, employers and platforms prohibit outside help or recording | README "Disclaimer" | 2026-10-28 |

## Catches (mandatory)
- **GPL-3.0** app; you bring your own model key (or run local).
- No demo media in the repo (only `assets/icon.png`) — video evidence is our own captures of the repo page.
- Ethics is the real catch: the repo itself warns that many interviews/exams prohibit outside help.

## Risk gates
- No radar flags. Not promoting cheating: the honest-rules line is spoken in the catch (repo's own disclaimer).
- Licence clear (GPL-3.0); no third-party media needed.

## Media plan
- All scenes: own captures (`desktop-full.jpg` / `desktop-top.jpg`) with region cameras on the real README (h_halo, Rewind section, shortcuts, privacy).
- The repo page is the product surface (F1 repo-drop style, like repo-harp-01).
