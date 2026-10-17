#!/usr/bin/env python3
"""Mixed lifecycle checks on disposable fixtures; never targets a physical phone."""
import argparse
import json
import subprocess
import time
from emulator_adb import lock_rotation
from startup_diagnostic import diagnose


PROTECTED = "dev.antishake.fixture.protectedapp"
CONTROL = "dev.antishake.fixture.control"


def cycle_plan(start, count):
    if start < 1 or count < 1 or start + count > 101:
        raise ValueError("Cycle range must be within 1..100")
    plan = []
    for cycle in range(start, start + count):
        kind = ("cold", "warm", "background", "ad", "normal")[(cycle - 1) % 5]
        row = {"cycle": cycle, "kind": kind}
        if kind in ("ad", "normal"):
            row["scenario"] = ("ad", "delayed", "missing")[((cycle - 1) // 5) % 3] if kind == "ad" else "normal"
        plan.append(row)
    return plan


def check_process(kind, previous, current):
    assert previous and current, "Fixture process is missing"
    assert (previous != current) == (kind == "cold"), (kind, previous, current)


def check_motion(before, after, protected, light, resumes):
    assert before["screen"] == "PROBE" and before["navigated"] == "false", before
    assert after["hook"] == str(protected).lower(), "Module not loaded or control unexpectedly hooked"
    assert after["lightAvailable"] == "true" and int(after["lightEvents"]) > 0, after
    assert float(after["lastLight"]) == light, "Stale light evidence"
    assert int(after["resumes"]) == resumes, "Probe was not resumed as expected: " + str(after)
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
    parser.add_argument("--start-cycle", type=int, default=1)
    parser.add_argument("--cycles", type=int, default=100)
    parser.add_argument("--startup-only", action="store_true",
                        help="Repeat normal-page cold starts to isolate missing package callbacks")
    args = parser.parse_args()
    if not args.serial.startswith("emulator-"):
        parser.error("Only an explicitly selected disposable emulator is supported")
    try:
        plan = cycle_plan(args.start_cycle, args.cycles)
    except ValueError as error:
        parser.error(str(error))
    if args.startup_only:
        plan = [dict(row, kind="normal", scenario="normal") for row in plan]
    # Motion injection must not add unplanned system-driven Activity recreation.
    lock_rotation(args.serial)

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
            "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER",
            "-n", package + "/dev.antishake.fixture.MainActivity", "--es", "case", scenario)
        return wait_for(package, lambda state: "screen" in state)

    counts = dict.fromkeys(("cold", "warm", "background", "ad", "normal"), 0)
    try:
        for planned in plan:
            cycle, kind = planned["cycle"], planned["kind"]
            entry = dict(planned, evidence={})
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
                    final_pid = adb("shell", "pidof", package)
                    check_process("warm", current, final_pid)
                    entry["evidence"][package] = {"beforePid": previous, "afterPid": current,
                                                  "finalPid": final_pid, "before": before, "after": after}
            else:
                scenario = planned["scenario"]
                launch(PROTECTED, scenario)
                previous = adb("shell", "pidof", PROTECTED)
                expected = "RETURNED" if scenario == "missing" else ("NONE" if scenario == "normal" else "CLOSED")
                wait_for(PROTECTED, lambda state: state.get("screen") == "MAIN" and state.get("close") == expected)
                # Recheck the final state, not just a transient successful snapshot.
                time.sleep(3 if scenario == "normal" else 0.5)
                state = evidence(PROTECTED)
                try:
                    check_page(state, scenario)
                except AssertionError:
                    print(json.dumps({"cycle": cycle, "kind": kind, "result": "FAIL",
                                      "state": state, "pid": previous,
                                      "diagnostic": diagnose(adb, PROTECTED, previous, cycle)}), flush=True)
                    raise
                current = adb("shell", "pidof", PROTECTED)
                check_process("warm", previous, current)
                entry["scenario"] = scenario
                entry["evidence"][PROTECTED] = {"beforePid": previous, "finalPid": current, "after": state}
            counts[kind] += 1
            print(json.dumps(dict(entry, result="PASS"), ensure_ascii=False), flush=True)
        assert counts == {kind: sum(row["kind"] == kind for row in plan) for kind in counts}, counts
        print(json.dumps({"suite": "startup" if args.startup_only else "lifecycle", "result": "PASS", "cycles": len(plan),
                          "startCycle": args.start_cycle, "counts": counts}), flush=True)
    finally:
        sensor("acceleration", "0:0:9.81")
        sensor("gyroscope", "0:0:0")


if __name__ == "__main__":
    main()
