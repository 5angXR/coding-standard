"""Profile discovery and mapping definitions for coding-standard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROFILE_ALIASES = {
    "embedded-c": "c",
}

AVAILABLE_PROFILES = ["common", "c", "rust", "python"]


@dataclass
class ProfileFileSpec:
    # Relative path in profiles/<profile>/ directory
    src_rel_path: str
    # Relative path in target project directory
    target_rel_path: str
    # Whether this file is a managed base file tracked by manifest
    is_base: bool = False
    # If this is a base file, the compiled output filename
    compiled_filename: str | None = None
    # If this is a base file, the optional override filename
    override_filename: str | None = None


# Profile definitions: which files belong to each profile
PROFILE_SPECS: dict[str, list[ProfileFileSpec]] = {
    "common": [
        ProfileFileSpec(
            src_rel_path=".editorconfig",
            target_rel_path=".editorconfig",
            is_base=False,
        ),
        ProfileFileSpec(
            src_rel_path="_typos.toml",
            target_rel_path="_typos.toml",
            is_base=False,
        ),
    ],
    "c": [
        ProfileFileSpec(
            src_rel_path=".clang-format.base",
            target_rel_path=".clang-format.base",
            is_base=True,
            compiled_filename=".clang-format",
            override_filename=".clang-format.override",
        ),
    ],
    "rust": [
        ProfileFileSpec(
            src_rel_path="rustfmt.base.toml",
            target_rel_path="rustfmt.base.toml",
            is_base=True,
            compiled_filename="rustfmt.toml",
            override_filename="rustfmt.override.toml",
        ),
    ],
    "python": [
        ProfileFileSpec(
            src_rel_path="ruff.base.toml",
            target_rel_path="ruff.base.toml",
            is_base=True,
            compiled_filename="ruff.toml",
        ),
        ProfileFileSpec(
            src_rel_path="ruff.toml",
            target_rel_path="ruff.toml",
            is_base=False,
        ),
    ],
}


def normalize_profile_name(name: str) -> str:
    """Normalize and alias profile names (e.g. embedded-c -> c)."""
    clean = name.strip().lower()
    return PROFILE_ALIASES.get(clean, clean)


def validate_profiles(names: list[str]) -> tuple[list[str], list[str]]:
    """Validate profile names. Returns (valid_normalized_names, invalid_names)."""
    valid: list[str] = []
    invalid: list[str] = []
    for raw in names:
        norm = normalize_profile_name(raw)
        if norm in AVAILABLE_PROFILES:
            if norm not in valid:
                valid.append(norm)
        else:
            invalid.append(raw)
    return valid, invalid


def get_profile_files(profile: str) -> list[ProfileFileSpec]:
    """Get list of file specs for a profile."""
    norm = normalize_profile_name(profile)
    return PROFILE_SPECS.get(norm, [])
