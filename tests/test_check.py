"""Unit tests for scripts/check.py."""

import tempfile
import unittest
from pathlib import Path

from scripts.check import check_project
from scripts.install import install_profiles
from scripts.lib.manifest import MANIFEST_FILENAME


class TestCheck(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target_dir = Path(self.temp_dir.name) / "project"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_check_nonexistent_directory(self):
        code = check_project(self.target_dir)
        self.assertNotEqual(code, 0)

    def test_check_missing_manifest(self):
        self.target_dir.mkdir(parents=True, exist_ok=True)
        code = check_project(self.target_dir)
        self.assertNotEqual(code, 0)

    def test_check_corrupted_manifest(self):
        self.target_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.target_dir / MANIFEST_FILENAME
        manifest_path.write_text("invalid [[ toml syntax = {", encoding="utf-8")
        code = check_project(self.target_dir)
        self.assertNotEqual(code, 0)

    def test_check_healthy_project(self):
        install_profiles(self.target_dir, ["c", "rust"])
        code = check_project(self.target_dir)
        self.assertEqual(code, 0)

    def test_check_missing_managed_file(self):
        install_profiles(self.target_dir, ["c"])
        (self.target_dir / ".clang-format.base").unlink()

        code = check_project(self.target_dir)
        self.assertNotEqual(code, 0)

    def test_check_modified_managed_file_fails(self):
        install_profiles(self.target_dir, ["c"])
        base_file = self.target_dir / ".clang-format.base"
        base_file.write_text("IndentWidth: 8\n", encoding="utf-8")

        code = check_project(self.target_dir)
        self.assertNotEqual(code, 0)

    def test_check_missing_compiled_file_fails(self):
        install_profiles(self.target_dir, ["c"])
        (self.target_dir / ".clang-format").unlink()

        code = check_project(self.target_dir)
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
