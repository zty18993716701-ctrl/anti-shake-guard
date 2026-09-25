#!/usr/bin/env python3
"""Black-box tests against real APKs. Hooked mode FAILS if Xposed is not active."""
import argparse
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument("--adb", default="adb")
parser.add_argument("--serial", required=True, help="Explicit test emulator serial; never targets a phone by default")
parser.add_argument("--mode", choices=["baseline", "hooked"], required=True)
args = parser.parse_args()
if not args.serial.startswith("emulator-"):
    parser.error("This script injects virtual sensors and only supports an emulator.")

PROTECTED = "dev.antishake.fixture.protectedapp"
CONTROL = "dev.antishake.fixture.control"
results = []


def adb(*command):
    return subprocess.check_output([args.adb, "-s", args.serial, *command], text=True, timeout=25).strip()


def evidence(package):
    raw = adb("shell", "run-as", package, "cat", "files/probe.properties")
    return dict(line.split("=", 1) for line in raw.splitlines() if "=" in line and not line.startswith("#"))


def wait_for(package, condition, timeout=8):
    deadline = time.monotonic() + timeout
    latest = {}
    while time.monotonic() < deadline:
        try:
            latest = evidence(package)
            if condition(latest):
                return latest
        except subprocess.CalledProcessError:
            pass
        time.sleep(0.15)
    raise AssertionError(f"Timed out: {package}: {latest}")


def sensor(name, value):
    response = adb("emu", "sensor", "set", name, value)
    if "KO" in response:
        raise AssertionError(response)


def launch(package, scenario):
    adb("shell", "am", "force-stop", package)
    # Remove stale evidence so a failed launch cannot pass on the preceding scenario.
    adb("shell", "run-as", package, "rm", "-f", "files/probe.properties")
    sensor("acceleration", "0:0:9.81")
    sensor("gyroscope", "0:0:0")
    adb("shell", "am", "start", "-W", "-n", package + "/dev.antishake.fixture.MainActivity",
        "--es", "case", scenario)
    return wait_for(package, lambda state: "screen" in state)


def shake():
    for _ in range(8):
        sensor("acceleration", "20:0:9.81")
        sensor("gyroscope", "4:0:0")
        time.sleep(0.12)
        sensor("acceleration", "-20:0:9.81")
        sensor("gyroscope", "0:0:0")
        time.sleep(0.12)
    sensor("acceleration", "0:0:9.81")


def record(name, state):
    results.append({"test": name, "result": "PASS", "evidence": state})
    print(json.dumps(results[-1], ensure_ascii=False), flush=True)


def tap_close(package):
    adb("shell", "uiautomator", "dump", "/data/local/tmp/antishake-window.xml")
    tree = ET.fromstring(adb("shell", "cat", "/data/local/tmp/antishake-window.xml"))
    for node in tree.iter("node"):
        if node.get("resource-id") == package + ":id/close_ad":
            x1, y1, x2, y2 = map(int, re.findall(r"\d+", node.attrib["bounds"]))
            adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
            return
    raise AssertionError("Fixture close button not present")


try:
    # Always prove the input causes real navigation in the unprotected control.
    for package in [CONTROL, PROTECTED]:
        launch(package, "probe")
        wait_for(package, lambda state: state.get("screen") == "PROBE")
        time.sleep(0.5)
        sensor("light", "123")
        light = wait_for(package, lambda state: float(state.get("lastLight", "-1")) == 123)
        assert light["lightAvailable"] == "true" and int(light["lightEvents"]) > 0, light
        record(package + ": non-motion light preserved", light)
        shake()
        protected = args.mode == "hooked" and package == PROTECTED
        if protected:
            state = evidence(package)
            assert state["hook"] == "true", "Module not loaded; refusing false positive"
            assert state["screen"] == "PROBE" and state["navigated"] == "false", state
            assert state["events"] == "0" and state["sensorCount"] == "0", state
        else:
            state = wait_for(package, lambda state: state.get("screen") == "TARGET")
            assert state["hook"] == "false" and state["navigated"] == "true", state
            assert int(state["events"]) > 0 and int(state["sensorCount"]) > 0, state
        record(package + ": motion", state)

    for scenario in ["ad", "delayed", "missing", "normal"]:
        launch(PROTECTED, scenario)
        if args.mode == "hooked":
            expected = {"ad": "CLOSED", "delayed": "CLOSED", "missing": "RETURNED", "normal": "NONE"}[scenario]
            state = wait_for(PROTECTED, lambda value: value.get("screen") == "MAIN" and value.get("close") == expected)
            time.sleep(0.5)
            state = evidence(PROTECTED)
            assert state["hook"] == "true" and state["navigated"] == "false", state
            assert state["normalClicks"] == "0", state
        else:
            time.sleep(3)
            state = evidence(PROTECTED)
            assert state["hook"] == "false" and state["close"] == "NONE", state
            assert state["screen"] == ("MAIN" if scenario == "normal" else "AD"), state
            if scenario in ("ad", "delayed"):
                tap_close(PROTECTED)
                state = wait_for(PROTECTED, lambda value: value.get("close") == "CLOSED" and value.get("screen") == "MAIN")
        record(scenario, state)
    print(json.dumps({"mode": args.mode, "result": "PASS", "tests": len(results)}))
finally:
    sensor("acceleration", "0:0:9.81")
    sensor("gyroscope", "0:0:0")
