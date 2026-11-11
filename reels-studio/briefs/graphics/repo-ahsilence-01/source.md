# Source digest: AhmadHassan-BTed/AhSilence (fetched 2026-11-09)

## GitHub repo API (api.github.com/repos/ahmadhassan-bted/ahsilence)

full_name=AhmadHassan-BTed/AhSilence; stargazers_count=4876; forks_count=10;
created_at=2026-07-03; language=Kotlin; license=Apache 2.0; pushed_at=2026-11-09.
description: "An open-source Android Active Noise Cancellation (ANC) engine."

## README (master branch, verbatim excerpts)

> AhSilence
> Silence the ambient hum. Find your perfect quiet.

> AhSilence is a native Android active noise cancellation (ANC) engine built with Jetpack Compose and Kotlin. It bridges the gap between complex digital signal processing (DSP) and human comfort by analyzing the environment for persistent, low-frequency hums (such as AC units or electrical drones) and emitting phase-inverted audio waves that mathematically neutralize acoustic disturbances.

> An open-source Android Active Noise Cancellation (ANC) engine. Leveraging low-latency DSP to neutralize environmental hums and help you reclaim your quiet.

> FFT Engine | Custom Cooley-Tukey Radix-2 algorithm on real-time PCM buffers | Automatically detects the dominant background drone

> Phase Calibrator | Continuous 360° trigonometric dial bound to memory blocks | Manual wave alignment to compensate for hardware/BT latency

> AhSilence is fully offline — zero network calls, zero data collection, zero telemetry.

> See ROADMAP.md for planned features including multi-frequency cancellation, adaptive algorithms, and Bluetooth latency compensation.

README mermaid sequence diagram note: "7-Second Ambient Scan" (microphone -> DSP -> FFT).

## SUPPORT.md FAQ (verbatim excerpts)

> **Q: Why does the app need microphone permission?**
> A: AhSilence captures a 7-second ambient audio sample to detect the dominant low-frequency hum (e.g., AC units). Audio is processed in-memory and never recorded or transmitted.

> **Q: Does it work with Bluetooth headphones?**
> A: Yes, but Bluetooth introduces latency. Use the Phase Calibrator dial to manually compensate for the delay.

> **Q: The cancellation isn't perfect. What can I do?**
> A: Enable PRO mode and fine-tune the Phase Shift dial. Small adjustments (±5°) around 180° can significantly improve cancellation depending on your hardware and environment.
