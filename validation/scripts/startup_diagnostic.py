"""Observe a failed fixture in-place; never turns the original failure into a pass."""
import time


def collect_timeout(adb, package):
    """Read-only triage; the caller bounds transport time and retains the original timeout."""
    result = {}
    for name, command in (("crashLog", ("logcat", "-b", "crash", "-d", "-v", "threadtime")),
                          ("exitInfo", ("shell", "dumpsys", "activity", "exit-info", package)),
                          ("pid", ("shell", "pidof", package))):
        try:
            result[name] = adb(*command)
        except Exception as error:
            result[name + "Error"] = type(error).__name__ + ": " + str(error)
    return result


def diagnose(adb, package, expected_pid, cycle, pause=time.sleep):
    result = {"outcome": "inconclusive", "expectedPid": expected_pid}

    def state():
        raw = adb("shell", "run-as", package, "cat", "files/probe.properties")
        return dict(line.split("=", 1) for line in raw.splitlines()
                    if "=" in line and not line.startswith("#"))

    def sensor(name, value):
        reply = adb("emu", "sensor", "set", name, value)
        assert "KO" not in reply, reply

    def same_process():
        pid = adb("shell", "pidof", package)
        assert pid and pid == expected_pid, "Diagnostic process changed: " + pid
        return pid

    try:
        result["beforePid"] = same_process()
        result["original"] = state()
        sensor("acceleration", "0:0:9.81")
        sensor("gyroscope", "0:0:0")
        # Clear only the Activity task. Do not stop the process or remove its evidence.
        adb("shell", "am", "start", "-W", "-f", "0x10008000",
            "-n", package + "/dev.antishake.fixture.MainActivity", "--es", "case", "probe")
        same_process()
        light = 700 + cycle
        sensor("light", str(light))
        for _ in range(40):
            result["before"] = state()
            if (result["before"].get("screen") == "PROBE"
                    and float(result["before"].get("lastLight", "-1")) == light):
                break
            pause(0.15)
        else:
            raise AssertionError("Diagnostic probe/light did not become ready")
        for _ in range(4):
            sensor("acceleration", "20:0:9.81")
            sensor("gyroscope", "4:0:0")
            pause(0.12)
            sensor("acceleration", "-20:0:9.81")
            sensor("gyroscope", "0:0:0")
            pause(0.12)
        pause(0.3)
        result["after"] = after = state()
        result["afterPid"] = same_process()
        assert float(after.get("lastLight", "-1")) == light and int(after.get("lightEvents", "0")) > 0, after
        if after.get("hook") == "false":
            if (after.get("screen") == "TARGET" and after.get("navigated") == "true"
                    and int(after.get("events", "0")) > 0 and int(after.get("sensorCount", "0")) > 0):
                result["outcome"] = "motion-navigation-marker-false"
            elif (after.get("screen") == "PROBE" and after.get("navigated") == "false"
                  and after.get("events") == "0" and after.get("sensorCount") == "0"):
                result["outcome"] = "motion-blocked-marker-false"
    except Exception as error:
        result["error"] = type(error).__name__ + ": " + str(error)
    finally:
        try:
            sensor("acceleration", "0:0:9.81")
            sensor("gyroscope", "0:0:0")
        except Exception as error:
            result["resetError"] = type(error).__name__ + ": " + str(error)
    return result
