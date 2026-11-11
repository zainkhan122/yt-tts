"""Shared test setup.

yt-dlp is installed per user (~/.local/bin). Tests that call it must not depend on the shell's PATH
(failure 1 Nov: test_top_comments_returns_list failed when ~/.local/bin was not exported).
"""
import os
from pathlib import Path

_local_bin = str(Path.home() / ".local" / "bin")
if _local_bin not in os.environ.get("PATH", "").split(os.pathsep):
    os.environ["PATH"] = _local_bin + os.pathsep + os.environ.get("PATH", "")
