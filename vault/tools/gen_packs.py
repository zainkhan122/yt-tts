#!/usr/bin/env python3
"""gen_packs.py — one-shot R26 upgrade of ALL metadata packs.
Outputs to /home/user/metadata_packs/: 'metadata for video N.md' (1-16) and
'metadata for short N hook.md' / 'metadata for short N payoff.md' (4-16).
v4-v15 are fixed from the repo packs (opener prepended, hashtags 5, tags
keyword-first, v4 title shortened). v1-v3 reconstructed from the R23 register
(videos already live; user pastes into YouTube Studio)."""
import re, os, subprocess, sys

SRC = {n: open(f"/tmp/packs/v{n}.md").read() for n in
       ["004","005","006","007","008","009","010","011","012","013","014","015"]}
OUT = "/home/user/metadata_packs"
os.makedirs(OUT, exist_ok=True)

CFG = {
 "004": dict(title="The Loneliest Personality Types (And Why They Hide)",
   opener="Why do the loneliest personality types — INFJ, INTJ, INFP, INTP — keep walking right past each other?",
   tags=["the loneliest personality types","loneliest personality types","infj lonely","why you feel alone in a crowd","rare personality types","intj","infp","intp","mbti","jungian psychology","deep thinkers","finding your people"],
   hts="#psychology #infj #deepthinkers #jungianpsychology #carljung",
   short_hook=("The Loneliest Types Keep Missing Each Other",
     "Why the loneliest personality types (INFJ, INTJ, INFP, INTP) walk past their own people every day."),
   short_pay=("You're Invisible to Your Own People",
     "Jung: the loneliest types wear disguises — and the mask makes you invisible to the people looking for you.")),
 "005": dict(
   opener="Carl Jung's darkest insight: your shadow is not your dark side — it's your unlived life.",
   tags=["carl jung darkest insight","jung shadow","the unlived life","shadow work jung","carl jung","jungian psychology","shadow self","individuation","infj","intj","infp","intp","self transformation"],
   hts="#psychology #jungianpsychology #carljung #shadowwork #infj",
   short_hook=("The Self You Buried Years Ago", "The version of you that you buried to be loved — Jung called it the shadow."),
   short_pay=("Your Shadow Isn't Dark. It's Unlived.", "Jung's darkest insight: the shadow is everything you were never allowed to be.")),
 "006": dict(
   opener="Overthinking at 3AM? It's the Ni–Ti loop — and once you see the mechanism, there's a way out.",
   tags=["overthinking at night","why your brain wont stop overthinking","3am overthinking","ni ti loop","infj overthinking","rumination","how to stop overthinking","intj","infp","intp","jungian psychology","mbti","sleep"],
   hts="#psychology #overthinking #infj #jungianpsychology #carljung",
   short_hook=("It's 3AM and Your Brain Won't Stop", "3AM overthinking: the live panel discussion your brain runs every night."),
   short_pay=("The Ni–Ti Loop (It's Not Anxiety)", "Intuition + logic, alone together, form the loop that keeps you awake.")),
 "007": dict(
   opener="The psychology of people who are \"too much\" — too intense, too deep, too sensitive — and why Jung said the shadow is gold.",
   tags=["people who are too much","too intense personality","the shadow is gold","jung shadow","infj too sensitive","deep thinkers","too deep too serious","jungian psychology","carl jung","infj","intj","infp","intp"],
   hts="#psychology #infj #deepthinkers #jungianpsychology #carljung",
   short_hook=("You're Not Too Much. Here's the Proof.", "Too intense, too deep, too much — what Jung would actually tell you."),
   short_pay=("Too Much — for Who, Exactly?", "You were never too much. You were aimed at people too little.")),
 "008": dict(
   opener="Why are you attracted to people who can't love you? Jung called it projection — you fall for the quality you exiled.",
   tags=["attracted to unavailable partners","why you cant have who you love","jung projection","attachment wound","infj relationships","shadow projection","why do i chase what i cant have","jungian psychology","carl jung","love psychology","infj","intj"],
   hts="#psychology #infj #jungianpsychology #carljung #relationships",
   short_hook=("Same Person, Different Body", "You keep falling for the same person in a different body. Here's why."),
   short_pay=("Jung Called It Projection", "The quality you exiled is the quality you keep falling for.")),
 "009": dict(
   opener="Why do people disappear without warning? The psychology of ghosting, the door slam, and the autonomous complex.",
   tags=["people who disappear without warning","infj door slam","ghosting psychology","why friends cut you off no explanation","autonomous complex jung","shadow possession","jungian psychology","carl jung","infj","silence as a weapon","mbti"],
   hts="#psychology #infj #jungianpsychology #carljung #doorSlam",
   short_hook=("Why They Disappeared Without Warning", "One day you're in their life. The next, you never existed."),
   short_pay=("When the Shadow Takes Over", "In the moment of the door slam, you become the very thing you fear.")),
 "010": dict(
   opener="Why does being yourself feel so lonely? Jung, Nietzsche, and Rilke on the loneliness of becoming.",
   tags=["being yourself feels lonely","loneliness of becoming","individuation jung","why authenticity is lonely","borrowed life","carl jung","jungian psychology","infj lonely","intj","infp","intp","authenticity"],
   hts="#psychology #jungianpsychology #carljung #individuation #infj",
   short_hook=("Lonely in a Room Full of People?", "Everything you've been told about loneliness is backwards."),
   short_pay=("The Loneliness of Becoming", "Not the loneliness of being alone — the loneliness of becoming yourself.")),
 "011": dict(
   opener="Introverted intuition (Ni): why you see what others don't — and the three prices you pay for it.",
   tags=["introverted intuition","infj intuition","ni function","why you know things before they happen","gut feelings that come true","jung functions","mbti","infj","intj","jungian psychology","highly intuitive people"],
   hts="#psychology #infj #intuition #jungianpsychology #carljung",
   short_hook=("You See What Others Don't", "The micro-expressions, the tension in the room, the lie before it lands."),
   short_pay=("Your Mind Hands You the Answer", "It collects everything, assembles beneath the surface — and skips the steps.")),
 "012": dict(
   opener="Carl Jung said four people live inside you — the Persona, the Shadow, the Anima, and the Self. A field guide to meeting them.",
   tags=["four archetypes jung","persona shadow animus self","jung archetypes","carl jung four people inside you","the self jung","jungian psychology","individuation","infj","intj","infp","intp","mbti"],
   hts="#psychology #jungianpsychology #carljung #archetypes #infj",
   short_hook=("Four People Live Inside You", "You've only met one of them — and the other three run your life."),
   short_pay=("You Were Built to Be Four", "You've been at war with your own house. Here's the map.")),
 "013": dict(
   opener="Why do you feel like an old soul? Precocious introverted intuition — the Jungian reason you've felt different since childhood.",
   tags=["why you feel like an old soul","old soul psychology","old soul meaning","precocious intuition","infj old soul","jungian psychology","carl jung","infj","intj","infp","intp","spiritual maturity"],
   hts="#psychology #oldsoul #infj #jungianpsychology #carljung",
   short_hook=("Why You Feel Like an Old Soul", "You didn't get here early by accident."),
   short_pay=("Your Mind Arrived Early", "An old soul isn't damaged. It's precocious intuition.")),
 "014": dict(
   opener="The psychology of people who apologize for existing — the sorry reflex, explained through Jung's extraverted feeling.",
   tags=["people who apologize for everything","over apologizing psychology","sorry reflex","extraverted feeling","infj people pleasing","why do i apologize so much","jungian psychology","carl jung","infj","self erasure","fawn response","mbti"],
   hts="#psychology #infj #peoplepleaser #jungianpsychology #carljung",
   short_hook=("The Sorry Reflex", "You say sorry for existing. Here's what's actually happening."),
   short_pay=("Stop Saying Sorry for Existing", "Excuse me instead of sorry — the first move of extraverted feeling.")),
 "015": dict(
   opener="Why do INFJs push people away when they need them most? The Fe–Ti loop under stress, explained through Jung.",
   tags=["why infjs push people away","infj push people away","fe ti loop","infj under stress","refusing help","self sabotage relationships","jungian psychology","carl jung","infj","intj","mbti","emotional withdrawal"],
   hts="#infj #psychology #jungianpsychology #carljung #infjs",
   short_hook=("Why INFJs Push People Away", "The moment you need people most, you disappear."),
   short_pay=("The Fe–Ti Loop, Explained", "Fe feels your need as a burden. Ti rationalizes: handle it alone.")),
 "016": dict(
   opener="Why are deep thinkers — INFJ, INTJ, INFP, INTP — always exhausted? You woke up tired today.",
   tags=["why you're exhausted as a deep thinker","exhausted deep thinker","why am i always tired","infj exhausted","deep thinker psychology","jungian psychology","carl jung","psychic energy","cognitive drain","introvert exhaustion","intj","infp","intp","mbti"],
   hts="#psychology #infj #deepthinkers #jungianpsychology #carljung",
   short_hook=("Tired in a Way Sleep Can't Fix", "You did nothing today — and you're drained to the last drop."),
   short_pay=("Broke From Thinking", "Maya did nothing all Saturday. The list filled three pages.")),
}

