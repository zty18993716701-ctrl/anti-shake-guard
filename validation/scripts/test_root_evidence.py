import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from root_evidence import capture


class EvidenceTest(unittest.TestCase):
    def test_timeout_keeps_partial_output_and_original_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "probe.txt"
            with self.assertRaises(subprocess.TimeoutExpired):
                capture([sys.executable, "-u", "-c", "import time; print('started'); time.sleep(5)"], output, 0.2)
            self.assertIn("started", output.read_text())
            self.assertIn("TIMEOUT", output.read_text())

    def test_best_effort_timeout_does_not_replace_primary_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(AssertionError, "primary"):
                try:
                    raise AssertionError("primary")
                finally:
                    capture([sys.executable, "-c", "import time; time.sleep(5)"],
                            Path(folder) / "logs.txt", 0.2, best_effort=True)

    def test_nonzero_exit_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            result = capture([sys.executable, "-c", "print('failed'); exit(7)"], Path(folder) / "logs.txt", 2)
            self.assertEqual(result.returncode, 7)
            self.assertIn("failed", result.stdout)


if __name__ == "__main__":
    unittest.main()
