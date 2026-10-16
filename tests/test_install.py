"""Unit tests for scripts/install.py."""

import tempfile
import unittest
from pathlib import Path

from scripts.install import install_profiles, safe_rel_path
from scripts.lib.manifest import MANIFEST_FILENAME, load_manifest


class TestInstall(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target_dir = Path(self.temp_dir.name) / "project"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_single_profile_install(self):
        code = install_profiles(self.target_dir, ["c"])
        self.assertEqual(code, 0)

        # .coding-standard.toml should exist
        manifest = load_manifest(self.target_dir)
        self.assertIsNotNone(manifest)
        assert manifest is not None
        self.assertIn("common", manifest.profiles)
        self.assertIn("c", manifest.profiles)

        # Expected files exist
        self.assertTrue((self.target_dir / ".editorconfig").exists())
        self.assertTrue((self.target_dir / ".clang-format.base").exists())
        self.assertTrue((self.target_dir / ".clang-format").exists())

    def test_multiple_profile_install(self):
        code = install_profiles(self.target_dir, ["rust", "python"])
        self.assertEqual(code, 0)

        manifest = load_manifest(self.target_dir)
        self.assertIsNotNone(manifest)
        assert manifest is not None
        self.assertIn("rust", manifest.profiles)
        self.assertIn("python", manifest.profiles)

        # Check rust files
        self.assertTrue((self.target_dir / "rustfmt.base.toml").exists())
        self.assertTrue((self.target_dir / "rustfmt.toml").exists())

        # Check python files
        self.assertTrue((self.target_dir / "ruff.base.toml").exists())
        self.assertTrue((self.target_dir / "ruff.toml").exists())

    def test_alias_embedded_c(self):
        code = install_profiles(self.target_dir, ["embedded-c"])
        self.assertEqual(code, 0)
        manifest = load_manifest(self.target_dir)
        self.assertIsNotNone(manifest)
        assert manifest is not None
        self.assertIn("c", manifest.profiles)
        self.assertTrue((self.target_dir / ".clang-format").exists())

    def test_invalid_profile(self):
        code = install_profiles(self.target_dir, ["invalid_lang"])
        self.assertNotEqual(code, 0)

    def test_do_not_silently_overwrite_unmanaged_file_without_force(self):
        self.target_dir.mkdir(parents=True, exist_ok=True)
        custom_editorconfig = self.target_dir / ".editorconfig"
        custom_editorconfig.write_text("# my custom editorconfig\n", encoding="utf-8")

        # Install without force
        code = install_profiles(self.target_dir, ["c"], force=False)
        self.assertEqual(code, 0)

        # Custom content must be preserved!
        self.assertEqual(custom_editorconfig.read_text(encoding="utf-8"), "# my custom editorconfig\n")

    def test_force_overwrite(self):
        self.target_dir.mkdir(parents=True, exist_ok=True)
        custom_editorconfig = self.target_dir / ".editorconfig"
        custom_editorconfig.write_text("# my custom editorconfig\n", encoding="utf-8")

        # Install with force
        code = install_profiles(self.target_dir, ["c"], force=True)
        self.assertEqual(code, 0)

        # Should now have the standard content
        self.assertIn("root = true", custom_editorconfig.read_text(encoding="utf-8"))

    def test_path_traversal_prevention(self):
        with self.assertRaises(ValueError):
            safe_rel_path(self.target_dir, "../../etc/passwd")


if __name__ == "__main__":
    unittest.main()
