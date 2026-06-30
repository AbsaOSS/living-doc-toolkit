# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project scaffolding and directory structure
- Root pyproject.toml with Black, Mypy, and pytest configuration
- CHANGELOG.md following Keep a Changelog format
- Copyright header template for Python files
- Updated README.md with project overview and quickstart
- `packages/services/coverage_matrix` — new `living-doc-service-coverage-matrix` package
  - `loader.py` — I/O boundary: loads `doc-source.json` (bare array or envelope) and `ui-tests.json`
  - `matcher.py` — pure function: builds `CoverageMatrix` from parsed doc and test lists
  - `summary.py` — pure tallying: `compute_us_summary()` / `compute_summary()` (deprecated ACs excluded from `coverage_pct`)
  - `model/coverage_item.py` — output dataclasses serialising to `coverage-matrix.json`
  - `service.py` — orchestration with optional `--fail-under` threshold enforcement
  - `schema/coverage-matrix-v1.0.0-schema.json` — JSON Schema draft-07 for the output contract
- `living-doc coverage-matrix` CLI command (`apps/cli/src/living_doc_cli/commands/coverage_matrix.py`)
- `make py-qa-coverage` target for the new service package

### Changed

### Fixed

### Removed