def fix_long(n, cfg):
    md = SRC[n]
    if "title" in cfg:   # v4 shorten
        md = re.sub(r"\*\*The Loneliest Personality Types \(And Why They Can't Find Each Other\)\*\*",
                    f"**{cfg['title']}**", md)
        md = md.replace("1. The Loneliest Personality Types (And Why They Can't Find Each Other)",
                        f"1. {cfg['title']}")
    # prepend opener to description body
    md = re.sub(r"(## DESCRIPTION \(copy-paste\)\n\n)", rf"\1{cfg['opener']}\n\n", md, count=1)
    # hashtags -> 5 strongest
    md = re.sub(r"(#[\w]+\s*){6,}", cfg["hts"] + "\n", md, count=1)
    # tags rewrite
    md = re.sub(r"## TAGS\n(.*?)(?=\n\n## |\n\n\")", "## TAGS\n" + ", ".join(cfg["tags"]) + "\n", md, count=1, flags=re.S)
    return md

# --- long-form packs v4-v15 ---
num_map = {"004":4,"005":5,"006":6,"007":7,"008":8,"009":9,"010":10,"011":11,"012":12,"013":13,"014":14,"015":15}
for n, cfg in CFG.items():
    if n == "016":
        continue
    open(f"{OUT}/metadata for video {num_map[n]}.md", "w").write(fix_long(n, cfg))

