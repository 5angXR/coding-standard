"""Compiler for combining .base configurations with project .override files."""

from __future__ import annotations

import re
from pathlib import Path


def _parse_yaml_key_values(content: str) -> dict[str, str]:
    """Parse top-level simple key-value pairs from YAML content."""
    kv: dict[str, str] = {}
    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#") or trimmed in ("---", "..."):
            continue
        # Match top-level key: value (not indented list items or nested blocks)
        match = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if match:
            key = match.group(1).strip()
            val = match.group(2).strip()
            kv[key] = val
    return kv


def _parse_toml_key_values(content: str) -> dict[str, str]:
    """Parse top-level simple key-value pairs from TOML content."""
    kv: dict[str, str] = {}
    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#") or trimmed.startswith("["):
            continue
        if "=" in line:
            key, val = (part.strip() for part in line.split("=", 1))
            kv[key] = val
    return kv


def compile_clang_format(
    base_file: Path,
    override_file: Path | None,
    output_file: Path,
) -> None:
    """Compile .clang-format.base + optional .clang-format.override -> .clang-format."""
    base_content = base_file.read_text(encoding="utf-8")

    if override_file is None or not override_file.exists():
        output_file.write_text(base_content, encoding="utf-8")
        return

    override_content = override_file.read_text(encoding="utf-8")
    overrides = _parse_yaml_key_values(override_content)

    new_lines: list[str] = []
    applied_keys: set[str] = set()

    for line in base_content.splitlines():
        match = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if match and match.group(1) in overrides:
            key = match.group(1)
            new_lines.append(f"{key}: {overrides[key]}")
            applied_keys.add(key)
        elif line.strip() == "..." and (set(overrides.keys()) - applied_keys):
            # Append extra keys before terminating ...
            new_lines.append("")
            new_lines.append("# --- Project Local Overrides (from .clang-format.override) ---")
            for k, v in overrides.items():
                if k not in applied_keys:
                    new_lines.append(f"{k}: {v}")
            new_lines.append("...")
        else:
            new_lines.append(line)

    # If ... was not found and there are still unapplied keys, append them
    remaining_keys = set(overrides.keys()) - applied_keys
    if remaining_keys and "..." not in base_content:
        new_lines.append("")
        new_lines.append("# --- Project Local Overrides (from .clang-format.override) ---")
        for k in remaining_keys:
            new_lines.append(f"{k}: {overrides[k]}")

    output_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def compile_rustfmt(
    base_file: Path,
    override_file: Path | None,
    output_file: Path,
) -> None:
    """Compile rustfmt.base.toml + optional rustfmt.override.toml -> rustfmt.toml."""
    base_content = base_file.read_text(encoding="utf-8")

    if override_file is None or not override_file.exists():
        output_file.write_text(base_content, encoding="utf-8")
        return

    override_content = override_file.read_text(encoding="utf-8")
    overrides = _parse_toml_key_values(override_content)

    new_lines: list[str] = []
    applied_keys: set[str] = set()

    for line in base_content.splitlines():
        trimmed = line.strip()
        if "=" in trimmed and not trimmed.startswith("#") and not trimmed.startswith("["):
            key = trimmed.split("=", 1)[0].strip()
            if key in overrides:
                new_lines.append(f"{key} = {overrides[key]}")
                applied_keys.add(key)
                continue
        new_lines.append(line)

    remaining_keys = set(overrides.keys()) - applied_keys
    if remaining_keys:
        new_lines.append("")
        new_lines.append("# --- Project Local Overrides (from rustfmt.override.toml) ---")
        for k in remaining_keys:
            new_lines.append(f"{k} = {overrides[k]}")

    output_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def compile_ruff(
    base_file: Path,
    default_ruff_file: Path,
    target_dir: Path,
) -> None:
    """Ensure ruff.base.toml is copied, and default ruff.toml is provided if not present."""
    # target_dir / ruff.base.toml is handled by file copier
    ruff_target = target_dir / "ruff.toml"
    if not ruff_target.exists():
        content = default_ruff_file.read_text(encoding="utf-8")
        ruff_target.write_text(content, encoding="utf-8")
