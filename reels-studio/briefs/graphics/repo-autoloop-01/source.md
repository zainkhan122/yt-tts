# Source snapshot: KKKKhazix/agent-autoloop

Fetched 2026-11-07 from  (README, English version where the repo ships one).

HTML tags and images removed; wording unchanged.


---

## KKKKhazix-agent-autoloop.en.md

# Agent Autoloop

**Let your command-line agents pick up work and follow it through in the background — staying quiet when they can handle it, and sending you a card only when a decision is yours to make.**

中文 | **English**

Get started · Recipes · Plugins · Kernel · Docs

## What problem does it solve?

Most of us use command-line agents like Claude Code or Codex by babysitting a terminal: you type a prompt, watch it run, and answer its questions. Close the window or walk away, and the work stops.

**Agent Autoloop** turns your command-line agents into a background loop. At the center is a deterministic **kernel** with zero runtime dependencies. Around it, event sources, agents, notification channels, and even CI/CD delivery pipelines are all swappable **plugins**.

- **One machine, one install command.** Runs on Windows, macOS, or Linux. No cloud server or inbound ports required.
- **Connect a new agent in one line.** No SDK, no agent source code to fork. Any CLI tool that takes a prompt and prints a final reply can plug in.
- **No web dashboard.** Cards reach you on Feishu, DingTalk, WeCom, Slack, Discord, or desktop notifications when you are needed. Everything else is one command away.

## Get started

Works on Windows, macOS, and Linux. You need Node 24 or newer, Git, and a command-line agent already signed in; macOS/Linux also use curl. No GitHub account required. You can hand the installation guide to your agent.

Windows PowerShell:

```powershell
irm  | iex
```

macOS / Linux:

```bash
curl -fsSL  | sh
```

The installer and `agent-autoloop update` both install the newest release, which has passed every check.

Then run a real loop with your own agent — ask, exit while it waits, make the call, resume:

```bash
agent-autoloop try
```

> CLI output and default notification strings are still Chinese until they are translated. Sample CLI output in this README is that same text written in English.

Here is the output from Codex in a non-interactive terminal, written in English:

```text
Event sent. The agent is getting to work...

The agent finished this round and asked you a question. No process is running for it now, and it is not spending tokens.

[Your call] #1 Try run: pick a color
This is a try run. Either choice is fine.
  1. Blue
  2. Green
Answer: agent-autoloop answer 1
After you answer, run agent-autoloop status to see it pick the work back up and finish.
```

In an interactive terminal, just type the option number. In a non-interactive terminal, run `agent-autoloop answer 1 2` to pick green. Then `agent-autoloop status` shows that the agent resumed its conversation and finished, along with rounds, tokens, and cost for today and the past seven days (how they are counted).

## How a piece of work flows

The numbers match the diagram above:

1. **An event comes in.** A 9:00 AM schedule, a new GitHub issue, or a production alert becomes a standard event sent to the kernel.
2. **Dispatched by your rules.** Your rules decide which agent handles it and in which folder. New events for the same subject while it is queued merge into one round.
3. **Work one round and exit.** The agent puts its result in its final message, and the process exits.
4. **Asks only when needed.** For sensitive actions like deleting data, restarting a service, spending money, or messaging people, the kernel sends you a card through Feishu or a desktop notification. While you take your time, no agent process runs and no tokens are spent.
5. **One tap resumes it.** Your answer picks up the original conversation and finishes the job.

Anything the agent can handle alone takes the auto-loop at the top of the diagram: finish outright, or schedule a follow-up check (say, in 30 minutes) without bothering you.

## Day-to-day usage

### Write your rules (`rules.json`)

No glue code needed. Open `~/.agent-autoloop/rules.json` and, under `rules`, declare **what happened, who handles it, and where they work**. Set `to` to a name already under `agents`. For example, write a brief every morning at 9:

```json
{
  "name": "Morning brief",
  "when": { "cron": "0 9 * * *" },
  "to": "codex",
  "cwd": "~/notes",
  "prompt": "Summarize yesterday's notes and commits into today's brief."
}
```

External events work the same way once the source is connected. To hand new GitHub issues to Codex, first register `github` under `sources` (guide):

