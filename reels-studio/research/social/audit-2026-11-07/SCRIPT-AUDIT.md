# Script audit · our seven vs the two reference accounts

**Owner's correction (2026-11-07):** *"You have not fully audited the script; your script reads like a readme file while
theirs is what a user needs, want to hear."* This document is that audit. It is the companion to `AUDIT.md` (which covered
frames, colour, layout, audio) and it is deliberately metrics-first, so the fix can be checked later.

**No code changes.** Everything here is measurement, diagnosis and a written spec.

---

## 1. What was measured

| Corpus | Files | Words | Source |
|---|---|---|---|
| `@buildwithai.club` (TikTok) | 10 | 1 671 | word-timed transcripts already in `measurements.json` |
| ours, batch 2026-11-08 | 7 | 857 | same ASR pass, same model, same settings |
| `@classified.ai` (Instagram) | 2 narrated | — | **excluded from this table**: Roman-Urdu speech, `tiny.en` garbles it, so a word-level register score would be noise. Its *visual* grammar is used qualitatively in §4. |

Tool: `script_audit.py` (in this folder) → `script_metrics.json`, per-video and per-group. Every number below is
reproducible with `python3 script_audit.py`.

Method: sentence split on `.?!`; per-100-word densities for person, promise, consequence, number and jargon terms; a
fixed word list for spec-sheet ("readme") verbs and for technical nouns; the first sentence classified into
question / situation / status-gap / definition / statement; the last sentence classified into comment-ask / save-ask /
action-ask / none; and a scan for a copyable prompt (a line the viewer says or types *into the tool*).

---

## 2. The numbers

| Metric (median per video) | **@buildwithai.club (n=10)** | **ours (n=7)** | Gap |
|---|---|---|---|
| words spoken | **163** | 120 | we say **26 % less** in a similar runtime |
| mean sentence length | 15.1 w | 12.9 w | we are choppier, not tighter |
| **"you / your" per 100 w** | **5.8** | 4.0 | we address the viewer 30 % less |
| **"you can / you get / you don't" per 100 w** | **2.1** | 0.9 | half |
| **consequence clauses per 100 w** ("so you can…", "before you…", "instead of…", "without…") | **1.3** | **0.0** | *we never say what the viewer gets* |
| **numbers per 100 w** (a number with a stake) | **3.7** | 0.9 | 4× fewer |
| **technical/jargon nouns per 100 w** (api, sdk, cli, module, runtime, mcp, gpu, schema…) | **0.0** | **2.6** | we speak spec, they speak product |
| **copyable prompt in the script** | **40 %** of videos | 14 % | they tell you what to *type* |
| **opens with a question** | **0 %** | **71 %** | our signature move is not theirs at all |
| opens with a status gap ("everyone…", "top 1 %", "someone just…") | **30 %** | 0 % | no social tension |
| **enumerated demo** (three ways / five connectors / one does X, another Y) | **40 %** | 14 % | no list to hang shots on |
| **admits a limit ("the catch")** | **30 %** | **86 %** | we make the compromise the section |
| **ends with "comment X and I'll pin it"** | **0 %** | **86 %** | their CTA is a save or an in-tool action |

Hook classification, all 17 scripts: reference **5 statement / 3 status-gap / 2 situation / 0 question**;
ours **5 question / 2 statement / 0 status-gap**.

---

## 3. The six ways ours reads like a README

Quoted lines are from the transcripts (`measurements.json`).

### S1. The tool is the subject; the viewer is not

| ours | reference |
|---|---|
| "It turns a command line agent into a loop on one machine… your rules pick which agent handles it." | "You tell it what you sell and who your ideal customer is." |
| "It installs Ubuntu, Node, and the harness inside the app with no root and no termux." | "You give it one task. It sends the same task to a bunch of agents." |
| "It exports GLB, URDF, USD, OBJ or STL" | "You just connect Claude code to your TV, give it the setup prompt, and approve the apps you wanted disabled." |
| "Every part edge and faces reach by name and the same program builds the same mesh every time." | "**You** can answer tool approvals, send a message while it's replying…" *(they have this too — but it is one sentence, not the whole script)* |

