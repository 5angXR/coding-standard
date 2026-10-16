"""Unit tests for scripts/lib/compiler.py."""

import tempfile
import unittest
from pathlib import Path

from scripts.lib.compiler import (
    compile_clang_format,
    compile_ruff,
    compile_rustfmt,
)


class TestCompiler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compile_clang_format_without_override(self):
        base_file = self.work_dir / ".clang-format.base"
        base_file.write_text("IndentWidth: 4\nColumnLimit: 100\n...\n", encoding="utf-8")
        out_file = self.work_dir / ".clang-format"

        compile_clang_format(base_file, None, out_file)
        self.assertTrue(out_file.exists())
        content = out_file.read_text(encoding="utf-8")
        self.assertIn("IndentWidth: 4", content)
        self.assertIn("ColumnLimit: 100", content)

    def test_compile_clang_format_with_override(self):
        base_file = self.work_dir / ".clang-format.base"
        base_file.write_text("IndentWidth: 4\nColumnLimit: 100\n...\n", encoding="utf-8")

        override_file = self.work_dir / ".clang-format.override"
        override_file.write_text("ColumnLimit: 120\nTabWidth: 8\n", encoding="utf-8")

        out_file = self.work_dir / ".clang-format"
        compile_clang_format(base_file, override_file, out_file)

        content = out_file.read_text(encoding="utf-8")
        self.assertIn("IndentWidth: 4", content)
        self.assertIn("ColumnLimit: 120", content)
        self.assertNotIn("ColumnLimit: 100", content)
        self.assertIn("TabWidth: 8", content)

    def test_compile_rustfmt_with_override(self):
        base_file = self.work_dir / "rustfmt.base.toml"
        base_file.write_text('edition = "2021"\nmax_width = 100\n', encoding="utf-8")

        override_file = self.work_dir / "rustfmt.override.toml"
        override_file.write_text("max_width = 120\nhard_tabs = true\n", encoding="utf-8")

        out_file = self.work_dir / "rustfmt.toml"
        compile_rustfmt(base_file, override_file, out_file)

        content = out_file.read_text(encoding="utf-8")
        self.assertIn('edition = "2021"', content)
        self.assertIn("max_width = 120", content)
        self.assertNotIn("max_width = 100", content)
        self.assertIn("hard_tabs = true", content)

    def test_compile_ruff(self):
        base_file = self.work_dir / "ruff.base.toml"
        base_file.write_text("line-length = 100\n", encoding="utf-8")
        default_ruff = self.work_dir / "default_ruff.toml"
        default_ruff.write_text('extend = "ruff.base.toml"\n', encoding="utf-8")

        compile_ruff(base_file, default_ruff, self.work_dir)
        target_ruff = self.work_dir / "ruff.toml"
        self.assertTrue(target_ruff.exists())
        self.assertIn('extend = "ruff.base.toml"', target_ruff.read_text(encoding="utf-8"))

        # If ruff.toml already exists, compile_ruff should not overwrite it
        target_ruff.write_text('extend = "ruff.base.toml"\nline-length = 110\n', encoding="utf-8")
        compile_ruff(base_file, default_ruff, self.work_dir)
        self.assertIn("line-length = 110", target_ruff.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
