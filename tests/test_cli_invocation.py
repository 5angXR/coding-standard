"""Integration tests for calling scripts from different working directories."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestCliInvocation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.project_dir = self.temp_path / "app"
        self.other_cwd = self.temp_path / "other_workdir"
        self.other_cwd.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_run_from_different_cwd(self):
        install_script = REPO_ROOT / "scripts" / "install.py"
        sync_script = REPO_ROOT / "scripts" / "sync.py"
        check_script = REPO_ROOT / "scripts" / "check.py"

        # 1. Run install from other_cwd
        proc = subprocess.run(
            [
                sys.executable,
                str(install_script),
                "--profile",
                "c,rust,python",
                "--target",
                str(self.project_dir),
            ],
            cwd=str(self.other_cwd),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, f"install.py failed:\n{proc.stderr}\n{proc.stdout}")

        # 2. Run check from other_cwd
        proc_check = subprocess.run(
            [
                sys.executable,
                str(check_script),
                "--target",
                str(self.project_dir),
            ],
            cwd=str(self.other_cwd),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_check.returncode, 0, f"check.py failed:\n{proc_check.stderr}\n{proc_check.stdout}")

        # 3. Run sync from other_cwd
        proc_sync = subprocess.run(
            [
                sys.executable,
                str(sync_script),
                "--target",
                str(self.project_dir),
            ],
            cwd=str(self.other_cwd),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_sync.returncode, 0, f"sync.py failed:\n{proc_sync.stderr}\n{proc_sync.stdout}")


if __name__ == "__main__":
    unittest.main()
