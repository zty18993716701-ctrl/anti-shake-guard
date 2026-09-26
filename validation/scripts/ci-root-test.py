#!/usr/bin/env python3
"""Root/Vector integration on a disposable CI emulator with unmodified fixture APKs."""
import json
import os
from pathlib import Path
import subprocess
import time
from root_evidence import capture

os.chdir(Path(__file__).resolve().parent.parent)
SERIAL = "emulator-5554"
MODULE = "dev.antishake.guard"
PROTECTED = "dev.antishake.fixture.protectedapp"
CLI = "/data/adb/modules/zygisk_vector/cli"
EVIDENCE = Path("build/root-evidence")
EVIDENCE.mkdir(parents=True, exist_ok=True)


def adb(*args, timeout=45):
    return subprocess.check_output(["adb", "-s", SERIAL, *args], text=True, timeout=timeout).strip()


def save(name, value):
    (EVIDENCE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def root():
    adb("root")
    adb("wait-for-device")
    assert adb("shell", "id", "-u") == "0", "Disposable emulator adbd is not root"
    assert "30.7" in adb("shell", "/debug_ramdisk/magisk", "-v")


def cli(*args):
    response = json.loads(adb("shell", CLI, "--json", *args))
    assert response.get("success") is True, response
    return response["data"]


def ready():
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            return cli("status")
        except (subprocess.CalledProcessError, json.JSONDecodeError, AssertionError):
            time.sleep(2)
    raise AssertionError("Vector CLI not ready after 90 seconds")


def reboot(label):
    previous = adb("shell", "cat", "/proc/sys/kernel/random/boot_id")
    adb("reboot")
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            current = adb("shell", "cat", "/proc/sys/kernel/random/boot_id", timeout=10)
            if current != previous and adb("shell", "getprop", "sys.boot_completed", timeout=10) == "1":
                root()
                save(label + "-reboot.json", {"before": previous, "after": current, "framework": ready()})
                return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        time.sleep(2)
    raise AssertionError("Emulator did not complete a new boot")


def configuration(label, scoped, enabled):
    scope = cli("scope", "ls", MODULE)
    expected = [{"APP_PACKAGE": PROTECTED, "USER_ID": 0}] if scoped else []
    assert scope == expected, scope
    modules = cli("modules", "ls")
    module = [entry for entry in modules if entry["PACKAGE"] == MODULE]
    assert len(module) == 1 and module[0]["STATUS"] == ("enabled" if enabled else "disabled"), modules
    save(label + "-configuration.json", {"scope": scope, "module": module, "framework": ready()})
    # Framework cache refresh is asynchronous; behavior still must pass independently.
    time.sleep(2)


def smoke(label, mode):
    result = capture(["python3", "scripts/emulator-smoke.py", "--serial", SERIAL, "--mode", mode],
                     EVIDENCE / (label + ".jsonl"), 180)
    print(result.stdout, flush=True)
    assert result.returncode == 0, f"{label} failed: {result.returncode}"
    summaries = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{"mode":')]
    assert summaries == [{"mode": mode, "result": "PASS", "tests": 8}], summaries


try:
    root()
    save("environment.json", {"fingerprint": adb("shell", "getprop", "ro.build.fingerprint"),
                              "magisk": adb("shell", "/debug_ramdisk/magisk", "-v"),
                              "selinux": adb("shell", "getenforce")})
    adb("shell", "mkdir", "-p", "/data/adb/magisk")
    adb("push", "build/root/magisk-env/.", "/data/adb/magisk/")
    adb("shell", "chmod", "-R", "755", "/data/adb/magisk")
    adb("install", "-r", "build/root/magisk.apk")
    adb("push", "build/root/vector.zip", "/data/local/tmp/antishake-vector.zip")
    adb("shell", "/debug_ramdisk/magisk", "--sqlite", '"INSERT OR REPLACE INTO settings (key,value) VALUES(\'zygisk\',1)"')
    print(adb("shell", "/debug_ramdisk/magisk", "--install-module", "/data/local/tmp/antishake-vector.zip", timeout=120), flush=True)
    reboot("framework-install")
    for apk in ["guard/build/outputs/apk/debug/guard-debug.apk",
                "fixture/build/outputs/apk/protectedApp/debug/fixture-protectedApp-debug.apk",
                "fixture/build/outputs/apk/control/debug/fixture-control-debug.apk"]:
        adb("install", "-r", apk)
    smoke("root-unconfigured", "baseline")
    result = cli("modules", "enable", MODULE)
    assert result["Failed"] == [] and MODULE in result["Enabled"], result
    cli("scope", "set", MODULE, PROTECTED + "/0")
    configuration("enabled", True, True)
    smoke("root-enabled", "hooked")
    reboot("protection-persistence")
    configuration("after-reboot", True, True)
    smoke("root-after-reboot", "hooked")
    cli("scope", "rm", MODULE, PROTECTED + "/0")
    configuration("scope-removed", False, True)
    smoke("root-scope-removed", "baseline")
    cli("scope", "set", MODULE, PROTECTED + "/0")
    configuration("scope-restored", True, True)
    smoke("root-scope-restored", "hooked")
    result = cli("modules", "disable", MODULE)
    assert result["Failed"] == [] and MODULE in result["Disabled"], result
    configuration("disabled", True, False)
    smoke("root-disabled", "baseline")
finally:
    capture(["adb", "-s", SERIAL, "logcat", "-d", "-s", "Vector:I", "LSPosed-Bridge:I", "AndroidRuntime:E"],
            EVIDENCE / "framework-logcat.txt", 30, best_effort=True)
