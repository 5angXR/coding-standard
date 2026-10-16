# Changelog

All notable changes to the `coding-standard` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-16

### Added
- Initial release of the multi-language coding standard repository.
- Shared engineering principles and code review guidelines in `docs/principles.md` and `docs/code-review.md`.
- Language-specific standards for C (with embedded development addendum), Rust (2021 edition), and Python (3.10+ modern style).
- Standard profile configurations:
  - `common`: `.editorconfig`
  - `c` (alias `embedded-c`): `.clang-format.base`
  - `rust`: `rustfmt.base.toml`
  - `python`: `ruff.base.toml` and `ruff.toml`
- Core tooling scripts in pure Python standard library:
  - `scripts/install.py`: Installs profiles, compiles bases, and generates `.coding-standard.toml` manifest.
  - `scripts/sync.py`: Upgrades managed base configs and regenerates target configs without overwriting local project overrides.
  - `scripts/check.py`: Verifies manifest integrity, profile validity, file hashes, and version alignment.
- Layered override mechanism:
  - Native `extend` support for Ruff.
  - `.base` + `.override` compilation pipeline for clang-format and rustfmt.
- Integration templates for pre-commit hooks and CI pipelines (GitHub Actions, GitLab CI).
- Comprehensive unit test suite with 100% standard library compliance.
