# Plan: from templates to guidelines for shorts

Status: proposal for owner approval. Nothing here is implemented yet.

## 1. Diagnosis

The system makes each short from a fixed shape:

- Brief `template` field, with a fixed scene order: hook → proof → how → catch → close.
- `brief_lint.py` (BL rules) forces that order, the word counts, and the timings.
- `seo_pack.py` builds copy from formulas: "Name: …", hashtag lists, keyword slots.
- `PLAYBOOK §8A` describes the same shape as the house style.

Result: every short looks and reads the same, so the algorithm sees repeated patterns and viewers skip. The copy I wrote this session (openers like "Scrawl: stop…", "fx0 design agent: …") is the same mistake in a smaller form. It was still a formula.

What to keep: the hard rules that protect the channel and the owner, not the shape of the content.

## 2. Keep as hard rules (not templates)

These stay enforced in code. Each is a rule about facts, legal, or platform safety, not about style.

1. No credits, attribution, capture dates, or "own captures" in visible copy.
2. Niche hashtags only. No generic tags (#AI, #Coding, #Video, #Tech, #viral).
3. The Facebook AI-narration disclosure is required whenever the voice is synthetic.
4. Licence is a one-time trust badge, not the hook and not repeated.
5. Every claim about a product must trace to a dated source, a capture, or the owner's own test. The production gate already checks this.
6. Captions and on-screen text never cover media. Safe-area check stays.
7. Every PASS, scheduled, or published claim needs read-back evidence.
8. Random 1–5 videos per day. The count is drawn before scheduling, and the record must match what is actually scheduled. This is a process rule, not a shape rule.

## 3. Replace with guidelines (judgment, per short)

For each short I write the script, copy, and edit from the question: **what does this specific viewer need, and what is the fastest honest way to show it?**

Guidelines, not steps:

- **Open on the viewer's situation**, in their words, at the moment they feel the problem. The first frame should already show something happening on screen.
- **Choose the proof for the claim.** A bug fix needs before/after on the same screen. A new feature needs the first real use. A model claim needs a side-by-side on the same input. Pick what would convince a skeptic in 3 seconds.
- **Let the length follow the idea.** Some ideas land in 18 seconds; some need 50. No fixed scene count.
- **Use the viewer's next project as the payoff**: what they can do tomorrow that they could not do before. Stated plainly, no slogan.
- **Vary the form across shorts**: a question, a bug reproduction, a comparison, a "wrong way vs right way", a live demo, a single surprising result. The reference channels show that the common thread is a clear moment, not a shared layout. Use the references for what they do well (speed of the first second, one idea per short), not to copy their structure.
- **Write like a person who has used the tool.** Short sentences. Name the specific thing that broke or worked. No hype adjectives, no "game-changer", no "in this video".
- **Cut anything the viewer does not need to decide whether to try it.**

Per-platform copy follows the same rule: write each caption for that viewer on that platform. YouTube titles are searchable; TikTok captions are a reason to stay; Instagram is the saved-for-later note; Facebook is the context for a non-developer; X is one sharp line. No shared formula.

## 4. Changes to the system

1. **Brief**: remove the required `template` and fixed scene order. A brief has an `idea`, `viewer`, `viewer_job`, `proof_plan` (what evidence and how it will be shown), `script` (free form), and `shot_list` tied to the capture pack. Keep the existing IDs and media references.
2. **brief_lint**: keep the checks that matter (JSON valid, media exists in the capture pack, timing sums to the video length, licence not in the hook, no unbalanced markup). Remove the rules that force scene order and word counts. Add checks that the proof_plan names an evidence source for each claim.
3. **seo_pack**: remove the formulas and keyword-position warnings. Keep the hard rules in section 2 and the character limits. The writer supplies the copy; the lint only checks the rules.
4. **Review step**: a short gets a written review before scheduling. The review asks: does the first second earn a second? Is every claim supported? Does the copy sound like a person? If the answer is no, rewrite, do not template-patch.
5. **Measure**: after each short, record the 3-second hold, the watch time, and the viewers' comments. Feed these back into the next idea choice. Replace guesses with the Buffer insights already in the repo.

## 5. Rollout

1. Owner approves this plan and the list of hard rules in section 2.
2. Write the new guideline document (replacing PLAYBOOK §8A) and the brief schema change. Tests for the hard rules stay; tests for the old structure are removed.
3. Rewrite the copy for the pending shorts from scratch with the new process, not by editing the formula output. Currently scheduled: tool-scrawl-01 (YouTube, Facebook, Instagram) and tool-fx0-01 (Instagram). Those posts were written with the formula, so the owner decides whether to replace them before they publish.
4. Make the next 3 shorts under the new process. Compare their early retention with the last 10 shorts from the templated system.
5. Review at the end of the week with the owner. Keep what works and adjust the guidelines.

## 6. Open questions for the owner

- Approve section 2 as the complete list of hard rules?
- For tool-scrawl-01 and tool-fx0-01, should I rewrite their copy and reschedule before they publish, or leave them as they are?
- Are the 40 already-sent posts with credits and capture notes a problem to fix now, or only to avoid repeating?
- Should the brief `template` field be removed entirely, or kept as an optional hint?
