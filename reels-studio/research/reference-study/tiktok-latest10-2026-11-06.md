# TikTok reference study: latest 10 videos, full scripts (6 Nov 2026)

Source: the TikTok reference list in `research/sources.csv` (12 accounts). Latest 10 videos across those accounts,
ranked by upload date. Method: yt-dlp for the video list, metadata and audio; faster-whisper (base.en, CPU) for the
transcripts. Scripts are quoted for study only. We do not copy wording.
Engagement is the public count at fetch time (6 Nov 2026, about 04:30 UTC). Most videos are only hours old.

## Engagement at fetch time

| Posted | Account | Views | Likes | Comments | Shares |
|---|---|---|---|---|---|
| 2026-11-06 | @ai_vanta_ai | 2 | 0 | 0 | - |
| 2026-11-06 | @github.signals | 465 | 19 | 0 | 2 |
| 2026-11-06 | @skip_ci | 183 | 10 | 1 | 3 |
| 2026-11-05 | @github.signals | 1,082 | 43 | 0 | 3 |
| 2026-11-05 | @github.signals | 1,114 | 22 | 1 | - |
| 2026-11-05 | @ai_vanta_ai | 1 | 0 | 0 | - |
| 2026-11-05 | @github.signals | 1,495 | 30 | 0 | 5 |
| 2026-11-05 | @skip_ci | 162 | 6 | 0 | - |
| 2026-11-05 | @remy_engineering | 304,900 | 38,600 | 555 | 1617 |
| 2026-11-05 | @dr_cintas | 59 | 2 | 0 | - |

Only one video broke out: @remy_engineering (304,900 views, 38,600 likes, 555 comments, 1,617 shares).
The other nine are between 1 and about 1,500 views. Follower counts are not public through this route, so we
cannot measure subscriptions per video.

## Full scripts (transcribed speech)

Three videos have no usable speech: @ai_vanta_ai (6 Nov) is music or on-screen text only, @ai_vanta_ai (5 Nov)
is a three-word fragment, and @github.signals (Fable 5.5, 5 Nov) is one word. Their captions are given instead.


## How they start (first 3 seconds)

- **A question about the viewer's own problem.** @remy_engineering: "how do hackers bypass youtube ads?" The viewer
  already knows the pain.
- **A contrast with a number.** @skip_ci: "A 2.8 trillion parameter model needs a data center full of GPUs."
  Then the claim: it runs on a laptop.
- **A command that names a harm.** @dr_cintas: "Stop your Smart TV from spying on you plus remove all its ads."
- **A problem-first line.** @github.signals (Looking Ahead): "Make video AI that actually understands physics."

## What they sell

One outcome the viewer can have today, in one sentence:
- "run that exact model on a basic laptop" (skip_ci, Kimi K3 in C)
- "watch YouTube without ads" (remy_engineering)
- "stop your TV spying on you" (dr_cintas)
- "build 3D objects from short code an AI can write" (github.signals, sand3d)

Each script then gives one concrete proof: a number, a time, a price, or a named tool. Numbers do the persuading.
Most also add a real requirement ("1.7 terabytes of NVMe", "tap build 7 times"). That is usable detail, not legal
text.

## How they try to get comments, likes and subs

