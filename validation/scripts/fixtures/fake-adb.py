#!/usr/bin/env python3
"""Local subprocess boundary for evidence-collector tests; no Android behavior is simulated."""
from pathlib import Path
import sys
import time

root = Path(__file__).parent
log = root / "device.log"
log.touch(exist_ok=True)
args = sys.argv[3:]
if args == ["root"]:
    count = root / "root-attempts"
    attempt = int(count.read_text()) + 1 if count.exists() else 1
    count.write_text(str(attempt))
    if (root / "deny-root").exists():
        print("adbd cannot run as root in production builds", file=sys.stderr)
        sys.exit(1)
    if (root / "root-closed").exists() and attempt == 1:
        print("adb: unable to connect for root: closed", file=sys.stderr)
        sys.exit(1)
    print("restarting adbd as root")
elif args == ["shell", "id", "-u"]:
    print("2000" if (root / "stay-shell").exists() else "0")
elif args[:2] == ["shell", "settings"]:
    operation, namespace, key, *value = args[2:]
    assert namespace == "system" and key in ("accelerometer_rotation", "user_rotation")
    if operation == "put":
        if not (root / "ignore-rotation").exists():
            (root / key).write_text(value[0])
    elif operation == "get":
        print((root / key).read_text() if (root / key).exists() else "null")
    else:
        raise AssertionError(operation)
elif args[:2] == ["shell", "log"]:
    if not ((root / "lose-markers").exists()
            or ((root / "lose-end").exists() and args[-1].endswith(":END"))):
        with log.open("a") as output:
            output.write(args[-1] + "\n")
elif args[:3] == ["shell", "am", "start"] and (root / "stall-am-start").exists():
    print("Starting: transport stalled before activity response", flush=True)
    time.sleep(30)
elif args and args[0] == "logcat":
    if "-d" in args:
        snapshot = log.read_text() if "all" in args else ""
        if (root / "snapshot-loses-record").exists():
            snapshot = "".join(line for line in snapshot.splitlines(keepends=True) if "missing from snapshot" not in line)
        print(snapshot, end="")
    else:
        position = 0
        while True:
            data = log.read_text()
            tail = data[position:]
            if (root / "stream-omit-end").exists():
                tail = "".join(line for line in tail.splitlines(keepends=True)
                               if not line.strip().endswith(":END") and "snapshot-only:" not in line)
            sys.stdout.write(tail)
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
