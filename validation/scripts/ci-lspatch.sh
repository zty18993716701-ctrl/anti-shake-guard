#!/usr/bin/env bash
# Only patches this repository's disposable fixture, never a third-party APK.
set -euo pipefail
validation_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$validation_dir"
mkdir -p build/lspatch build/device-evidence
trap 'adb -s emulator-5554 logcat -d -s LSPosed:I LSPosed-Bridge:I AndroidRuntime:E > build/device-evidence/lspatch-logcat.txt || true' EXIT

curl --fail --location --retry 2 \
  https://github.com/JingMatrix/LSPatch/releases/download/v1.2/lspatch-v1.2-487-release.jar \
  --output build/lspatch/patcher.jar
echo 'd238fdc414d121b7fa454d8b4ccf420df3a8c97d563761861ff92bd9c5da2165  build/lspatch/patcher.jar' | sha256sum --check
java -jar build/lspatch/patcher.jar \
  fixture/build/outputs/apk/protectedApp/debug/fixture-protectedApp-debug.apk \
  -m guard/build/outputs/apk/debug/guard-debug.apk \
  -o build/lspatch -d -l 0 --version-code 1
patched=build/lspatch/fixture-protectedApp-debug-487-lspatched.apk
test -f "$patched"
# Prove the actual module under test was embedded, not an old downloaded module.
unzip -p "$patched" assets/lspatch/modules/dev.antishake.guard.apk \
  | cmp - guard/build/outputs/apk/debug/guard-debug.apk
sha256sum build/lspatch/patcher.jar "$patched" guard/build/outputs/apk/debug/guard-debug.apk \
  > build/device-evidence/lspatch-sha256.txt

# The preceding baseline installed this disposable package. Its signature changes.
adb -s emulator-5554 uninstall dev.antishake.fixture.protectedapp
adb -s emulator-5554 install "$patched"
for iteration in 1 2 3; do
  python3 scripts/emulator-smoke.py --serial emulator-5554 --mode hooked \
    | tee "build/device-evidence/lspatch-hooked-$iteration.jsonl"
done

# Same loaded module, repeated real lifecycle transitions; bounded to 15 minutes.
timeout 900s python3 -u scripts/emulator-lifecycle.py --serial emulator-5554 2>&1 \
  | tee build/device-evidence/lspatch-lifecycle.jsonl

# Prove removal restores motion/navigation, not a permanently disabled fixture.
adb -s emulator-5554 uninstall dev.antishake.fixture.protectedapp
adb -s emulator-5554 install fixture/build/outputs/apk/protectedApp/debug/fixture-protectedApp-debug.apk
python3 scripts/emulator-smoke.py --serial emulator-5554 --mode baseline \
  | tee build/device-evidence/lspatch-restored-baseline.jsonl
