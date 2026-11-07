# Source snapshot: ccch1mneyyy/dsh-Go

Fetched 2026-11-07 from  (README, English version where the repo ships one).

HTML tags and images removed; wording unchanged.


---

## ccch1mneyyy-dsh-Go.en.md

简体中文 · English

  An Android client for DeepSeek Harness. Run DSH right on your phone, or drive the one on your computer.

  #1 on Trendshift's all-language daily ranking · 2026-10-30

Deepy and Whale girl keep you company

They code, flip, wave and nap along with DSH, and can follow you to the home screen.

Download DSH Go

Get the latest APK from GitHub Releases or the download page at go.dshtui.com. Most phones need the arm64 package.

  &emsp;

  Thank you all for supporting and loving DSH Go! iOS and HarmonyOS versions are coming as soon as I can make them. The more stars, the faster they come, hehe

  New here? Start with the user guide, and bring questions to the forum and QQ group.
  An early test build signed with a different key can't be updated in place: uninstall it first, which clears your chats, the Linux environment and settings.

Runs on your phone. Drives your computer.

A Linux environment built in, no root and no Termux. Switch to the DSH on your computer in one tap.

Chime in, interrupt, stay tidy

Send a message while DSH is replying, and tap "Send now" whenever you like. Finished steps fold into one line.

Native, with the web interface one tap away

Switch between the native app and the official web interface on the same chat. It reopens in whichever you used last.

Share cards, replays and links

Turn a reply into a share card. Share a whole chat as a link that replays in any browser, end-to-end encrypted.

Landscape and tablets

New layouts for landscape phones and tablets: the sidebar stays, content stays centered, the keyboard never crowds.

Colors and home screen icons

Six accent colors, your wallpaper's, or your own. Four home screen icons and three icon styles.

English and 中文

The whole app speaks both. It follows your system, or pick one in Settings.

Phone control

DSH reads the screen and taps for you. Sensitive actions stay with you by default; understand the risks before relaxing app rules or lifting limits.

## Features

DSH Go combines a chat interface, an on-device runtime and remote connections. It is a third-party project built on DeepSeek Harness. The DSH engine runs on your phone; model requests are still handled by the model provider you configure.

- **On-device runtime:** install Ubuntu, Node.js and DSH from the app without Root or a separate Termux installation.
- **Remote connections:** use DSH on a computer or server through SSH or DSHarness Remote, developed by Li Guobao (liguobao).
- **Chat and tools:** switch models, send images, use voice input, and respond to tool approvals and questions. Chat and web interfaces are available.
- **Plugin interfaces:** use native tool cards, forms and panels from plugins adapted for DSH Go. This repository includes an SDK, guides and examples.
- **Phone control:** after you enable the required permissions, let the local engine read the screen, tap and type. You can stop it at any time.
- **Sharing and appearance:** share, export and replay conversations, and customize themes, icons and pets.

Capabilities depend on the host and connection. DSHarness Remote currently accepts image attachments only, does not open the web interface inside the app, limits plugin management to enabling or disabling plugins, and does not support DS Bot or conversation-log export. See Engine and remote hosts.

## Install

Installation requires Android 8.0 (API 26) or later. The **arm64** package on the Releases page is for typical 64-bit Android phones; the x64 package for x86_64 devices and emulators is under “Other builds” at the end of the release notes. This repository has no 32-bit ARM build.

1. Download the APK for your device architecture from GitHub Releases or the download page, and follow Android's prompt to allow that installation source.
2. On first launch, choose an on-device runtime or a remote host.
3. Configure a model and its credentials for the selected host, then start a conversation. Some remote providers must be configured on the host itself.

A remote-only setup does not need a local runtime on the phone. Phone control works with the local engine outside safe mode and requires permissions such as Accessibility, as explained in the app. Non-disruptive mode additionally requires Android 14 or later and Shizuku or self-ADB. Follow the user guide for setup.

