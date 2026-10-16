#!/usr/bin/env python3
"""check.py - Verify standard configuration integrity and manifest compliance in a target project."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.manifest import (
    MANIFEST_FILENAME,
    compute_sha256,
    load_manifest,
)
from scripts.lib.profiles import AVAILABLE_PROFILES, get_profile_files


def get_current_version() -> str:
    version_file = REPO_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.1.0"


def check_project(target_dir: Path) -> int:
    target_dir = target_dir.resolve()
    if not target_dir.exists():
        print(f"[FAIL] Target directory does not exist: {target_dir}", file=sys.stderr)
        return 1

    manifest_path = target_dir / MANIFEST_FILENAME
    if not manifest_path.exists():
        print(
            f"[FAIL] Manifest {MANIFEST_FILENAME} missing in {target_dir}.\n"
            f"Fix: Run `python scripts/install.py --profile <profile> --target {target_dir}` to initialize.",
            file=sys.stderr,
        )
        return 1

    try:
        manifest = load_manifest(target_dir)
    except Exception as e:
        print(f"[FAIL] Failed to parse {MANIFEST_FILENAME}: {e}", file=sys.stderr)
        return 1

    if manifest is None:
        print(f"[FAIL] Invalid manifest content in {manifest_path}", file=sys.stderr)
        return 1

    issues: list[str] = []
    warnings: list[str] = []
    checks_passed = 0

    repo_version = get_current_version()
    if manifest.version != repo_version:
        warnings.append(
            f"Standard version mismatch: project has v{manifest.version}, repo is at v{repo_version}.\n"
            f"     Fix: Run `python scripts/sync.py --target {target_dir}` to update."
        )

    # Validate profiles
    for p in manifest.profiles:
        if p not in AVAILABLE_PROFILES:
            issues.append(f"Invalid profile recorded in manifest: '{p}' (valid: {AVAILABLE_PROFILES})")
        else:
            checks_passed += 1

    # Check managed files
    if not manifest.files:
        issues.append("No managed files listed in manifest.")

    for f_entry in manifest.files:
        f_path = target_dir / f_entry.path
        if not f_path.exists():
            issues.append(
                f"Missing managed file: {f_entry.path} (profile: {f_entry.profile})\n"
                f"     Fix: Run `python scripts/sync.py --target {target_dir}` to restore."
            )
            continue

        # Check checksum
        actual_sha = compute_sha256(f_path)
        if actual_sha != f_entry.sha256:
            issues.append(
                f"Checksum mismatch for {f_entry.path}.\n"
                f"     Expected: {f_entry.sha256}\n"
                f"     Actual:   {actual_sha}\n"
                f"     Fix: Use .override files for custom rules, or run `sync.py --force` to overwrite."
            )
        else:
            checks_passed += 1

    # Check that compiled output files exist for profiles
    for profile in manifest.profiles:
        specs = get_profile_files(profile)
        for spec in specs:
            if spec.is_base and spec.compiled_filename:
                compiled_path = target_dir / spec.compiled_filename
                if not compiled_path.exists():
                    issues.append(
                        f"Compiled configuration missing: {spec.compiled_filename} (from {spec.src_rel_path})\n"
                        f"     Fix: Run `python scripts/sync.py --target {target_dir}` to generate."
                    )
                else:
                    checks_passed += 1

    print(f"\n--- Coding Standard Integrity Check: {target_dir.name} ---")
    print(f"Project Standard Version: v{manifest.version} (Standard Repo: v{repo_version})")
    print(f"Active Profiles: {', '.join(manifest.profiles)}")
    print(f"Checks passed: {checks_passed}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  [WARN] {w}")

    if issues:
        print("\nFailures detected:", file=sys.stderr)
        for issue in issues:
            print(f"  [FAIL] {issue}", file=sys.stderr)
        return 1

    print("\n[PASS] All coding standard integrity checks passed successfully.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check coding-standard configuration integrity in a target project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/check.py --target ../my_project
""",
    )
    parser.add_argument(
        "-t",
        "--target",
        dest="target",
        required=True,
        help="Target project directory path to check.",
    )

    args = parser.parse_args()
    return check_project(Path(args.target))


if __name__ == "__main__":
    sys.exit(main())
