import subprocess
import unittest

from startup_diagnostic import diagnose


class StartupDiagnosticTest(unittest.TestCase):
    def run_probe(self, protected=False, restarted=False, dead=False, stale=False):
        calls = []
        phase = {"opened": False, "motion": False}

        def adb(*args):
            calls.append(args)
            if args[:2] == ("shell", "pidof"):
                if dead:
                    raise subprocess.CalledProcessError(1, args)
                return "202" if restarted and phase["opened"] else "101"
            if args[:3] == ("shell", "am", "start"):
                phase["opened"] = True
            if args[:4] == ("emu", "sensor", "set", "gyroscope") and args[-1] == "4:0:0":
                phase["motion"] = True
            if args[:3] == ("shell", "run-as", "dev.antishake.fixture.protectedapp"):
                moved = phase["motion"] and not protected
                page = "MAIN" if not phase["opened"] else ("TARGET" if moved else "PROBE")
                return "\n".join(["hook=false", "screen=" + page,
                                  "navigated=" + str(moved).lower(),
                                  "events=" + ("2" if moved else "0"),
                                  "sensorCount=" + ("0" if protected else "2"),
                                  "lightEvents=1", "lastLight=" + ("709.0" if stale else "710.0")])
            return "OK"

        return diagnose(adb, "dev.antishake.fixture.protectedapp", "101", 10,
                        pause=lambda _: None), calls

    def test_missing_marker_is_not_assumed_to_mean_missing_motion_protection(self):
        result, calls = self.run_probe(protected=True)
        self.assertEqual(result["outcome"], "motion-blocked-marker-false")
        self.assertEqual(result["beforePid"], "101")
        self.assertEqual(result["afterPid"], "101")
        self.assertEqual(result["original"]["screen"], "MAIN")
        self.assertFalse(any("force-stop" in call or "rm" in call for call in calls))

    def test_real_motion_navigation_in_the_same_failed_process_is_retained(self):
        result, _ = self.run_probe()
        self.assertEqual(result["outcome"], "motion-navigation-marker-false")
        self.assertEqual(result["after"]["screen"], "TARGET")
        self.assertEqual(result["afterPid"], "101")

    def test_restart_or_dead_process_is_inconclusive_not_a_protection_verdict(self):
        result, _ = self.run_probe(restarted=True)
        self.assertEqual(result["outcome"], "inconclusive")
        self.assertIn("process changed", result["error"])
        result, calls = self.run_probe(dead=True)
        self.assertEqual(result["outcome"], "inconclusive")
        self.assertFalse(any("start" in call for call in calls))

    def test_stale_light_cannot_be_mistaken_for_a_live_motion_probe(self):
        result, _ = self.run_probe(protected=True, stale=True)
        self.assertEqual(result["outcome"], "inconclusive")
        self.assertIn("did not become ready", result["error"])


if __name__ == "__main__":
    unittest.main()