Ours is a description of a machine. Theirs is a description of **you operating a machine**. In ours the only "you" is
possessive ("your rules", "your agent") — the viewer owns things but never does anything.

### S2. Capability taxonomy instead of a promise

Ours states what the software *supports*; theirs states what changes for the viewer.

> ours: "A part takes two to six times fewer tokens than the same part in Blender Python or CAD query and the whole API
> fits in a prompt."
> theirs: "It takes your trade and simulates the rest of the trading day 10 000 times… **so you get to see the historical
> odds before putting your money on the line**."

The measured version of this is the **0.0 consequence clauses per 100 words**. Not one of our seven videos ever finishes
a sentence with a "so you can / before you / instead of / without" clause. The reference does it 1.3 times per 100 words —
roughly twice per video — and it is always where the value lands.

### S3. The limitation is a section, not a sentence

Six of seven of ours contain the literal phrase **"the catch"**, followed by a compatibility list:

> "The catch, you need Claude Code or Codex, and the story video needs Playwright and ffmpeg."
> "The catch it needs Blender's BPI module, which only ships for certain Python versions. So check yours first."

The reference admits limits too — but as a *concession inside the pitch*, and always paired with what still holds:

> "Of course, it's a simulation, not a guarantee."
> "You still approve emails before they're sent by default."
> "You still have to record, edit and upload yourself, but Claude can handle a huge part of the planning."
> "There's even a backup and restore option to get your old setup back."

