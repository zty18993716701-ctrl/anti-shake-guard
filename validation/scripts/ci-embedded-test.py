#!/usr/bin/env python3
"""Keep full emulator diagnostics across the existing embedded-hook suite."""
import os
from pathlib import Path
import subprocess

from crash_evidence import Evidence
from emulator_adb import ensure_root
from root_evidence import capture

os.chdir(Path(__file__).resolve().parent.parent)
serial = "emulator-5554"
# Debug transport privilege for diagnostics, not a Root/Xposed framework installation.
ensure_root(serial)
Path("build/device-evidence").mkdir(parents=True, exist_ok=True)
capture(["adb", "-s", serial, "shell", "getprop"], Path("build/device-evidence/initial-properties.txt"), 10,
        best_effort=True)
capture(["adb", "-s", serial, "shell", "cat", "/proc/cmdline"],
        Path("build/device-evidence/initial-kernel-command-line.txt"), 10, best_effort=True)
with Evidence(Path("build/device-evidence"), "embedded-suite", serial):
    for script in ("ci-baseline.sh", "ci-lspatch.sh"):
        subprocess.run(["bash", "scripts/" + script], check=True, timeout=1500)
