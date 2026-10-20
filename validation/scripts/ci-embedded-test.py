#!/usr/bin/env python3
"""Keep full emulator diagnostics across the existing embedded-hook suite."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from crash_evidence import Evidence
from emulator_adb import ensure_root
from root_evidence import capture

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--suite", choices=("combined", "lifecycle", "startup"), default="combined")
args = parser.parse_args()
os.chdir(Path(__file__).resolve().parent.parent)
serial = "emulator-5554"
# Debug transport privilege for diagnostics, not a Root/Xposed framework installation.
ensure_root(serial)
Path("build/device-evidence").mkdir(parents=True, exist_ok=True)
Path("build/device-evidence/suite.json").write_text(json.dumps({"suite": args.suite}) + "\n")
capture(["adb", "-s", serial, "shell", "getprop"], Path("build/device-evidence/initial-properties.txt"), 10,
        best_effort=True)
capture(["adb", "-s", serial, "shell", "cat", "/proc/cmdline"],
        Path("build/device-evidence/initial-kernel-command-line.txt"), 10, best_effort=True)
with Evidence(Path("build/device-evidence"), "embedded-suite", serial):
    subprocess.run(["bash", "scripts/ci-baseline.sh"], check=True, timeout=1500)
    subprocess.run(["bash", "scripts/ci-lspatch.sh", args.suite], check=True, timeout=1500)
