# Wireless Battery

[![Support me on Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20me-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/krisgfx)
[![Donate with PayPal](https://img.shields.io/badge/PayPal-Donate-00457C?logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/krisgfx)
[![GitHub Sponsors](https://img.shields.io/badge/GitHub-Sponsor-EA4AAA?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/krisgfx9)
[![Join our Discord](https://img.shields.io/badge/Discord-Join%20us-5865F2?logo=discord&logoColor=white)](https://discord.gg/ZgDDUPP8ye)
[![Star on GitHub](https://img.shields.io/github/stars/krisgfx9/Wireless-Device-Battery-Monitor?style=flat&logo=github&label=Star)](https://github.com/krisgfx9/Wireless-Device-Battery-Monitor)
[![Share on Reddit](https://img.shields.io/badge/Reddit-Share-FF4500?logo=reddit&logoColor=white)](https://www.reddit.com/submit?url=https%3A%2F%2Fgithub.com%2Fkrisgfx9%2FWireless-Device-Battery-Monitor&title=Wireless%20Battery%3A%20battery%20levels%20of%20your%20wireless%20devices%20on%20the%20Windows%20taskbar)
[![Report a device](https://img.shields.io/badge/Report-a%20device-2EA44F?logo=github&logoColor=white)](https://github.com/krisgfx9/Wireless-Device-Battery-Monitor/issues/new)
[![Help translate](https://img.shields.io/badge/Help-translate-6F42C1?logo=googletranslate&logoColor=white)](https://github.com/krisgfx9/Wireless-Device-Battery-Monitor/pull/129)

Battery levels of your wireless mouse, headset, keyboard and controller, right on the Windows taskbar.

![Wireless Battery on the taskbar](docs/screenshot.png)

> **Just want it working?** Download **[WirelessBattery-Setup](https://github.com/krisgfx9/Wireless-Device-Battery-Monitor/releases/latest)** from the latest release, run it and click through. That's it.
>
> **Experienced users** can grab the portable zip, use the [command-line options](#command-line), or [build it from source](#build) with `make` or `build.bat`.
>
> **Like it?** Wireless Battery is free and open source. If it saves you a trip into vendor software, you can support it on [Ko-fi](https://ko-fi.com/krisgfx), [PayPal](https://www.paypal.com/paypalme/krisgfx) or [GitHub Sponsors](https://github.com/sponsors/krisgfx9). It helps me keep my apps free alongside my studies. Not able to donate? A ⭐ star, sharing it, or reporting an unsupported device with a `--dump` helps just as much.

- **Tiny**: a ~350 KB app using about 2 MB of RAM. It's plain C++/Win32, with no runtime and no background service, and installs in seconds without admin rights.
- **No vendor software needed**: it talks to the devices directly. G HUB, Synapse, iCUE, GG and NGenuity can stay closed (or keep running; they don't conflict).
- **Many brands**: Logitech, Razer, SteelSeries, Corsair, HyperX, Glorious, Jabra, JBL, PlayStation and Xbox controllers, Samsung Galaxy Buds, any Bluetooth device Windows knows a battery level for, and every headset the bundled [HeadsetControl](https://github.com/Sapd/HeadsetControl) supports.

## Display

**On the taskbar (default):** `🎧 30%  🖱 93%` next to the notification area, drawn with the Windows icon font.
- **Low battery:** a red number means 15% or less.
- **Charging:** a blue ⚡ appears next to the number.
- **Asleep:** dimmed text means the device is asleep and the last known value is shown.
- **Two devices of one kind:** with two mice (or two controllers...) both would get the same icon, so each one gets a tiny caption of up to 3 letters in the corner of its icon, taken from its name (`MX`, `PRO`), or a number when the names do not tell them apart. A device that is alone in its kind shows no caption.
- **Theme:** it follows light/dark mode and DPI scaling.
- **Transparent taskbar themes** (e.g. Windhawk's Taskbar Styler): turn on *Background behind taskbar text* in the menu to keep the text readable over the wallpaper.
- **Several monitors:** the widget shows on every monitor's taskbar, next to its clock, so it stays visible while a game runs fullscreen. *Show the widget on* in the menu picks *All monitors*, *Main monitor only*, or one display (e.g. only *Display 3*).
- **More display options:** *Icons above percentages* stacks each icon over its level to save width; *Brand colors* shows known brands in their color (Razer green, HyperX red, ...) with a small level bar; two devices of the same kind get a tiny caption so they can be told apart; left and right taskbars get a column of devices.
- **Languages:** English, العربية, Deutsch, Español, Français, עברית, 日本語, Polski, Português (Brasil), Русский, Türkçe, 简体中文 and 繁體中文. The app follows the Windows display language; *Language* in the menu picks another one. See [Translations](#translations) to add or improve a language.
- **Brand colors:** devices of 15 known brands get their maker's color, with a soft glow and a thin level bar under the
  percentage: Razer green, Logitech blue, SteelSeries orange, Corsair yellow, HyperX / ROG / ZOWIE red, PlayStation,
  Xbox, Samsung, Apple, Jabra, JBL, Cooler Master and Steam. Each color has a dark- and a light-taskbar shade. The brand
  comes from the driver that found the device, then the vendor ID, then the name; colors and rules are in
  `src/brands.cpp`. Turn it off with *Brand colors* in the menu.

**Tray icons:** one icon per device with the number drawn in it, plus a "Low battery" notification at 15%. The app switches to this automatically when the taskbar is vertical or can't be found.

Hover for details. Click for the menu: every device (click one to hide or show it), display mode, *Refresh now*, *Start with Windows*, and *Exit*. Levels refresh every 60 seconds, and right away when a device is plugged in or the PC wakes up.

## Supported devices

| Vendor | Devices | How |
|---|---|---|
| **ASTRO** | A50 X (`046D:0B0B`, tested), A50 Gen 5 (`046D:0B1C`), A50 Gen 4 (`9886:002C` tested, `002D`/`002A`), A50 Gen 3 (`9886:0014`/`0015`/`0018`/`001D`/`0026`), A20 Wireless (`9886:0037`–`0045`), via USB base station | Battery percentage, charging and docked status |
| **Logitech** | Mice and keyboards on Unifying, Bolt, Lightspeed (including the PRO X3 SUPERSTRIKE dongle `046D:C54F`) and Nano receivers, over USB or Bluetooth; G headsets (G533, G535, G633/G635/G733/G933/G935, G PRO/PRO X); G435 on the newer `046D:0ADF` dongle | HID++ 1.0 / 2.0 with feature discovery: unified battery, battery level, voltage, ADC; G435: CRC-16 framed vendor reports, `GET_BATTERY` in mV |
| **Razer** | Wireless mice, keyboards and dongles; BlackShark V2 HyperSpeed, V2 Pro (2020/2023), V3 / V3 Pro / V3 X headsets; Barracuda X (2022) on its 2.4 GHz receiver (`1532:0550`); Barracuda Pro (`1532:053A`) | Razer feature-report protocol; BlackShark vendor protocols (V3 / V3 Pro / V3 X queried every 5 min); Barracuda X: Airoha battery and cable queries through the receiver |
| **SteelSeries** | Arctis 1/7/7+/9/Pro/Pro Wireless, Arctis Nova 3P/5/7/7X/7P/Pro Wireless (including `1038:225D`), Arctis Nova Elite (base station `1038:2244`), GameBuds; Aerox 3/5/9 Wireless, Prime Wireless, Rival 3 Wireless (Gen 2), Rival 650, Rival Pro | Vendor HID reports |
| **Corsair** | Void / Void Pro / Void Elite / HS70 / HS80 wireless; Bragi devices (Virtuoso, Void V2, HS80 MAX, Slipstream mice and keyboards, including the newer Slipstream receiver `1B1C:2B00`, e.g. Scimitar Elite SE Wireless) | Vendor HID reports, Bragi `GET` (read-only) |
| **Corsair** | Void / Void Pro / Void Elite / HS70 / HS80 wireless; Bragi devices (Virtuoso, Void V2, HS80 MAX, Slipstream mice and keyboards, e.g. Dark Core RGB Pro SE) | Vendor HID reports, Bragi `GET` (read-only) |
| **Razer** | Wireless mice, keyboards and dongles; BlackShark V2 HyperSpeed, V2 Pro (2020/2023), V3 / V3 Pro / V3 X headsets; Barracuda X (2022) on its 2.4 GHz receiver (`1532:0550`) | Razer feature-report protocol; BlackShark vendor protocols (V3 / V3 Pro / V3 X queried every 5 min); Barracuda X: Airoha battery and cable queries through the receiver |
| **Razer** | Wireless mice, keyboards and dongles; BlackShark V2 HyperSpeed, V2 Pro (2020/2023), V3 / V3 Pro / V3 X headsets; Barracuda X (2022) on its 2.4 GHz receiver (`1532:0550` or `1532:0552`) | Razer feature-report protocol; BlackShark vendor protocols (V3 / V3 Pro / V3 X queried every 5 min); Barracuda X: Airoha battery and cable queries through the receiver |
| **SteelSeries** | Arctis 1/7/7+/9/Pro/Pro Wireless, Arctis Nova 3P/5/7/7X/7P/Pro Wireless, GameBuds; Aerox 3/5/9 Wireless, Prime Wireless, Rival 3 Wireless (Gen 2), Rival 650, Rival Pro | Vendor HID reports |
| **SteelSeries** | Arctis 1/7/7+/9/Pro/Pro Wireless, Arctis Nova 3P/5/7/7X/7P/Pro Wireless (including `1038:225D`), GameBuds; Aerox 3/5/9 Wireless, Prime Wireless, Rival 3 Wireless (Gen 2), Rival 650, Rival Pro | Vendor HID reports |
| **Corsair** | Void / Void Pro / Void Elite / HS70 / HS80 wireless; Bragi devices (Virtuoso, Void V2, HS80 MAX, Slipstream mice and keyboards, including the newer Slipstream receiver `1B1C:2B00`, e.g. Scimitar Elite SE Wireless, and Dark Core RGB Pro SE); Sabre V2 Pro Ultralight Wireless (`1B1C:2B2A`) | Vendor HID reports, Bragi `GET` (read-only), Compx 17-byte battery protocol (read-only) |
| **Cooler Master** | MM712, MM731 (2.4 GHz dongle or USB cable) | Vendor HID status report (read-only) |
| **HyperX** | Cloud III Wireless, Cloud III S Wireless, Cloud II Wireless (HP, Kingston, DTS), Cloud II Core Wireless, Cloud Alpha Wireless, Cloud Alpha 2 Wireless, Cloud Flight, Cloud Flight S, Cloud Stinger Core Wireless, Cloud Core Wireless DTS, Pulsefire Haste 2 Core Wireless (2.4 GHz dongle), Pulsefire Haste 2 Wireless (2.4 GHz dongle `03F0:0F98`, tested; `0D97` untested) | Vendor HID reports (Haste 2: [protocol notes](docs/hyperx_haste_2.md)) |
| **Glorious** | Model O / O- / D / D- Wireless, Model O 2 / D 2 PRO | Vendor feature report |
| **Hitscan** | Hyperlight X, Hyperlight N | Vendor feature report (same protocol as Glorious) |
| **Kysona / Pulsar / ATK (VXE) / Hitscan** | Kysona M600 / Mercury, Pulsar and ATK VXE wireless mice (e.g. VXE X3 Pro, VXE Dragonfly R1 / R1 Pro Max / R1 SE+, ATK F1 Extreme), Hitscan Hyperlight | Shared vendor protocol with checksummed replies |
| **Pulsar X2 V3** | X2 V3 on the 1K dongle (`3710:5402`) or USB cable (`3710:3402`); X2 V3 eS on the 8K dongle (`3710:5403`) or USB cable (`3710:3406`) | 64-byte vendor feature report, battery register `08 81 01` (read-only) |
| **ATK / VXE NK** | VXE R1 NK and other NearLink mice on the NK mouse NANO dongle (`373B:1216`) | ATK BITMOUSE output report 08 on `FF05:0001` (battery and charging) |
| **ATK headsets** | ATK N9 Pro, N9 Ultra (first generation) | Virtual COM port protocol (the ATK desktop app must be closed) |
| **G-Wolves** | Fenrir, Fenrir Pro / Max / Asym, HTX, HTS, HSK, HTR, HT-S2, Lycan, WARG, VUK and their 8K dongles | Glorious or Kysona protocol, depending on the model |
| **Keychron mice** | M4 and other Keychron mice on the 2.4 GHz receiver; 4K mice (M4 4K, M3 4K, M3 mini 4K, M6 4K ...) on the Keychron 4K Link receiver (`3434:D038`); 8K mice (M5 8K, G6 HE 8K ...) on the TurboLink 8K receiver; older mice (M1, M2, M3, M3 mini, M6, M7 ...) on the 1K receiver (`3434:D030` / `D031`); Nape Pro trackball on the Link-KM receiver or cable | Vendor report from Keychron Launcher (1K receiver: feature report 51 06, as used by the Keychron desktop app; Nape Pro: raw HID A7 31) |
| **CHERRY** | MX 3.0S Wireless keyboard on its 2.4 GHz dongle (`046A:00EA`, tested) or USB cable (`046A:00E3`, tested) | Vendor HID query `1A` on `FF1C:0092` (read-only), with USB-powered state. Bluetooth is covered by the Bluetooth support |
| **Arbiter Studio** | Akitsu (`373E:000A` 8K receiver, `373E:0009` cable), Akitsu 3950 (`373E:0039` 8K receiver, `373E:0038` cable), Akitsu Medium (`373E:0067` 8K receiver and `373E:0066` cable, both tested) | Read-only vendor feature report `0x83` on `FFFF:0000` from Arbiter Web HUB (battery and charging) |
| **LAMZU** | Maya X, Maya, Maya M, Tachi, Inca, Paro, Thorn, Atlantis Mini / OG Champion, Orcus (cable, 1K and 4K/8K dongles) | Vendor feature report from LAMZU Aurora |
| **Endgame Gear** | OP1w 4k (v1 / v2), XM2w 4k (v1 / v2) on the 4K dongle; XM2we on its original receiver (`3367:1961`) | Vendor feature report `A1`, battery command `B4` (read-only) |
| **ATK keyboards** | ATK V75X on the 2.4 GHz receiver (`320F:5088`) or USB cable (`320F:5055`) | Evision output report `04`, battery command `1A` (from ATK HUB); asked at most every 10 minutes over the receiver |
| **Audeze** | Maxwell on the USB dongle (`3329:4B19`) or USB-C cable (`3329:4B1A`); Xbox and Maxwell 2 ids untested | Vendor report `06` / input report `07`, battery attribute `0CD6` (single read-only query) |
| **NZXT** | Lift Elite Wireless on its dongle (`1E71:2101`) or USB cable (`1E71:2129`) | Vendor read `4E 02 81 .. B0` (from NZXT CAM captures) |
| **Poly / Plantronics** | Voyager 8200 UC and other headsets behind the BT600 adapter (`047F:02EE` / `02F7`) | Report `07` get/set protocol, battery item `0A 1A` (read only) |
| **WLMouse** | YING Magnesium (YING 8K receiver `36A7:A874`); Beast X 8K, Beast X Mini / Mini Pro, Beast X Pro, Beast MAX, Sword X 8K (receiver or cable; not the Beast X 4K); Beast X V2 (8K receiver `36A7:A856`) | Vendor feature report, status command `0x83` (YING: same protocol as Glorious) |
| **VAXEE** | Wireless mouse on the VAXEE 4K receiver (`3057:1002`); ZYGEN NP-01S V2 Wireless over USB cable (`3057:1011`) | Read-only vendor feature report `0E` on `FF05:0001`; battery in 5% steps, charging state ([protocol notes](docs/vaxee.md)) |
| **Finalmouse** | UltralightX on its 2.4 GHz dongle (`361D:0100`, tested); Starlight X on its dongle (`361D:0300` / `0301`, tested). Not on the mouse's own cable | xpanel vendor reports on `FF00`: read-only GETs, then *wake/all* (`0xE0`); battery voltage on xpanel's curve, or the Starlight X's own percentage, plus charging state |
| **VAXEE** | Wireless mouse on the VAXEE 4K receiver (`3057:1002`) or 8K receiver (`3057:2002`, e.g. NP-01 Ergo Wireless 8K); ZYGEN NP-01S V2 Wireless over USB cable (`3057:1011`) | Read-only vendor feature report `0E` on `FF05:0001`; battery in 5% steps, charging state ([protocol notes](docs/vaxee.md)) |
| **WLMouse** | YING Magnesium (YING 8K receiver `36A7:A874`); Beast X 8K, Beast X Mini / Mini Pro, Beast X Pro, Beast MAX, Sword X 8K (receiver or cable; not the Beast X 4K) | Vendor feature report, status command `0x83` (YING: same protocol as Glorious) |
| **HECATE** | G5M PRO and other HECATE mice on the same receiver, and USB cable `35BB:D3FA / D3FC / D3FD` | Kysona protocol |
| **Redragon** | Compx-based wireless mice: M916 Pro 1K (tested), M913 Impact Elite (tri-mode), G49 (receiver or cable) | Kysona protocol (the Areson `25A7` receivers are listed under Areson) |
| **Taidu (钛度)** | TSG808 on its Compx 2.4 GHz receiver `3554:F5D5` (tested) | Kysona protocol |
| **Areson (Redragon)** | M915RGB-WL (tested), original M913 Impact Elite and other mice on the `25A7:FA07` / `FA08` receiver | 17-byte `GetPower` feature report; level in 10% steps and a charging flag |
| **Ninjutso** | Sora V2 on the 1K receiver (`1915:AE1C`, tested) or USB cable (`1915:AE11`, tested) | NinjaForce feature report 0x05, status command 0x15; battery, online and charging state |
| **Ninjutso** | Sora V2 on the 1K receiver (`1915:AE1C`, tested); Ten Air (receiver `093A:EB01` and USB cable `093A:E020`, tested) / Ten (`093A:EB01` / `E020`, untested) | NinjaForce feature report `0x05` (`0x15` for Sora V2) and `0x06` (`0x13`/`0x12`/`0x11` for Ten / Ten Air) |
| **Sprime** | PM1 on the 2.4 GHz receiver (`1915:AC1C`, tested; `1915:AD8C`) or USB cable | Same feature report 0x05, status command 0x15, from Sprime's web driver (sprime.pro) |
| **AULA** | F75 / F87 Pro / F99 wireless keyboards on the 2.4 GHz receiver | Report 0x13 frame, command 0x4A, sum checksum (Bluetooth and wired modes untested) |
| **DAREU** | EM901X on the `260D:1074` 2.4 GHz receiver (battery reading tested; charging transitions untested) | Battery-only feature report `08`, command `04`; reply `09` on a separate vendor collection. Requires one unambiguous input/feature pair; USB cable mode and other receiver IDs are not enabled |
| **SONiX keyboards (AJAZZ / AULA / EPOMAKER)** | AJAZZ AK820 MAX (tested), EPOMAKER EA75 (tested), AULA F108 Pro on the `05AC:024F` 2.4G dongle; AJAZZ AK980 V2 on the `0C45:FEFE` dongle | Vendor report `20 01` on usage page FF60, sum checksum (2.4G mode only; no charging indication) |
| **DAREU** | EM901X on the `260D:1074` 2.4 GHz receiver or `260D:1090` USB cable (battery reading tested on both; receiver dock/undock charging-flag transitions tested) | Battery-only feature report `08`, command `04`; reply `09` on a separate vendor collection. Requires one unambiguous input/feature pair per product ID. Prefers a valid USB reading when both are connected; the receiver can return cached telemetry even with the mouse switched off |
| **SONiX keyboards (AJAZZ / AULA)** | AJAZZ AK820 MAX (tested), AULA F108 Pro on the `05AC:024F` 2.4G dongle; AJAZZ AK980 V2 on the `0C45:FEFE` dongle | Vendor report `20 01` on usage page FF60, sum checksum (2.4G mode only) |
| **ZOWIE** | EC1/EC2/EC3-CW, DW series (U2-DW, S2-DW ...) and U2 on its 2.4 GHz receiver | Community-documented read-only vendor commands |
| **Royal Kludge (RK)** | MG6 Pro on the 2.4 GHz dongle (`2E3C:00A6` / `00E6`) or USB cable (`2E3C:00A5` / `00E5`) | QiWang 64-byte frame from RK's web driver, `GET_BATTER_VOL` read (percent, voltage, charging) |
| **ASUS ROG** | Strix Scope II 96 (RX), Azoth, Falchion keyboards; Keris, Harpe, Gladius, Chakram, Spatha, Pugio, Strix Impact mice; Pelta headset (2.4 GHz dongle); the Omni Receiver | ROG HID battery query |
| **Machenike** | L7 Arctic / L7 Mix on the `248A:FF4C` 2.4 GHz receiver or `248A:FF4E` USB cable (both tested) | Read-only feature report `51`, status command `06`; battery and charging. [Protocol notes](docs/machenike.md) |
| **MCHOSE** | L7 / L7 Pro / L7 Ultra (L7 Ultra tested), M7 / M7 Ultra, A7 / A7 Ultra, K7 mice on the 2.4 GHz receiver or USB cable; G3 V2 (2.4 GHz receiver `3837:4245` and USB cable `3837:418C`) | Vendor feature report, inverted payload (protocol from alexfrih/mchose-linux); G3 V2: read-only vendor query on `FF01:0010` |
| **MSI** | VERSA 300 ELITE WIRELESS on its 2.4 GHz dongle (`0DB0:9E22`); CLUTCH GM31 Lightweight Wireless (2.4 GHz receiver `0DB0:0D3C`, tested; USB cable `0DB0:0D3B`) and CLUTCH GM41 Lightweight Wireless (receiver `0DB0:0D4C` / cable `0DB0:0D4B`, from an owner's captures) | Read-only vendor query `0F 20` on `FF0D:00B0` and `FF00:0001`; battery and charging flag in one byte (protocol from MSI Center's Gaming Gear module); GM41: passive `A0 xx 07 …` reports on `FF10:0006` |
| **MCHOSE** | L7 / L7 Pro / L7 Ultra (L7 Ultra tested), M7 / M7 Ultra, A7 / A7 Ultra, K7 mice on the 2.4 GHz receiver or USB cable; A5 V2 Ultra (2.4 GHz receiver `3837:100C`, tested), K7 Ultra (2.4 GHz receiver `3837:1001`, tested; A7 V2 Ultra+ `3837:100B` expected to work, issue 227); G3 V2 (2.4 GHz receiver `3837:4245` and USB cable `3837:418C`) | Vendor feature report, inverted payload (protocol from alexfrih/mchose-linux); Realtek `3837` dongles answer the same query with the vid field set to `41E4` (A5 V2 Ultra) or `3837` (K7 Ultra); G3 V2: read-only vendor query on `FF01:0010` |
| **MCHOSE** | L7 / L7 Pro / L7 Ultra (L7 Ultra tested), M7 / M7 Ultra, A7 / A7 Ultra, K7 mice on the 2.4 GHz receiver or USB cable; G3 V2 (2.4 GHz receiver `3837:4245` and USB cable `3837:418C`); K7 V2 Ultra+ on the 2.4 GHz receiver `3837:1014` (tested; the other new-family receiver ids `1018`, `1016`, `102C`, `102D` are untested) | Vendor feature report, inverted payload (protocol from alexfrih/mchose-linux); G3 V2: read-only vendor query on `FF01:0010`; K7 V2 Ultra+: 64-byte report `0x4D`, device-info command `0x0900` on `FF01:0001` (protocol from M HUB's web driver) |
| **MCHOSE headsets** | V9 Pro 2 on the 2.4 GHz dongle (`3837:6011`, tested) | M HUB's read-only "MC" battery frame (report `0x55`, sub-command `0x0B`) on `FF07:0222`; battery and charging flag in one byte (protocol from M HUB's web driver) |
| **AULA / MCHOSE keyboards** | AULA F75 / F87 Pro / F99; MCHOSE K99 V2, G75 Pro, X75 and the other M HUB keyboards on the 2.4 GHz receiver (`3554:FA09`, `41E4:2001`) | Report 0x13 frame, command 0x4A (MCHOSE models identified by command 0x05, as in M HUB); Bluetooth and wired modes not covered |
| **AULA HERO 68 Air** | HERO 68 Air on the 8K Wireless Receiver (`372E:106C`) | Acknowledged 20-byte frames on usage page FF60 (four data frames and a trailer per message), read-only battery command 0x87, charging flag 0x10 after the level; Bluetooth and wired modes not covered |
| **ASUS ROG** | Strix Scope II 96 (RX), Azoth, Falchion keyboards; Keris, Harpe, Gladius, Chakram, Spatha, Pugio, Strix Impact mice; the Omni Receiver | ROG HID battery query |
| **ZOWIE** | EC1/EC2/EC3-CW and DW series (U2-DW, S2-DW ...) | Community-documented read-only vendor commands |
| **Rapoo VT** | VT3 Max Gen 2 (tested); other Nordic 54L VT mice exposing the same status interface; legacy VT3 Pro (experimental) | Passive HID status report `07` on `FF00:0002`; legacy `BB` restricted to VT3 Pro `1215/4415`. Receiver and USB cable, with charging state |
| **Rapoo VT** | VT3 Max Gen 2 (tested); other Nordic 54L VT mice exposing the same status interface; legacy VT3 Pro (experimental); VT1 Pro Max (from the owner's USB captures) | Passive HID status report `07` on `FF00:0002`; legacy `BB` restricted to VT3 Pro `1215/4415` and VT1 Pro Max `1233/4433`. Receiver and USB cable, with charging state |
| **Motospeed / Delux / Ajazz** | Motospeed X6, Delux M900 Pro (Xenta models 30/50; legacy 3D), Delux M800 Pro, Ajazz AJ179 family; AJ159 and other AJ-series mice on the 3151 receiver; AJ139 V2 MC (`A8A5:2255` receiver, `A8A4:2255` cable) | Vendor reports (M900 Pro: passive Xenta events 40/41; AJ-series: 0xF7 status poll, then feature report 0x05) |
| **Rapoo VT** | VT3 Max Gen 2 (tested); VT9 Gen 2 (tested); other Nordic 54L VT mice exposing the same status interface; legacy VT3 Pro (experimental); VT1 Pro Max (from the owner's USB captures) | Passive HID status report `07` on `FF00:0002` (16 or 19 bytes); legacy `BB` restricted to VT3 Pro `1215/4415` and VT1 Pro Max `1233/4433`. Receiver and USB cable, with charging state |
| **Motospeed / Delux / Ajazz** | Motospeed X6, Delux M900 Pro, Delux M800 Pro, Ajazz AJ179 family; AJ159 and other AJ-series mice on the 3151 receiver; AJ139 V2 MC (`A8A5:2255` receiver, `A8A4:2255` cable) | Vendor reports (Delux: passive status broadcasts or feature query; AJ-series: 0xF7 status poll, then feature report 0x05) |
| **Incott** | G23 V2 / G24 (`093A:522C` receiver, `093A:622C` cable) | Read-only status feature report 09 |
| **Attack Shark and other Chinese brands** | Rongyuan receivers (81 models: Attack Shark R3, K86, X82 PRO HE, Ajazz keyboards, some MSI and others; the K86 over Bluetooth is shown as a keyboard); Xenta receivers (Attack Shark X6 / R1, X11, X3 Max, V3 Pro, V6); Semico 1A2C keyboards (Attack Shark X98 on `1A2C:8FFF` dongle, tested, and `1A2C:A034` cable; AJAZZ AK820 Max Plus on `1A2C:8FFF` / `1A2C:A036`) | Rongyuan status report; Xenta passive broadcasts; Semico read-only `0x0E` status query (`AA 55 CC 33` on `FF02:0002`; charging flag omitted because X98 reports `state=1` both on battery and while charging) |
| **Wraith** | W1 / W1 Freestyle (`093A:522C` receiver, `093A:622C` cable; same ids as Incott, told apart by the model code) | Read-only per-button reads `86` (feature report 09) over all buttons, then the pushed status input report 09 |
| **Fantech** | Helios Go XD5 (wired `25A7:FA7B`, 2.4 GHz dongle `25A7:FA7C`) | Vendor feature report `08`, command `04`, sum-to-`0x55` checksum |
| **Sony** | DualShock 4, DualSense, DualSense Edge (USB, Bluetooth, wireless adapter); INZONE H9 II and H5 headsets; INZONE Buds (USB-C dongle) | Input report; INZONE vendor protocol |
| **Fractal Design** | Scape headset on its 2.4 GHz dongle or USB-C cable | Vendor `GET_DEVICE_STATE` query from Fractal's Adjust Pro web app (usage page FF00) |
| **Jabra** | Headsets on a Jabra Link 380a / 380c / 390 dongle (USB-A and USB-C, UC and MS versions: Evolve2 / Evolve3 and others); name read from the headset | GNP status query (class 12 / op 02) on usage page FF00 |
| **Flydigi** | Vader 5 Pro / 黑武士 5 Pro (`37D7:2401`), 2.4 GHz receiver or USB | Vendor HID info query on `FFA0:0001`; 0–5 battery level mapped to 0–100% in 20% steps, with charging state; no Space Station service required |
| **GameSir** | Nova Lite, Nova 2, Nova 2 Lite on the 2.4 GHz receiver; Nova 2 Lite on USB; G7 Pro (tested: Zenless Zone Zero edition, receiver `3537:105E`) and other GameSir pads in Xbox (GIP) mode; Cyclone 2 (XInput mode, receiver or cable) | Vendor device-info query (usage page FF7A); Windows.Gaming.Input battery report (real %) in Xbox mode; Cyclone 2: vendor battery request (usage page FFF0) |
| **8BitDo** | Ultimate 2 Wireless in D-input mode (`2DC8:6012`: hold B while turning it on), on the 2.4 GHz dongle, USB cable or Bluetooth; firmware 1.03 or later. In X-input mode (`2DC8:310B`) the dongle reports no level | Battery byte of the gamepad input report `01` (read-only), with charging state |
| **BEITONG** | KP20 / BTP-KP20 on its 2.4 GHz receiver (`20BC:5128`, XInput mode, tested); BEITONG iControl not required | Vendor "get base info" query on usage page `00FF` (report `02`, nibble-scrambled payload), with charging state |
| **8BitDo** | Ultimate 2 Wireless (X-input `2DC8:310B` tested on 2.4 GHz dongle, D-input `2DC8:6012` firmware 1.03+), Ultimate 2C Wireless, Ultimate 3-mode, Ultimate 2.4G, Ultimate Bluetooth, Pro 3, Pro 2, SN30 Pro, SF30 Pro | Vendor HID status query (`FF7A`/`FFA0`) and SDL gamepad input report `01`/`04`, with charging state |
| **Samsung** | Galaxy Buds, Buds+, Buds Live, Buds Pro, Buds2, Buds2 Pro, Buds FE, Buds Core, Buds3 / Buds3 Pro / Buds3 FE (Bluetooth) | Status frame the earbuds push on Samsung's RFCOMM (SPP) service, read-only. The tray shows the lower earbud; the tooltip lists left, right and case. The Galaxy Buds app must be closed |
| **Sony** | DualShock 4, DualSense, DualSense Edge (USB, Bluetooth, wireless adapter); INZONE H9 II and H5 headsets | Input report; INZONE vendor protocol |
| **MOONDROP** | GM01 Pro headset on its 2.4 GHz dongle (`35D8:0133`); on its USB cable it shows as charging with the last level | WalkPlay vendor read command on report `4B` (read-only) |
| **JBL** | Quantum 650 Wireless (tested, 2.4 GHz dongle); Quantum 520, 650X, 850, 950, 950X Wireless (dongle or USB cable, same protocol, untested) | JBL "HIDV3" device-info query for the battery feature (usage page FF12), with charging state |
| **JBL** | Quantum 350 Wireless (tested on Windows with the `0ECB:206B` 2.4 GHz receiver) | HIDV1 feature reports for wireless connection and battery percentage |
| **GameSir** | Nova Lite, Nova 2, Nova 2 Lite on the 2.4 GHz receiver; Nova 2 Lite on USB | Vendor device-info query (usage page FF7A) |
| **Xbox** | Controllers on the Xbox Wireless adapter, USB or Bluetooth; headsets plugged into a controller | Windows.Gaming.Input battery report (real %), XInput fallback |
| **Switch Pro-compatible** | Controllers presenting as `057E:2009` (tested: GameSir Tarantula Pro via the 2.4 GHz receiver in Switch mode) | Five battery levels from HID report `0x30` after Steam Input or another host enables full reports |
| **Apple AirPods / Beats** | AirPods Max (tested, `200A` Lightning and `201F` USB-C), AirPods Pro 3 (tested, `2027`), AirPods Pro 1 / 2, AirPods 1–5 and Beats headphones/earbuds | BLE "proximity pairing" (`0x07`) broadcasts (single battery for AirPods Max and Beats headphones; left, right and case for earbuds, in 10% steps with charging state), matched to the paired model |
| **Phones (Phone Link)** | Any Android phone linked with Microsoft Phone Link, over Wi-Fi or Bluetooth (tested: Nothing Phone (4a) Pro) | Battery from Phone Link's Windows 11 Start menu card (`StartMenuCompanion.json`); no Bluetooth needed |
| **Darmoshark** | M3 on the 2.4 GHz receiver (`248A:FF30`) on Windows | HID feature report for mouse identity and battery |
| **Alienware** | AW920H headset on its 2.4 GHz dongle (`413C:A515`, tested); over Bluetooth it is covered by the Bluetooth row | Vendor query `06 C0 0A` on `FF13:0001`, reply report `07` with an XOR checksum; level, charging and critical-level fields as decoded by Alienware Command Center's AW920H plugin |
| **Niceboy** | MW400 on its 2.4 GHz receiver (`248A:FA02`, tested) | Read-only report `05` query `24 FA 48`; battery voltage mapped to 10% steps with the vendor app's table, charging flag |
| **Bluetooth** | Anything that shows a battery in *Settings → Bluetooth & devices* (earbuds, headphones, BLE mice and keyboards) | Windows device property |
| **Generic HID** | Devices reporting the standard HID *Battery Strength* usage | HID usage page 0x06 / 0x85 |
| **HeadsetControl** | [Every headset it supports](https://github.com/Sapd/HeadsetControl#supported-headsets) (Audeze, Jabra, Sony INZONE, newer Logitech and more) | Bundled; runs `headsetcontrol -o json` |
| **MAONO PD200W** | 2.4 GHz receiver (352F:040E) | Battery percentage; hardware-tested |


**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`), Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`), Finalmouse UltralightX (dongle `361D:0100`) and Finalmouse Starlight X (on its dongle).
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`), Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`), HyperX Cloud Stinger Core Wireless (PlayStation receiver `0951:1713`; charging untested) and HyperX Cloud Core Wireless DTS (receiver `0951:173F`; full-charge level untested).
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), MSI VERSA 300 ELITE WIRELESS (dongle `0DB0:9E22`; charging and sleep handling untested), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`) and Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`).
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`), Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`) and HyperX Cloud Stinger Core Wireless (PlayStation receiver `0951:1713`; charging untested).
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), MSI VERSA 300 ELITE WIRELESS (dongle `0DB0:9E22`; charging and sleep handling untested), MSI Clutch GM31 Lightweight Wireless (receiver `0DB0:0D3C`; the GM41 uses the same driver from an owner's captures), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`) and Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`).
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`), HyperX Pulsefire Haste 2 Core Wireless (dongle `03F0:0AB5`; the Haste 2 Wireless dongles are untested) and Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`).
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), AirPods Max (Bluetooth, model `200A`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`) and Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`).
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`), AULA HERO 68 Air (8K Wireless Receiver `372E:106C`) and Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`).
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`), Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`) and Ninjutso Ten Air (receiver `093A:EB01` and USB cable `093A:E020`).
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`) and Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`).
Also hardware-tested: Machenike L7 Arctic / L7 Mix (`248A:FF4C` receiver and `248A:FF4E` cable), including charging and cable/receiver duplicate suppression. Bluetooth and low-battery/full-charge boundaries were not hardware-tested.
Also hardware-tested: MCHOSE V9 Pro 2 (`3837:6011` dongle); battery level read, charging and sleep untested.
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), MCHOSE K7 Ultra (receiver `3837:1001`), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`) and Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`).
**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), MCHOSE K7 V2 Ultra+ (receiver `3837:1014`; charging state untested), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`) and Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`).
Also hardware-tested: EPOMAKER EA75 on its `05AC:024F` 2.4 GHz receiver, using the existing SONiX driver from [PR #60](https://github.com/krisgfx9/Wireless-Device-Battery-Monitor/pull/60). Battery percentage, receiver reconnection and power-on recovery were verified. Charging indication and wired battery reporting are not supported by this driver; Bluetooth battery reporting was not tested. The reported percentage can jump to 100% when USB power is attached, which is not a reliable charging indicator.

**Tested on real hardware:** Glorious Model O Wireless, HyperX Cloud III Wireless, Cooler Master MM712 (dongle), Rapoo VT3 Max Gen 2 (receiver `24AE:1417` and USB cable `24AE:4617`; other Rapoo models are untested, see [Rapoo protocol notes](docs/rapoo.md)) Redragon M916 Pro 1K (receiver `3554:F55D`), Redragon M916 Pro 1K (receiver `3554:F55D`), Taidu TSG808 (receiver `3554:F5D5`), Redragon M915RGB-WL (receiver `25A7:FA07`; other Areson models are untested, see [Areson protocol notes](docs/areson.md)), SteelSeries Rival 650 Wireless (receiver `1038:1726` and USB cable `1038:172B`), HECATE G5M PRO (receiver `35BB:D3FB`), WLMouse YING Magnesium (8K receiver `36A7:A874`), ATK N9 Ultra (receiver `373B:1204`), Corsair Scimitar Elite SE Wireless (Slipstream receiver `1B1C:2B00`), DAREU EM901X (receiver `260D:1074`; charging and sleep/wake untested), Jabra Evolve3 75 on a Link 390 (`0B0E:2E51`), MCHOSE G3 V2 (receiver `3837:4245` and USB cable `3837:418C`), MCHOSE K7 V2 Ultra+ (receiver `3837:1014`; charging state untested), AJAZZ AK820 MAX (dongle `05AC:024F`), AirPods Pro 3 (Bluetooth, model `2027`), Sprime PM1 (receiver `1915:AC1C`), MOONDROP GM01 Pro (dongle `35D8:0133`), SteelSeries Arctis Nova Pro Wireless (base station `1038:225D`; battery reading tested, charging and power transitions untested), Delux M800 Pro (receiver `248A:5B2F`), Razer Barracuda X (2022) (receiver `1532:0550`; battery level read, charging transitions untested), Razer BlackShark V3 X (HyperSpeed dongle `1532:057D`), Fantech Helios Go XD5 (dongle `25A7:FA7C`) and Corsair Dark Core RGB Pro SE (Slipstream receiver `1B1C:1BDC`), Corsair Sabre V2 Pro Ultralight (2.4 GHz receiver `1B1C:2B2A`; battery reading verified).
**Implemented from protocol documentation and other projects, not yet tested:** everything else. If you own one of these devices, please report whether it works by [opening an issue](https://github.com/krisgfx9/Wireless-Device-Battery-Monitor/issues).

## Install

[![Latest version](https://img.shields.io/github/v/release/krisgfx9/Wireless-Device-Battery-Monitor?label=latest%20version&style=for-the-badge)](https://github.com/krisgfx9/Wireless-Device-Battery-Monitor/releases/latest)

1. Download **`WirelessBattery-Setup-<version>.exe`** from the [latest release](https://github.com/krisgfx9/Wireless-Device-Battery-Monitor/releases/latest).
2. Run it and click through. It needs **no administrator rights** and **nothing else installed**: no
   runtimes, no drivers, no vendor apps. HeadsetControl comes bundled.

The installer adds a Start menu entry and an uninstaller (*Settings → Apps*), and can start the app
when you sign in. Prefer no installer? Download `WirelessBattery-<version>-portable.zip`, unzip it
anywhere and run `WirelessBattery.exe`.

**Notes:**
- **SmartScreen warning:** the exe is not code-signed, so Windows may say "Windows protected your PC". Click *More info → Run anyway*, or build it yourself.
- **Tray-icon mode on Windows 11:** new tray icons go to the `^` overflow. Drag them onto the taskbar or enable them in *Settings → Personalization → Taskbar → Other system tray icons*.
- **Keeping the app away from a device:** if a device misbehaves while the app is running, list it in the registry string `IgnoreDevices` under `HKCU\Software\WirelessBattery` as `VID:PID` pairs (hex, separated by commas, e.g. `28BD:0947, 1234:ABCD`; `--dump` shows the ids). The app then never opens it. Drawing tablets are skipped automatically.

## Command line

```
WirelessBattery.exe --list     # print every device and its battery level, then exit
WirelessBattery.exe --dump     # every HID collection, HID devices that could not be opened, all USB devices (also ones
                               # without a HID interface) and Bluetooth devices; also saved to %TEMP%\WirelessBattery-dump.txt
WirelessBattery.exe --report   # open the "Request support for a device" window
WirelessBattery.exe --demo     # sample devices of every brand instead of real ones (screenshots, checking colors)
WirelessBattery.exe --quit     # close the running instance
```

**Device not shown?** Right-click the widget or tray icon and choose **Request support for a device...**. Pick the device, check
what will be sent (it is shown word for word: the device name, its type, its USB/HID ids and interface layout, and your optional
name and notes) and click **Send**. It goes on the public list at [krisgfx.com/tools](https://krisgfx.com/tools/#requested) and
opens or updates a GitHub issue. **Copy full report** puts the complete `--dump` on the clipboard for the issue. This window is
the only place the app connects to the internet, and only when you click Send.

## Build

You need [MinGW-w64](https://www.mingw-w64.org/), e.g. from [MSYS2](https://www.msys2.org/) (`pacman -S mingw-w64-x86_64-gcc make`).

```
make            # MSYS2 / any shell with make
build.bat       # plain cmd with g++ and windres on PATH
```

To build the installer and portable zip, install [Inno Setup](https://jrsoftware.org/isinfo.php) and run
`powershell -File installer\build-installer.ps1 -Version 1.0.0`. It downloads the pinned
HeadsetControl release and verifies its checksum. GitHub Actions does all of this automatically:
pushing a tag like `v1.0.0` publishes a release with the installer, the portable zip and the
HeadsetControl source (as its GPL license requires).

`WirelessBattery.exe` on its own also works. Without `headsetcontrol.exe` next to it (or on `PATH`) you
just lose the extra headsets.

## Linux (experimental)

A Linux build sits alongside the Windows app. It uses the same vendor drivers with a hidraw-based
HID backend and a GTK4 StatusNotifierItem tray icon; the Windows code path is unchanged.
All Linux-only files are in `linux/` and `src/linux/`, and `build-linux.sh` builds it (Windows keeps using `build.bat`).

| | Fedora | Ubuntu / Debian |
|---|---|---|
| Compiler & make | `sudo dnf install gcc-c++ make` | `sudo apt install g++ make` |
| GTK4 + Cairo | `sudo dnf install gtk4-devel cairo-devel` | `sudo apt install libgtk-4-dev libcairo2-dev` |

No extra HID library is needed (hidraw is used directly).

```sh
./build-linux.sh
./build-linux.sh test         # unit test for the HID report-descriptor parser
./wireless-battery --list     # print detected levels and exit
./wireless-battery --dump     # list HID collections
./wireless-battery --quit     # close the running tray instance
```

HID access needs a udev rule, otherwise the app starts but finds no devices:

```sh
sudo cp linux/99-wireless-battery.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
# log out and back in
```

The tray icon works natively on KDE Plasma; GNOME needs an AppIndicator host such as
`gnome-shell-extension-appindicator`. The optional launcher is `linux/wireless-battery.desktop`
(install it plus `linux/wireless-battery.svg` and the binary into `~/.local/`).

Phase 1 covers Logitech, Razer, SteelSeries, Corsair, HyperX, PlayStation, Cooler Master, Glorious,
Finalmouse and the shared Kysona/Pulsar/ATK/G-Wolves protocols. Bluetooth/UPower fallbacks, HeadsetControl and
the remaining vendors are planned follow-up phases.

## Limitations

- **Primary monitor only:** the taskbar widget sits on the primary monitor's taskbar.
- **Crowded taskbars:** with a very full centered Windows 11 taskbar, the app buttons can reach the widget. On Windows 10 the task-button area is narrowed automatically.
- **Phones:** read from a file Phone Link writes for the Start menu companion card, which is not a documented API and may change with Phone Link updates. The phone shows while Phone Link reports it as connected; a card older than 3 hours is shown dimmed. Charging state is not available there.
- **Sleeping devices:** a device that is asleep may not answer. Its last value stays visible, dimmed. Logitech receivers drop sleeping devices from the link, so their last value is kept for 30 minutes.
- **Keychron keyboards:** they only report their battery over Bluetooth (shown via the Bluetooth support). Over the 2.4 GHz receiver the firmware does not expose it. Keychron mice are supported.
- **Baseus AeQur GH02 headset:** the 2.4 GHz dongle (`10D6:4802`, Actions chip) only carries audio, media keys and the chip's firmware-update channel, not the battery. Connect the headset over Bluetooth to see its level (shown via the Bluetooth support when Windows reports one).
- **Rapoo:** supported VT mice push their status, so a refresh can wait up to 4 seconds per matching interface. Sleeping mice may stay dimmed with their last reading for up to 30 minutes. Support is for Nordic 54L report `07` and legacy VT3 Pro `BB`; CH584 report `08`, office MT/M-series mice and other firmware protocols are not covered by this driver.
- **Rapoo:** supported VT mice push their status, so a refresh can wait up to 4 seconds per matching interface. Sleeping mice may stay dimmed with their last reading for up to 30 minutes. Support is for Nordic 54L report `07` and legacy `BB` (VT3 Pro, VT1 Pro Max); CH584 report `08`, office MT/M-series mice and other firmware protocols are not covered by this driver.
- **Flydigi:** this driver targets Vader 5 Pro only; Bluetooth and other Flydigi models are not covered. Percentages represent coarse battery levels. The implementation follows SDL and Windows hardware traces; local hardware validation is pending.
- **Not supported yet:** MSI wireless mice other than the VERSA 300 ELITE and the CLUTCH GM31 / GM41, MSI wireless keyboards, Razer Kraken headsets and the Barracuda models other than the Barracuda X (2022) on `1532:0550`, HyperX Pulsefire mice other than the Haste 2 Wireless / Haste 2 Core Wireless and the Xbox Wireless Headset on the Xbox adapter: their battery protocols are not documented. The Xbox Wireless Headset works over Bluetooth. A USB capture from an owner (see CONTRIBUTING.md) is the way to add them.
- **Not supported yet:** MSI wireless mice and keyboards, Razer Kraken headsets and the Barracuda models other than the Barracuda X (2022) on `1532:0550`, other HyperX Pulsefire mice and the Xbox Wireless Headset on the Xbox adapter: their battery protocols are not documented. The Xbox Wireless Headset works over Bluetooth. A USB capture from an owner (see CONTRIBUTING.md) is the way to add them.
- **Other devices:** some 2.4 GHz devices use undocumented protocols and are not supported yet. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to help add one.

## How it works

Each vendor driver in [`src/drivers/`](src/drivers) recognises its devices by USB vendor and product ID, and only ever sends read-only battery queries. Unknown devices are never written to. The generic fallbacks (HID battery usage, Bluetooth, XInput, HeadsetControl) only look at devices no vendor driver has claimed.

The taskbar widget is a layered child window of `Shell_TrayWnd`, placed left of `TrayNotifyWnd`. If Explorer restarts, it is re-created.

## Translations

Every language is a plain UTF-8 text file in [`lang/`](lang): English on the left, the translation on the right.

```
@code = it
@name = Italiano
Refresh now = Aggiorna ora
{name} is at {percent}% = {name} è al {percent}%
```

- **Use your own language right away:** choose *Language → Add your own language...* in the menu. It opens `%APPDATA%\WirelessBattery\lang` with `_template.txt`, which lists every phrase. Copy it to e.g. `it.txt`, fill in `@code`, `@name` and the translations, and the language appears in the menu (no restart needed). A file there with the same `@code` as a built-in language replaces its phrases, so you can also fix a single word locally.
- **Share it with everyone:** send the file as a pull request to [`lang/`](lang). The build includes every file in that folder automatically; no code change is needed.
- Keep `{placeholders}` as they are, and add `@rtl = 1` for right-to-left scripts. Phrases left empty stay English, so a partial translation is fine.
- The `--list` and `--dump` output stays English on purpose: it is pasted into GitHub issues.

## Credits

App icon by [nik-txt](https://github.com/nik-txt) ([`res/app.svg`](res/app.svg)).

The protocols come from these projects' research:

- [HeadsetControl Astro drivers](https://github.com/Sapd/HeadsetControl/blob/master/lib/devices/logitech_astro_a50.hpp), [eh-fifty](https://github.com/tdryer/eh-fifty), and [AstroBar](https://github.com/nichtlegacy/AstroBar): Astro A50 X / Gen 5 / Gen 4 / Gen 3 / A20 battery protocols

- [mouse-battery-monitor](https://github.com/stuffz/mouse-battery-monitor) (stuffz): VAXEE battery and charging commands ([protocol documentation](https://github.com/stuffz/mouse-battery-monitor/blob/main/docs/VAXEE.md))

- [HeadsetControl](https://github.com/Sapd/HeadsetControl): SteelSeries, Corsair, HyperX, Logitech and Sony INZONE headsets
- [inzone-buds-battery-tray](https://github.com/kinako19/inzone-buds-battery-tray) (kinako19) and [inzone-buds-battery-tray](https://github.com/takamachi66/inzone-buds-battery-tray) (takamachi66): Sony INZONE Buds
- [OpenRazer](https://github.com/openrazer/openrazer): Razer
- [Solaar](https://github.com/pwr-Solaar/Solaar) and the Logitech HID++ 2.0 documents: Logitech
- [g435-battery-percentage](https://github.com/portyporty/g435-battery-percentage) and [logitech-g435-battery](https://github.com/deddroid/logitech-g435-battery): Logitech G435 (`0ADF` dongle)
- [rivalcfg](https://github.com/flozz/rivalcfg): SteelSeries mice (Rival Pro from its pull request #294)
- [glorious-indicator](https://github.com/ikajdan/glorious-indicator) and [glorious-ctl](https://github.com/louis4craft/glorious-ctl): Glorious
- Hitscan's web configurator ([control.hitscan.com](https://control.hitscan.com)): Hitscan
- Linux `hid-kysona` (Lode Willems): Kysona, Pulsar and ATK
- ATK's web configurator ([hub.atk.pro](https://hub.atk.pro)): ATK mice and the N9 Pro / N9 Ultra headsets
- [PulsarBattery](https://github.com/darthsoup/PulsarBattery): Pulsar X2 V3 / X2 V3 eS
- ATK's web configurator ([hub.atk.pro](https://hub.atk.pro)): ATK mice and the N9 Pro headset
- [HaloBattery](https://github.com/HeyOkay/HaloBattery) PR #350 and [mouse-battery](https://github.com/qwr79/mouse-battery): ATK / VXE NK NANO dongle
- [HaloBattery](https://github.com/HeyOkay/HaloBattery) (MIT): Audeze Maxwell, NZXT Lift Elite, Poly BT600, Razer Barracuda Pro, SteelSeries Arctis Nova Elite, ATK V75X and Endgame Gear XM2we, ported from its providers (each driver names its source)
- G-Wolves' web driver ([mouse.xyz](https://mouse.xyz)): G-Wolves models and their protocols
- [BatteryWatch](https://github.com/B1Chat/BatteryWatch): CHERRY keyboards on the 2.4 GHz dongle (frame format and battery query)
- Keychron Launcher ([launcher.keychron.com](https://launcher.keychron.com)): Keychron mice
- [NinjaForce](https://www.ninjaforce.co/) and [ninjutso-battery-tray](https://github.com/DrStopor/ninjutso-battery-tray): Ninjutso Ten / Ten Air feature queries
- [nape_pro](https://github.com/nvalis/nape_pro) and [KeychronNapeBatteryWidget](https://github.com/gtun/KeychronNapeBatteryWidget): Keychron Nape Pro on the Link-KM receiver
- LAMZU Aurora ([lamzu.net](https://www.lamzu.net)): LAMZU mice
- [vole](https://github.com/johanneszab/vole) and [Endgame_Gear_Web_Configurator](https://github.com/Janlhin/Endgame_Gear_Web_Configurator): Endgame Gear 4K mice
- [mouse-gauge](https://github.com/djnawara/mouse-gauge) and [HaloBattery](https://github.com/Waturus/HaloBattery): WLMouse
- [OpenMouse mouse-protocol](https://github.com/OpenMouse-Project/mouse-protocol) and [FinalmousePollingRateSwitcher](https://github.com/xBambooz/FinalmousePollingRateSwitcher): Finalmouse UltralightX / Starlight X (from Finalmouse's xpanel)
- [redragon-battery-omarchy](https://github.com/EliottV17/redragon-battery-omarchy) and [g49-web-control](https://github.com/pingpingjinping/g49-web-control): Redragon ids
- [m913-ctl](https://github.com/Qehbr/m913-ctl) and [redragon-m913-battery-tray](https://github.com/Doomguy-BFG9000/redragon-m913-battery-tray): Areson `25A7` frame layout and `GetPower` command
- [peripheral-battery-tray](https://github.com/SteveWang92/peripheral-battery-tray) / [G-Helper](https://github.com/seerge/g-helper): ASUS ROG
- [peripheral-battery-tray](https://github.com/SteveWang92/peripheral-battery-tray) / [G-Helper](https://github.com/seerge/g-helper): ASUS ROG; [pelta-control](https://github.com/jimm0thy/pelta-control) / [BatteryWatch](https://github.com/B1Chat/BatteryWatch): ROG Pelta
- [zowie-battery](https://github.com/yleshchuk/zowie-battery) and [zowie-battery-tray](https://github.com/IgnacioBarb/zowie-battery-tray): ZOWIE EC-CW and DW
- RK's web driver ([drive.rkgaming.com](https://drive.rkgaming.com)): Royal Kludge MG6 Pro
- [MCHOSE-Monitor](https://github.com/Jstdi001/MCHOSE-Monitor): MCHOSE G3 V2
- [LGSTrayBattery-MotospeedX6](https://github.com/Jacobz888/LGSTrayBattery-MotospeedX6), [omarchy-delux-m900](https://github.com/AeonArcHQ/omarchy-delux-m900), [aj179-linux](https://github.com/Rockeyxx/aj179-linux): Motospeed, Delux, Ajazz
- [AreYouLowBattery](https://github.com/ryan-mant/AreYouLowBattery): CompX receiver reports for Delux M900 Pro
- [ajazz-aj139-macos](https://github.com/werquess/ajazz-aj139-macos) and [AjazzAJ139V2](https://github.com/nico2525nn/AjazzAJ139V2): Ajazz AJ139 V2
- [Incott-Manager](https://github.com/OmarK6/Incott-Manager), [incott-mouse-app](https://github.com/HeHaoren/incott-mouse-app) and [MouseBattery](https://github.com/FelixNg21/MouseBattery): Incott
- The Wraith web driver ([w1.software](https://www.w1.software/)): Wraith W1
- OpenRazer PR #2794 and [omarchy-blackshark-v3](https://github.com/ReedME/omarchy-blackshark-v3): BlackShark V3
- OpenRazer PR #2862 and [HaloBattery](https://github.com/HeyOkay/HaloBattery): BlackShark V2 Pro (2023)
- [razer-barracuda-x-battery](https://github.com/mehdibouchami/razer-barracuda-x-battery) and [barracuda-x-battery](https://github.com/nightdevx/barracuda-x-battery): Razer Barracuda X (2022) on the `1532:0550` receiver; [razer-barracuda-battery-tray](https://github.com/KhromotozzDevOut/razer-barracuda-battery-tray): framing of the `1532:0552` receiver
- [OpenRazer PR #2899](https://github.com/openrazer/openrazer/pull/2899): BlackShark V3 X
- [HyperXWM](https://github.com/Medprj/HyperXWM): HyperX Cloud III Wireless
- [HyperHeadset](https://github.com/LennardKittner/HyperHeadset): HyperX Cloud III S, Cloud II Core, Cloud Flight S
- [HyperBatteryMonitor](https://github.com/davidsantanaalves/HyperBatteryMonitor): HyperX Cloud Stinger Core Wireless
- [BatteryTray](https://github.com/qu1ncky/BatteryTray): Rongyuan and Xenta receivers (Attack Shark and others)
- [sonix-keyboard-studio](https://github.com/donglover69/sonix-keyboard-studio): SONiX keyboards on their 2.4G dongle (AJAZZ AK820 MAX, AK980 V2, AULA F108 Pro)
- [openajazz](https://github.com/shrey715/openajazz) and [Kraber](https://github.com/AkashPanja/Kraber): Semico `1A2C` (`AA 55 CC 33` / `0x0E`) status protocol for Attack Shark X98 and AJAZZ AK820 Max Plus
- [coolermaster-usb-protocol](https://github.com/syntactic-spice/coolermaster-usb-protocol) and [MM731-Controller](https://github.com/riVFerd/MM731-Controller): Cooler Master MM712 and MM731
- [GamesirBatteryTray](https://github.com/WWWyyy452/GamesirBatteryTray) and [Gamesir-Nova-2-Lite-Battery-Detection](https://github.com/AJAY0406/Gamesir-Nova-2-Lite-Battery-Detection): GameSir Nova
- [jabridge](https://github.com/Watchdog0x/jabridge): Jabra GNP protocol (Link 380 / 390 dongles)
- [xd5-go-web](https://github.com/jarjut/xd5-go-web): Fantech Helios Go XD5
- Linux `hid-playstation`: DualShock 4 / DualSense report layout
- [SDL's Flydigi HID driver](https://github.com/libsdl-org/SDL/blob/main/src/joystick/hidapi/SDL_hidapi_flydigi.c) and [HaloBattery issue #191](https://github.com/HeyOkay/HaloBattery/issues/191): Vader 5 Pro query framing and battery layout
- [SDL's 8BitDo HID driver](https://github.com/libsdl-org/SDL/blob/main/src/joystick/hidapi/SDL_hidapi_8bitdo.c): 8BitDo Ultimate 2 battery byte
- BEITONG iControl (its KP20 page and the receiver's USB traffic): BEITONG KP20 battery query and payload scrambling
- [SDL's 8BitDo HID driver](https://github.com/libsdl-org/SDL/blob/main/src/joystick/hidapi/SDL_hidapi_8bitdo.c) and [8bitdo-ultimate2-linux](https://github.com/MiguelSanzBr/8bitdo-ultimate2-linux): 8BitDo battery byte and vendor HID protocol
- JBL QuantumENGINE (its HIDV3 device-info messages): JBL Quantum headsets
- [HaloBattery](https://github.com/HeyOkay/HaloBattery/blob/main/docs/protocols.md): Corsair Sabre V2 Pro Ultralight, Compx protocol on `FF02:0002`
- JBL QuantumENGINE: HIDV1 connection and battery reports for the Quantum 350, and HIDV3 device-info messages for newer Quantum headsets

## License

[GNU General Public License v3.0 or later](LICENSE). You may use, modify and redistribute this
software, but anything you distribute that is based on it must be released under the same license,
with its source code.
