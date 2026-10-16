"""Unit tests for scripts/lib/manifest.py."""

import tempfile
import unittest
from pathlib import Path

from scripts.lib.manifest import (
    MANIFEST_FILENAME,
    ManagedFile,
    Manifest,
    _parse_simple_toml,
    compute_sha256,
    load_manifest,
    save_manifest,
)


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compute_sha256(self):
        test_file = self.target_dir / "sample.txt"
        test_file.write_text("hello coding standard\n", encoding="utf-8")
        sha = compute_sha256(test_file)
        self.assertIsInstance(sha, str)
        self.assertEqual(len(sha), 64)

        # Same content produces same sha
        test_file2 = self.target_dir / "sample2.txt"
        test_file2.write_text("hello coding standard\n", encoding="utf-8")
        self.assertEqual(sha, compute_sha256(test_file2))

    def test_save_and_load_manifest(self):
        m = Manifest(version="0.1.0", profiles=["common", "c"])
        m.upsert_file(
            ManagedFile(
                path=".editorconfig",
                profile="common",
                sha256="abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
                is_base=False,
            )
        )
        m.upsert_file(
            ManagedFile(
                path=".clang-format.base",
                profile="c",
                sha256="1111222233334444111122223333444411112222333344441111222233334444",
                is_base=True,
            )
        )
        save_manifest(self.target_dir, m)

        manifest_file = self.target_dir / MANIFEST_FILENAME
        self.assertTrue(manifest_file.exists())

        loaded = load_manifest(self.target_dir)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.version, "0.1.0")
        self.assertEqual(loaded.repository, "coding-standard")
        self.assertEqual(loaded.profiles, ["common", "c"])
        self.assertEqual(len(loaded.files), 2)

        f0 = loaded.get_file(".editorconfig")
        self.assertIsNotNone(f0)
        assert f0 is not None
        self.assertEqual(f0.profile, "common")
        self.assertFalse(f0.is_base)

        f1 = loaded.get_file(".clang-format.base")
        self.assertIsNotNone(f1)
        assert f1 is not None
        self.assertTrue(f1.is_base)

    def test_load_nonexistent_manifest(self):
        self.assertIsNone(load_manifest(self.target_dir))

    def test_fallback_parser(self):
        toml_sample = """
version = "0.2.0"
repository = "custom-repo"
profiles = ["common", "rust"]

[[files]]
path = "rustfmt.base.toml"
profile = "rust"
sha256 = "deadbeef"
is_base = true
"""
        parsed = _parse_simple_toml(toml_sample)
        self.assertEqual(parsed["version"], "0.2.0")
        self.assertEqual(parsed["repository"], "custom-repo")
        self.assertEqual(parsed["profiles"], ["common", "rust"])
        self.assertEqual(len(parsed["files"]), 1)
        self.assertEqual(parsed["files"][0]["path"], "rustfmt.base.toml")
        self.assertTrue(parsed["files"][0]["is_base"])


if __name__ == "__main__":
    unittest.main()
