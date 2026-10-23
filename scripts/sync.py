#!/usr/bin/env python3
"""sync.py - Synchronize and update coding-standard configurations in a target project."""

from __future__ import annotations

import argparse
import datetime
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.compiler import (
    compile_ast_grep_rules,
    compile_clang_format,
    compile_ruff,
    compile_rustfmt,
)
from scripts.lib.manifest import (
    ManagedFile,
    compute_sha256,
    load_manifest,
    save_manifest,
)
from scripts.lib.profiles import get_profile_files


def get_current_version() -> str:
    version_file = REPO_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.1.0"


def safe_rel_path(target_dir: Path, rel_str: str) -> Path:
    resolved_target = target_dir.resolve()
    dest = (target_dir / rel_str).resolve()
    if not str(dest).startswith(str(resolved_target)):
        raise ValueError(f"Path traversal detected: {rel_str} escapes {target_dir}")
    return dest


def sync_project(target_dir: Path, force: bool = False) -> int:
    target_dir = target_dir.resolve()
    if not target_dir.exists():
        print(f"[ERROR] Target directory does not exist: {target_dir}", file=sys.stderr)
        return 1

    manifest = load_manifest(target_dir)
    if manifest is None:
        print(
            f"[ERROR] No .coding-standard.toml found in {target_dir}. Run install.py first.",
            file=sys.stderr,
        )
        return 1

    current_version = get_current_version()
    old_version = manifest.version
    print(f"[sync] Synchronizing target: {target_dir}")
    print(f"[sync] Version in project: v{old_version} -> Current standard: v{current_version}")
    print(f"[sync] Active profiles: {', '.join(manifest.profiles)}")

    profiles_dir = REPO_ROOT / "profiles"
    updated_files: list[str] = []
    conflict_files: list[str] = []
    missing_in_repo: list[str] = []

    # Iterate through all profiles recorded in project
    for profile in manifest.profiles:
        specs = get_profile_files(profile)
        for spec in specs:
            src_file = profiles_dir / profile / spec.src_rel_path
            if not src_file.exists():
                missing_in_repo.append(str(src_file))
                continue

            try:
                dest_file = safe_rel_path(target_dir, spec.target_rel_path)
            except ValueError as e:
                print(f"[ERROR] {e}", file=sys.stderr)
                return 1

            # Skip ruff.toml sync (project wrapper)
            if spec.target_rel_path == "ruff.toml" and dest_file.exists():
                continue

            existing_entry = manifest.get_file(spec.target_rel_path)
            src_sha = compute_sha256(src_file)

            if dest_file.exists():
                curr_sha = compute_sha256(dest_file)
                # If file exists and manifest has record, check if user modified it
                if existing_entry is not None and existing_entry.sha256 != curr_sha:
                    if not force:
                        conflict_files.append(
                            f"{spec.target_rel_path} (locally modified, checksum mismatch with manifest; use --force to overwrite)"
                        )
                        continue
                    else:
                        print(f"[sync] Force overwriting locally modified file: {spec.target_rel_path}")

            # Safe update
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            new_sha = compute_sha256(dest_file)

            manifest.upsert_file(
                ManagedFile(
                    path=spec.target_rel_path,
                    profile=profile,
                    sha256=new_sha,
                    is_base=spec.is_base,
                )
            )
            updated_files.append(spec.target_rel_path)

            # Re-compile base outputs with project overrides
            if spec.is_base:
                if profile == "c":
                    compiled_file = target_dir / spec.compiled_filename
                    override_file = target_dir / spec.override_filename if spec.override_filename else None
                    compile_clang_format(dest_file, override_file, compiled_file)
                    updated_files.append(f"{spec.compiled_filename} (recompiled)")
                elif profile == "rust":
                    compiled_file = target_dir / spec.compiled_filename
                    override_file = target_dir / spec.override_filename if spec.override_filename else None
                    compile_rustfmt(dest_file, override_file, compiled_file)
                    updated_files.append(f"{spec.compiled_filename} (recompiled)")
                elif profile == "python":
                    default_ruff = profiles_dir / "python" / "ruff.toml"
                    compile_ruff(dest_file, default_ruff, target_dir)
                elif profile == "common":
                    compiled_file = target_dir / spec.compiled_filename
                    override_file = target_dir / spec.override_filename if spec.override_filename else None
                    active_langs = [p for p in manifest.profiles if p in ("c", "rust", "python")]
                    compile_ast_grep_rules(dest_file, override_file, compiled_file, languages=active_langs or None)
                    updated_files.append(f"{spec.compiled_filename} (recompiled)")

    # Refresh manifest version and timestamp
    manifest.version = current_version
    manifest.updated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_manifest(target_dir, manifest)

    # Report results
    print("\n[sync] Sync finished.")
    if updated_files:
        print("Updated / Recompiled files:")
        for f in sorted(set(updated_files)):
            print(f"  + {f}")
    if conflict_files:
        print("\n[WARNING] Conflicts detected (preserved without overwriting):", file=sys.stderr)
        for f in conflict_files:
            print(f"  ! {f}", file=sys.stderr)
        print("Hint: If you wish to overwrite your local modifications, run with --force.", file=sys.stderr)
        print("Hint: To preserve custom rules permanently, put them in .override files.", file=sys.stderr)
    if missing_in_repo:
        print("\n[WARNING] Files missing in standard repo:", file=sys.stderr)
        for f in missing_in_repo:
            print(f"  ? {f}", file=sys.stderr)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync coding-standard configuration files in target project with repository version.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/sync.py --target ../my_project
  python scripts/sync.py --target ../my_project --force
""",
    )
    parser.add_argument(
        "-t",
        "--target",
        dest="target",
        required=True,
        help="Target project directory path to sync.",
    )
    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Force overwrite locally modified managed files.",
    )

    args = parser.parse_args()
    return sync_project(Path(args.target), force=args.force)


if __name__ == "__main__":
    sys.exit(main())
