#!/usr/bin/env bash
# Read-only forensics for the exact ART build in the retained native tombstone.
set -euo pipefail
evidence_dir="${1:?Select the diagnostic evidence directory}"
mkdir -p build/root "$evidence_dir"
adb -s emulator-5554 pull /apex/com.android.art/lib64/libart.so build/root/libart-forensics.so
sha256sum build/root/libart-forensics.so > "$evidence_dir/art-sha256.txt"
readelf --notes build/root/libart-forensics.so > "$evidence_dir/art-notes.txt"
if grep -q '62338b1c62e3991543c9b8b8bae2b361' "$evidence_dir/art-notes.txt"; then
  # Handler, unknown frame #03 and Thread::CreateCallback from the original tombstone.
  objdump --disassemble --demangle --start-address=0x503610 --stop-address=0x503790 \
    build/root/libart-forensics.so > "$evidence_dir/art-sigsegv-disassembly.txt"
  objdump --disassemble --demangle --start-address=0x9b2560 --stop-address=0x9b2680 \
    build/root/libart-forensics.so > "$evidence_dir/art-frame03-disassembly.txt"
  objdump --disassemble --demangle --start-address=0x8c5700 --stop-address=0x8c5d00 \
    build/root/libart-forensics.so > "$evidence_dir/art-thread-disassembly.txt"
else
  echo 'ART build changed; original crash addresses must not be applied to this binary.' \
    > "$evidence_dir/art-address-mismatch.txt"
fi
# libart-forensics.so stays outside the evidence upload path; no runtime binary is distributed.
