"""Unit tests for scripts/sync.py."""

import tempfile
import unittest
from pathlib import Path

from scripts.install import install_profiles
from scripts.lib.manifest import compute_sha256, load_manifest, save_manifest
from scripts.sync import sync_project


class TestSync(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target_dir = Path(self.temp_dir.name) / "project"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sync_without_manifest_fails(self):
        self.target_dir.mkdir(parents=True, exist_ok=True)
        code = sync_project(self.target_dir)
        self.assertNotEqual(code, 0)

    def test_sync_unmodified_files(self):
        install_profiles(self.target_dir, ["c"])

        # Manually alter manifest version to pretend it was an older version
        manifest = load_manifest(self.target_dir)
        self.assertIsNotNone(manifest)
        assert manifest is not None
        manifest.version = "0.0.1"
        save_manifest(self.target_dir, manifest)

        code = sync_project(self.target_dir)
        self.assertEqual(code, 0)

        # Version must be refreshed
        refreshed = load_manifest(self.target_dir)
        self.assertIsNotNone(refreshed)
        assert refreshed is not None
        self.assertNotEqual(refreshed.version, "0.0.1")

    def test_sync_detects_conflict_without_force(self):
        install_profiles(self.target_dir, ["c"])

        # User modifies .clang-format.base
        base_file = self.target_dir / ".clang-format.base"
        base_file.write_text("# user manually modified this line\n", encoding="utf-8")

        # Sync without force
        code = sync_project(self.target_dir, force=False)
        self.assertEqual(code, 0)

        # Local modification must be preserved!
        self.assertEqual(base_file.read_text(encoding="utf-8"), "# user manually modified this line\n")

    def test_sync_force_overwrites_conflict(self):
        install_profiles(self.target_dir, ["c"])

        base_file = self.target_dir / ".clang-format.base"
        base_file.write_text("# user manually modified this line\n", encoding="utf-8")

        # Sync with force
        code = sync_project(self.target_dir, force=True)
        self.assertEqual(code, 0)

        # Must be overwritten by standard version
        self.assertIn("BasedOnStyle: LLVM", base_file.read_text(encoding="utf-8"))

    def test_sync_recompiles_with_project_override(self):
        install_profiles(self.target_dir, ["c"])

        # Create a local override
        override_file = self.target_dir / ".clang-format.override"
        override_file.write_text("ColumnLimit: 140\n", encoding="utf-8")

        code = sync_project(self.target_dir)
        self.assertEqual(code, 0)

        compiled_file = self.target_dir / ".clang-format"
        self.assertTrue(compiled_file.exists())
        self.assertIn("ColumnLimit: 140", compiled_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