The local engine uses compatible PRoot startup by default. Direct startup is off by default in Developer options; see Troubleshooting for compatibility and fallback behavior. The current Android build targets APK sideloading, not Google Play distribution.

## Data and permissions

Model requests go to the provider you configure. During phone-control tasks, relevant screen text may be sent to the model, and vision-capable models may receive screenshots. Read the app's permission disclosure before enabling the feature.

“Send anonymous usage statistics” is on by default. You can turn it off during onboarding or in Settings → Privacy and sharing. See Troubleshooting for the fields collected and what happens when it is disabled. Review content before sharing it; recipients can save a copy of a shared link or file's contents.

## Risks and disclaimer

DSH Go is an unofficial community project. It is not affiliated with, endorsed by, or a representative of DeepSeek. Before using it, please understand:

- **AI is fallible:** answers, code and actions may be wrong, and malicious instructions in web pages, messages or files may mislead it. Verify important results; do not rely solely on AI output for high-stakes medical, legal or investment decisions.
- **Tools have real effects:** commands and file changes on local or remote hosts, as well as phone control, may cause data loss, privacy breaches, or harm to accounts, funds or devices. Skipping confirmations, relaxing app rules or lifting limits reduces safeguards; confirmation and blocking mechanisms cannot eliminate all risks. Keep default protections, grant only necessary permissions, and avoid lifting limits on devices holding payment or banking details. See the phone-control guide.
- **Third-party services and costs:** models, remote hosts and plugins operate under their own terms. Data handling, availability and charges depend on the services and configuration you choose. Running locally does not mean the model is offline or that data never leaves the device.
- **Take precautions:** back up important data, connect only to trusted hosts, install only trusted plugins, and monitor model usage and costs. Do not leave AI unattended on irreversible or high-risk tasks.
- **No warranty and limits of liability:** to the extent permitted by applicable law, the software is provided “as is,” without guarantees of accuracy, continuous availability or fitness for a particular purpose. See sections 15–17 of LICENSE for warranty disclaimers and liability limits. This notice does not exclude or limit liability that cannot legally be excluded or limited, or reduce your statutory rights.

## FAQ

Is this an official DeepSeek app?

No. DSH Go is an unofficial client made by the community, built on the open-source DeepSeek Harness. DSH itself runs on your phone; model requests go to the provider you configure, so it needs a connection and bills your account with that provider.

Is it safe?

The local web interface only answers to the app itself. Shared links are end-to-end encrypted: the key lives only in the link, and the server never sees the content, but anyone with the complete link can read and save it. Phone control retains sensitive-action protections by default; relaxing app rules or using “Lift limits” reduces those protections. Safeguards cannot guarantee zero risk. See Risks and disclaimer and the phone-control guide.

Will the system kill it in the background?

Some battery savers hold apps back. When that happens, DSH Go tells you and opens the right setting, on vivo, Xiaomi, Huawei, Honor and OPPO.

What phone do I need?

Android 8 or later. On a phone, download the package on the Releases page; the x86_64 build for emulators is under “Other builds” at the end of the release notes. Running DSH on the phone needs the built-in environment, so keep about 1 GB free; connecting to DSH on a computer or server doesn't.

Is it open source?

Yes. The code is in this repository under AGPL-3.0; `sdk/` and `examples/` are MIT. The DSH Go name and logo, and the mascots Deepy and Whale girl, are not covered by the open-source license; see ASSETS.md. Credit requirements for forks and redistributed builds are in License scope and redistribution.

## Build from source

The following workflow targets **Linux x86_64**. The toolchain script currently defaults to JDK 17, Flutter 3.47.7 and the Android SDK/NDK. The app requires Dart `^3.13.5`. Prepare Bash, Git, curl, tar, unzip, xz, Python 3, zstd (for unpacking zstd-compressed deb archives when Python does not provide `compression.zstd`), file and standard GNU utilities. Resolving Ubuntu package locks again also requires gpgv.

