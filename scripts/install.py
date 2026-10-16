#!/usr/bin/env python3
"""install.py - Install coding-standard configuration profiles into a target project."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# Add scripts directory to sys.path so scripts/lib can be imported directly
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.compiler import compile_clang_format, compile_ruff, compile_rustfmt
from scripts.lib.manifest import (
    ManagedFile,
    Manifest,
    compute_sha256,
    load_manifest,
    save_manifest,
)
from scripts.lib.profiles import (
    AVAILABLE_PROFILES,
    get_profile_files,
    normalize_profile_name,
    validate_profiles,
)


def get_current_version() -> str:
    version_file = REPO_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.1.0"


def safe_rel_path(target_dir: Path, rel_str: str) -> Path:
    """Validate against path traversal attacks."""
    resolved_target = target_dir.resolve()
    dest = (target_dir / rel_str).resolve()
    if not str(dest).startswith(str(resolved_target)):
        raise ValueError(f"Path traversal detected: {rel_str} escapes {target_dir}")
    return dest


def install_profiles(
    target_dir: Path,
    requested_profiles: list[str],
    force: bool = False,
) -> int:
    target_dir = target_dir.resolve()
    if not target_dir.exists():
        print(f"[install] Creating target directory: {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)

    # Validate profiles
    valid_profiles, invalid_profiles = validate_profiles(requested_profiles)
    if invalid_profiles:
        print(f"[ERROR] Invalid profile(s): {', '.join(invalid_profiles)}", file=sys.stderr)
        print(f"Available profiles: {', '.join(AVAILABLE_PROFILES)} (aliases: embedded-c -> c)", file=sys.stderr)
        return 1

    # 'common' profile is always included
    if "common" not in valid_profiles:
        valid_profiles.insert(0, "common")

    version = get_current_version()
    manifest = load_manifest(target_dir) or Manifest(version=version)
    manifest.version = version

    for p in valid_profiles:
        manifest.add_profile(p)

    installed_files: list[str] = []
    skipped_files: list[str] = []
    errors: list[str] = []

    profiles_dir = REPO_ROOT / "profiles"

    for profile in valid_profiles:
        file_specs = get_profile_files(profile)
        for spec in file_specs:
            src_file = profiles_dir / profile / spec.src_rel_path
            if not src_file.exists():
                errors.append(f"Source file missing in standard repo: {src_file}")
                continue

            try:
                dest_file = safe_rel_path(target_dir, spec.target_rel_path)
            except ValueError as e:
                errors.append(str(e))
                continue

            # Safety check: if destination already exists
            if dest_file.exists():
                existing_entry = manifest.get_file(spec.target_rel_path)
                curr_hash = compute_sha256(dest_file)
                is_modified = existing_entry is not None and existing_entry.sha256 != curr_hash
                is_unmanaged = existing_entry is None

                if (is_modified or is_unmanaged) and not force:
                    # Special exception: if target is ruff.toml and it exists, we don't overwrite it
                    if spec.target_rel_path == "ruff.toml":
                        skipped_files.append(f"{spec.target_rel_path} (exists, left untouched)")
                        continue
                    skipped_files.append(
                        f"{spec.target_rel_path} (already exists and has local changes; use --force to overwrite)"
                    )
                    continue

            # Copy file
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            new_sha = compute_sha256(dest_file)

            # Record in manifest if it is a managed file
            # For ruff.toml (the project-side wrapper), we don't track its SHA so user can freely edit
            if spec.target_rel_path != "ruff.toml":
                manifest.upsert_file(
                    ManagedFile(
                        path=spec.target_rel_path,
                        profile=profile,
                        sha256=new_sha,
                        is_base=spec.is_base,
                    )
                )
            installed_files.append(spec.target_rel_path)

            # Handle compilation for .base files
            if spec.is_base:
                if profile == "c":
                    compiled_file = target_dir / spec.compiled_filename
                    override_file = target_dir / spec.override_filename if spec.override_filename else None
                    compile_clang_format(dest_file, override_file, compiled_file)
                    installed_files.append(spec.compiled_filename)
                elif profile == "rust":
                    compiled_file = target_dir / spec.compiled_filename
                    override_file = target_dir / spec.override_filename if spec.override_filename else None
                    compile_rustfmt(dest_file, override_file, compiled_file)
                    installed_files.append(spec.compiled_filename)
                elif profile == "python":
                    default_ruff = profiles_dir / "python" / "ruff.toml"
                    compile_ruff(dest_file, default_ruff, target_dir)

    save_manifest(target_dir, manifest)

    # Print summary
    print(f"\n[coding-standard] Successfully installed profile(s): {', '.join(valid_profiles)} (v{version})")
    print(f"Target directory: {target_dir}")
    if installed_files:
        print("Installed/Generated files:")
        for f in sorted(set(installed_files)):
            print(f"  + {f}")
    if skipped_files:
        print("\nPreserved / Skipped files:")
        for f in skipped_files:
            print(f"  * {f}")
    if errors:
        print("\nErrors encountered:", file=sys.stderr)
        for err in errors:
            print(f"  ! {err}", file=sys.stderr)
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install coding-standard profiles into a target project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/install.py --profile c --target ../my_project
  python scripts/install.py --profile rust --target ../my_rust_app
  python scripts/install.py --profile c,python --target ../mixed_project
  python scripts/install.py --profile embedded-c --target ../firmware --force
""",
    )
    parser.add_argument(
        "-p",
        "--profile",
        dest="profiles",
        action="append",
        required=True,
        help="Profile(s) to install (e.g. c, embedded-c, rust, python). Can be specified multiple times or comma-separated.",
    )
    parser.add_argument(
        "-t",
        "--target",
        dest="target",
        required=True,
        help="Target project directory path.",
    )
    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Force overwrite existing unmanaged or modified files.",
    )

    args = parser.parse_args()

    # Flatten comma-separated profiles
    flat_profiles: list[str] = []
    for item in args.profiles:
        for p in item.split(","):
            if p.strip():
                flat_profiles.append(p.strip())

    target_path = Path(args.target)
    return install_profiles(target_path, flat_profiles, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
