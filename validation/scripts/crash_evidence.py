"""Unfiltered, bounded evidence capture for disposable rooted Android emulators."""
import json
from pathlib import Path
import re
import subprocess
import time
import uuid

from root_evidence import capture


PACKAGES = ("dev.antishake.guard", "dev.antishake.fixture.protectedapp", "dev.antishake.fixture.control")


class Evidence:
    def __init__(self, folder, label, serial, adb="adb", allow_crash=False, marker_timeout=5):
        if not re.fullmatch(r"emulator-\d+", serial):
            raise ValueError("Only an explicitly selected disposable emulator is supported")
        self.folder = Path(folder) / label
        self.folder.mkdir(parents=True, exist_ok=True)
        self.command = [adb, "-s", serial]
        self.token = "AntiShakeEvidence-" + uuid.uuid4().hex
        self.timeout = marker_timeout
        self.allow_crash = allow_crash
        self.report = {"label": label, "serial": serial, "token": self.token, "commands": {}, "errors": []}

    def marker(self, suffix):
        marker = self.token + ":" + suffix
        subprocess.run(self.command + ["shell", "log", "-p", "i", "-t", "AntiShakeEvidence", marker],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if marker.encode() in (self.folder / "logcat-all.txt").read_bytes():
                return
            if self.process.poll() is not None:
                break
            time.sleep(0.05)
        raise AssertionError("Log stream did not capture " + suffix + " marker")

    def __enter__(self):
        self.output = (self.folder / "logcat-all.txt").open("wb")
        try:
            self.process = subprocess.Popen(self.command + ["logcat", "-b", "all", "-v", "threadtime"],
                                            stdout=self.output, stderr=subprocess.STDOUT)
            self.marker("START")
            return self
        except BaseException as error:
            self.__exit__(type(error), error, error.__traceback__)
            raise

    def snapshot(self, name, args):
        path = self.folder / name
        try:
            result = capture(self.command + args, path, 30)
            self.report["commands"][name] = {"returncode": result.returncode, "bytes": path.stat().st_size}
            if result.returncode != 0:
                raise AssertionError(f"{name} exited {result.returncode}")
            if name != "logcat-crash.txt" and path.stat().st_size == 0:
                raise AssertionError(name + " is empty")
        except Exception as error:
            self.report["errors"].append(str(error))

    def __exit__(self, error_type, primary, traceback):
        try:
            self.marker("END")
        except Exception as error:
            self.report["errors"].append(str(error))
        finally:
            if hasattr(self, "process"):
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
            self.output.close()

        self.snapshot("logcat-crash.txt", ["logcat", "-b", "crash", "-d", "-v", "threadtime"])
        self.snapshot("logcat-snapshot.txt", ["logcat", "-b", "all", "-d", "-v", "threadtime"])
        self.snapshot("dropbox.txt", ["shell", "dumpsys", "dropbox", "--print"])
        self.snapshot("kernel.txt", ["shell", "dmesg"])
        self.snapshot("boot-id.txt", ["shell", "cat", "/proc/sys/kernel/random/boot_id"])
        for package in PACKAGES:
            self.snapshot(package + "-exit-info.txt", ["shell", "dumpsys", "activity", "exit-info", package])
        tombstones = self.folder / "tombstones"
        tombstones.mkdir(exist_ok=True)
        self.snapshot("tombstones-pull.txt", ["pull", "/data/tombstones/.", str(tombstones)])

        text = (self.folder / "logcat-all.txt").read_text(errors="replace")
        start = text.find(self.token + ":START")
        end = text.find(self.token + ":END")
        if start < 0 or end <= start:
            self.report["errors"].append("Log coverage markers missing or out of order")
        elif not self.allow_crash:
            targets = "(?:" + "|".join(re.escape(package) for package in PACKAGES) + ")"
            crash = re.search(r"(?:Process: |>>> |ANR in )" + targets + r"(?=[:, <\r\n]|$)", text[start:end])
            if crash:
                self.report["errors"].append("Unexpected fixture crash/ANR: " + crash.group())
        self.report["complete"] = not self.report["errors"]
        self.report["operation_succeeded"] = error_type is None
        (self.folder / "capture.json").write_text(json.dumps(self.report, indent=2) + "\n")
        print(json.dumps({"capture": self.report["label"], "complete": self.report["complete"],
                          "errors": self.report["errors"]}), flush=True)
        if self.report["errors"] and primary is None:
            raise AssertionError("Incomplete or failed crash evidence: " + "; ".join(self.report["errors"]))
        return False