Start with the complete source tree and project assets. Fonts, images and other files declared in `app/pubspec.yaml` are build inputs. The following script generates the runtime bundle.

```bash
git clone 
cd dsh-go

bash tooling/setup-toolchain.sh
source tooling/env.sh
flutter --version
java -version

bash runtime/build-runtime.sh arm64-v8a
DSH_BETA_TOKEN_FILE= bash tooling/build-apk.sh -f arm64 --keep-daemon
```

The toolchain script downloads the SDK/NDK and emulator images and runs Android SDK license acceptance. Its default location is `~/dev`; set `DEV_ROOT` to use a separate directory. The script reuses existing installations, so check their versions before building.

The output is `app/build/app/outputs/flutter-apk/app-arm64-release.apk`. Runtime assembly uses the versions and verification data pinned in the repository and needs network access to download dependencies. `DSH_BETA_TOKEN_FILE=` leaves out the maintainer's beta-channel token. `--keep-daemon` preserves Gradle daemons, which is useful when working on other Android projects at the same time.

For an x86_64 APK, generate its runtime first:

```bash
bash runtime/build-runtime.sh x86_64
DSH_BETA_TOKEN_FILE= bash tooling/build-apk.sh -f x64 --keep-daemon
```

Without `app/android/key.properties`, a local release build uses debug signing. It cannot replace an official installation signed with a different key. Use a test device and preserve existing data; do not uninstall your daily-use app just to resolve a signing mismatch. Do not commit signing keys or their configuration.

To inspect APK build commands without building:

```bash
DSH_BETA_TOKEN_FILE= bash tooling/build-apk.sh --dry-run -f all
```

## Repository layout

| Path | Contents |
| --- | --- |
| `app/` | Flutter interface and Android Kotlin platform code |
| `packages/dsh_client/` | Dart client for the DSH Web API |
| `packages/dsh_remote/` | Dart client for DSH Remote |
| `runtime/` | Linux runtime assembly, engine patches and the app bridge |
| `sdk/plugin-kit/` | Native plugin authoring kit, used from the repository and not published to npm |
| `examples/plugins/` | Example plugins |
| `docs/guide/`, `docs/plugins/` | User and plugin development guides |
| `docs/assets/` | Showcase images, pet animations and community QR codes used on this page |
| `tooling/` | Toolchain, APK build and diagnostic scripts |
| `services/`, `site/`, `infra/` | Companion sharing service, website and deployment materials |

## Contribute

Report bugs and suggest improvements in Issues. For code, documentation and translation changes, start with CONTRIBUTING.en.md. Plugin authors can use the plugin guides and SDK.

Report security issues through SECURITY.en.md. Keep vulnerability details and credentials out of public issues.

## Community

- **Forum**: forum.dshtui.com
- **QQ group**: `1132118290` (join)
- **WeChat group**: scan the code below; if it has expired, join the QQ group

  &emsp;&emsp;

  QQ group 1132118290. On a computer, join with one click. The WeChat code changes every week; if it has expired, join the QQ group.

## Friends' Links

- **DSH-TUI**: the interactive terminal UI for DeepSeek Harness by the same author — the desktop counterpart to DSH Go, with a pixel whale, live status and time travel (GitHub).

## License scope and redistribution

The code is open source under AGPL-3.0, and forking it to study, self-host or build on is welcome. Please respect the original author and project origin:

- **Please contact the author before making modifications.** If you plan to modify this project, develop it further or publish a derivative product, please contact the original author, ccch1mneyyy, through Issues or the community in advance and describe your intended use and plans.
- **Please credit the upstream repository and author in forks.** When publishing a modified version, please clearly credit  and the original author, ccch1mneyyy, in the repository README, in-app About screen and release page. Retain copyright, license and modification notices as required by the applicable license.
- **No unauthorized commercial reskins.** Do not use this project's brand graphics or protected assets, including Deepy and Whale girl, in reskinned products for sale, paid distribution or other commercial products without permission. Do not violate the applicable license by removing required copyright and license notices or distributing derivative code without the required source, or impersonate the original author or an official release.
- **The name and assets are separate.** The DSH Go name and logo, and the Deepy and Whale girl mascots, are not covered by AGPL-3.0. Ship a modified build under your own name and assets; see ASSETS.md.

