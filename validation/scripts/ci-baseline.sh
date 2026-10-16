#!/usr/bin/env bash
set -euo pipefail
validation_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$validation_dir"
mkdir -p build/device-evidence
adb -s emulator-5554 install -r guard/build/outputs/apk/debug/guard-debug.apk
adb -s emulator-5554 install -r fixture/build/outputs/apk/protectedApp/debug/fixture-protectedApp-debug.apk
adb -s emulator-5554 install -r fixture/build/outputs/apk/control/debug/fixture-control-debug.apk
adb -s emulator-5554 shell getprop ro.build.fingerprint > build/device-evidence/fingerprint.txt
adb -s emulator-5554 emu sensor status > build/device-evidence/sensors.txt
python3 scripts/emulator-smoke.py --serial emulator-5554 --mode baseline | tee build/device-evidence/baseline.jsonl
# An unhooked device must not pass protection verification. Check the precise reason.
if python3 scripts/emulator-smoke.py --serial emulator-5554 --mode hooked > build/device-evidence/no-hook-negative.txt 2>&1; then
  echo 'ERROR: unhooked emulator falsely passed protection verification' >&2
  exit 1
fi
grep -q 'Module not loaded; refusing false positive' build/device-evidence/no-hook-negative.txt
# The mixed lifecycle suite must independently reject an unhooked protected fixture.
if python3 scripts/emulator-lifecycle.py --serial emulator-5554 > build/device-evidence/lifecycle-no-hook-negative.txt 2>&1; then
  echo 'ERROR: unhooked emulator falsely passed lifecycle verification' >&2
  exit 1
fi
grep -q 'Module not loaded' build/device-evidence/lifecycle-no-hook-negative.txt
