import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("lifecycle", Path(__file__).with_name("emulator-lifecycle.py"))
lifecycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lifecycle)


class LifecycleTest(unittest.TestCase):
    def test_empty_startup_state_reports_triage_before_the_original_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            adb = root / "adb"
            shutil.copy(Path(__file__).with_name("fixtures") / "fake-adb.py", adb)
            adb.write_text("#!" + sys.executable + "\n" + adb.read_text().split("\n", 1)[1])
            adb.chmod(0o755)
            result = subprocess.run([sys.executable, str(Path(__file__).with_name("emulator-lifecycle.py")),
                                     "--serial", "emulator-5554", "--start-cycle", "96", "--cycles", "1"],
                                    env=dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"]),
                                    capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Timed out: dev.antishake.fixture.control: {}", result.stderr)
            rows = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["state"], {})
            self.assertEqual(rows[0]["diagnostic"]["exitInfo"], "diagnostic snapshot")
            self.assertIn("crashLog", rows[0]["diagnostic"])

    def test_five_chunks_are_exactly_the_original_100_cycle_plan(self):
        whole = lifecycle.cycle_plan(1, 100)
        chunks = [row for start in (1, 21, 41, 61, 81)
                  for row in lifecycle.cycle_plan(start, 20)]
        self.assertEqual(chunks, whole)
        self.assertEqual([row["cycle"] for row in whole], list(range(1, 101)))
        for kind in ("cold", "warm", "background", "ad", "normal"):
            self.assertEqual(sum(row["kind"] == kind for row in whole), 20)
        self.assertEqual([row["scenario"] for row in whole if row["kind"] == "ad"],
                         ["ad", "delayed", "missing"] * 6 + ["ad", "delayed"])

    def test_invalid_or_out_of_range_chunks_are_rejected(self):
        for start, count in ((0, 20), (1, 0), (-1, 20), (81, 21), (101, 1)):
            with self.subTest(start=start, count=count), self.assertRaises(ValueError):
                lifecycle.cycle_plan(start, count)

    def protected(self):
        return {"screen": "PROBE", "navigated": "false", "resumes": "2", "hook": "true",
                "events": "0", "sensorCount": "0", "lightAvailable": "true",
                "lightEvents": "2", "lastLight": "207.0"}

    def test_missing_hook_cannot_pass_with_zero_motion_events(self):
        before = {"screen": "PROBE", "navigated": "false", "resumes": "1"}
        after = dict(before, hook="false", events="0", sensorCount="0",
                     lightAvailable="true", lightEvents="1", lastLight="201.0")
        with self.assertRaisesRegex(AssertionError, "Module not loaded"):
            lifecycle.check_motion(before, after, True, 201, 1)

    def test_protected_resume_passes_only_with_fresh_light_and_no_motion(self):
        state = self.protected()
        lifecycle.check_motion(state, state, True, 207, 2)
        for field, invalid in [("lastLight", "206.0"), ("resumes", "1"),
                               ("events", "1"), ("sensorCount", "1"),
                               ("screen", "TARGET"), ("navigated", "true"),
                               ("lightAvailable", "false"), ("lightEvents", "0")]:
            with self.subTest(field=field), self.assertRaises(AssertionError):
                lifecycle.check_motion(state, dict(state, **{field: invalid}), True, 207, 2)

    def test_control_must_actually_navigate_on_motion(self):
        before = self.protected()
        after = dict(before, hook="false", screen="TARGET", navigated="true", events="4", sensorCount="2")
        lifecycle.check_motion(before, after, False, 207, 2)
        for field, invalid in [("hook", "true"), ("events", "0"), ("sensorCount", "0"),
                               ("screen", "PROBE"), ("navigated", "false")]:
            with self.subTest(field=field), self.assertRaises(AssertionError):
                lifecycle.check_motion(before, dict(after, **{field: invalid}), False, 207, 2)

    def test_warm_and_background_cycles_must_not_hide_a_process_restart(self):
        for kind in ("warm", "background"):
            lifecycle.check_process(kind, "101", "101")
            with self.subTest(kind=kind), self.assertRaises(AssertionError):
                lifecycle.check_process(kind, "101", "202")
        lifecycle.check_process("cold", "101", "202")
        with self.assertRaises(AssertionError):
            lifecycle.check_process("cold", "101", "101")
        for dead in ("", None):
            with self.subTest(pid=dead), self.assertRaises(AssertionError):
                lifecycle.check_process("warm", "101", dead)

    def test_normal_page_and_completed_ad_are_rechecked_after_settling(self):
        normal = {"hook": "true", "screen": "MAIN", "close": "NONE", "normalClicks": "0", "navigated": "false"}
        lifecycle.check_page(normal, "normal")
        lifecycle.check_page(dict(normal, close="CLOSED"), "ad")
        lifecycle.check_page(dict(normal, close="RETURNED"), "missing")
        for field, invalid in [("screen", "AD"), ("close", "RETURNED"),
                               ("normalClicks", "1"), ("navigated", "true"), ("hook", "false")]:
            with self.subTest(field=field), self.assertRaises(AssertionError):
                lifecycle.check_page(dict(normal, **{field: invalid}), "normal")


if __name__ == "__main__":
    unittest.main()