**License clarification:** AGPL-3.0 permits modification, redistribution and commercial use subject to its terms. Advance contact and the requested credit locations above are collaboration requests from the author, not additional restrictions on the code license. Brand and asset use remains subject to their own terms; this notice does not change the licenses of `sdk/`, `examples/` or third-party content.

## License and acknowledgments

This project is licensed under AGPL-3.0. `sdk/` and `examples/` remain **MIT**. Third-party code and assets retain the terms stated in their own notices.

- DeepSeek Harness: the agent DSH Go runs and connects to.
- DSH-TUI: home of the mascots, Deepy and Whale girl.

Code derived from Phase is used with the author's permission. DeepSeek Harness, PiPilot, DS Bot, DSH Remote and other third-party components and assets retain their own licenses and attribution. See THIRD_PARTY_NOTICES.md for sources and terms.

The DSH Go name, logo and mascots (Deepy and Whale girl) are not covered by the AGPL; see ASSETS.md for their terms.

Remote connections draw on the ds-harness-remote project and its server. Thanks to its author, liguobao.

DSH Go is an unofficial client made by the community. It is not affiliated with or endorsed by DeepSeek. DeepSeek names and marks belong to their owners.


---

## ccch1mneyyy-dsh-Go.md

简体中文 · English

  DeepSeek Harness 的 Android 客户端。手机上直接跑，也能遥控你电脑上的 DSH。

  Trendshift 全语言日榜 #1 · 2026-10-30

Deepy 和鲸娘，陪你干活

干活时敲代码，做完来个空翻，等你确认会举手。打开「App 外显示」，它们还会跟你到桌面。

下载 DSH Go

从 GitHub Releases 或官网下载页获取最新版 APK，常见手机选 arm64 包。

  &emsp;

  感谢大家对 DSH Go 的支持和喜爱，我将尽快适配 iOS 和鸿蒙！大家 Star 点得越多，我适配得越快哦 hhh

  第一次用可以先看使用指南，遇到问题欢迎来论坛和 QQ 群。
  手机上装过签名不同的早期测试包时不能直接覆盖安装，需要先卸载旧版；卸载会清空对话、Linux 环境和设置。

本机运行，也能遥控电脑

内置 Linux 环境，免 Root、免 Termux。电脑上的 DSH，也能一键切过去接着用。

插话、打断，过程自动收好

回复中途也能插话，排队的消息随时「立即发送」。做完的过程折叠成一行。

原生界面，也有网页版

和官方网页版一键切换，停在同一段对话，下次打开还是你上次用的那个。

分享卡、对话回放和链接

回复一键做成分享卡。整段对话生成链接，对方在浏览器里回放，链接端到端加密。

横屏与平板

横屏手机和平板重新排版：侧栏常驻，内容居中，弹出键盘也不挤。

主题配色与桌面图标

六套主题色，也能跟随壁纸或自选颜色。四款桌面图标，三种功能图标风格。

中文，也说 English

全部界面支持英文，在设置里切换，默认跟随系统。

手机操控

看屏幕、帮你点，三档确认随你选。敏感操作默认交还给你；放宽应用规则或解除限制前，请先了解风险。

## 可以做什么

DSH Go 提供聊天界面、本机运行环境和远程连接，是基于 DeepSeek Harness 的第三方项目。运行在手机上的是 DSH 引擎；模型请求仍由你配置的模型提供方处理。