- **Breakout (@remy_engineering):** a list of named tricks the viewer can try (the dot trick, Brave, NewPipe,
  SmartTube). A personal aside that invites a reply ("I like my 30-second tutorial... thinking about my car
  insurance"). A closing question that asks the viewer to answer: "But in front of the whole family?" It has no
  explicit CTA, and it still earned 555 comments.
- **Small accounts:** an explicit CTA on every script. "Link in profile / our Telegram" (@skip_ci, both videos).
  "Follow for more AI news and tutorials" (@dr_cintas). "Repo: github.com/..." in the description (@skip_ci,
  @github.signals).
- The breakout asks a question people want to answer. The small accounts ask people to click a link. Views come
  from the first, and the link clicks come from the second.

## What we take into our Short (no copying)

1. Hook: a question or an outcome about the viewer's own task, true to the README, usable now.
2. Points: each one is a thing the viewer can do with the tool. Install command, first snapshot, click by ref, what
   STALE_REF means for them.
3. Proof: one real number from the README or the repo (one npm command, 3 platforms, 5 example refs).
4. Close: a question plus a comment keyword ("Comment DESKTOP and I'll send you the repo link"), like the breakout.
5. No stage-of-development lines, no legal or permission lines. The viewer should feel they can use it now.

## Full transcripts

### 2026-11-06 @ai_vanta_ai (7704892349775727905)

(no usable speech) CAPTION: Claude just revealed a hidden feature most users don’t know about. Discover this smart AI secret that can change your experience with Claude and unlock new possibilities. #AI #AITools #ArtificialIntelligence #TechSecrets #Innovation

### 2026-11-06 @github.signals (7704890735065042184)

LiveLive Player is a small web player that brings a 2D character to life with lip sync and webcam face tracking. A few lines of JavaScript put a character in a page, a stream overlay, or an app, and the core is about 30 kilobytes with no dependencies. Lip Sync and Face Tracking are separate modules, loaded only when you ask for them, and both run in the browser. One API plays three kinds of characters. LiveLive Models, VRM Avatars, and PNG Tubers. 21 Ready Characters ship with it from Senna and Elio Tannana, the mascot, free for personal projects with credit. The same character also drops into any site with an iframe and works as an OBS browser source for streams. Becode is Apache licensed, so a talking character is a few lines away.

### 2026-11-06 @skip_ci (7704841832345160978)

A 2.8 trillion parameter model needs a data center full of GPUs. Moonshot calls KIMI-K3 the world's first open model this big. KIMI-K3 and C runs that exact model on a basic laptop. It's written in plain C and streams the weights off your SSD. Only the experts each token needs get loaded into RAM. And no GPU, no PyTorch, just a C compiler and your CPU. But give it less memory and the wait time changes a lot. Its own benchmark? 8GB, 26.5 seconds a token. 128, just 5.6. The catch? You'll need 1.7 terabytes of fast NVMe storage. Same output whether it runs with 8GB or 128GB of RAM. This and a lot more on our telegram, link in profile.

### 2026-11-05 @github.signals (7704832731083066645)

Sand3D from SanFlow writes 3D objects as short Python programs built for language models to write. Every part has a name and a recipe, a profile, an extrusion, a whole, a fillet on top of Blender. The same part takes two to six times fewer tokens than Blender Python, CadQuery or FeatureScript, and the whole API fits in a prompt. A washing machine is 38 lines, cabinet, drum, door, drawer and dial, plus four joints that say how they move. The same program always builds the same mesh, an experts to GLB, to URDF for robot simulators, and to USD. SandFlow has also released datasets of these programs on hugging face, rebuilt from objectverse, CAD models and articulated objects. It makes 3D something a model can read, edit and write like code.

### 2026-11-05 @github.signals (7704803346649058580)

(no usable speech) CAPTION: Fable 5.5 made rainbow jelly grow back after cuts; Gemini 4 Carbon's stayed cut. Both got the same prompt: rainbow jelly you can cut, nail and torch. Gemini took 32 minutes and cost $4.30; Fable took 45 minutes and cost $48.50. via @0xRhinoX https://x.com/0xRhinoX/status/2118415577299460432 #SoftBodyPhysics #PhysicsSimulation #VibeCoding #Fable #Gemini

### 2026-11-05 @ai_vanta_ai (7704783444659817761)

(no usable speech) CAPTION: Training your own custom AI model is now possible right from a laptop, unlocking accessible AI innovation for everyone. This breakthrough makes building personalized AI smarter, faster, and trending as the new DIY tech breakthrough. #AI #AITools #MachineLearning #TechNews 

### 2026-11-05 @github.signals (7704750595848162581)

Otter aggressive video models build a clip, chunk by chunk, each piece conditioned on what came before, trained with teacher forcing, they can coast on the frames right behind them, without learning how a scene evolves. Future chunk prediction adds training only branches that predict chunks further ahead, without seeing the frames in between. To get those right, the model has to learn what happens next. Ice pops melt, beer fills the mug, dominoes keep falling. On the WAN 2.2 model, physics IQ rises from 30.4 to 33.8. Nothing changes at inference time, and the 1.3B and 5B weights are open. It points toward Otter aggressive world models that learn how scenes evolve.

### 2026-11-05 @skip_ci (7704749183059676434)

You risk real money on a setup you haven't tested. Daytrader skill is 11-clod skills for exactly that. One scans thousands of charts for breakouts, flags, and oversold bounces. Another times your entry and sets your exit first. But one skill checks if the trade's worth it at all. The time machine replays the rest of the session 10,000 times. Plus, every past day that exact setup fired for real odds. One real Tesla trade came back close to a coin flip. The catch? It only paper trades until you plug in a broker. No trade fires without your yes, now backed by real odds. This and a lot more on our Telegram, Lincoln Profile.

### 2026-11-05 @remy_engineering (7704725972116950305)

How do you get YouTube premium for free when apparently some people want to watch a video without sitting through two ads before it even starts? I know, people are getting demanding. People used to skip YouTube ads by adding a dot right after YouTube.com. Now the ads still play, but hey, at least you got to type a dot. Now some people open YouTube and Brave, a browser with a built-in ad blocker. Personally, when I click on the 30 second tutorial, I like to spend the first two minutes thinking about my car insurance. On Android, some people go as far as installing new pipe. They watch videos without ads and they can even keep listening when they lock their phone. With the screen off, the nerve. And then there's SmartTube. People actually install an app on their Android TV just to watch YouTube without ads from their couch. On your phone, fine. But in front of the whole family?

### 2026-11-05 @dr_cintas (7704724093915974925)

Cloud Code can now hack your TV and in about 15 minutes it looks like a brand new Apple TV. Smart TV nowadays comes with a sponsor rose, tracking and apps that you can learn and install. Clean your TV, fixes that with tested links for 300 TV models from 91 brands. To set it up you have to tap build 7 times to unlock the developer mode, turn on the USB debugging and then paste the ripples prompt into your code in a year with your TV model. The Christmas part it never deletes anything. It just disables the app and one line restore than all. If you want to learn about the latest AI news and tutorials follow for more.
