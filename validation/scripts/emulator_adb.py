"""Bounded debug-root negotiation across emulator adbd restarts."""
import argparse
import re
import subprocess
import time


def ensure_root(serial, adb="adb", timeout=30):
    if not re.fullmatch(r"emulator-\d+", serial):
        raise ValueError("Only an explicitly selected disposable emulator is supported")
    deadline = time.monotonic() + timeout
    latest = ""
    while time.monotonic() < deadline:
        try:
            result = subprocess.run([adb, "-s", serial, "root"], text=True, capture_output=True,
                                    timeout=min(5, max(0.01, deadline - time.monotonic())))
            latest = result.stdout + result.stderr
            if result.returncode and not any(word in latest.lower() for word in ("closed", "offline", "not found", "no devices")):
                raise AssertionError(latest)
            if result.returncode == 0:
                uid = subprocess.run([adb, "-s", serial, "shell", "id", "-u"], text=True, capture_output=True,
                                     timeout=min(5, max(0.01, deadline - time.monotonic())))
                if uid.returncode == 0 and uid.stdout.strip() == "0":
                    return
                latest = "UID=0 not verified: " + uid.stdout + uid.stderr
        except subprocess.TimeoutExpired as error:
            latest = str(error)
        print("Emulator root negotiation pending: " + latest.strip(), flush=True)
        time.sleep(min(0.5, max(0, deadline - time.monotonic())))
    raise AssertionError("Emulator UID=0 not ready within deadline: " + latest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    ensure_root(parser.parse_args().serial)