- **本机运行**：在 App 内安装 Ubuntu、Node.js 与 DSH 运行环境，无需 Root 或另装 Termux。
- **远程连接**：通过 SSH 或李国宝老师开发的 DSHarness Remote 使用电脑、服务器上的 DSH。
- **聊天与工具**：切换模型，发送图片、使用语音输入，处理工具审批和提问；支持聊天界面与网页模式。
- **插件界面**：使用适配 DSH Go 的原生工具卡、表单和面板；仓库提供 SDK、教程和示例。
- **手机操控**：在你开启权限后，让本机引擎读取屏幕、点按和输入，并可随时停止。
- **分享与外观**：分享、导出和回放对话，调整主题、图标和桌宠。

功能随主机和连接方式不同。DSHarness Remote 当前只支持图片附件，不能在 App 内打开网页版，插件管理限于开关，且不支持 DS Bot 和对话日志导出。详见本机引擎与远程主机。

## 安装

安装要求为 Android 8.0（API 26）及以上。Release 页面上的 **arm64** 安装包适用于常见的 64 位 Android 手机；x86_64 设备和模拟器用的 x64 包在发布说明末尾的「其他版本下载」里。仓库没有 32 位 ARM 构建。

1. 从 GitHub Releases 或官网下载页下载对应架构的 APK，并按系统提示允许该安装来源。
2. 首次启动时，选择在本机安装运行环境，或连接远程主机。
3. 为所选主机配置模型和所需凭据，再开始对话；部分远程渠道需要在主机侧配置。

仅连接远程主机时，不必在手机上安装本机运行环境。手机操控只对正常模式下的本机引擎开放，需要按界面说明开启无障碍等权限；不打扰模式另外要求 Android 14 及以上，以及 Shizuku 或自连 ADB。首次使用可按使用指南逐项配置。

本地引擎默认使用 PRoot 兼容启动。开发者选项中的直接启动默认关闭，开启后的兼容性和回退方式见常见问题。当前 Android 构建以 APK 侧载为目标，不是 Google Play 发布配置。

## 数据与权限

模型请求会发送给你配置的提供方。开启手机操控后，任务需要的屏幕文字可能发送给模型，支持看图的模型也可能收到截图；请先阅读 App 的权限说明。

“发送匿名使用统计”默认开启，可在首次引导或“设置 → 隐私与分享”关闭。采集范围和关闭后的处理见常见问题。分享内容前，请检查预览；收到链接或文件的人可以保存其中的内容。

## 风险提示与免责声明

DSH Go 是社区开发的非官方项目，与 DeepSeek 无关联，也不代表 DeepSeek。使用前请了解：

- **AI 并非万无一失**：回答、代码和操作可能出错，也可能被网页、消息或文件中的恶意指令误导。请核验重要结果；医疗、法律、投资等高风险决策不应仅依赖 AI 输出。
- **工具会产生真实影响**：本机或远程主机上的命令、文件修改及手机操控可能导致数据丢失、隐私泄露、账号、资金或设备损失。免确认、放宽应用规则或解除限制会减少保护；确认与拦截机制不能保证消除所有风险。建议保留默认保护，只授予必要权限，不在存有支付或银行信息的设备上解除限制。详见手机操控指南。
- **第三方服务与费用**：模型、远程主机和插件等按各自条款运行；相关数据处理、服务可用性和费用取决于你选择的服务与配置。本机运行不等于模型离线，也不代表数据不会离开设备。
- **使用前做好防护**：备份重要数据，只连接可信主机、安装可信插件，留意模型用量与费用；不要让 AI 无人值守地处理不可逆或高风险任务。
- **无担保与责任范围**：在适用法律允许的范围内，本软件按“现状”提供，不保证准确性、持续可用性或满足特定用途；相关无担保及责任限制见 LICENSE 第 15–17 条。本声明不排除或限制依法不得排除或限制的责任，也不减损你依法享有的权利。

## 常见问题

和 DeepSeek 官方是什么关系？

