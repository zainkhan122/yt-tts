# Poki source snapshot (README, tool reference, verification)

<!-- source: README.md (fetched 2026-11-06) -->

<p align="center">
  <img src="docs/images/poki-icon.png" width="72" height="72" alt="Poki icon">
</p>

<h1 align="center">Poki uses your iPhone like you do</h1>

<p align="center">
  <img src="docs/images/poki-home.gif" width="720" alt="Poki website home page animation">
</p>

<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a><br>
  <a href="https://poki.bot">poki.bot</a>
</p>

<!-- badges:start -->
<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0--only-blue" alt="License: AGPL-3.0-only"></a>
  <a href="https://github.com/JosssphZhou/poki/stargazers"><img src="https://img.shields.io/github/stars/JosssphZhou/poki" alt="GitHub stars"></a>
  <a href="https://github.com/JosssphZhou/poki/forks"><img src="https://img.shields.io/github/forks/JosssphZhou/poki" alt="GitHub forks"></a>
  <a href="https://github.com/JosssphZhou/poki/issues"><img src="https://img.shields.io/github/issues/JosssphZhou/poki" alt="GitHub issues"></a>
  <a href="https://github.com/JosssphZhou/poki/releases"><img src="https://img.shields.io/github/v/release/JosssphZhou/poki" alt="Latest release"></a>
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20iOS-lightgrey" alt="Platform: macOS and iOS">
</p>
<!-- badges:end -->

## Quick start

**Let your agent install it.** Copy this to your agent:

```text
Install https://github.com/JosssphZhou/poki following its root AGENTS.md, including the MCP skill, and stop whenever you need me to act.
```

**Poki MCP.** Already using Claude Code, Codex, or another MCP client? Connect Poki MCP and use your own subscription. No extra model account needed.

Start the server and keep it running:

```sh
git clone https://github.com/JosssphZhou/poki.git
cd poki
./bin/setup
npm start
```

Requires macOS 15 or later, full Xcode, Rust, Node.js 24+, and ffmpeg. `./bin/setup` checks for missing dependencies. The initial build takes a few minutes.

