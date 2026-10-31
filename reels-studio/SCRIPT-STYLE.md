# Script style: viewer-first (MANDATORY for every script, human or AI)

Owner rule, 2026-10-30. Every spoken script in `briefs/*.json` (the `say` lines of each scene)
must follow this file. A script that breaks it is rejected, however accurate it is.

## 1. What viewer-first means

The viewer has a question or a problem in their head. The script starts there, answers it with
the tool, and explains only what the viewer needs to decide whether to try it.

- The script is what the viewer wants to hear, in the order they want to hear it.
- The tool is the answer, not the subject of a sales pitch.
- Speak like a person who has tried the thing and is telling a friend what it does.
- No product commentary ("this is a powerful, game-changing tool"). No promotional adjectives.
- No praise, no verdict on the tool's quality beyond the facts the viewer needs.
- Facts only. Every number and claim comes from the brief's `facts` and `claims`.

## 2. The rules (check every script against each one)

1. **Hook (first sentence, 12 words or fewer):** the viewer's question, or a concrete promise
   with a number when the number is true. The tool is named in the hook or the next sentence.
2. **Name by about 7 seconds** (usually the second sentence): what it is, in plain words.
3. **How it works, in order of use:** the first thing the viewer does, then the next. Short
   setup, real commands only when they are in the repo's own docs.
4. **One proof moment:** something the viewer can see or check, from the tool's own media.
5. **The catch, as user impact:** what the viewer must have or accept ("you need Node.js",
   "it's a preview", "Fire TV gets only the cleanup part"). Never a release-note or legal line.
6. **Close:** the viewer's benefit restated, then one question with the keyword CTA:
   "Comment KEYWORD and I'll pin the link."
7. **Sentences:** natural, connected, about 15 words each, never above 18. Vary the length.
   No clipped fragments in a row. Contractions are fine.
8. **Length:** 100–125 spoken words (about 35–42 seconds).
9. **No sources, licences, legal or privacy text, citations or links** in the spoken script.
   The tool's page link lives only in the YouTube description (see `GUIDELINES.md`).