# --- v16: copy the already-fixed repo pack ---
import urllib.request, json
pat = open("/home/user/secrets/github_pat.txt").read().strip()
req = urllib.request.Request("https://raw.githubusercontent.com/zainkhan122/yt-tts/main/vault/video_016/metadata.md",
                             headers={"Authorization": "Bearer " + pat})
open(f"{OUT}/metadata for video 16.md", "w").write(urllib.request.urlopen(req).read().decode())

# --- v1-v3 reconstructed (live videos; paste into YouTube Studio) ---
RECON = {
 1: ("The Psychology of People Who Feel Everything Too Deeply",
   "feel everything too deeply",
   "Why do some people feel everything too deeply? For the rare intuitive types — INFJ, INTJ, INFP, INTP — emotions don't arrive one at a time; they arrive as weather. This is the psychology of emotional absorption: porous boundaries, taking on rooms, carrying what was never yours.\n\nThrough a Jungian lens, this is theFe/Fi overload: feeling as the dominant function, with no membrane between your inner world and everyone else's. This video walks through what it's like to absorb every mood in a room, why you can't watch the news without spiraling, why crowded places leave you hollow — and the boundary work that lets you keep your depth without drowning in everyone else.\n\nIt's not a flaw. It's an unguarded instrument. You don't need to feel less — you need a frame that can hold what you feel.\n\n💬 Tell me in the comments: what's the last emotion you absorbed that wasn't yours?\n\n⚠️ Disclaimer: This channel is for educational and informational purposes only. It is not a substitute for professional mental health or medical advice.\n\n#psychology #infj #empath #jungianpsychology #carljung",
   ["people who feel everything too deeply","feeling everything too deeply","why do i feel so much","emotional absorption","infj empath","highly sensitive person psychology","porous boundaries","jungian psychology","carl jung","infj","intj","infp","intp","mbti"]),
 2: ("Why Smart People Feel Chronically Misunderstood",
   "chronically misunderstood",
   "Why do smart people feel chronically misunderstood? Not occasionally — permanently, and in every room. This is the psychology of intellectual isolation for rare cognitive types (INFJ, INTJ, INFP, INTP).\n\nThe Jungian mechanism: rare Ni/Ti cognition — a way of processing that connects everything into patterns before most people have finished describing the surface. You speak in conclusions; they hear jumps. You see the whole; they see a detail. Every conversation becomes a translation nobody asked for.\n\nThis video is about the loneliness of a mind that runs a different operating system: the small-talk gap, the 'you're overthinking it' reflex, the slow surrender where you stop explaining — and what it costs to finally meet a mind that runs at your speed.\n\n💬 Comments: when was the last time you felt genuinely understood?\n\n⚠️ Disclaimer: educational content only; not a substitute for professional advice.\n\n#psychology #infj #jungianpsychology #carljung #deepthinkers",
   ["smart people feel misunderstood","chronically misunderstood","intellectual isolation","rare personality types","infj misunderstood","ni ti cognition","why no one understands me","jungian psychology","carl jung","infj","intj","infp","intp","mbti"]),
 3: ("The Psychology of People Who Go Quiet When They're Hurt",
   "go quiet when hurt",
   "Why do you go quiet when you're hurt? No outburst, no complaint — you just get silent. This is the psychology of turning inward when wounded, especially for feeling-dominant types (INFJ, INFP, INTJ, INTP).\n\nThe Jungian mechanism is introverted feeling: when something cuts, the pain is processed in a sealed room. It's not coldness — it's the opposite. The feeling is too large to say out loud, so it goes underground. To others it looks like distance; inside, it's a storm being metabolized in private.\n\nThis video covers why your silence is mistaken for indifference, what happens when the sealed room never opens, and how to translate the storm before it turns to frost.\n\n💬 Comments: what do you actually want people to know when you go quiet?\n\n⚠️ Disclaimer: educational content only; not a substitute for professional advice.\n\n#psychology #infj #jungianpsychology #carljung #infp",
   ["go quiet when hurt","people who go silent","introverted feeling","infj goes quiet","fi function","why i shut down when hurt","silent treatment vs processing","jungian psychology","carl jung","infj","infp","intj","intp","mbti"]),
}
for k, (title, kw, desc, tags) in RECON.items():
    open(f"{OUT}/metadata for video {k}.md", "w").write(
f"""# VIDEO {k:03d} — METADATA PACK (RECONSTRUCTED 2026-08-26 — original sources lost; paste into YouTube Studio)

## TITLE (recommended)
**{title}**

## DESCRIPTION (copy-paste)

{desc}

## TAGS
{", ".join(tags)}
""")

# --- shorts packs ---
for n, cfg in CFG.items():
    v = num_map.get(n, 16)
    for kind in ("hook", "payoff"):
        t, d = cfg["short_hook"] if kind == "hook" else cfg["short_pay"]
        open(f"{OUT}/metadata for short {v} {kind}.md", "w").write(
f"""# SHORT — video {v} {kind}

## TITLE
**{t}**

## DESCRIPTION (copy-paste)
{d} Watch the full video on the channel.

{cfg['hts'].split()[0]} #shorts {' '.join(cfg['hts'].split()[1:3])}

## TAGS
{cfg['tags'][0]}, shorts, youtube shorts, {', '.join(cfg['tags'][1:5])}
""")
print("generated:", len(os.listdir(OUT)), "packs in", OUT)