没有关系。DSH Go 是社区开发的非官方客户端，基于开源的 DeepSeek Harness 构建。手机上运行的是 DSH 本身；模型请求发给你配置的模型提供方，需要联网，按你在提供方的账户计费。

安全吗？

本机网页版只接受 App 自己的访问。分享链接端到端加密，密钥只在链接里，服务器看不到内容，但获得完整链接的人可以读取并保存内容。手机操控默认保留敏感操作保护；放宽应用规则或开启「解除限制」会减少这些保护。安全机制不能保证零风险，详见风险提示与免责声明和手机操控指南。

切到后台会被杀吗？

部分系统的省电策略会拦住后台。DSH Go 发现后会提醒你，并直达对应的放行设置，vivo、小米、华为、荣耀、OPPO 都有。

对手机有什么要求？

Android 8 及以上。手机直接下载 Release 页面上的安装包即可，模拟器用的 x86_64 版在发布说明末尾的「其他版本下载」里。在手机上运行 DSH 要先准备内置的运行环境，请预留约 1 GB 空间；只连电脑或服务器上的 DSH 可以不装。

开源吗？

开源，代码就在这个仓库，以 AGPL-3.0 发布，`sdk/` 和 `examples/` 为 MIT。DSH Go 的名称和标识，以及 Deepy、鲸娘两位吉祥物，不在开源授权范围内，见 ASSETS.md。再发布和 fork 时的署名要求见授权范围与再发布。

## 从源码构建

以下流程面向 **Linux x86_64**。当前工具链脚本默认安装 JDK 17、Flutter 3.47.7 和 Android SDK/NDK；App 要求 Dart `^3.13.5`。准备 Bash、Git、curl、tar、unzip、xz、Python 3、zstd（Python 未提供 `compression.zstd` 时用于解包 zstd 压缩的 deb）、file 和常见 GNU 命令；重新解析 Ubuntu 软件包锁时还需要 gpgv。

先取得完整源码和项目资源。`app/pubspec.yaml` 声明的字体、图片等都是构建输入，运行时包由下面的脚本生成。

```bash
git clone 
cd dsh-go

bash tooling/setup-toolchain.sh
source tooling/env.sh
flutter --version
java -version

bash runtime/build-runtime.sh arm64-v8a
DSH_BETA_TOKEN_FILE= bash tooling/build-apk.sh -f arm64 --keep-daemon
```

工具链脚本会下载 SDK/NDK 与模拟器镜像，并执行 Android SDK 许可接受步骤。默认安装到 `~/dev`；可通过 `DEV_ROOT` 指定独立目录。脚本会复用已有安装，构建前请核对版本。

产物为 `app/build/app/outputs/flutter-apk/app-arm64-release.apk`。运行时构建使用仓库固定的版本与校验信息，并需要联网下载依赖。示例中的 `DSH_BETA_TOKEN_FILE=` 不嵌入维护者的内测通道令牌；`--keep-daemon` 保留 Gradle daemon，适合同时开发其他 Android 项目的环境。

构建 x86_64 包时，先生成对应运行时：

```bash
bash runtime/build-runtime.sh x86_64
DSH_BETA_TOKEN_FILE= bash tooling/build-apk.sh -f x64 --keep-daemon
```

未配置 `app/android/key.properties` 时，本地 release 构建使用 debug 签名。它不能直接覆盖不同签名的官方安装包；请在测试设备上安装，保留已有数据，不要为解决签名冲突直接卸载正在使用的 App。发布签名与密钥文件不要提交到仓库。

只查看 APK 构建命令，可运行：

```bash
DSH_BETA_TOKEN_FILE= bash tooling/build-apk.sh --dry-run -f all
```

## 目录

