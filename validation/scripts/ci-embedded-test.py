#!/usr/bin/env python3
"""Keep full emulator diagnostics across the existing embedded-hook suite."""
import os
from pathlib import Path
import subprocess

from crash_evidence import Evidence

os.chdir(Path(__file__).resolve().parent.parent)
serial = "emulator-5554"
# Debug transport privilege for diagnostics, not a Root/Xposed framework installation.
subprocess.run(["adb", "-s", serial, "root"], check=True, timeout=30)
subprocess.run(["adb", "-s", serial, "wait-for-device"], check=True, timeout=30)
assert subprocess.check_output(["adb", "-s", serial, "shell", "id", "-u"], text=True, timeout=30).strip() == "0"
with Evidence(Path("build/device-evidence"), "embedded-suite", serial):
    for script in ("ci-baseline.sh", "ci-lspatch.sh"):
        subprocess.run(["bash", "scripts/" + script], check=True, timeout=1500)
