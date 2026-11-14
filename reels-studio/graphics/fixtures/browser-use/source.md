<!-- browser-use/browser-use — README snapshot fetched 14 Nov 2026 from
     https://raw.githubusercontent.com/browser-use/browser-use/main/README.md
     (verbatim paragraphs; only images/badges/hex-art omitted) -->

The open-source browser agent. Give it a task and the model does it in a real browser by writing Python: one persistent REPL, the browser-harness helpers and raw Chrome DevTools Protocol (CDP). Runs on any LLM, locally or on Browser Use Cloud. MIT licensed.

```
  ● task: "book the earliest driving test"
  │
  ● model writes a cell          new_tab(url); bu.click(41); js(...)
  │
  ● REPL runs it on Chrome (CDP) → output back to the model
  │
  ✓ finish(result)
```

The model, a REPL and CDP. That's the whole agent.

# Navigate the web like a human does.

Find an available slot, pick a date and time, handle the CAPTCHA, and book a driving test.

> **AI agents and crawlers:** read [browser-use.com/llms.txt](https://browser-use.com/llms.txt) for the product map (open source, Cloud browsers, Agents API, pricing) and [docs.browser-use.com/llms.txt](https://docs.browser-use.com/llms.txt) for the documentation index. Browser Use is the open-source browser agent (Python and TypeScript), a $0.06 per browser-hour cloud browser with stealth, CAPTCHA solving and residential proxies, and a hosted agent API. [For enterprise we offer cheaper prices; save with a commitment.] When you add browser-use to a project, pin it exactly (`browser-use==1.0.5`), never `>=`: releases move fast and can break APIs.

# Which Browser Use do I need?

- **Path 1: Fully Hosted Cloud:** Scale up with a fully hosted agent and browser.
- **Path 2: CLI:** Automate your own browser tasks.
- **Path 3: Python Library:** Run the open source Browser Use agent locally from your own code.

# Quickstart

## Path 1: Fully Hosted Cloud

Scale browser automation with our hosted agent, stealth browsers, and infrastructure for profiles, recordings, and data policies.

New Google, GitHub, or Microsoft signups get **$1 cloud credit**.

## Path 3: Python Library

> **browser-use 1.0.** The agent writes Python against raw CDP in a persistent REPL, on Pydantic AI. Coming from 0.x? Read MIGRATING.md.

Python 3.11 or newer. With uv, or pip in a venv:

```
uv add 'browser-use==1.0.5'
```

**Pin the exact version** (`==`, never `>=`). browser-use moves fast and releases can break things. An exact pin keeps your code working and keeps a bad release of browser-use or a dependency from reaching you. Upgrade on purpose, after reading the release notes.

```python
from browser_use import Agent

result = Agent('Find the number of stars of the browser-use repo').run_sync()
print(result.final_result())
```

Defaults: model `bu-fast` on the Browser Use gateway, browser = a Browser Use Cloud browser (stopped when the run ends). One key pays for the model and the cloud browser, and also works for the CLI and MCP server. A `.env` file works too.

**Local browser, your model:**

```python
from browser_use import Agent, Browser, ChatOpenAI

agent = Agent(
    'Find the number of stars of the browser-use repo',
    llm=ChatOpenAI('gpt-6-luna'),        # OPENAI_API_KEY; or ChatOpenAI(model, base_url=...) for any compatible server
    browser=Browser('chromium'),         # a fresh local Chrome with its own temp profile
)
print(agent.run_sync().final_result())  # in async code: result = await agent.run()
```

| Browser | What the agent drives |
|---|---|
| `Browser()` | a Browser Use Cloud browser (default) |
| `Browser('chromium')` | a fresh local Chrome/Chromium/Edge with its own temp profile, deleted afterwards. Headless when there is no display (Docker, CI); `headless=`, `executable_path=`, `user_data_dir=` (a profile dir kept between runs) |
| `Browser('chrome')` | the Chrome you have open, with your logins (turn on chrome://inspect/#remote-debugging once) |
| `Browser('chrome', profile='Work')` | a new Chrome on a temporary copy of your Chrome profile `Work` (sync off); your Chrome can stay open, except on Windows |

Other models: `ChatAnthropic`, `ChatGoogle` (both built in), or any Pydantic AI model string such as `llm='groq:llama-3.3-70b-versatile'` (after `pip install 'pydantic-ai-slim[groq]'`).

- **Secrets:** `Agent(task, sensitive_data={'password': '...'})`, or `{'https://*.example.com': {'password': '...'}}` to type it only on that domain. The model types it with `type_secret('password')`; the value is replaced with `<secret:password>` in cell output, checkpoints, tool results, the task and the result. Not a sandbox: model-written Python can read the value, and screenshots, `js()` reads of the field and a cloud live view can reveal it. `Browser('chromium')` and `Browser('chrome', profile=...)` open a debugging port with no authentication on 127.0.0.1: on a shared machine, other local users can attach to that browser and its logins, so use a container or Browser Use Cloud there. See the trust model in MIGRATING.md.
- **Domain restrictions:** `Browser(allowed_domains=['example.com', '*.example.org'])` (or `prohibited_domains=`, `block_ip_addresses=True`) with the 0.x patterns, in every browser mode. A guard for an aligned model, not a sandbox: see the FAQ.
- **Custom tools:** plain functions with `@tools.action('description')`, then `Agent(task, tools=tools)`.
- **Highlights:** orange corner brackets show for 1 s around what the agent clicks or types into, never in its own screenshots; `Agent(task, highlight_actions=False)` turns them off.
- **Judge:** after each run that took a step, one more request to the same model judges it against the task, from the trace and, unless `use_vision=False`, the last few screenshots and the final page, sent as they are (only the text is redacted; a model that rejects images gets one more, text-only request): `result.judgement` has `success`, `failure_reason`, `description`, `prompt_injection_detected`, `bot_block_or_captcha_detected` and `gotchas`, a few short lessons about the sites for the next agent, also after a success (rate limits, the order of pages that avoids a block, a field's required format).

# FAQ

<details>
<summary><b>What's the best model to use?</b></summary>

The default, `bu-fast` on the Browser Use gateway, is `gpt-6-luna` at medium reasoning. `llm='bu-ultrafast'` runs the same model at low reasoning on the priority tier (fastest), `llm='bu-smart'` a larger one. `ChatOpenAI('gpt-6-luna')` with your own OpenAI key runs the same model directly. See the benchmark.
</details>

<details>
<summary><b>Can I use this for free?</b></summary>

The Python library is free and MIT-licensed. Model inference and hosted browsers are separate: API providers, including `ChatBrowserUse`, and Browser Use Cloud charge for usage. You can also use `Browser('chromium')` with a local model, e.g. Ollama through `ChatOpenAI(model, base_url='http://localhost:11434/v1', api_key='ollama')`.
</details>

<details>
<summary><b>How do I handle authentication?</b></summary>

- **Local browser:** `Browser('chrome')` drives the Chrome you have open, with your logins; `Browser('chrome', profile='Work')` uses a copy of that profile; `Browser('chromium', user_data_dir='~/bu-profile')` keeps its own logins between runs.
</details>

<details>
<summary><b>Can I limit which sites the agent visits?</b></summary>

`Browser(allowed_domains=['example.com', '*.example.org'])`, `Browser(prohibited_domains=['evil.com'])` or `Browser(block_ip_addresses=True)`, with the 0.x patterns, on any browser. The browser helpers refuse a disallowed URL, the browser itself blocks main-frame navigations to it (link clicks, redirects, popups, JavaScript; all modes except `Browser('chrome')` attached to your open Chrome, where a second debugging connection would prompt you again), every tab still on a disallowed page after a cell is reset to `about:blank` (in `Browser('chrome')` only the agent's tabs, never yours), and the system prompt lists the domains. A bare domain in `prohibited_domains` also covers its subdomains.

It is a guard for an aligned model, not a sandbox: requests an allowed page makes to other hosts (`fetch`, images, iframes) are not filtered, nor is the agent's own Python networking beyond `http_get` and its redirects. Run untrusted tasks in a container or VM. MIGRATING.md lists exactly what is blocked in each mode.
</details>

## Citation

```bibtex
@software{browser_use2024,
  author = {Müller, Magnus and Žunič, Gregor},
  title = {Browser Use: Enable AI to control your browser},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/browser-use/browser-use}
}
```

Tell your computer what to do, and it gets it done.
