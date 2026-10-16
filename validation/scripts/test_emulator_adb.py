from pathlib import Path
import sys
import tempfile
import unittest

from emulator_adb import ensure_root


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


if __name__ == "__main__":
    unittest.main()
