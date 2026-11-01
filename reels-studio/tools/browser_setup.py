#!/usr/bin/env python3
"""One-time, no-root setup of headless Chromium for the local layout audit (lesson 16).

Installs Playwright's Chromium into the user cache and unpacks the system libraries it needs
(Debian packages downloaded with apt-get download, extracted into ~/libs/root). Nothing is
installed system-wide. Re-run after a workspace restore if preflight reports the browser as missing.
"""
import subprocess
import sys
from pathlib import Path

LIBS = Path.home() / ".local" / "share" / "reels-browser"
PKGS = ["libnspr4", "libnss3", "libasound2t64", "libatk1.0-0t64", "libatk-bridge2.0-0t64", "libcups2t64",
        "libxkbcommon0", "libxcomposite1", "libxdamage1", "libxrandr2", "libgbm1", "libpango-1.0-0",
        "libcairo2", "libatspi2.0-0t64", "libavahi-common3", "libavahi-client3", "libdbus-1-3", "libxi6",
        "libxtst6", "libxfixes3", "libxext6", "libx11-xcb1", "libdrm2", "libxshmfence1", "libwayland-client0",
        "libxcb-randr0", "libxcb-shm0", "libxss1"]


def main():
    subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-q", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    root = LIBS / "root"
    if not root.exists():
        LIBS.mkdir(parents=True, exist_ok=True)
        subprocess.run(["apt-get", "download", *PKGS], cwd=LIBS, check=True)
        for deb in LIBS.glob("*.deb"):
            subprocess.run(["dpkg", "-x", str(deb), str(root)], check=True)
    print("browser ready:", root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
