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


LANGUAGE_CONFIGS: dict[str, dict[str, list[str]]] = {
    "c": {
        "exclude_kinds": ["preproc_include"],
        "exclude_patterns": ["^(__builtin_)"],
    },
    "rust": {
        "exclude_kinds": ["use_declaration"],
        "exclude_patterns": [],
    },
    "python": {
        "exclude_kinds": ["import_statement", "import_from_statement"],
        "exclude_patterns": [],
    },
}


def compile_ast_grep_rules(
    base_file: Path,
    override_file: Path | None,
    output_file: Path,
    languages: list[str] | tuple[str, ...] | None = None,
) -> None:
    """Compile abbreviations.base.toml + optional abbreviations.override.toml -> naming.yml."""
    base_content = base_file.read_text(encoding="utf-8")
    raw_abbrs = _parse_toml_key_values(base_content)
    abbr_map: dict[str, str] = {
        k.strip(): v.strip().strip("\"'") for k, v in raw_abbrs.items()
    }

    if override_file is not None and override_file.exists():
        override_content = override_file.read_text(encoding="utf-8")
        raw_overrides = _parse_toml_key_values(override_content)
        for k, v in raw_overrides.items():
            val = v.strip().strip("\"'")
            if not val or val.lower() in ("false", "disabled", "none", "null"):
                abbr_map.pop(k.strip(), None)
            else:
                abbr_map[k.strip()] = val

    target_langs = (
        [lang for lang in languages if lang in LANGUAGE_CONFIGS]
        if languages
        else list(LANGUAGE_CONFIGS.keys())
    )

    docs: list[str] = []
    for lang in target_langs:
        cfg = LANGUAGE_CONFIGS[lang]
        exclude_kinds = cfg.get("exclude_kinds", [])
        exclude_patterns = cfg.get("exclude_patterns", [])

        exclude_kind_block = ""
        if exclude_kinds:
            kind_lines = "\n".join(f"            - kind: {k}" for k in exclude_kinds)
            exclude_kind_block = f"""    - not:
        inside:
          any:
{kind_lines}
          stopBy: end\n"""

        exclude_pattern_block = ""
        for pat in exclude_patterns:
            exclude_pattern_block += f"""    - not:
        regex: "{pat}"\n"""

        for full, abbr in sorted(abbr_map.items()):
            rule_yaml = f"""id: {lang}-naming-{full}
language: {lang}
severity: warning
message: "标识符 '$NAME' 包含 '{full}'，建议缩写为 '{abbr}'"
rule:
  all:
    - kind: identifier
      pattern: $NAME
    - regex: "(?i)({full})"
{exclude_kind_block}{exclude_pattern_block}""".rstrip()
            docs.append(rule_yaml)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n---\n".join(docs) + "\n", encoding="utf-8")

