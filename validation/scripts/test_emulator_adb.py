from pathlib import Path
import sys
import tempfile
import unittest

from emulator_adb import ensure_root, lock_rotation


class RootReadinessTest(unittest.TestCase):
    def fake(self, root):
        source = (Path(__file__).with_name("fixtures") / "fake-adb.py").read_text()
        adb = root / "adb"
        adb.write_text("#!" + sys.executable + "\n" + source.split("\n", 1)[1])
        adb.chmod(0o755)
        return str(adb)

    def test_closed_transport_is_retried_and_actual_root_is_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "root-closed").touch()
            ensure_root("emulator-5554", adb=self.fake(root))
            self.assertEqual("2", (root / "root-attempts").read_text())

    def test_unsupported_root_is_not_retried_as_transport_noise(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "deny-root").touch()
            with self.assertRaisesRegex(AssertionError, "production builds"):
                ensure_root("emulator-5554", adb=self.fake(root))
            self.assertEqual("1", (root / "root-attempts").read_text())

    def test_successful_root_command_without_uid_zero_still_fails_within_deadline(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "stay-shell").touch()
            with self.assertRaisesRegex(AssertionError, "UID=0"):
                ensure_root("emulator-5554", adb=self.fake(root), timeout=0.2)

    def test_phone_is_rejected(self):
        with self.assertRaises(ValueError):
            ensure_root("phone")

    def test_rotation_is_fixed_without_changing_sensor_access(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(lock_rotation("emulator-5554", adb=self.fake(root)),
                             {"accelerometer_rotation": "0", "user_rotation": "0"})
            self.assertEqual((root / "accelerometer_rotation").read_text(), "0")
            self.assertEqual((root / "user_rotation").read_text(), "0")
        with self.assertRaises(ValueError):
            lock_rotation("phone")

    def test_ignored_rotation_setting_is_not_reported_as_locked(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "ignore-rotation").touch()
            with self.assertRaisesRegex(AssertionError, "rotation"):
                lock_rotation("emulator-5554", adb=self.fake(root))


if __name__ == "__main__":
    unittest.main()
