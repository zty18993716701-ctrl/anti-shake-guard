import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from crash_evidence import Evidence


class CrashEvidenceTest(unittest.TestCase):
    def fake_adb(self, root):
        adb = root / "adb"
        shutil.copy(Path(__file__).with_name("fixtures") / "fake-adb.py", adb)
        adb.write_text("#!" + sys.executable + "\n" + adb.read_text().split("\n", 1)[1])
        adb.chmod(0o755)
        return str(adb)

    def test_segment_keeps_unfiltered_logs_and_reports_capture_health(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with Evidence(root / "evidence", "phase", "emulator-5554", adb=self.fake_adb(root)):
                with (root / "device.log").open("a") as log:
                    log.write("unrelated-tag: useful native diagnostic\n")
            report = json.loads((root / "evidence" / "phase" / "capture.json").read_text())
            self.assertTrue(report["complete"])
            self.assertIn("useful native diagnostic", (root / "evidence" / "phase" / "logcat-all.txt").read_text())
            self.assertTrue((root / "evidence" / "phase" / "logcat-crash.txt").exists())
            self.assertTrue((root / "evidence" / "phase" / "dropbox.txt").exists())

    def test_lost_tail_is_incomplete_not_a_clean_crash_record(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "lose-end").touch()
            with self.assertRaisesRegex(AssertionError, "Incomplete"):
                with Evidence(root / "evidence", "phase", "emulator-5554",
                              adb=self.fake_adb(root), marker_timeout=0.2):
                    pass
            report = json.loads((root / "evidence" / "phase" / "capture.json").read_text())
            self.assertFalse(report["complete"])

    def test_full_snapshot_can_cover_stream_only_marker_loss_without_replacing_raw_stream(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "stream-omit-end").touch()
            with Evidence(root / "evidence", "phase", "emulator-5554",
                          adb=self.fake_adb(root), marker_timeout=0.2):
                with (root / "device.log").open("a") as log:
                    log.write("unrelated-tag: preserved record\n")
            evidence = root / "evidence" / "phase"
            report = json.loads((evidence / "capture.json").read_text())
            self.assertTrue(report["complete"])
            self.assertEqual(report["coverage_file"], "logcat-snapshot.txt")
            self.assertIn("END", report["stream_warning"])
            self.assertNotIn(":END", (evidence / "logcat-all.txt").read_text())
            self.assertIn(":END", (evidence / "logcat-snapshot.txt").read_text())
            self.assertIn("preserved record", (evidence / "logcat-snapshot.txt").read_text())

    def test_missing_native_dumps_fail_capture_but_do_not_mask_primary_error(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "deny-tombstones").touch()
            adb = self.fake_adb(root)
            with self.assertRaisesRegex(AssertionError, "Incomplete"):
                with Evidence(root / "evidence", "missing", "emulator-5554", adb=adb):
                    pass
            with self.assertRaisesRegex(ValueError, "primary"):
                with Evidence(root / "evidence", "failed", "emulator-5554", adb=adb):
                    raise ValueError("primary")
            report = json.loads((root / "evidence" / "failed" / "capture.json").read_text())
            self.assertFalse(report["complete"])
            self.assertFalse(report["operation_succeeded"])

    def test_snapshot_with_markers_cannot_cover_records_it_lost(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "stream-omit-end").touch()
            (root / "snapshot-loses-record").touch()
            with self.assertRaisesRegex(AssertionError, "Incomplete"):
                with Evidence(root / "evidence", "phase", "emulator-5554",
                              adb=self.fake_adb(root), marker_timeout=0.2):
                    with (root / "device.log").open("a") as log:
                        log.write("unrelated-tag: missing from snapshot\n")
            report = json.loads((root / "evidence" / "phase" / "capture.json").read_text())
            self.assertFalse(report["complete"])

    def test_crash_only_in_complete_snapshot_still_fails_the_segment(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "stream-omit-end").touch()
            with self.assertRaisesRegex(AssertionError, "Unexpected fixture crash"):
                with Evidence(root / "evidence", "phase", "emulator-5554",
                              adb=self.fake_adb(root), marker_timeout=0.2):
                    with (root / "device.log").open("a") as log:
                        log.write("snapshot-only: Process: dev.antishake.guard, PID: 10\n")
            report = json.loads((root / "evidence" / "phase" / "capture.json").read_text())
            self.assertEqual(report["coverage_file"], "logcat-snapshot.txt")
            self.assertFalse(report["complete"])

    def test_java_native_and_anr_are_rejected_outside_calibration(self):
        for line in ("Process: dev.antishake.guard, PID: 10",
                     ">>> dev.antishake.fixture.control <<<", "ANR in dev.antishake.fixture.protectedapp"):
            with self.subTest(line=line), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                with self.assertRaisesRegex(AssertionError, "Unexpected fixture crash"):
                    with Evidence(root / "evidence", "phase", "emulator-5554", adb=self.fake_adb(root)):
                        with (root / "device.log").open("a") as log:
                            log.write(line + "\n")

    def test_calibration_crash_is_retained_but_not_reported_as_product_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with Evidence(root / "evidence", "calibration", "emulator-5554",
                          adb=self.fake_adb(root), allow_crash=True):
                with (root / "device.log").open("a") as log:
                    log.write("Process: dev.antishake.guard, PID: 10\n")
            self.assertIn("Process: dev.antishake.guard", (root / "evidence" / "calibration" / "logcat-all.txt").read_text())

    def test_preinitialized_native_process_is_identified_by_system_crash_event(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaisesRegex(AssertionError, "Unexpected fixture crash"):
                with Evidence(root / "evidence", "phase", "emulator-5554", adb=self.fake_adb(root)):
                    with (root / "device.log").open("a") as log:
                        log.write("F DEBUG : pid: 7020, tid: 7024 >>> <pre-initialized> <<<\n"
                                  "I am_crash: [590,0,dev.antishake.fixture.protectedapp,547896902,Native crash,Segmentation fault,unknown,0,0]\n")

    def test_old_or_other_package_system_crash_is_not_assigned_to_this_segment(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "device.log").write_text("I am_crash: [590,0,dev.antishake.fixture.protectedapp,1,Native crash]\n")
            with Evidence(root / "evidence", "phase", "emulator-5554", adb=self.fake_adb(root)):
                with (root / "device.log").open("a") as log:
                    log.write("I am_crash: [590,0,dev.antishake.fixture.protectedapp.other,1,Native crash]\n")

    def test_physical_device_is_rejected_before_any_adb_operation(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            Evidence(folder, "phase", "physical-phone")

    def test_empty_required_snapshot_is_not_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "empty-dropbox").touch()
            with self.assertRaisesRegex(AssertionError, "empty"):
                with Evidence(root / "evidence", "phase", "emulator-5554", adb=self.fake_adb(root)):
                    pass


if __name__ == "__main__":
    unittest.main()