| 路径 | 内容 |
| --- | --- |
| `app/` | Flutter 界面与 Android Kotlin 平台实现 |
| `packages/dsh_client/` | DSH Web API 的 Dart 客户端 |
| `packages/dsh_remote/` | DSH Remote 的 Dart 客户端 |
| `runtime/` | Linux 运行时打包、引擎补丁与 App 桥接 |
| `sdk/plugin-kit/` | 原生插件作者工具包；在仓库中使用，未发布到 npm |
| `examples/plugins/` | 插件示例 |
| `docs/guide/`、`docs/plugins/` | 用户指南与插件开发文档 |
| `docs/assets/` | 本页用到的展示图、桌宠动图和社群二维码 |
| `tooling/` | 工具链、APK 构建与诊断脚本 |
| `services/`、`site/`、`infra/` | 配套分享服务、网站和部署材料 |

## 参与贡献

问题反馈和改进建议可提交到 Issues。代码、文档和翻译贡献请先看 CONTRIBUTING.md。插件作者可以从插件教程和 SDK开始。

安全问题请按 SECURITY.md 报告，避免在公开 Issue 中提交漏洞细节或凭据。

## 社区

- **论坛**：forum.dshtui.com
- **QQ 群**：`1132118290`（点此加群）
- **微信群**：扫下方二维码，过期请加 QQ 群

  &emsp;&emsp;

  QQ 群号 1132118290，电脑上可直接点此加群。微信群二维码每周更新，过期请加 QQ 群。

## 友情链接

- **DSH-TUI**：同一作者的作品，面向 DeepSeek Harness 的交互式终端界面。手机上用 DSH Go，电脑上就用它——像素鲸鱼、实时状态、时间回溯，装上即开工（GitHub）。

## 授权范围与再发布

代码以 AGPL-3.0 开源，欢迎 fork 学习、自用和二次开发。请尊重原作者和项目来源：

- **改造前请提前联系作者**：如需基于本项目进行改造、二次开发或衍生产品发布，请先通过 Issues 或社区联系原作者 ccch1mneyyy，说明用途与计划。
- **fork 请标注主仓库与作者**：基于本仓库改造并发布时，请在仓库说明、应用「关于」页和发布页面清楚标注主仓库  与原作者 ccch1mneyyy，并按适用许可证保留版权、许可及修改声明。
- **禁止未授权商业化套皮**：不得未经授权将本项目的品牌标识、Deepy、鲸娘等受保护素材用于套皮售卖、收费分发或其他商业产品；不得违反适用许可证，删除应保留的版权与许可声明、闭源分发衍生代码，或冒充原作者、官方版本。
- **名称与素材另有限制**：DSH Go 的名称、标识，以及 Deepy、鲸娘形象不在 AGPL 授权范围内，以修改版身份发布时请换成自己的名称和素材，见 ASSETS.md。

**许可说明**：AGPL-3.0 允许符合其条款的修改、再发布和商业使用；上述提前联系及署名位置是作者的协作请求，不是对代码许可证追加的限制。品牌与素材须遵守各自的授权条件；本说明不改变 `sdk/`、`examples/` 及第三方内容的许可。

## 许可证与致谢

本项目采用 AGPL-3.0；`sdk/` 和 `examples/` 保持 **MIT**。第三方代码和素材以各自声明为准。

- DeepSeek Harness：DSH Go 运行和连接的就是它。
- DSH-TUI：吉祥物 Deepy 小鲸鱼和鲸娘来自这里。

Phase 相关代码经作者许可使用。DeepSeek Harness、PiPilot、DS Bot、DSH Remote 及其他第三方组件、素材保留各自的许可证和署名。具体来源和条款见 THIRD_PARTY_NOTICES.md。

DSH Go 的名称、标识、Deepy 小鲸鱼和鲸娘等形象不在 AGPL 授权范围内，使用条款见 ASSETS.md。

远程连接参考了 ds-harness-remote 的项目和服务器，感谢作者李国宝。

DSH Go 是社区开发的非官方客户端，与 DeepSeek 没有关联，也不代表 DeepSeek。DeepSeek 名称与标识归其所有者所有。
