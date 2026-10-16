#!/usr/bin/env python3
"""Local subprocess boundary for evidence-collector tests; no Android behavior is simulated."""
from pathlib import Path
import sys
import time

root = Path(__file__).parent
log = root / "device.log"
log.touch(exist_ok=True)
args = sys.argv[3:]
if args[:2] == ["shell", "log"]:
    if not ((root / "lose-markers").exists()
            or ((root / "lose-end").exists() and args[-1].endswith(":END"))):
        with log.open("a") as output:
            output.write(args[-1] + "\n")
elif args and args[0] == "logcat":
    if "-d" in args:
        print(log.read_text() if "all" in args else "", end="")
    else:
        position = 0
        while True:
            data = log.read_text()
            sys.stdout.write(data[position:])
            sys.stdout.flush()
            position = len(data)
            time.sleep(0.01)
elif args and args[0] == "pull":
    if (root / "deny-tombstones").exists():
        print("permission denied", file=sys.stderr)
        sys.exit(7)
    Path(args[-1]).mkdir(parents=True, exist_ok=True)
    print("0 files pulled")
else:
    if not ((root / "empty-dropbox").exists() and "dropbox" in args):
        print("diagnostic snapshot")