Poki targets macOS. For Linux, see the community port [poki-for-linux](https://github.com/carrotciallo/poki-for-linux) ([#16](https://github.com/JosssphZhou/poki/issues/16)), maintained outside this repo.

### Prebuilt macOS arm64 package

Download `poki-v0.1.1-macos-arm64.tar.gz` from the release and run:

```sh
tar -xzf poki-v0.1.1-macos-arm64.tar.gz
cd poki-v0.1.1
npm ci --no-audit --no-fund
npm start
```

The package includes the native bridge and idevice tools. You do not need Rust or `./bin/setup`. You still need macOS on Apple Silicon, full Xcode, Node.js 24+, Python 3, and ffmpeg. Register your MCP client and install the optional Agent as described below.

In another terminal, from the same directory, register the MCP server:

```sh
claude mcp add --scope user poki-mcp -- node "$PWD/src/stdio.mjs"   # Claude Code
codex mcp add poki-mcp -- node "$PWD/src/stdio.mjs"                 # Codex
```

**Poki Agent.** For Poki's standalone terminal agent or messaging channels, keep `npm start` running and open another terminal in the same directory. Install the agent, add its command to this terminal's path, and sign in:

```sh
npm ci --prefix agent
export PATH="$PWD/bin:$PATH"
poki login
poki status
```

Poki Agent uses GPT-6.1 Terra (`gpt-6.1-terra`) with low reasoning by default. We recommend keeping it: it is the fastest setup we have tested for phone tasks. Override it with `POKI_AGENT_MODEL`; see [Run Poki Agent](agent/README.md).

For a physical iPhone, pair it with your Mac over USB first. See [Physical iPhone setup](docs/physical-iphone.md).

Update with `./bin/poki update`. Set `POKI_NO_UPDATE_CHECK=1` to disable the daily anonymous GitHub release check. See [Update](AGENTS.md#update) for the request URL, restart steps, and prebuilt packages.

## Try a task

With Poki Agent, one connected iPhone is selected automatically. With multiple devices, add `--device '<device UUID>'`.

```sh
node bin/call.mjs list_devices   # Find your device UUID
poki "Search esp32 in Chrome and summarize the top result"
```

> **Note:** Poki controls your real iPhone. If you ask it to send messages or make payments, it will. Screen contents are sent to your configured model service.

Gets faster with use: Poki Agent remembers past tasks and runs them faster on repeat.

**Channels:** After configuring an authorized channel, start it with `poki imessage` or `poki telegram`. See [Poki Agent](agent/README.md) for setup.

**MCP clients:** Claude Code, Codex, and any client supporting `mcpServers` JSON.

Physical iPhone support has been verified only on iPhones using the Chinese interface. Physical devices support portrait orientation only. App container export and direct links to Settings subpages are unavailable. See [verification and known limits](docs/verification.md).

## Docs

| Topic | Read |
| --- | --- |
| Installation, other MCP clients, and troubleshooting | [Install guide](docs/install.md) |
| Poki Agent, models, iMessage, and Telegram | [Run Poki Agent](agent/README.md) |
| MCP tool reference | [Tool behavior](docs/tools.md) |
| Environment variables and sessions | [Configuration](docs/configuration.md) |
| USB pairing, Developer Mode, and Wi-Fi | [Physical iPhone setup](docs/physical-iphone.md) |
| Test results, known limits, and disclaimers | [Verification](docs/verification.md) |
| Bridge architecture | [Native bridge](native/NATIVE.md) and [simulator adapter](native/simulator.md) |
| Roadmap | [poki.bot](https://poki.bot) |

## Roadmap

<p align="center">
  <img src="docs/images/roadmap.png" width="860" alt="Poki roadmap. Shipped: Poki MCP, Poki Agent, iMessage and Terminal integrations, self-learning routes, remote connections. In Progress: persistent connection performance improvements, Telegram integration, native text input (clipboard-free), simplified tool interface. Planned: Poki App, which runs locally on iPhone and is available while your Mac is powered off. Future: iPhone Duo support, physical device support (no Xcode required), additional model providers.">
</p>

## Star History

<a href="https://www.star-history.com/?repos=JosssphZhou%2Fpoki&type=date&legend=top-left">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=JosssphZhou/poki&type=date&theme=dark&legend=top-left">
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=JosssphZhou/poki&type=date&legend=top-left">
    <img alt="Star History chart" src="https://api.star-history.com/chart?repos=JosssphZhou/poki&type=date&legend=top-left">
  </picture>
</a>

## Core contributors

<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="50%"><a href="https://github.com/igc110"><img src="https://avatars.githubusercontent.com/u/241411380?v=4&size=240" width="120" height="120" alt="igc110"/><br /><sub><b>igc110</b></sub></a><br />Measured each stage in <a href="https://github.com/JosssphZhou/poki/issues/10">#10</a> and found why a tap on a physical iPhone took about 7 seconds: every request read the screen back and started a new poki-native process. The fix that followed made taps on a physical iPhone about a third faster.</td>
      <td align="center" valign="top" width="50%"><a href="https://github.com/ZhehanZhang"><img src="https://avatars.githubusercontent.com/u/67270559?v=4&size=240" width="120" height="120" alt="ZhehanZhang"/><br /><sub><b>ZhehanZhang</b></sub></a><br />Proposed driving a physical iPhone over Tailscale in <a href="https://github.com/JosssphZhou/poki/issues/2">#2</a>, the idea behind remote connections (<a href="https://github.com/JosssphZhou/poki/pull/8">#8</a>).</td>
    </tr>
  </tbody>
</table>

## Thanks

Thanks to everyone who opened an issue or pull request. Your feedback and fixes make Poki better.

<!-- THANKS-WALL:START -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="20%"><a href="https://github.com/ZhehanZhang"><img src="https://avatars.githubusercontent.com/u/67270559?v=4&size=160" width="80" height="80" alt="ZhehanZhang"/><br /><sub><b>ZhehanZhang</b></sub></a></td>
      <td align="center" valign="top" width="20%"><a href="https://github.com/carrotciallo"><img src="https://avatars.githubusercontent.com/u/69567867?v=4&size=160" width="80" height="80" alt="carrotciallo"/><br /><sub><b>carrotciallo</b></sub></a></td>
      <td align="center" valign="top" width="20%"><a href="https://github.com/edge369"><img src="https://avatars.githubusercontent.com/u/63720633?v=4&size=160" width="80" height="80" alt="edge369"/><br /><sub><b>edge369</b></sub></a></td>
      <td align="center" valign="top" width="20%"><a href="https://github.com/guangtouge82"><img src="https://avatars.githubusercontent.com/u/269691899?v=4&size=160" width="80" height="80" alt="guangtouge82"/><br /><sub><b>guangtouge82</b></sub></a></td>
      <td align="center" valign="top" width="20%"><a href="https://github.com/igc110"><img src="https://avatars.githubusercontent.com/u/241411380?v=4&size=160" width="80" height="80" alt="igc110"/><br /><sub><b>igc110</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="20%"><a href="https://github.com/kilingzhang"><img src="https://avatars.githubusercontent.com/u/17439300?v=4&size=160" width="80" height="80" alt="kilingzhang"/><br /><sub><b>kilingzhang</b></sub></a></td>
      <td align="center" valign="top" width="20%"><a href="https://github.com/makirqi-alt"><img src="https://avatars.githubusercontent.com/u/295395617?v=4&size=160" width="80" height="80" alt="makirqi-alt"/><br /><sub><b>makirqi-alt</b></sub></a></td>
      <td align="center" valign="top" width="20%"><a href="https://github.com/mawenhao1028"><img src="https://avatars.githubusercontent.com/u/70818670?v=4&size=160" width="80" height="80" alt="mawenhao1028"/><br /><sub><b>mawenhao1028</b></sub></a></td>
      <td align="center" valign="top" width="20%"><a href="https://github.com/zcyoung2000"><img src="https://avatars.githubusercontent.com/u/62181891?v=4&size=160" width="80" height="80" alt="zcyoung2000"/><br /><sub><b>zcyoung2000</b></sub></a></td>
    </tr>
  </tbody>
</table>
<!-- THANKS-WALL:END -->

## Disclaimer

Poki is an independent open source project. It is not affiliated with, or endorsed by, Apple, OpenAI, or the makers of any app or website it operates. iPhone is a trademark of Apple Inc.

Automating third-party apps and websites may violate their terms of service. Decide for yourself whether to use Poki with a given service. You are responsible for what it does on your device and accounts, including messages it sends, changes it makes, and any account restrictions that result.

Poki is provided "as is", without warranty, as set out in the AGPL-3.0 license.

## License

Poki is open source under the [AGPL-3.0-only license](LICENSE).

Copyright (c) 2026 Joseph Zhou and contributors. Open-source dependencies retain their respective licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). To contribute, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Acknowledgments

<p align="center">
  <img src="docs/images/acknowledgments.png" width="860" alt="Built on open source: pi, idevice, idb, BlueBubbles, Hermes Agent, MCP SDK, sharp, and FFmpeg"><br>
  <sub>Open source acknowledgments: <a href="https://github.com/earendil-works/pi">pi</a> | <a href="https://github.com/jkcoxson/idevice">idevice</a> | <a href="https://github.com/facebook/idb">idb</a> | <a href="https://github.com/BlueBubblesApp/bluebubbles-server">BlueBubbles</a> | <a href="https://github.com/NousResearch/hermes-agent">Hermes Agent</a> | <a href="https://github.com/modelcontextprotocol/typescript-sdk">MCP SDK</a> | <a href="https://github.com/lovell/sharp">sharp</a> | <a href="https://github.com/FFmpeg/FFmpeg">FFmpeg</a></sub>
</p>


---

<!-- source: docs/tools.md (fetched 2026-11-06) -->

# Tool behavior and conventions

**Poki MCP** is a local macOS MCP server that lets AI clients inspect and control an iPhone or iOS Simulator. By default it lists the tools for phone tasks, and it can expose a complete catalog for screenshots, accessibility and Vision OCR inspection, touch and keyboard input, application management, screen recording, and diagnostics.

- **Screen & UI Inspection**: Capture screenshots (`take_screenshot`, `save_screenshot`) and inspect UI hierarchies via Accessibility or Vision OCR (`list_elements`).
- **Touch & Keyboard Input**: Send taps, swipes, hardware keys, and Unicode text across simulators and paired physical devices.
- **App & Device Lifecycle**: Manage applications, open URLs, inspect containers, record video, and run diagnostic checks.
- **Local Daemon Architecture**: Runs a local service (`127.0.0.1:47825` by default) with serialized device execution, per-client session isolation, and interactive local approval gates for sensitive actions. Loopback only unless `POKI_BIND_HOST` names another address, and `POKI_HOST_ALLOW` then lists the `Host` names it answers to; `127.0.0.1` is always served, because local clients read that endpoint from `mcp.json`.

Tool names and input validation schemas live in [`src/data/tools.json`](../src/data/tools.json) with remote connection maintenance definitions in [`src/tools.mjs`](../src/tools.mjs). MCP serves them through `tools/list`. `poki_mcp_status` returns the selected device, available device count, approval mode, and separate counts for device, observation, management, and total tools.

## MCP tool profiles

The default `tools/list` response contains the tools for phone tasks. Tool names, arguments, and execution behavior are unchanged.

| Use | Default tools |
| --- | --- |
| Service and devices | `poki_mcp_status`, `list_devices`, `select_device` |
| Read the screen | `list_elements`, `take_screenshot`, `get_foreground_app` |
| Apps and URLs | `list_apps`, `launch_app`, `terminate_app`, `open_url` |
| Touch and input | `tap`, `tap_text`, `long_press`, `double_tap`, `drag`, `pinch`, `fill`, `type_text`, `scroll`, `scroll_to`, `swipe`, `press_key`, `go_back`, `hide_keyboard`, `press_button`, `get_clipboard` |
| Wait, prompts, and batches | `wait_for`, `handle_alert`, `batch_commands` |

The runtime default list is defined in `src/tools.mjs`. The complete catalog includes simulator management, app installation, recording, location, appearance, and device leases.

### Complete catalog

`POKI_MCP_TOOLS=all` makes `tools/list` return the complete catalog. Any other value, including an unset or empty value, selects the default list.

For a stdio client, the variable belongs to the MCP process environment. This client configuration enables the complete catalog:

```json
{
  "mcpServers": {
    "poki": {
      "command": "node",
      "args": ["/absolute/path/to/poki-mcp/src/stdio.mjs"],
      "env": {
        "POKI_MCP_TOOLS": "all"
      }
    }
  }
}
```

The client needs to reconnect after a configuration change. Each stdio client has its own profile, independent of the daemon's profile.

Direct HTTP clients receive the daemon's profile. Starting the daemon with `POKI_MCP_TOOLS=all npm start` enables the complete catalog for those clients.

### Calls and device selection

Profiles affect discovery only. Every tool remains callable by name through `tools/call`, including tools absent from `tools/list`. The same applies to steps inside `batch_commands`. Argument validation, approvals, cancellation, and device arbitration still apply.

Consecutive device calls do not require `acquire_device`. With one available device, calls select it automatically. With multiple devices, `list_devices` and `select_device` identify the target. An explicit lease remains available for sessions that need exclusive access across several calls. Another session's lease can still block access.

Poki Agent starts its own stdio process with `POKI_MCP_TOOLS=all`. Its existing tool allowlist determines which tools reach its model.

## Ask in plain language

Ask your agent for the task you want done:

```text
Start an iPhone simulator, open Settings, and tell me the iOS version.
```

Three tools handle most interactions:

- `batch_commands` runs a known multi-step task in a single call and returns the visible on-screen text at the end, saving a screenshot round trip.
- `fill` focuses an input field, replaces its text, and verifies the new value.
- `tap_text` waits up to five seconds for its target to appear. If the target is not found, it aborts without tapping and returns what is currently on screen.

Installing apps, opening URLs, and reading the clipboard trigger a macOS approval dialog on your Mac. See [Approval & Clipboard Behavior](#approval--clipboard-behavior).

## Optional action verification

`tap`, `tap_text`, `swipe`, and `scroll` accept `verify: false`. These calls omit the reads that compare the screen before and after an action. Their results include `verified: false` and do not confirm that the app accepted the input. Omitting `verify`, or setting it to `true`, keeps the default verification.

`tap_text` still reads the current screen to locate its target. With verification disabled, it uses the first matching position without waiting for two stable positions. Coordinate actions still obtain the current display dimensions. This option does not promise a call with no device reads.

`batch_commands` also accepts `verify: false`. Supported steps inherit that value, and a step can override it with `arguments.verify: true`. A batch with unverified steps reads the final screen once. That snapshot does not verify each preceding action. An unknown input outcome still stops the batch, including with `stop_on_error: false`.

Accessibility can miss changes that affect only pixels, such as Calculator's display after AC. Default batches can still stop with `no_change` in that case. An unverified tap does not produce `no_change`; inspect the final screenshot before reporting the task result.

## All MCP tools

| Group | Tool | What it does |
| --- | --- | --- |
| Devices | `list_devices` | Find attached iOS devices and booted or previously used simulators. |
| Devices | `start_simulator` | Boot an existing simulator by id or name, or create one from an available model. |
| Devices | `shut_down_simulator` | Shut down the selected simulator. |
| Devices | `reconnect_device` | Attempt a replacement RemotePairing tunnel while preserving a working tunnel if replacement fails. Does not replay input. |
| Devices | `disconnect_device` | Close the selected RemotePairing helper and tunnel. |
| Devices | `select_device` | Select one connected device by id or unambiguous name for this MCP session. |
| Devices | `get_device_info` | Read device identity, capture dimensions in logical points, and optionally platform settings. |
| Devices | `poki_mcp_status` | Report tool counts, connected-device count, selected device, and approval mode. |
| Coordination | `acquire_device` | Exclusively occupy one device across tool calls in this MCP session. |
| Coordination | `renew_device` | Extend this session’s active device lease by 1–600 seconds (default 120). |
| Coordination | `release_device` | Release this session’s device lease after cancelling accepted work and awaiting recording/location cleanup. |
| Coordination | `cancel_device` | Stop all previously accepted work and background recording/location in this MCP session, including calls without a lease. |
| Screen | `observe_device` | Capture one image with its structured observation, non-reused element references and prompt check. |
| Screen | `take_screenshot` | Capture the current display and return a JPEG image with screen dimensions and a prompt warning check. |
| Screen | `save_screenshot` | Save a full-resolution screenshot to an absolute PNG or JPEG path or directory. |
| Screen | `start_recording` | Start recording the selected device display to an H.264 movie. |
| Screen | `stop_recording` | Finalize the session recording and inspect the saved movie before returning its path and media details. |
| Screen | `get_foreground_app` | Read the current foreground application from accessibility services. |
| Screen | `list_elements` | Read accessibility elements, or OCR when auto mode cannot use accessibility. |
| Screen | `wait_for` | Poll visible text until it appears, or disappears when gone=true. |
| Screen | `wait` | Pause for seconds without interacting with a device. |
| Touch | `tap` | Tap at x/y in screen points or at the center of a current element ref. |
| Touch | `tap_text` | Find one visible element matching text, waiting up to five seconds for it to appear and hold still, trying OCR when needed, and tap it. |
| Touch | `double_tap` | Send two taps at x/y in logical screen points or at a current element ref. |
| Touch | `long_press` | Hold one touch at x/y or an element ref. |
| Touch | `swipe` | Move a touch from from_x/from_y to to_x/to_y in logical screen points. |
| Touch | `scroll` | Scroll up, down, left, or right around x/y, or the screen center when omitted. |
| Touch | `scroll_to` | Search for visible text and scroll until it is found, content stops changing, or max_scrolls is reached. |
| Touch | `drag` | Hold a touch, then move between the supplied logical-point endpoints. |
| Touch | `pinch` | Perform a two-finger gesture centered at x/y in screen points. |
| Text and keys | `fill` | Focus a field by ref, coordinates, or matching field label/placeholder/value/identifier, replace its text, and optionally submit after text verification. |
| Text and keys | `type_text` | Enter text into the focused field, optionally clearing it first and sending Return after verification. |
| Text and keys | `press_key` | Send a named keyboard key with optional modifiers and count (default one). |
| Text and keys | `hide_keyboard` | Detect a visible keyboard, send its toggle event, and verify dismissal. |
| Text and keys | `get_clipboard` | Read clipboard contents supported by the platform. |
| Text and keys | `set_clipboard` | Replace the selected device clipboard with text. |
| System | `press_button` | Send a hardware-style button event such as Home, lock, volume, mute, or Siri. |
| System | `system_gesture` | Send the requested system navigation gesture. |
| System | `go_back` | Tap a uniquely identified back control when available, otherwise swipe from the left edge. |
| System | `rotate` | Request a display orientation and invalidate cached coordinates. |
| System | `set_appearance` | Request light or dark appearance through the selected platform adapter. |
| System | `set_accessibility` | Change supported text-size or accessibility display settings. |
| System | `set_location` | Start a simulated latitude/longitude for the selected device. |
| System | `clear_location` | Stop the location simulation owned by this service for the selected device. |
| System | `handle_alert` | Choose a visible alert button by text or accept/dismiss action, waiting up to five seconds for it to appear. |
| System | `request_human_action` | Show a macOS dialog asking the user to complete a step on the device. |
| Apps | `list_apps` | List installed applications, excluding system apps unless include_system=true. |
| Apps | `launch_app` | Launch an application by bundle_id or unambiguous name. |
| Apps | `terminate_app` | Stop an application identified by bundle_id on the selected device. |
| Apps | `install_app` | Install an application from a local path. |
| Apps | `uninstall_app` | Remove an installed application identified by bundle_id. |
| Apps | `open_settings` | Open a supported Settings page or an application settings page. |
| Apps | `open_url` | Ask the selected device to open a URL. |
| Apps | `build_and_run` | Build an Xcode project or workspace from project_path, install the result, and launch it. |
| Apps | `download_app_container` | Copy an accessible application container to a local destination, or the service state directory by default. |
| Apps | `list_crashes` | List available reports, optionally filtering by process name or bundle identifier and kind. |
| Apps | `get_crash` | Read a report by path from list_crashes, or find the newest report for process. |
| Batches | `batch_commands` | Do a whole known task in one call: launch the app, tap, fill, scroll, go back and answer alerts, each {tool, arguments}. |

## Agent skills

[Unlock an iPhone](../agent/skills/iphone-unlock/SKILL.md) packages an authorized passcode workflow, a calibrated portrait keypad, and a native helper that keeps one connection open for the entire input sequence. Poki Agent loads this skill and exposes the host-side `unlock_device` tool when the user has configured a passcode locally. It requires Poki device ownership; it does not add an MCP tool. The skill documents the physical-device evidence and supported layout.

## Coordinates, Screenshots, and Recordings

- All coordinates and element frames use **logical screen points**.
- `take_screenshot` returns JPEG data. Passing `max_width` scales the returned image without changing logical interaction coordinates.
- `save_screenshot` writes a full-resolution PNG or JPEG based on the file extension.
- The `lossless` parameter does not alter either screenshot rule.
- On a simulator, the screen's rounded corners and Dynamic Island area are black in screenshots. Without this mask, that area differs between frames of a still screen, which would expire element refs.
- Default output directories:
  - Screenshots: `~/Pictures/Poki MCP`
  - Recordings: `~/Movies/Poki MCP`

## Element Inspection & Delivery Flags

- `list_elements` prefers Accessibility in `auto` mode and falls back to Vision OCR when Accessibility cannot be read. Every response reports which source was used.
- Element `ref` identifiers are never reassigned within an MCP session. They expire after known input, a device change, a newly captured image showing a change, or **30 seconds**. Input and image changes observed by another session in the same daemon also invalidate the old observation. Re-fetch elements before acting on stale refs. Poki cannot detect an external touch or controller change until it observes that change; it does not continuously watch the display.
- In action responses, `sent=true` means the touch or key report was written to the connection. It does not mean the device acted on it. The device does not acknowledge reports, and a dropped report returns no error.
- A standalone action reads the screen back after it runs. `screen` lists the foreground app and visible text. When `screen_change_verified=true`, `screen_changed` indicates whether the accessibility output changed. This covers elements, text, values, positions, and selected, enabled, or focused states. `false` means no change was observed. It does not prove the action failed. The effect might not be exposed to accessibility, such as a canvas update, or might not have appeared yet. `true` does not prove the action caused the change, because another element may have updated at the same time. `screen_change_verified=false` means the before and after states could not be compared, such as in an app with no accessibility elements. In that case, inspect the screen directly.

## Device ownership and stopping work

Consecutive calls do not require a lease. For exclusive ownership across several calls, call `acquire_device` with an explicit device ID or unambiguous name. Acquisition resolves the device without booting it and returns `lease_id`, `device`, `state` and `expires_at`. Each session can hold one device lease. While holding it, release before switching to another device. Acquisition is serialized with ordinary operations; renewal, release and cancellation bypass that queue.

- `acquire_device({device, ttl_seconds?})`: default TTL 120 seconds, allowed integer range 1–600 seconds. Another session cannot acquire, observe or operate this device during the lease. Selection, aliases, automatic selection, batch steps and existing simulator startup all pass through the same device check. Creating a new simulator reserves its creation operation before running it; an existing lease must be released first.
- `renew_device({lease_id, ttl_seconds?})`: extend the matching session's active lease from the current time. Long operations do not renew automatically. Renew before expiry, including while a long tool is running.
- `release_device({lease_id})`: invalidate accepted work, stop recording and simulated location owned by this session, await cleanup, then make the device available. A lease stays `releasing` until cleanup finishes.
- `cancel_device({lease_id?})`: stop **all previously accepted work in this MCP session**, including queued calls made without a lease, and stop its background recording/location. If supplied, `lease_id` must match this session's active lease. Other sessions are unaffected. New work may be submitted after cleanup finishes; an old queued operation never resumes as an unleased operation.

The stop result identifies its scope, reason and cleanup outcomes. Cancellation stops owned local processes and waits; it cannot undo input already dispatched to the device. Inspect the screen before retrying an unknown outcome. The stdio bridge forwards SDK request cancellation to the corresponding daemon operation, including waits, device helpers and the local approval dialog. A normal HTTP response closing is not a session cancellation. Normal stdio EOF or termination requests session cleanup; a crashed client holding an explicit lease is bounded by its TTL. A client without a lease has no persistent ownership guarantee after an abnormal exit; use an explicit lease for recordings and multi-call tasks.

`list_devices` still reports discovery and occupancy (`occupied`, `owned_by_session`, `state`, `expires_at`) without exposing another session's task. Occupied physical devices are not queried for additional name/model information by other sessions. If an alias has not been discovered, use the displayed device ID. An unleased recording or location must be stopped by its owner before a different session can acquire that device.

This arbitration exists only in **one shared Poki daemon**. Different daemon instances and different `POKI_MCP_STATE_DIR` values are independent. It does not lock out other control software or a person touching the screen. Run one daemon for the clients that need to coordinate; do not start multiple daemons against the same endpoint directory. No persistent task database or recovery across daemon restarts is provided.

## Observations, deadlines and receipts

`observe_device` returns one PNG plus structured elements and a prompt check. Its observation records a unique ID, device, point dimensions, capture start/end, structure completion time and AX/OCR source. AX and image are collected sequentially and are explicitly **not atomic**. `list_elements`, `take_screenshot` and successful `wait_for` also identify the observation; successful `wait_for` includes its matching image so the caller need not capture a different moment. OCR is reused for the same image when checking prompts or falling back after an AX miss, with no persistent vision service.

`wait_for` uses a monotonic deadline covering capture, AX, OCR and polling. It starts no new read after that deadline, aborts in-flight external work and waits for owned processes to close. Consequently response delivery can include bounded process termination time after the deadline; the deadline is not a claim that the HTTP response arrives at the exact requested millisecond.

Input receipts retain `sent`, `text_verified`, `submit_sent` and other confirmed facts when recording recovery fails. The separate `recording` object reports recovery failure. Unconfirmed delivery remains `outcome: "unknown"`; it is never automatically replayed. Automatic recovery is suspended while native input intentionally interrupts the media stream. Normal reconnection after an explicit input is counted as `input_reconnects` and does not consume the automatic retry budget, so healthy multi-step recording is not limited to three inputs. Only background recovery from unexpected stream disconnects consumes `automatic_retries`, at most three per recording lifetime. Each reconnect still has a five-second first-frame deadline. `reconnects` is the total of these two counters. A failed reconnect leaves an explicit error; stop/start a recording to begin a new automatic budget. Stop, release, cancellation and session cleanup disable retries and await owned recording processes, and cleanup reports finalization errors separately.

Batch results retain the executed prefix and each step's `elapsed_ms`, then report `stop_reason`. A step's `device` applies to that step alone; steps without one use the session selection, and the screen read after the last step comes from the device that step used. Human handoff, cancellation, expiry, timeout and unknown input outcomes always stop subsequent steps even with `stop_on_error=false`. A successful action's receipt remains present if stopping occurs later. A detected human-only prompt in `handle_alert`, `take_screenshot`, `observe_device` or the screen read after the last step sets the same `needs_human_action` stop reason; observation tools retain their captured image and structure. With the default `stop_on_error`, every step is checked before any runs, so a mistyped step costs nothing. The last block carries `screen`, and after a stop also `failed_step`, `remaining_steps` and `next`, so the following call can fix one step and send only what is left.

Tool responses include `_meta.timing.stages` with queue, capture, AX, OCR, input, recording recovery and external-process durations where exercised. Each stage has an ID and parent ID. Parent durations include their children, so do not add parents and children. External-process time includes helper startup, connection and work inside the helper; those internal costs are not separately measured. Timing metadata contains no input text, device identifiers or image content, and it does not measure model reasoning or client round-trip time. No end-to-end speed multiplier is claimed.

## Efficient short workflows

- **Put the whole known task in one batch:** When the request already names what to do, send `launch_app` and every step in one `batch_commands` call. `launch_app` on a simulator returns once the interface is readable; `tap_text`, `fill` and `handle_alert` wait up to five seconds for their target to appear and hold still, so a batch can cross screens; the reply ends with the visible text, so a closing `take_screenshot` is only needed for pixels. Leave out a step when whether to do it depends on what an earlier step shows, or when it needs the user's decision. A wrong target stops the batch without tapping and reports the closest text on screen. Each step result reports `elapsed_ms`, which reflects server-side execution time only and excludes model reasoning and client round-trip overhead.
- **Use `fill` for known input fields:** Call `fill` directly instead of chaining `tap` and `type_text`; `field` can be left out when one text field is visible. On physical devices, `fill` focuses, replaces, and verifies text within a single native input session to avoid an extra connection wait. On simulators it taps, waits for focus and types, and a verified mismatch is an error. Plain text typed on a simulator first switches its keyboard to `en_US` (`simctl keyboard`), because a simulator created on a Chinese Mac types through Pinyin and rewrites Latin text and punctuation; the setting stays on that simulator. Because `fill` replaces existing field content, review your draft beforehand; reserve `type_text` for appending to an already-focused field.
- **Review and submit with `return`:** To inspect text before sending, `fill` and read the `screen` it returns. After verifying the draft, submit using `press_key` with `return` and inspect the resulting screen. Do not re-enter the full text or call `type_text` with an empty string to submit. Note that `text_verified` only confirms text entry into the field and `sent` only confirms the action was dispatched; neither guarantees application-level delivery.
- **Handle `CoreDeviceError` 4016 via observed UI:** If launching an app fails with `CoreDeviceError` 4016, inspect the current screen and continue through an observed Home Screen or App Switcher entry point. Do not repeatedly retry the same launch path unless device conditions change. This serves as invocation guidance and does not permanently mark the app as unavailable after a single failure.

## Approval & Clipboard Behavior

- **Local approval dialog**: Installing or uninstalling apps, building and running projects, opening URLs, downloading app containers, and reading or writing the clipboard trigger a local macOS approval dialog by default.
- Setting `POKI_MCP_APPROVAL_MODE=allow` bypasses this local daemon prompt for preapproved workflows, but it **never** auto-completes iOS/macOS system authorization dialogs or makes `request_human_action` succeed automatically.
- **Unicode paste & clipboard restoration**:
  - Unicode text entry may use the device clipboard. On physical devices, Poki MCP attempts to save and restore a complete clipboard snapshot; if full restoration is not possible, the response explicitly reports restoration as unavailable.
  - The snapshot is held only in memory for the duration of that single operation and cannot be restored by a subsequent tool call after a human handoff.
  - If a paste prompt is pending or the target field cannot be verified, automatic submission stops and leaves the intended text on the clipboard.
  - Poki MCP **never** auto-accepts an iOS **Allow Paste** prompt. Note that a true first-time **Allow Paste** human-handoff flow remains unverified on hardware (prior successful paste checks did not trigger the system prompt).


---

<!-- source: docs/verification.md (fetched 2026-11-06) -->

# Verification and known limits

## Status

The Simulator path is tested end to end from a fresh clone. Physical iPhone support has been verified only with the Chinese interface in portrait orientation. `sent: true` only means the touch was written to the connection. The device does not acknowledge it, so check `screen_changed` and the returned screen.

## Physical iPhone status

The earlier measurements below come from a single iPhone running iOS 27.3 over Wi-Fi. Treat them as a test log from that setup, not a guarantee for other apps or devices.

- With the old connection handling, tapping a specific search field in a chat app dropped 2 of 70 touches. Every dropped touch still returned `sent: true`. Keeping the connection open until the post-touch wait finished dropped 0 of 70 touches, and the final build dropped 0 of 24. These numbers only apply to that single search field.
- Via MCP in the same app, `tap_text` took effect 12 of 12 times. Batches that launched the app and called `tap_text` opened the conversation 14 of 14 times.
- Via MCP, `fill` on that search field worked 6 of 6 times and took about 15 seconds. If `fill` cannot verify the entered text, it now returns an error and stops the batch, matching Simulator behavior. `tap_text` took about 8 seconds.
- Two earlier `tap_text` calls on a conversation row returned `sent: true` but had no effect. We have not reproduced this failure, so it may have a different cause. Why the device drops touches is unknown.
- Touches sent too soon after app launch may have no effect. At 1.5 seconds after launch, 0 of 3 taps opened the conversation. At 2.8 seconds or later, 12 of 12 did. Via MCP, the pre-tap screen reads have so far delayed the tap past this window.
- Tapping a target next to a bottom floating bar had no effect 4 of 4 times in the Settings app. This is not fixed. Those taps now return `screen_changed: false`.
- We only measured taps. `drag` and `pinch` use the same connection path and were not measured. The latest update to how `screen_changed` compares screens has not been tested with touches on a physical phone.
- In one landscape game, taps on button coordinates had no effect, while portrait taps in the same session worked. The cause is unknown.

## Measured on simulators only

Known tasks ran on iOS 27.0 simulators with the disposable fixture app. A fresh client window got the tool descriptions and one sentence of task. Time covers the whole session, from client start to the last reply. Values are medians of 5 interleaved runs per client, task, and group. The single-step group was the same commit with `batch_commands` hidden.

| Client | Task | Round trips, batch | Round trips, single-step | Seconds, batch | Seconds, single-step |
| --- | --- | --- | --- | --- | --- |
| Claude Code | Counter | 3 | 5 | 17.1 | 24.6 |
| Claude Code | Form | 3 | 8 | 20.0 | 31.6 |
| Codex CLI | Counter | 2 | 7 | 24.4 | 36.4 |
| Codex CLI | Form | 2 | 7 | 28.7 | 46.1 |

A task with a deliberately wrong button name showed no measurable time difference. The ratio changes with task and machine load, so do not read it as a constant. These numbers were measured before the later physical-tap changes. They have not been re-run. To run the measurement yourself, see `bin/eval-first-call.mjs`.

## Test Suites

**Current state on an iOS 27.0 simulator.** `bin/verify-fixture.mjs` passes. `bin/verify-platform.mjs --with-core` passes and reports the pasteboard limit below, so it does not verify clipboard writes on this runtime. `npm test` passes on a loaded Mac. Occasional failures were seen under heavy load, and the cause of one is not known yet.

- **Protocol suite (`npm test`)**: Runs against an isolated temporary state directory and ephemeral port. It verifies the `stdio`-to-HTTP bridge, authentication, tool discovery, absent-device error handling, and wait-only batches without injecting input into a phone or simulator. All external device programs are replaced in an isolated copied runtime, including discovery and the approval dialog. No phone, simulator UI or real system dialog is used. The coordination suite covers two clients, lease expiry and exit cleanup, queued/SDK cancellation, stale references, OCR reuse, read deadlines, recording receipt preservation and bounded recovery. Node dependencies must be installed; native helpers need not be built.
- **Live simulator verification (`bin/verify-fixture.mjs`, `bin/verify-platform.mjs`)**: Optional scripts that perform real UI and application mutations. They require a dedicated disposable simulator named `Poki MCP QA` with the `PokiMCPFixture` app (`local.pokimcp.fixture`) installed, and are intentionally excluded from `npm test`.

These coordination checks use external-process fixtures. They do not establish real-device cancellation, gesture effects, first-time system permissions, or an independent new-user installation. Those checks still require separately authorized device acceptance.

## Known Platform Limits

- **First release on physical iPhones**: Portrait orientation only. Landscape control is unsupported. App container export (`download_app_container`) and direct Settings subpage links (`open_settings` with a page) are unavailable. Open Settings normally and navigate its visible controls instead. These limits do not change simulator support.

- **Pasteboard (iOS 27 Simulator)**: On the tested iOS 27.0 runtime (24A5370g) and iOS 27.1 runtime (24A94425), `simctl pbcopy` leaves the simulator pasteboard empty. Because of this, `set_clipboard` fails its readback and non-ASCII text cannot reach a simulator field. `fill` reports this as a mismatch. Plain ASCII text does not use the pasteboard and is not affected.
- **Emoji keyboard dismissal (iOS 27 Simulator)**: On the tested iOS 27 simulator, the emoji panel remains visible after toggling the keyboard. `hide_keyboard` truthfully reports failure while preserving field text; use the on-screen keyboard hide button or an app-supported outside tap instead.
- **Settings & Accessibility services**: Some Settings routes are unavailable. Simulator *Reduce Motion* and *Reduce Transparency* require direct Settings UI interaction, and a tested physical device returned `not implemented` for the larger-accessibility-sizes service.
- **Signing & container permissions**: Installing or building apps for physical devices requires valid Apple signing credentials (none are bundled), and container access is bound by platform permissions.
- **Private Apple interfaces**: CoreSimulator and physical-device bridges rely on Apple private interfaces whose behavior may change across OS releases. The size of the tool catalog does not imply complete tool/parameter validation across every iOS, macOS, or Xcode version.
- **Crash symbolication**: Only matches UUIDs and architectures from builds known to the current MCP session.

For deeper architecture notes, see the [physical-device bridge documentation](../native/NATIVE.md) and [simulator and platform adapter documentation](../native/simulator.md). Keep runtime outputs and test evidence inside the git-ignored `.runtime/` directory; never commit device screenshots, clipboard contents, or pairing records.

## Disclaimers

- Speed scales with the model and service tier you choose. Actual time depends on the model service, your Mac, and the phone's state.
- Saved routes require the page to stay the same. When it changes, Poki falls back to the model.
- Screen contents are sent to your configured model service.
- Poki does not confirm actions on the device. It operates a real device as instructed, and you are responsible for any messages sent or payments made.
- Provided as is under the AGPL-3.0-only license, without warranty.
- Poki is not affiliated with Apple. iPhone and iMessage are trademarks of Apple.