```json
{
  "name": "Handle issues",
  "when": { "source": "github", "types": ["issues.opened"] },
  "to": "codex",
  "cwd": "~/code/app",
  "skill": "handle-issue",
  "parallel": 3
}
```

`agent-autoloop pause ` and `resume ` pause and resume one rule: while paused it skips its scheduled times and doesn't take events, and a resume doesn't catch up on what was skipped. `agent-autoloop run ` runs it once now. These are kept in the hub's log; `rules.json` is not changed.

Changes take effect within seconds of saving. Run `agent-autoloop check` to validate, `agent-autoloop check ` to validate a draft without touching the running hub, `agent-autoloop rules explain` to see the rules in effect and their next runs, and `agent-autoloop emit  --dry-run` to preview who an event would go to (it doesn't contact the hub or write to the log). If you make a mistake, or the file is deleted or can't be read, the hub keeps running the previous valid rules and sends you a card about it.

### How agents talk back to the hub

The hub asks only one thing of an agent: **put your result in your final message**. When the job is done, a one-line conclusion is enough. To ask you something, the agent appends an `agent-autoloop` block:

````text
Order checked. We have enough stock in the warehouse.

```agent-autoloop
{
  "ask": [{
    "title": "How should we ship it?",
    "text": "Both options can go out today.",
    "options": ["Courier", "Pickup"],
    "key": "shipping"
  }]
}
```
````

Besides `ask`, receipts can send notifications (`notice`), resolve open cards (`resolve`), schedule follow-up checks (`later`), and emit new events (`events`). A notice asks for nothing, but you can add a line of your own when you settle one, and it stays on the card; one marked `fyi` is only there to tell you, and has no button. If the JSON is invalid, the hub has the agent rewrite just that final message in the same session, without repeating completed work. If rewriting also fails, it keeps the original conclusion and tells you the receipt was not applied (a plain command has no session, so it goes straight to this). Going on in an old session works the same way: a new session starts only when the old one can't be continued. If it was continued and then broke partway, the run counts as failed and is retried in that session a few minutes later, not redone in a new one. A new event on the same thread starts a new session by default; with `"resume": true` in the rule it goes on in the last round's session.

## Ready-to-use recipes

Each recipe includes rules, a task Skill, and setup instructions (written in Chinese).

| Task | Included workflow |
|---|---|
| Morning brief | Summarize local notes and Git commits at 8 AM by default; write `briefs/YYYY-MM-DD.md` |
| GitHub issues | Poll every five minutes, edit code locally, and notify you to review; no commits, pushes, or issue replies |
| Production alerts | Receive an error, investigate local code, ask before restarting, and continue after your answer |
| User feedback | Re-read current feedback, fix, deliver and verify, then prepare a reply; ask you in Feishu and resume after your answer |
| Website watch | Check status and expected content every five minutes; wake the agent on a new incident, keep ongoing failures quiet, and update the card on recovery |
| Feishu weekly and business brief | Read selected reports and tables with your permissions at 6 PM Sunday; summarize locally and send only a short summary to Feishu |
| Inbox triage | Read unread mail from the last 24 hours at 8 AM by default; write a local checklist with reply drafts, without sending or changing the mailbox |
| PR delivery | Add `deliver` to a PR to review it, wait for CI, merge, wait for deployment, and verify the live version |

**To enable one:** open its instructions, put the task Skill in your agent's skills directory, merge the sample rules into `~/.agent-autoloop/rules.json`, replace worker names and paths, then run `agent-autoloop check`.

Feedback, website watch, Feishu briefs, and inbox triage default to Asia/Shanghai and send only to the owner's private Feishu chat. Sample data is fictional; scripts and receipts have been verified only with local HTTP and a fake Feishu CLI, not run end to end on a live account.

More: Claude-to-Codex browser handoff, weekly code cleanup, ship a PR.

## Plugin ecosystem: swap any of the four sides

Built-in plugins ship with the program and are enabled through configuration. Use `agent-autoloop add ` for third-party plugins.

| Side | Built in | Setup |
|---|---|---|
| **Events**: how work is found | GitHub Webhook, GitLab Webhook, HTTP API, cron rules, issue polling script | Guide |
| **Agents**: who does the work | Claude Code, Codex, ACP, DeepSeek Harness, generic command | Guide |
| **Channels**: how cards reach you | Desktop notifications (on by default), Feishu, DingTalk / WeCom / Slack / Discord | Guide |
| **Delivery**: CI/CD as a plugin | `delivery` | Guide |

**What has been tested:** Claude Code, Codex, and ACP (with the official Codex ACP adapter) have run multi-turn Q&A and session resumption across processes. Feishu has run real delivery, button callbacks, and card updates. The four webhook templates have only been checked against local mock servers, and the GitLab webhook against the payloads in its docs, not a real GitLab. These text channels answer through a link, so `hub.publicUrl` must be reachable from your phone or computer.

**Built-in agents through another service.** To send Claude Code or Codex to a third-party model service, or to set environment variables before it starts, write a small script that sets them and starts the program, then put `"program": "/path/to/script"` on the agent. Session resumption and usage reporting still work. See the guide.

**Other CLI agents connect in one line.** Set `use: "command"` and pass a command array; `{prompt}` is a single argument, never evaluated as shell code. These commands come from each tool's official docs, and we have not run each of them yet:

| Agent | Command |
|---|---|
| DeepSeek Harness older versions (the built-in plugin needs 0.2.2 or newer) | `dsh --profile headless {prompt}` |
| pi | `pi --print {prompt}` |
| OpenClaw | `openclaw agent exec {prompt}` |
| Hermes | `hermes chat -Q -q {prompt}` |
| Cursor | `agent -p --trust {prompt}` |
| WorkBuddy / CodeBuddy | `codebuddy -p {prompt}` |

Agents that speak ACP connect with `use: "acp"` and can go on in the same session: Gemini CLI is `"command": ["gemini", "--acp"]`, and OpenCode is `"command": ["opencode", "acp"]`. These also come from the official docs and have not been run yet.

**Delivery pipeline.** Add the `deliver` label to a GitHub PR and it follows through to release: **review → wait for CI → merge → wait for deploy → verify the live version**. Settings are read only from `main`, and PR code is never checked out or run on the worker machine. Queueing, concurrency, and retries come from the kernel.

**Write your own.** Start from the runnable agent, channel, and event templates and the plugin guide. For web tasks, read browser access first. The CLI and MCP can also inspect and answer cards.

## Four kernel mechanisms

The kernel is about 1,850 lines with zero runtime dependencies. It reads no clock, uses no randomness, and makes no outbound requests; plugins connect in, and credentials stay with the plugins that use them. Identical inputs always give identical results. It brings four proven systems patterns to command-line agents:

- **Zero-cost wait**: The process exits while waiting for your call, and the waiting state lives in SQLite, so the agent does not stay alive. If you reply three days later, no agent process runs and no tokens are spent in the meantime — only the lightweight hub waits in the background; your answer resumes the original conversation.
- **Event sourcing**: All state is derived from an append-only fact log, committed in the same SQLite transaction as its indexes before the hub replies. Confirmed facts survive `SIGKILL` (whole-machine power loss is not separately tested), every run can be traced with a single command, and format changes rebuild from the log without migration scripts.
- **Code / data split**: Like parameterized SQL. Issue titles, bodies, and other external text are written only to a local data file, never into the prompt, which carries only character-checked types, IDs, and links; `rules.json` alone decides which agent runs, in which folder, and with what access. Events carrying `cwd`, `agent`, or `access` fields are rejected outright.
- **Hop circuit breaker**: Like packet TTL in networking. Events returned by an agent can dispatch more agents, and the hop count keeps growing — across human questions and scheduled follow-ups too — and an agent cannot reset it. Past 8 hops, the kernel records the event, stops dispatching, and sends you a notice card.

### Check it yourself

On Windows use `npm run test:windows` and `node scripts/install-smoke-windows.ts`. These run the common behavior tests and native process/install checks; Unix shell fixtures remain on Linux/macOS.

Run these from `~/.agent-autoloop/app`:

| What it checks | Command |
|---|---|
| The full story of any round | `agent-autoloop why 1` |
| 200,000 simulated steps of network loss, dropped packets, crashes, and duplicate requests, reproducible from one seed | `node sim/random.ts 24301 200000` |
| 1,000 process kills with no acknowledged record lost | `node sim/crash.ts 1000 12648430` |
| The benchmarks below | `npm run benchmark` |

```text
Round 1 · Demo
11-03 20:47:25  Rules version #1
11-03 20:47:25  Triggering event: source local · type demo.start · subject example
11-03 20:47:25  local picked it up (demo program)
11-03 20:47:25  Finished: demo complete
```

### Benchmarks

Apple M5 Pro, 24 GB, Node 24.21.0. Each write is a separate request, acknowledged only after its transaction is durable.

| Metric | Measured |
|---|---:|
| Cold start | 88.78 ms |
| Idle memory | 59.94 MB RSS |
| 1,000 concurrent waiting polls | 170.49 MB RSS |
| Durable writes | 2,394 events/s |
| Dispatch p99 | 1.82 ms |
| Held-back heartbeat p99 with 5,000 queued | 1.66 ms |
| Startup at 1.1 million facts | 99.8 ms |
| Kernel lines (with comments and blanks) | about 1,850 |
| Runtime dependencies | 0 |

As history grows, the status summary slows down and the log and indexes keep using disk. The first start after a format change rebuilds from the log, which took 43.1 seconds for 1.1 million facts. Full numbers and method (in Chinese).

## Usage and provider terms

The hub invokes command-line tools you have already installed and signed into on your machine; it never reads or exports their credentials. Model usage is billed to your own account under each provider's terms.

For automated workloads, providers generally recommend using API keys rather than personal subscription quotas (which are designed around interactive personal use — see Anthropic and OpenAI). Use API keys if you are running services for others. This project is independent and is not affiliated with or endorsed by those providers.

## Documentation

- Installation guide
- Configuration & delivery pipeline manual
- Writing plugins
- Full HTTP protocol specification
- Security boundaries
- Contributing and community
- Development guidelines

Repository layout

| Location | Contents |
|---|---|
| `kernel/` | Decisions, fact log, projections, deadlines, rule matching, endpoint behavior, and card forms |
| `host/` | Node HTTP, files and SQLite connections, clock, configuration, status summary, background services, and plugin loading |
| `protocol/` | Wire formats, JSON Schema, input validation, HTTP client, and conformance checks |
| `worker/` | Claim work, run agents, handle heartbeats and cancellation, read and submit receipts |
| `cli/`, `bin/` | User commands and entry point: status, answers, `why`, MCP, updates, and uninstall |
| `plugins/` | Built-in agent, event, channel, and delivery plugins |
| `examples/recipes/` | Complete recipes with rules, a task Skill, and setup instructions |
| `examples/plugins/`, `examples/skills/`, `examples/*.sh` | Minimal plugin templates, standalone task guides, and Shell examples |
| `skills/agent-autoloop/` | The hub's configuration and operation manual, also made available to agents during installation |
| `docs/` | Protocol, plugin guide, and Chinese / English architecture diagrams |
| `tests/`, `sim/` | Everyday behavior tests, simulation, enumeration, crash tests, and mutation checks |
| `scripts/`, `.github/workflows/` | Performance and real-agent checks, installation smoke scripts, and Windows / Linux / macOS CI |
| Root documents and `install.sh` | Chinese / English READMEs, installation, security, development guidelines, license, and installer |

Start reading at `bin/agent-autoloop.ts` → `cli/main.ts`, then follow the feature into `host/`, `worker/`, or `plugins/`. Read the protocol for kernel design. Similarly named files serve different layers: `host/http.ts` adapts Node requests while `kernel/http.ts` defines endpoint behavior; `protocol/rules.ts` validates input while `kernel/rules.ts` defines rule types and matching.

MIT License


---

## KKKKhazix-agent-autoloop.md

# Agent Autoloop

**让你的命令行 Agent 在后台自己接活、自己跟进到底；平时不烦你，遇到拿不准的事才发卡片找你拍板。**

**中文** | English

上手 · 场景模板 · 插件 · 内核 · 文档

## 它解决什么问题？

平时我们用 Claude Code、Codex 这类命令行 Agent，大多是“人守着终端用”：你输一句话，盯着它跑，等它问你下一步；一旦关掉窗口或者人走开，事情就断了。

**Agent Autoloop** 是一个极轻量的自动化中台。它把任务调度做成一个零外部依赖的**内核**，把事件来源、Agent、通知通道，甚至代码上线流水线全部拆成可随时插拔的**插件**。

- **一台电脑、一条命令就能跑。** 装在你的 Windows、Mac 或 Linux 上，不用买云服务器，也不用开放公网端口。
- **一行配置接新 Agent。** 不需要 SDK，也不需要改 Agent 源码，能接收提示词并打印最后一条回复的命令行工具都能接。
- **没有后台界面。** 需要你拍板时把卡片推到飞书、钉钉、企微、Slack、Discord 或桌面通知；想看全局进展，敲一行命令。

## 上手

支持 Windows、macOS 和 Linux。需要 Node 24 或更新、Git，以及一个已经登录的命令行 Agent；macOS/Linux 还需要 curl，不需要 GitHub 账号。也可以把安装说明交给你的 Agent。

Windows PowerShell：

```powershell
irm  | iex
```

macOS / Linux：

```bash
curl -fsSL  | sh
```

安装和 `agent-autoloop update` 都装最新的 Release，那是通过了全部检查的版本。

装好后用你本机的 Agent 真实走一遍“提问 → 退出等回复 → 拍板 → 接着干完”：

```bash
agent-autoloop try
```

下面是在终端里的真实输出：

```text
事件发出去了，Agent 开始干活……

Agent 结束了这一轮，问了你一个问题。它现在不占进程、不花 Token。

【等你决定】#1 试跑：选一个颜色
这是一次试跑，选哪个都行。
  1. 蓝色
  2. 绿色
回答：agent-autoloop answer 1
答完运行 agent-autoloop status，能看到它接着把活干完。
```

交互终端里直接输入数字回车；非交互终端运行 `agent-autoloop answer 1 2` 选择“绿色”。再跑 `agent-autoloop status`，就能看到它接上刚才的会话并显示“你选了绿色，试跑通过”，还有今天和最近 7 天的轮数、Token 和费用（统计口径）。

## 一件事怎么转起来

编号和上面的架构图一一对应：

1. **新事件进来。** 早上 9 点的定时任务、GitHub 上新提的 Issue、业务系统报的错，都变成一条标准事件送进内核。
2. **按规则派活。** 内核照你写的规则，决定交给哪个 Agent、去哪个目录干。同一件事排队时又来的消息，会合并成一轮处理。
3. **干完一轮就退出。** Agent 把结果写在最后一条回复里，进程直接退出。
4. **拿不准才问你。** 碰到删数据、重启服务、花钱、对外发消息这类事，内核通过飞书或桌面通知发一张卡片给你。等你回复期间，它不占后台进程，也不消耗 Token。
5. **点一下，接着干。** 你选完，它接上原来的对话，把剩下的活干完。

能自己搞定的事走图上方的自动闭环：直接办完，或者约个时间（比如半小时后）再醒来复查，全程不打扰你。

## 日常怎么配？

### 写一份规则（`rules.json`）

不需要写胶水代码。打开 `~/.agent-autoloop/rules.json`，在 `rules` 里写清楚**什么事、交给谁、在哪个目录干**。`to` 填 `agents` 里已有的名字。比如每天早上 9 点写早报：

```json
{
  "name": "早报",
  "when": { "cron": "0 9 * * *" },
  "to": "codex",
  "cwd": "~/notes",
  "prompt": "整理昨天的笔记和提交，写今天的早报。"
}
```

外部事件写法一样，只是要先接好来源。比如有人提新 Issue 时交给 Codex，先按说明在 `sources` 里登记 `github`：

```json
{
  "name": "处理 issue",
  "when": { "source": "github", "types": ["issues.opened"] },
  "to": "codex",
  "cwd": "~/code/app",
  "skill": "handle-issue",
  "parallel": 3
}
```

`agent-autoloop pause `、`resume ` 暂停和恢复一条规则，暂停期间到点不跑、来事件不接，恢复后不补跑；`agent-autoloop run ` 立即跑一轮。这些记在中台的日志里，不改 `rules.json`。

保存后几秒内自动生效，可以运行 `agent-autoloop check` 检查，`agent-autoloop check ` 检查一份草稿，不碰正在跑的中台；`agent-autoloop rules explain` 看生效的规则和下次定时，`agent-autoloop emit  --dry-run` 预演一条事件会派给谁（不连接中台、不写日志）。就算改错了，或者文件被删、读不到，系统也会继续按旧规则跑，并发卡片提醒你。

### Agent 怎么跟中台配合？

中台对 Agent 只有一个约定：**在最后一条回复里交代结果**。事情办完了，正常输出一句结论就行。需要向你请示时，在回复末尾附一段 `agent-autoloop` 代码块：

````text
订单已经核对完毕，库存充足。

```agent-autoloop
{
  "ask": [{
    "title": "怎么发货？",
    "text": "两种方式今天都能发出。",
    "options": ["快递", "自提"],
    "key": "shipping"
  }]
}
```
````

除了提问（`ask`），还能发通知（`notice`）、关闭已解决的卡片（`resolve`）、预约复查（`later`）和触发新事件（`events`）。通告不需要回答，但结案时可以顺手写一句处理说明，这句话会留在卡片上；只是告诉一声的通告标成 `fyi`，不带按钮。万一 JSON 写错了，中台只让它在原会话里重写最后这段回复，不会把已经干完的业务重做一遍；重写也失败时，保留原结论并通知你回执没有生效（通用命令没有会话，直接走这一步）。接着旧会话跑也一样：会话接不上才开新的；接上了、干到一半断了，就算没跑成，过几分钟回到原会话重试，不开新会话重做。同一事项的新事件默认开新会话；规则写 `"resume": true` 就接着上一轮的会话。

## 拿来即用的场景模板

每套模板都带规则、任务 Skill 和启用说明。

| 想做什么 | 已经封装好的流程 |
|---|---|
| 每日早报 | 默认每天 8 点整理本地笔记和 Git 提交，写入 `briefs/YYYY-MM-DD.md` |
| 跟进 GitHub Issue | 每 5 分钟查新 Issue，在本地改代码并通知你查看；不提交、不推送、不回复 Issue |
| 线上告警排查 | 接收报错、对照代码查原因，需要重启时发卡片询问，回答后继续 |
| 用户反馈处理 | 重读反馈当前状态、修复、交付核实、准备回复；需要决定时飞书问你，回答后继续 |
| 网站巡检 | 每 5 分钟检查状态和关键内容，首次异常交给 Agent，持续异常不重复通知，恢复后更新原卡片 |
| 飞书周报与业务摘要 | 周日 18 点按你的权限读汇报和指定表格，生成本地摘要；飞书只发简短摘要，完整稿留在本机 |
| 收件箱分诊 | 默认每天 8 点读过去 24 小时的未读邮件，写成清单和回复草稿；不发送、不改邮箱状态 |
| PR 自动交付 | 打上 `deliver` 标签后，审查、等 CI、合并、等发布并核对线上版本 |

**启用：** 打开对应说明，把任务 Skill 放进所用 Agent 的 skills 目录，把示例规则合入 `~/.agent-autoloop/rules.json`，替换电脑名和路径，再运行 `agent-autoloop check`。

反馈处理、网站巡检、飞书摘要和收件箱分诊默认使用北京时间，只发给本人的飞书私聊。样例数据都是虚构的；脚本和回执只用本地 HTTP 与假飞书 CLI 验证过，没有在真实账号上跑过完整业务。

更多模板：Claude 委托 Codex 处理网页、每周代码清理、交付 PR。

## 插件体系：四个方向都能自由替换

内置插件随程序安装，填好配置即可启用；第三方插件用 `agent-autoloop add ` 安装。

| 方向 | 内置 | 配置 |
|---|---|---|
| **事件**：怎么发现新活 | GitHub Webhook、GitLab Webhook、HTTP 接口、定时规则、Issue 轮询脚本 | 说明 |
| **Agent**：谁来干活 | Claude Code、Codex、ACP、DeepSeek Harness、通用命令 | 说明 |
| **通道**：去哪找你拍板 | 桌面通知（默认开启）、飞书、钉钉 / 企微 / Slack / Discord | 说明 |
| **交付**：把 CI/CD 也做成插件 | `delivery` | 说明 |

**实测情况：** Claude Code、Codex 和 ACP（官方 Codex ACP 适配器）跑通了多轮问答和跨进程会话续接；飞书跑通了发送、按钮回调和卡片更新；四种 Webhook 模板只在本地模拟服务上验证过，GitLab Webhook 按官方文档的格式测试，没连过真实 GitLab。这些文字通道靠回答链接拍板，要把 `hub.publicUrl` 配成手机或电脑能打开的地址。

**内置 Agent 走第三方网关。** Claude Code、Codex 要接第三方模型服务，或者启动前要先设好环境变量，写一个设好变量再启动它的小脚本，在 Agent 里写 `"program": "脚本路径"`，会话续接和用量统计照旧，见说明。

**其他命令行 Agent 一行接入。** 设置 `use: "command"` 并传入命令数组，`{prompt}` 作为独立参数传递，不会被当成 shell 代码执行。下面的命令整理自各家官方文档，我们还没有逐个跑过：

| Agent | 接入命令 |
|---|---|
| DeepSeek Harness 旧版（内置插件要 0.2.2 或更新） | `dsh --profile headless {prompt}` |
| pi | `pi --print {prompt}` |
| OpenClaw | `openclaw agent exec {prompt}` |
| Hermes | `hermes chat -Q -q {prompt}` |
| Cursor | `agent -p --trust {prompt}` |
| WorkBuddy / CodeBuddy | `codebuddy -p {prompt}` |

会说 ACP 的 Agent 用 `use: "acp"` 接，还能接着原来的会话做：Gemini CLI 写 `"command": ["gemini", "--acp"]`，OpenCode 写 `"command": ["opencode", "acp"]`。这两条同样整理自官方文档，还没跑过。

**交付流水线。** 给 GitHub PR 打上 `deliver` 标签后，它会自己跟进到上线：**审代码 → 等 CI → 合并 PR → 等部署 → 核对线上版本**。审查和交付配置只从 `main` 读取，绝不在接单电脑上检出或运行 PR 里的代码；排队、并发和重试直接复用内核。

**写自己的插件。** 从 Agent、通道、事件 三个可运行的最小模板开始，见插件开发说明。要让 Agent 操作网页，先看浏览器接入。命令行和 MCP 也能查看和回答卡片。

## 内核的四个机制

内核约 1850 行代码、零运行时依赖。它不读系统时钟、不用随机数、不向外发请求，插件主动连进来，账号凭据留在各自的插件里；同样的输入永远得出同样的结果。它把四个计算机领域的成熟做法用到了命令行 Agent 上：

- **挂起零消耗**：等你拍板时进程直接退出，等待状态存在数据库里，Agent 不用一直挂着。你三天没回，这三天就没有 Agent 进程在跑、不花 Token，只有很轻的中台在后台等着；你一回答，它接着原来的对话继续干。
- **事件溯源**：所有状态都从一条只追加的日志算出来，日志和索引在同一个事务里写进磁盘，写完才应答。进程被强杀，已经确认的事不丢（整机断电没有单独测过）；任何一轮为什么跑、结果是什么，一条命令就能查清；数据格式变了就从日志重建，不用写迁移脚本。
- **指令数据分离**：思路和 SQL 参数化一样。Issue 的标题和正文等外部文字只作为资料放进文件，不拼进提示词，提示词里只有校验过字符的类型、编号和链接；用哪个 Agent、在哪个目录、什么权限，只由你本机的规则决定，事件里带 `cwd`、`agent`、`access` 字段会被直接拒收。
- **跳数熔断**：思路和网络包的 TTL 一样。Agent 交回的事件会再派给 Agent，层数一路累加，经过人工提问和定时复查也不清零，Agent 自己改不了；超过 8 层就只记录、不再派活，并发一张卡片告诉你。

### 自己跑一遍

Windows 用 `npm run test:windows` 和 `node scripts/install-smoke-windows.ts`，运行共用行为测试与原生进程、安装检查；Unix shell 测试仍在 Linux/macOS 上跑。

在程序目录 `~/.agent-autoloop/app` 下运行：

| 验证什么 | 命令 |
|---|---|
| 任何一轮的来龙去脉 | `agent-autoloop why 1` |
| 20 万步模拟断网、丢包、崩溃和重复提交，一个种子就能复现 | `node sim/random.ts 24301 200000` |
| 强杀进程 1000 次，已确认的记录一条不丢 | `node sim/crash.ts 1000 12648430` |
| 下面的性能数字 | `npm run benchmark` |

```text
第 1 轮 · 演示
11-03 20:47:25  规则版本 #1
11-03 20:47:25  触发事件：来源 local · 类型 demo.start · 对象 example
11-03 20:47:25  local 领取（演示程序）
11-03 20:47:25  结束：演示完成
```

### 实测性能

Apple M5 Pro、24 GB、Node 24.21.0。写入逐条提交，事务落盘后才应答。

| 指标 | 实测 |
|---|---:|
| 冷启动 | 88.78 ms |
| 空闲内存 | 59.94 MB RSS |
| 1000 个同时等待的长轮询 | 170.49 MB RSS |
| 持久化写入 | 2394 条/秒 |
| 派活 p99 | 1.82 ms |
| 排队 5000 时被挡下的心跳 p99 | 1.66 ms |
| 110 万条事实时的启动 | 99.8 ms |
| 内核行数（含空行和注释） | 约 1850 |
| 运行时依赖 | 0 |

历史变大后，状态汇总会变慢，日志和索引也继续占磁盘；格式变化后的首次启动要从日志全量重建，110 万条用时 43.1 秒。完整数据和测法。

## 用量与合规说明

中台直接调用你本机已经安装并登录好的命令行工具，不会读取或转存你的账号凭据。模型调用消耗算在你自己的账号名下，额度和使用范围遵循各家模型厂商的服务条款。

在高频自动化场景下，各家厂商通常更建议使用 API Key（个人订阅额度主要是为日常人工交互设计的，详见 Anthropic 与 OpenAI 的官方说明）。如果你用它对外提供服务，请使用 API Key。本项目为独立开源项目，与上述厂商无隶属或背书关系。

## 更多文档

- 安装说明
- 规则与交付流水线配置手册
- 如何编写插件
- 完整通信协议
- 安全边界说明
- 参与贡献与交流
- 项目开发约定

仓库目录

| 位置 | 放什么 |
|---|---|
| `kernel/` | 内核：决策、事实日志、状态投影、到期任务、规则匹配、接口行为与卡片表单 |
| `host/` | 运行外壳：Node HTTP、文件与 SQLite 连接、时钟、配置、状态汇总、后台服务和插件加载 |
| `protocol/` | 通信格式、JSON Schema、输入校验、HTTP 客户端和一致性检查 |
| `worker/` | 接单程序：领活、运行 Agent、心跳与停止、读取和提交回执 |
| `cli/`、`bin/` | 用户命令及启动入口，包括状态、回答、`why`、MCP、更新与卸载 |
| `plugins/` | 内置 Agent、事件、通道和交付插件 |
| `examples/recipes/` | 完整场景：规则、任务 Skill 和启用说明 |
| `examples/plugins/`、`examples/skills/`、`examples/*.sh` | 最小插件模板、独立任务手册和 Shell 示例 |
| `skills/agent-autoloop/` | 中台的正式配置与操作手册，安装时也提供给 Agent 使用 |
| `docs/` | 通信协议、插件开发说明与中英文架构图 |
| `tests/`、`sim/` | 日常行为测试，以及模拟、穷举、强杀和变异检查 |
| `scripts/`、`.github/workflows/` | 性能与真机验证、安装冒烟脚本，以及 Windows / Linux / macOS CI |
| 根目录文档与 `install.sh` | 中英文 README、安装说明、安全边界、开发约定、许可证与安装脚本 |

读代码可以从 `bin/agent-autoloop.ts` → `cli/main.ts` 开始，再按功能进入 `host/`、`worker/` 或 `plugins/`；内核设计先看协议。同名文件分属不同层：`host/http.ts` 转换 Node 请求，`kernel/http.ts` 定义接口行为；`protocol/rules.ts` 校验输入，`kernel/rules.ts` 定义规则类型和匹配。

MIT License
