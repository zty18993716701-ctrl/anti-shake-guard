import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class EmbeddedSuiteTest(unittest.TestCase):
    def test_invalid_suite_is_rejected_before_downloading_or_using_adb(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            curl = root / "curl"
            curl.write_text("#!/bin/sh\necho unexpected-download >&2\nexit 93\n")
            curl.chmod(0o755)
            result = subprocess.run(["bash", str(Path(__file__).with_name("ci-lspatch.sh")), "invalid"],
                                    env=dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"]),
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("Unknown embedded suite: invalid", result.stderr)
            self.assertNotIn("unexpected-download", result.stderr)


if __name__ == "__main__":
    unittest.main()
