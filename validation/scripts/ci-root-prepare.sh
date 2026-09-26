#!/usr/bin/env bash
# Downloads only pinned upstream tools; patches a copy, never the SDK image.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/root/scripts build/root/magisk-env build/root-evidence
cd build/root
curl -fL --retry 2 --max-time 120 https://github.com/topjohnwu/Magisk/releases/download/v30.7/Magisk-v30.7.apk -o magisk.apk
curl -fL --retry 2 --max-time 120 https://github.com/JingMatrix/Vector/releases/download/v2.2/Vector-v2.2-3080-Release.zip -o vector.zip
curl -fL --retry 2 --max-time 120 https://raw.githubusercontent.com/topjohnwu/Magisk/e8a58776f1d7bdf852072ad0baa6eceb9a1e4aac/build.py -o build.py
curl -fL --retry 2 --max-time 120 https://raw.githubusercontent.com/topjohnwu/Magisk/e8a58776f1d7bdf852072ad0baa6eceb9a1e4aac/scripts/host_patch.sh -o scripts/host_patch.sh
printf '%s\n' \
 'e0d32d2123532860f97123d927b1bb86c4e08e6fd8a48bfc6b5bee0afae9ebd5  magisk.apk' \
 '9ee8323575d615f7b3f1076ff60b2a63a49390ef11881b52632311a37f6f79cc  vector.zip' \
 'd509cb1a11e64b7e3e2d01230051bc434cfb1c5d9875a57974233c4853face6e  build.py' \
 '1720669a684f75fe90a7318868dd4528f2e736a5ad5363f92a3c51c848d79703  scripts/host_patch.sh' \
 | sha256sum --check
export ANDROID_SERIAL=emulator-5554
adb -s "$ANDROID_SERIAL" root
adb -s "$ANDROID_SERIAL" wait-for-device
test "$(adb -s "$ANDROID_SERIAL" shell id -u | tr -d '\r')" = 0
python3 build.py avd_patch "$ANDROID_HOME/system-images/android-35/google_apis/x86_64/ramdisk.img" "$PWD/ramdisk.img" --apk "$PWD/magisk.apk"
test -s ramdisk.img
sha256sum magisk.apk vector.zip build.py scripts/host_patch.sh ramdisk.img > ../root-evidence/tool-sha256.txt
unzip -jo magisk.apk 'assets/*.sh' 'assets/stub.apk' 'lib/x86_64/*.so' -d magisk-env
for library in magisk-env/lib*.so; do
  name="${library##*/lib}"
  mv "$library" "magisk-env/${name%.so}"
done
unzip -p magisk.apk lib/x86/libmagisk.so > magisk-env/magisk32