10. **Numbers are exact.** Use the figure from the brief, with its scope ("in the authors'
    test", "on a Mac mini with 24 GB"). Round only as the brief allows.

## 3. The hook "sugar" (grab attention, stay true)

A plain question is good. Sugar makes it hit harder, if it stays accurate:

| Plain | With sugar | Why it works |
|---|---|---|
| Could a local AI model with 35 billion parameters run on your Mac? | Run a 35-billion-parameter AI model on your Mac with about 3 GB of memory. | Concrete number and outcome, in the viewer's terms. |
| Ever had an AI tutor forget everything you studied last week? | Your AI tutor forgot last week's lessons. This one remembers, and you can edit it. | Pain, then the payoff. |
| Is your Android TV home screen full of ads? | Your Android TV is full of ads. Clean it over Wi-Fi, no root. | Problem, then the fix with the key limit. |

**Accuracy test before any sugar is used:**
- Do not turn a scoped figure into a general one. "3 GB RAM" is wrong if the test used a 24 GB
  machine and the repo says the build runs on a 16 GB Mac. Write "about 3 GB of memory" and keep
  the machine in the proof line.
- Do not claim a result the brief does not show ("it's a lot faster" with no number).
- Keep it under 12 words. The keyword must be spoken within the first 3 seconds.

## 4. What to avoid (rejected for this channel)

- "In this video, I'll show you…" and any preamble.
- "Here's the thing", "game changer", "must-have", "insane", "mind-blowing", "you won't believe".
- Starting with the tool's name, its star count or its stats as the hook.
- Explaining the repo's layout, licence, install page or download links on screen or in speech.
- A robotic list of features in a row ("It does X. It does Y. It does Z.").
- A verdict that the tool is good or bad. Show the facts; the viewer decides.

## 5. Approved examples (owner-approved 2026-10-30, viewer-first)

These six scripts were approved by the owner. Use them as the reference for tone, rhythm and length.

**Example A, rea (reverse engineering)**
- Hook: "Ever wondered how an app really works inside? Now you can find out with rea, right from your coding agent."
- Name: "Point it at an app or a binary, and it digs into how it behaves. Want to build something similar? Start from what the app actually does, not guesses."
- How: "Setup is one command once Node.js is installed: npx rea-agents setup. It connects rea to Claude Code, Codex, Cursor and other agents."
- Proof: "For compiled programs, rea works with a disassembler like Hopper or Ghidra."
- Catch: "The catch: you need Node.js, and compiled programs need a disassembler installed."
- Close: "Next time an app does something clever, you'll know how it does it. Which app would you take apart first? Comment REA and I'll pin the link."

**Example B, DeepTutor (learning)**
- Hook: "Ever had an AI tutor forget everything you studied last week?"
- Name: "It's called DeepTutor. It builds a memory of what you've learned over time, and you can open that memory and see where each fact came from."
- How: "You can edit that memory too. Install it with pip or Docker, then connect your model provider in Settings."
- Proof: "You can also connect your own knowledge bases and study from them, in the same place."
- Catch: "The catch: it's a full self-hosted app, so setup takes more than one command."
- Close: "What would you want a tutor to remember about you? Comment TUTOR and I'll pin the link."

**Example C, impeccable (design for coding agents)**
- Hook: "Why does AI-built design so often look the same?"
- Name: "It's called impeccable. It gives your coding agent a design vocabulary, so you steer it with words like polish and bolder."
- How: "From your project root, run npx impeccable install. Then run the init command in your agent, and reload your coding tool."
- Proof: "The repo shows the same model and brief twice. Without impeccable, the page is a cream layout with pill buttons. With it, the page is built around one picture."
- Catch: "The catch: you review the result with critique and audit, so you still decide what looks right."
- Close: "Which page would you fix first? Comment POLISH and I'll pin the link."

**Example E, Edge0 (local models)**
- Hook: "Could a local AI model with 35 billion parameters run on your Mac?"
- Name: "Edge0 is one way to try it. It keeps the model on your SSD and loads only the parts it needs for each step."
- How: "The Python version runs on Apple Silicon Macs. The model download is about 23 gigabytes."
- Proof: "In the authors' own test, on a Mac mini with 24 gigabytes, it used about 3 gigabytes of memory and ran at 15 to 18 tokens per second."
- Catch: "The catch: it's a preview. In the authors' test it scores 81 on MMLU-Pro, against 84.6 for the full-precision base model."
- Close: "Would you run a model this size on your laptop? Comment EDGE and I'll pin the link."

**Example F, CleanYourTV (smart TV)**
- Hook: "Is your Android TV home screen full of ads?"
- Name: "CleanYourTV removes the preinstalled apps and gives you a clean home screen, over Wi-Fi. You don't need root, and nothing gets uninstalled."
- How: "On the TV, turn on developer options and USB debugging. Then, on a computer on the same Wi-Fi, run the three steps from the guide."
- Proof: "Preloaded apps are only disabled. One restore command brings back the stock home screen."
- Catch: "It works on Android TV and Google TV. Fire TV gets only the cleanup part. Samsung, LG and Roku aren't supported."
- Close: "Which TV brand would you clean first? Comment CLEAN and I'll pin the link."

## 6. Self-check before a script is saved

- [ ] Hook is 12 words or fewer, and the viewer's question or payoff is in it.
- [ ] The tool is named within about 7 seconds.
- [ ] Each sentence is 18 words or fewer, and the wording is natural.
- [ ] Every number and claim matches the brief's facts, with its scope.
- [ ] There is one proof moment and one honest catch.
- [ ] The close restates the benefit and ends with the keyword CTA.
- [ ] 100–125 words. No sources, licence or legal text, citations or links in speech.
- [ ] No promotional adjectives, no preamble, no feature list.