Ours ends the pitch on friction ("the CLI is still in Chinese", "Android only for now", "a research preview", "not a
DeepSeek product"). The viewer's last impression is that the tool is unfinished. Theirs is that the tool is honest.

### S4. No action the viewer can take *inside the tool*

Reference scripts contain, in plain speech, the exact thing to type:

> "Ask Claude, **build me a mod that shows my agents progress**."
> "Just type **/handwritten** before your topic."
> "Then tell Claude, **interview me about this job** until you understand it well enough to do it without me."

4 of 10 have one. Ours have none — because a repo README often doesn't quote a prompt, and our brief format only carries
claims. This is also the single largest animation opportunity we are leaving on the floor: a typed prompt is a
shot with a beginning, middle and end that is *already synced to the voice* (see §4).

### S5. Our only CTA is the same CTA

> ours, 6 of 7: "…**Comment, loop, and I'll pin it.**" / "Comment, pocket, and I'll pin it." / "Comment, agent, and I'll pin it."

Reference closes with the next action *in the product* or with a save:

> "Save this for your next Cloud code session." (save-ask)
> "just use these three prompts and it will finally make sense." (action-ask)
> "So now Claude can research, browse, analyze your product and take action across your tools." (a summary, no ask at all)

0 of 10 ask for a comment. A repeated comment-ask is also the most obviously templated line in our batch — the viewer
hears the same ending seven times.

### S6. We open with a question the viewer didn't ask

Five of seven open on "Could your phone run your coding agent?", "What if your agent could render the shot itself?",
"Could an agent run your repo without you watching it?", "Would you…". The reference opens on a **situation the viewer is
in** ("If Claude is giving you a bad answer…", "your white-coded app could be leaking private data to hackers that you
wouldn't know"), a **status gap** ("Everyone gives Claude prompts, but the top 1 % give it playbooks"), or a **flat factual
bomb** ("Someone just built an entire YouTube team inside Claude and made it completely free").

A question invites an answer the viewer doesn't have yet; a situation puts them in the scene. Ours also front-loads the
product name in the same breath ("Could your phone run your coding agent? It's DSH. Go, an Android coding agent…"), which
turns second 3 into a spec line.

---

## 4. Why this is also the animation problem

Owner's third correction — *"you are very far behind in creation of real-look-like animations synced with script"* — is
caused partly by the writing. Reference sentences are **sequences with objects and state changes**; ours are
**definitions with attribute lists**. An animator can only draw what the sentence contains.

| Reference sentence | What it hands the animator |
|---|---|
| "It **maps out** how your app works, then **sends** AI agents **through your code**." | a codebase diagram being drawn, then agents travelling along paths |
| "**Before an issue gets confirmed**, another agent tries to prove the first one wrong." | a claim card, a second card pushing it back, a "confirmed" stamp that fails |
| "It can **share** what it finds with **another session** writing your landing page." | two windows, content moving from one to the other |
| "**Just type /handwritten** before your topic and it **explains the whole thing like notes** a 10-year-old could follow." | a command bar being typed, then a page becoming a notebook |
| "It **replaced** the entire home screen with a clean interface that looks like Apple TV." | a row of icons being wiped, a new grid sliding in |
| "**Every 15 minutes** Harvey **checks** what needs to happen next." | a clock advance, a checklist re-running, a row updating |

Ours, by contrast: *"It exports GLB, URDF, USD, OBJ or STL"* (a list of five nouns — the best we can draw is five chips);
*"The whole API fits in a prompt"* (an abstraction); *"Every part edge and faces reach by name"* (also abstraction);
*"The catch… BPI module… certain Python versions"* (a compatibility table).

**The rule this implies:** a line earns a shot only if it contains **a subject acting on an object with a visible change
of state**. Definitions, taxonomies and compatibility lists get no shot — they get a single card, or they get cut.

---

## 5. The register rules (spec, not code)

Each rule has a measurable threshold so a lint pass can enforce it later. Targets are set from the reference medians, not
from taste.

| # | Rule | Threshold (per 40–45 s script) |
|---|---|---|
| **SR1** | **Viewer as subject.** At least half of the sentences have "you" as the actor, not the tool. | `you_per_100` ≥ **6.0**; tool-as-subject sentences ≤ 50 % |
| **SR2** | **Every claim ends in a consequence.** Each feature sentence is followed or closed by what the viewer gets/avoids. | `consequence_per_100` ≥ **1.5**; **≥ 3** "so you / before you / instead of / without" clauses per video |
| **SR3** | **No jargon nouns.** If the word only appears in a README (api, sdk, cli, schema, runtime, module, wrapper, wrapper, mcp), it is replaced by the thing it does. | `jargon_per_100` ≤ **0.5** |
| **SR4** | **One copyable action.** The script says the exact prompt/command the viewer types, in their words. | ≥ 1 per video, spoken and shown typed on screen |
| **SR5** | **Stakes, not specs, for numbers.** A number is allowed only if the sentence says what it buys or costs the viewer. | `numbers_per_100` **2.5–4.0**, all attached to a stake or a verifiable public count (stars, downloads, subscribers) |
| **SR6** | **Limit as a concession, not a section.** Drop the standing "The catch" section; put one honest boundary inside the payoff, with what still holds. | ≤ 1 concession per video, never in the closing sentence, never as its own scene |
| **SR7** | **Open on a situation or a status gap, never a question.** | `share_opening_question` = **0**; hook ∈ {situation, status-gap, factual bomb} |
| **SR8** | **Enumerated demo.** The middle is 3 items, each with its own object and its own shot ("one does X · another does Y · the one I use is Z"). | 3 items, ≥ 1 shot each, item names differ in *kind* not just wording |
| **SR9** | **CTA rotates.** Comment-ask at most **1 in 3 videos**; others: save-ask, in-tool action, or no ask at all (reference: 0 % comment-ask). | `share_comment_ask` ≤ 0.33 |
| **SR10** | **Length**: a 40–45 s Short carries 145–165 words at 205–218 wpm (reference: 163 w / 224 wpm). | 145–165 words; `wpm` 195–218; `pauses_over_250ms_per_min` ≤ 12 |

Sentence templates that satisfy SR1–SR4 (to be used as *shapes*, never pasted):

- "If you **<situation the viewer is in>**, **<the tool>** does **<one visible action>** — **so you get <outcome>**."
- "You tell it **<what you already know>**. It **<does the thing>**. You **<approve / steer / take over>**."
- "Type **<exact words>** and it **<visible result>**."
- "One **<item kind>** does **<job A>**. Another does **<job B>**. The one I'd use is **<job C>**, because **<consequence>**."
- "It's not **<the thing people assume>**. It's **<the thing it is>** — and you still **<the boundary that stays yours>**."

---

## 6. Rewrites

Three worked examples from the batch. Claims are unchanged — every fact below is already in the spec's
`source_note`, so the traceability rule still holds. What changes is the **register** and, with it, the **shot list**.

### 6.1 unslop (127 words → 152 words)

*Before* (spoken, verbatim ASR — hence the garbled `clawed code` / `FMPag`): "Why does AI UI design all look the same? It's called Unslop. A skill for clawed code
or codex that turns vibe-coded, AI-looking screens into a designed interface. First, it audits the screen and lists the
slop, gradients, glows, emoji labels. Then it sets a direction from your product. You steer that direction first. Then it
fixes the screen pass by pass, spacing, color, icons, copy, type, motion, like a designer's red line review. It works the
next day, yes, react, view, or playing CSS, and on a live site when a link is all you have. The catch, you need clawed
code or codex, and the story video needs playwright and FMPag."

*After* — 152 words, 8 beats, each with the artifact it forces on screen:

| # | Spoken | Shot this line demands |
|---|---|---|
| 1 | "You know that screen. Purple gradient, glow behind the card, three emoji in the buttons. You didn't design that. The model did." | a "generated app" screen with the gradient and glow, one emoji badge; cursor hovering, then the same screen in three near-identical variants |
| 2 | "Give it to Unslop — a skill that runs inside Claude Code or Codex — and it starts by naming every piece of slop out loud." | the same screen, elements being outlined one by one, labelled `gradient`, `glow`, `emoji`, `centered hero` |
| 3 | "Then it asks one question: what is this product actually about? You answer. **That answer becomes the design direction** — the character, the one or two moments that carry the colour." | a direction card being typed with the user's answer; palette chips condensing out of it |
| 4 | "From there it fixes the screen in passes: spacing first, then colour, icons, copy, type, motion. **You watch it happen on your own page**, like a designer redlining in front of you." | the same screen at t+0 / t+1 / t+2 with only one attribute changing per pass; each pass labelled in the corner |
| 5 | "It works on whatever you already have — Next.js, React, Vue, or plain CSS — and on a live site when all you have is a link." | a stack chip row that highlights each framework as spoken, then a browser address bar with a URL being pasted |
| 6 | "One boundary: it needs Claude Code or Codex to run, and the story video wants Playwright and ffmpeg. **Everything else is the same screen you already shipped.**" | a two-row requirements card (agent ✓ / playwright ✓) then a cut back to the finished screen |
| 7 | "Look at the difference. Same layout. Same content. Different product." | before/after split, a drag divider travelling across |
| 8 | "Try it on the screen you're least proud of. Comment UNSLOP and I'll pin the repo." | end card with the comment box mock |

Word count 152, "you" 11×, consequence clauses 4, jargon 0 (`Next.js`, `React`, `Vue`, `CSS` are product names the viewer
knows), one copyable action, one concession inside the payoff, hook = situation not question.

### 6.2 dshgo (114 words → 149 words)

*Before* (verbatim ASR): "Could your phone run your coding agent? It's DSH Go, an Android coding agent for deep-seek harness, it runs on
your phone or drives the one on your computer. It installs Ubuntu, Node, and the harness inside the app with no root and
no termux. You can answer tool approvals, send a message while it's replying, and finish steps fold into one line. With
permissions, it reads the screen and taps for you, and sensitive actions stay with you by default, the catch. It's Android
only for now, and remote mode takes images only, not the whole web interface."

*After* (149 words):

| # | Spoken | Shot |
|---|---|---|
| 1 | "Your agent is stuck on your laptop. You're on a bus." | a terminal mid-task, then the laptop lid closing, phone in hand |
| 2 | "DSH Go puts the whole harness on the phone — Ubuntu, Node, the agent — installed inside the app, no root, no Termux." | phone frame, three rows installing with a progress bar |
| 3 | "A tool call comes in. You tap approve. **The agent keeps going while you're standing in a queue.**" | an approval card sliding up over the phone's task view, thumb tap, work resuming |
| 4 | "You can also type while it's mid-reply — the message queues instead of interrupting." | a composer with a queued bubble waiting behind the streaming answer |
| 5 | "Finished steps fold into one line, so a twenty-step run reads as five." | a long step list collapsing, counter 20 → 5 |
| 6 | "Give it screen permission and it can read the page and tap for you. Anything sensitive still waits for your thumb." | an accessibility overlay highlighting a button; a second tap blocked with a "you" badge |
| 7 | "It's Android first, and remote mode is for looking, not full control — your desktop keeps the keyboard." | one boundary card, then a split: phone viewing, laptop driving |
| 8 | "So the next time you're away from the desk, your agent isn't. Comment POCKET for the repo." | end card + comment box |

### 6.3 vork (115 words → 156 words) — beat map only

1. "You ask an agent for a shot. It gives you a paragraph of description and a render you can't edit." → *a chat reply, then a flat image, cursor poking at it uselessly*
2. "Vork hands the agent the renderer instead." → *the image crumples / a code editor opens beside it*
3. "The scene is code. Camera, light, geometry. The agent writes it, renders a preview, looks at its own image, and changes the camera." → *code lines typing; a preview refreshing three times with a different camera angle each time*
4. "It can drop a shader into a shot mid-render, because the GPU is part of the loop." → *a shader parameter dragged; the surface of the render reacting live*
5. "The examples run from a million self-steering birds to VFX cut into real footage." → *the murmuration still, then the tracked desk shot with wireframe overlay*
6. "What you give up: no editor to fall back on, and it wants a Vulkan or Metal GPU. What you keep: every shot is a file you can diff." → *boundary card, then a git-style diff of two scene files*
7. "Ask it for your next shot. Comment RENDER for the repo."

---

## 7. How this gets enforced (later, not in this pass)

No code was changed. When the owner approves a rebuild, the script rules map onto the existing gates like this:

- `SR1, SR3, SR5, SR10` are countable from the transcript → a `script_lint` stage next to the existing plan lint
  (`research/production/batch-*/build.py` already lints claims, so the plumbing exists).
- `SR4` needs one new spec field: `copyable_action` (the exact string the viewer types). It is also what the animation
  layer types on screen, which is why it must live in the brief, not in the voice text alone.
- `SR7, SR8, SR9` are structural: hook type, three-item middle, CTA rotation. They belong in the brief schema
  (`PLAN` in `specs/*.py`) as `hook_type`, `demo_items[3]`, `cta_type`.
- `SR6` is a wording rule: ban the literal section title "The catch"; require the concession to sit inside a payoff beat.
- The wpm/word budget interacts with the existing QA gate: today's gate is 29–55 s / 167–211 wpm, and the reference runs
  224 wpm. **Recommendation: keep the gate but move the target to 195–215 wpm and 145–165 words** so the register has
  room to breathe. This needs owner sign-off because it is a measured gate.

---

## 8. Open questions for the owner

1. **Length vs pace.** 163 words needs ~224 wpm at 43.7 s. Our cap is 211 wpm. Do we (a) allow 215 wpm, (b) allow 48–52 s,
   or (c) accept ~145 words and drop one demo item?
2. **The comment CTA.** Reference never asks for a comment; ours does in 6 of 7. Do we retire it, keep it for one in three,
   or keep it because it is the only signal the channel currently converts on?
3. **The catch section.** It is currently a required beat (6 of 7 videos, its own scene). Do we demote it to a sentence
   inside the payoff — which removes one of the seven scenes we have to animate?
4. **Copyable action.** Adding `copyable_action` to the brief means the script will sometimes contain a prompt the README
   doesn't quote verbatim. Is that allowed, given the "every claim from the README" rule? (My reading: the *action* is a
   usage instruction, not a product claim — but it is your rule, so it is your call.)

---

*Files: this document; `script_audit.py` (the analyser); `script_metrics.json` (per-video and per-group numbers);
`AUDIT.md` (the visual/audio audit this sits beside); `measurements.json` (frame, audio and transcript data).*
