#!/usr/bin/env python3
"""Mixed lifecycle checks on disposable fixtures; never targets a physical phone."""
import argparse
import json
import subprocess
import time


PROTECTED = "dev.antishake.fixture.protectedapp"
CONTROL = "dev.antishake.fixture.control"


def check_process(kind, previous, current):
    assert previous and current, "Fixture process is missing"
    assert (previous != current) == (kind == "cold"), (kind, previous, current)


def check_motion(before, after, protected, light, resumes):
    assert before["screen"] == "PROBE" and before["navigated"] == "false", before
    assert after["hook"] == str(protected).lower(), "Module not loaded or control unexpectedly hooked"
    assert after["lightAvailable"] == "true" and int(after["lightEvents"]) > 0, after
    assert float(after["lastLight"]) == light, "Stale light evidence"
    assert int(after["resumes"]) == resumes, "Probe was not resumed as expected"
    if protected:
        assert after["screen"] == "PROBE" and after["navigated"] == "false", after
        assert after["events"] == "0" and after["sensorCount"] == "0", after
    else:
        assert after["screen"] == "TARGET" and after["navigated"] == "true", after
        assert int(after["events"]) > 0 and int(after["sensorCount"]) > 0, after


def check_page(state, scenario):
    expected = {"ad": "CLOSED", "delayed": "CLOSED", "missing": "RETURNED", "normal": "NONE"}[scenario]
    assert state["hook"] == "true" and state["screen"] == "MAIN", state
    assert state["close"] == expected and state["normalClicks"] == "0", state
    assert state["navigated"] == "false", state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    args = parser.parse_args()
    if not args.serial.startswith("emulator-"):
        parser.error("Only an explicitly selected disposable emulator is supported")

    def adb(*command):
        return subprocess.check_output(["adb", "-s", args.serial, *command], text=True, timeout=25).strip()

    def sensor(name, value):
        result = adb("emu", "sensor", "set", name, str(value))
        assert "KO" not in result, result

    def evidence(package):
        raw = adb("shell", "run-as", package, "cat", "files/probe.properties")
        return dict(line.split("=", 1) for line in raw.splitlines() if "=" in line and not line.startswith("#"))

    def wait_for(package, condition):
        deadline = time.monotonic() + 8
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

    def launch(package, scenario, cold=True):
        if cold:
            adb("shell", "am", "force-stop", package)
        adb("shell", "run-as", package, "rm", "-f", "files/probe.properties")
        sensor("acceleration", "0:0:9.81")
        sensor("gyroscope", "0:0:0")
        # FLAG_ACTIVITY_NEW_TASK | FLAG_ACTIVITY_CLEAR_TASK, supported by am's -f.
        adb("shell", "am", "start", "-W", "-f", "0x10008000",
            "-n", package + "/dev.antishake.fixture.MainActivity", "--es", "case", scenario)
        return wait_for(package, lambda state: "screen" in state)

    counts = dict.fromkeys(("cold", "warm", "background", "ad", "normal"), 0)
    try:
        for cycle in range(1, 101):
            kind = list(counts)[(cycle - 1) % 5]
            entry = {"cycle": cycle, "kind": kind, "evidence": {}}
            if kind in ("cold", "warm", "background"):
                # Control first: each motion input must still provoke real navigation.
                for package in (CONTROL, PROTECTED):
                    launch(package, "probe")
                    wait_for(package, lambda state: state.get("screen") == "PROBE")
                    previous = adb("shell", "pidof", package)
                    if kind in ("cold", "warm"):
                        launch(package, "probe", cold=kind == "cold")
                        resumes = 1
                    else:
                        adb("shell", "input", "keyevent", "KEYCODE_HOME")
                        time.sleep(0.3)
                        # Launcher semantics bring the existing task back, not a new scenario.
                        adb("shell", "am", "start", "-W", "-a", "android.intent.action.MAIN",
                            "-c", "android.intent.category.LAUNCHER", "-f", "0x10200000",
                            "-n", package + "/dev.antishake.fixture.MainActivity")
                        resumes = 2
                    before = wait_for(package, lambda state: state.get("screen") == "PROBE"
                                      and state.get("resumes") == str(resumes))
                    current = adb("shell", "pidof", package)
                    check_process(kind, previous, current)
                    light = 200 + cycle
                    sensor("light", light)
                    wait_for(package, lambda state: float(state.get("lastLight", "-1")) == light)
                    for _ in range(4):
                        sensor("acceleration", "20:0:9.81")
                        sensor("gyroscope", "4:0:0")
                        time.sleep(0.12)
                        sensor("acceleration", "-20:0:9.81")
                        sensor("gyroscope", "0:0:0")
                        time.sleep(0.12)
                    sensor("acceleration", "0:0:9.81")
                    if package == CONTROL:
                        wait_for(package, lambda state: state.get("screen") == "TARGET")
                    after = evidence(package)
                    check_motion(before, after, package == PROTECTED, light, resumes)
                    entry["evidence"][package] = {"beforePid": previous, "afterPid": current,
                                                  "before": before, "after": after}
            else:
                scenario = ("ad", "delayed", "missing")[counts[kind] % 3] if kind == "ad" else "normal"
                launch(PROTECTED, scenario)
                expected = "RETURNED" if scenario == "missing" else ("NONE" if scenario == "normal" else "CLOSED")
                wait_for(PROTECTED, lambda state: state.get("screen") == "MAIN" and state.get("close") == expected)
                # Recheck the final state, not just a transient successful snapshot.
                time.sleep(3 if scenario == "normal" else 0.5)
                state = evidence(PROTECTED)
                check_page(state, scenario)
                entry["scenario"] = scenario
                entry["evidence"][PROTECTED] = state
            counts[kind] += 1
            print(json.dumps(dict(entry, result="PASS"), ensure_ascii=False), flush=True)
        assert counts == {"cold": 20, "warm": 20, "background": 20, "ad": 20, "normal": 20}, counts
        print(json.dumps({"suite": "lifecycle", "result": "PASS", "cycles": 100, "counts": counts}), flush=True)
    finally:
        sensor("acceleration", "0:0:9.81")
        sensor("gyroscope", "0:0:0")


if __name__ == "__main__":
    main()
