"""Unit tests for scripts/lib/profiles.py."""

import unittest

from scripts.lib.profiles import (
    AVAILABLE_PROFILES,
    get_profile_files,
    normalize_profile_name,
    validate_profiles,
)


class TestProfiles(unittest.TestCase):
    def test_normalize_profile_name(self):
        self.assertEqual(normalize_profile_name("embedded-c"), "c")
        self.assertEqual(normalize_profile_name("C"), "c")
        self.assertEqual(normalize_profile_name("RUST"), "rust")
        self.assertEqual(normalize_profile_name("python"), "python")

    def test_validate_profiles(self):
        valid, invalid = validate_profiles(["c", "embedded-c", "rust", "nonexistent"])
        self.assertIn("c", valid)
        self.assertIn("rust", valid)
        self.assertEqual(invalid, ["nonexistent"])
        # embedded-c normalized to c and deduplicated
        self.assertEqual(valid.count("c"), 1)

    def test_get_profile_files(self):
        c_files = get_profile_files("c")
        self.assertTrue(any(f.src_rel_path == ".clang-format.base" for f in c_files))
        self.assertFalse(any(f.src_rel_path == "c-naming.yml" for f in c_files))

        rust_files = get_profile_files("rust")
        self.assertTrue(any(f.src_rel_path == "rustfmt.base.toml" for f in rust_files))
        self.assertFalse(any(f.src_rel_path == "rust-naming.yml" for f in rust_files))

        python_files = get_profile_files("python")
        self.assertTrue(any(f.src_rel_path == "ruff.base.toml" for f in python_files))
        self.assertFalse(any(f.src_rel_path == "python-naming.yml" for f in python_files))

        common_files = get_profile_files("common")
        self.assertTrue(any(f.src_rel_path == ".editorconfig" for f in common_files))
        self.assertTrue(any(f.src_rel_path == "sgconfig.yml" for f in common_files))
        self.assertTrue(any(f.src_rel_path == "abbreviations.base.toml" for f in common_files))


if __name__ == "__main__":
    unittest.main()
