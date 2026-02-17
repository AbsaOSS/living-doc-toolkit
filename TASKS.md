# Living Documentation Toolkit — Implementation Roadmap

**Version:** 1.0  
**Last Updated:** 2026-01-23  
**Status:** Active

---

## Purpose

This document provides an actionable, phase-by-phase implementation roadmap for the Living Documentation Toolkit. Each task includes checkboxes for tracking progress, and all tasks reference specific tools, tests, and quality gates.

**Quality Standards:**
- All Python code must pass Pylint (≥ 9.5), Black formatting, and Mypy type checking
- All features must have unit tests with ≥ 80% coverage
- All services must have integration tests and verification scripts
- All changes must be documented in CHANGELOG.md

---

## Phase 1: Repository Structure & Scaffolding

**Goal:** Set up monorepo directory structure and core configuration files.

### Tasks

- [ ] **1.1 Create monorepo directory structure**
  - Create `packages/`, `apps/`, `docs/`, `outputs/` directories
  - Create subdirectories: `packages/datasets_pdf/`, `packages/core/`, `packages/adapters/collector_gh/`, `packages/services/normalize_issues/`, `apps/cli/`
  - Create `docs/cookbooks/`, `docs/recipes/`
  - **Verification:** Directory structure matches SPEC.md section 4.1

- [ ] **1.2 Configure root `pyproject.toml`**
  - Add `[tool.black]` with `line-length = 120`, `target-version = ['py314']`
  - Add `[tool.mypy]` with `check_untyped_defs = true`, `python_version = "3.14"`
  - Add `[tool.coverage.run]` with `omit = ["tests/*"]`
  - Add `[tool.pytest.ini_options]` with coverage thresholds
  - **Reference:** `living-doc-collector-gh/pyproject.toml`
  - **Verification:** Run `black --check .`, `mypy .` (should pass with no errors)

- [ ] **1.3 Configure `.gitignore`**
  - Add `outputs/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.coverage`, `*.egg-info/`, `dist/`, `build/`
  - Add `.venv/`, `.env`, `.DS_Store`
  - **Verification:** No ignored files tracked in Git

- [ ] **1.4 Update `README.md`**
  - Add project overview and purpose
  - Add quickstart installation instructions
  - Add link to SPEC.md and TASKS.md
  - Add example CLI usage
  - **Verification:** README renders correctly on GitHub

- [ ] **1.5 Verify Apache 2.0 License**
  - Ensure `LICENSE` file is present and correct
  - Add copyright headers to all Python files (template)
  - **Reference:** `living-doc-collector-gh` license headers

- [ ] **1.6 Create `CHANGELOG.md`**
  - Add template with `## [Unreleased]` section
  - Add sections: `Added`, `Changed`, `Fixed`, `Removed`
  - Follow [Keep a Changelog](https://keepachangelog.com/) format

---

## Phase 2: Dataset/Contract Package (`packages/datasets_pdf`)

**Goal:** Create versioned Pydantic models and JSON schemas for `pdf_ready` and `audit` contracts.

### Tasks

- [ ] **2.1 Set up package structure**
  - Create `packages/datasets_pdf/pyproject.toml`
  - Define package as `living-doc-datasets-pdf`
  - Add dependencies: `pydantic ^2.10.0`, `jsonschema ^4.20.0`
  - Create `src/living_doc_datasets_pdf/__init__.py`
  - **Verification:** Package installable with `pip install -e packages/datasets_pdf`

- [ ] **2.2 Create `pdf_ready` v1.0 Pydantic models**
  - Create `src/living_doc_datasets_pdf/pdf_ready/v1/models.py`
  - Define `PdfReadyV1`, `Meta`, `Content`, `UserStory`, `Sections`, `SelectionSummary`
  - Add field validators (e.g., `schema_version` must be `"1.0"`)
  - Add `model_config` for strict validation
  - **Reference:** SPEC.md section 3.3
  - **Verification:** Models instantiate correctly with valid data

- [ ] **2.3 Create `audit` v1.0 Pydantic models**
  - Create `src/living_doc_datasets_pdf/audit/v1/models.py`
  - Define `AuditEnvelopeV1`, `Producer`, `Run`, `Source`, `TraceStep`, `Warning`
  - Add field validators (e.g., `source.systems` must be non-empty)
  - **Reference:** SPEC.md section 3.4
  - **Verification:** Models instantiate correctly with valid data

- [ ] **2.4 Export JSON Schemas**
  - Create `src/living_doc_datasets_pdf/pdf_ready/v1/schema.py`
  - Add function `export_json_schema()` using `model.model_json_schema()`
  - Write schema to `schemas/pdf_ready_v1.schema.json`
  - Repeat for `audit` → `schemas/audit_envelope_v1.schema.json`
  - **Verification:** Schemas validate against reference examples (SPEC.md 3.3.4)

- [ ] **2.5 Add serialization helpers**
  - Create `src/living_doc_datasets_pdf/pdf_ready/v1/serializer.py`
  - Add `to_json(model, indent=2, sort_keys=True)` for deterministic output
  - Add `from_json(json_str)` for parsing
  - **Verification:** Same input produces byte-identical output

- [ ] **2.6 Write unit tests**
  - Create `tests/test_pdf_ready_models.py`
    - Test valid input (example from SPEC.md 3.3.4)
    - Test invalid inputs (missing required fields, wrong types)
    - Test field validators (e.g., `schema_version` must be `"1.0"`)
  - Create `tests/test_audit_models.py`
    - Test valid audit envelope
    - Test invalid inputs
    - Test non-empty constraints (`systems`, `producer.name`)
  - **Tools:** `pytest`, `pytest-cov`
  - **Verification:** Run `pytest packages/datasets_pdf/tests/ --cov=packages/datasets_pdf/src --cov-report=term`
  - **Pass criteria:** Coverage ≥ 80%

---

## Phase 3: Core Utilities Package (`packages/core`)

**Goal:** Create reusable, service-agnostic helper utilities.

### Tasks

- [x] **3.1 Set up package structure**
  - Create `packages/core/pyproject.toml`
  - Define package as `living-doc-core`
  - Add dependencies: `click ^8.1.0` (for potential future use)
  - Create `src/living_doc_core/__init__.py`
  - **Verification:** Package installable with `pip install -e packages/core`

- [x] **3.2 Create JSON utilities**
  - Create `src/living_doc_core/json_utils.py`
  - Add `read_json(filepath)` with error handling
  - Add `write_json(filepath, data, indent=2, sort_keys=True)` for deterministic output
  - Add validation helpers
  - **Verification:** Read/write round-trip produces identical output

- [x] **3.3 Create logging configuration**
  - Create `src/living_doc_core/logging_config.py`
  - Add `setup_logging(verbose=False)` function
  - Configure log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`
  - Add log formatting: `[{level}] {message}`
  - **Verification:** Logging output matches expected format

- [x] **3.4 Create Markdown utilities**
  - Create `src/living_doc_core/markdown_utils.py`
  - Add `split_by_headings(markdown_text, level=2)` → dict of heading → content
  - Add `normalize_heading(text)` → lowercase, stripped
  - Add `extract_lists(markdown_text)` (optional, for future use)
  - **Verification:** Headings split correctly with test cases

- [x] **3.5 Create common error types**
  - Create `src/living_doc_core/errors.py`
  - Define `ToolkitError` (base exception)
  - Define `InvalidInputError`, `AdapterError`, `SchemaValidationError`, `NormalizationError`, `FileIOError`
  - Map error types to exit codes (from SPEC.md 3.1.2)
  - **Verification:** Error classes raise correctly with messages

- [x] **3.6 Write unit tests**
  - Create `tests/test_json_utils.py`
    - Test read/write with valid JSON
    - Test read with malformed JSON (should raise error)
    - Test write with invalid path (should raise error)
  - Create `tests/test_markdown_utils.py`
    - Test heading splitting with multiple levels
    - Test edge cases (no headings, content before first heading)
    - Test heading normalization
  - **Tools:** `pytest`, `pytest-cov`
  - **Verification:** Run `pytest packages/core/tests/ --cov=packages/core/src --cov-report=term`
  - **Pass criteria:** Coverage ≥ 80%

---

## Phase 4: Adapter Package (`packages/adapters/collector_gh`)

**Goal:** Create collector-gh adapter for input detection and parsing.

### Tasks

- [ ] **4.1 Set up package structure**
  - Create `packages/adapters/collector_gh/pyproject.toml`
  - Define package as `living-doc-adapter-collector-gh`
  - Add dependencies: `living-doc-core`, `pydantic ^2.10.0`
  - Create `src/living_doc_adapter_collector_gh/__init__.py`
  - **Verification:** Package installable with `pip install -e packages/adapters/collector_gh`

- [ ] **4.2 Create `AdapterResult` model**
  - Create `src/living_doc_adapter_collector_gh/models.py`
  - Define `AdapterResult` with fields: `items`, `metadata`, `warnings`
  - Define `AdapterItem` with fields: `id`, `title`, `state`, `tags`, `url`, `timestamps`, `body`
  - **Reference:** SPEC.md section 3.2.3
  - **Verification:** Model validates correctly

- [ ] **4.3 Create producer detection logic**
  - Create `src/living_doc_adapter_collector_gh/detector.py`
  - Add `can_handle(payload: dict) -> bool`
    - Check `payload["metadata"]["generator"]["name"] == "AbsaOSS/living-doc-collector-gh"`
  - Add `extract_version(payload: dict) -> str`
    - Return `payload["metadata"]["generator"]["version"]`
  - **Reference:** SPEC.md section 3.2.1
  - **Verification:** Detection works with fixture files

- [ ] **4.4 Create version compatibility checker**
  - Create `src/living_doc_adapter_collector_gh/compatibility.py`
  - Add `check_compatibility(version: str) -> list[Warning]`
  - Define confirmed range: `>=1.0.0,<2.0.0` (using `packaging.version`)
  - Return warning if outside range
  - **Reference:** SPEC.md section 3.2.2
  - **Verification:** Warnings generated for versions `0.9.0`, `2.0.0`

- [ ] **4.5 Create input parser**
  - Create `src/living_doc_adapter_collector_gh/parser.py`
  - Add `parse(payload: dict) -> AdapterResult`
  - Map `metadata.generator.*` → audit envelope fields
  - Map `issues[]` → `AdapterItem[]`
  - Store original `metadata` in result
  - **Reference:** SPEC.md section 3.4.3
  - **Verification:** Parser output matches expected structure

- [ ] **4.6 Add fixture files**
  - Create `tests/fixtures/collector_v1.0.0/input/doc-issues.json`
  - Create `tests/fixtures/collector_v1.2.0/input/doc-issues.json`
  - Use realistic examples (10-15 issues, varied markdown)
  - **Reference:** `living-doc-collector-gh` output format

- [ ] **4.7 Write unit tests**
  - Create `tests/test_detector.py`
    - Test detection with valid collector-gh payload
    - Test rejection with invalid payload
    - Test version extraction
  - Create `tests/test_parser.py`
    - Test parsing with fixture v1.0.0
    - Test parsing with fixture v1.2.0
    - Test audit mapping
  - Create `tests/test_compatibility.py`
    - Test version in range (no warnings)
    - Test version outside range (warnings generated)
  - **Tools:** `pytest`, `pytest-cov`
  - **Verification:** Run `pytest packages/adapters/collector_gh/tests/ --cov=packages/adapters/collector_gh/src --cov-report=term`
  - **Pass criteria:** Coverage ≥ 80%

---

## Phase 5: Service Package (`packages/services/normalize_issues`)

**Goal:** Implement normalize-issues service with markdown normalization and PDF-ready JSON builder.

### Tasks

- [ ] **5.1 Set up package structure**
  - Create `packages/services/normalize_issues/pyproject.toml`
  - Define package as `living-doc-service-normalize-issues`
  - Add dependencies: `living-doc-core`, `living-doc-datasets-pdf`, `living-doc-adapter-collector-gh`
  - Create `src/living_doc_service_normalize_issues/__init__.py`
  - **Verification:** Package installable with `pip install -e packages/services/normalize_issues`

- [ ] **5.2 Create markdown normalizer**
  - Create `src/living_doc_service_normalize_issues/normalizer.py`
  - Add `normalize_sections(markdown: str) -> dict`
  - Implement heading synonym mapping (SPEC.md 3.3.3)
    - `Description`, `Overview`, `Summary` → `description`
    - `Business Value`, `Value`, `Why` → `business_value`
    - `Acceptance Criteria`, `AC` → `acceptance_criteria`
    - etc.
  - Handle unknown headings (append to `description`)
  - Handle content before first heading (assign to `description`)
  - **Reference:** SPEC.md section 5.3
  - **Verification:** Deterministic output for same input

- [ ] **5.3 Create PDF-ready JSON builder**
  - Create `src/living_doc_service_normalize_issues/builder.py`
  - Add `build_pdf_ready(adapter_result, options) -> PdfReadyV1`
  - Map `AdapterItem` → `UserStory` with normalized sections
  - Generate stable `id` (e.g., `github:owner/repo#123`)
  - Populate `meta` fields (document_title, document_version, generated_at, etc.)
  - Augment `audit.trace[]` with normalization step
  - **Reference:** SPEC.md section 3.3
  - **Verification:** Output validates against `PdfReadyV1` schema

- [ ] **5.4 Create service orchestration**
  - Create `src/living_doc_service_normalize_issues/service.py`
  - Add `run_service(input_path, output_path, options) -> None`
  - Implement pipeline (SPEC.md 5.1):
    1. Load input JSON
    2. Detect adapter (auto or explicit)
    3. Check compatibility
    4. Parse into AdapterResult
    5. Normalize sections
    6. Build pdf_ready.json
    7. Validate output
    8. Write output file
    9. Log summary
  - **Reference:** SPEC.md section 5.1
  - **Verification:** End-to-end execution with fixture

- [ ] **5.5 Write unit tests**
  - Create `tests/test_normalizer.py`
    - Test heading synonym mapping
    - Test unknown heading handling
    - Test edge cases (no headings, empty body)
    - Test determinism (same input → same output)
  - Create `tests/test_builder.py`
    - Test `AdapterItem` → `UserStory` mapping
    - Test `meta` field population
    - Test audit augmentation
  - Create `tests/test_service.py`
    - Test full pipeline with valid input
    - Test error handling (invalid input, missing file)
  - **Tools:** `pytest`, `pytest-cov`
  - **Verification:** Run `pytest packages/services/normalize_issues/tests/ --cov=packages/services/normalize_issues/src --cov-report=term`
  - **Pass criteria:** Coverage ≥ 80%

- [ ] **5.6 Add golden file integration tests**
  - Create `tests/integration/test_golden_files.py`
  - Add fixtures: `tests/fixtures/golden/input.json`, `tests/fixtures/golden/expected_output.json`
  - Test: Run service, compare output to expected (ignore timestamps)
  - **Verification:** Golden file test passes

- [ ] **5.7 Create verification scripts**
  - Create `verifications/verify_golden.py`
    - Load fixture input
    - Run normalization
    - Compare to expected output
    - Print diff if mismatch
  - Create `verifications/verify_compatibility.py`
    - Test with collector v0.9.0 (should warn)
    - Test with collector v1.0.0 (should pass)
    - Test with collector v2.0.0 (should warn)
  - **Verification:** Scripts runnable with `python verifications/verify_golden.py`

---

## Phase 6: CLI Wrapper (`apps/cli`)

**Goal:** Create unified CLI with `living-doc` command and subcommands.

### Tasks

- [ ] **6.1 Set up package structure**
  - Create `apps/cli/pyproject.toml`
  - Define package as `living-doc-cli`
  - Add dependencies: `living-doc-core`, `living-doc-service-normalize-issues`, `click ^8.1.0`
  - Create `src/living_doc_cli/__init__.py`
  - **Verification:** Package installable with `pip install -e apps/cli`

- [ ] **6.2 Create CLI entrypoint**
  - Create `src/living_doc_cli/main.py`
  - Add `@click.group()` for `living-doc` command
  - Add `--version` flag
  - Add global `--verbose` flag
  - **Reference:** SPEC.md section 3.1.1
  - **Verification:** `living-doc --help` displays usage

- [ ] **6.3 Create `normalize-issues` subcommand**
  - Create `src/living_doc_cli/commands/normalize_issues.py`
  - Add `@click.command()` for `normalize-issues`
  - Add arguments: `--input`, `--output`, `--source`, `--document-title`, `--document-version`, `--verbose`
  - Call `run_service()` from service package
  - Handle exceptions and map to exit codes (SPEC.md 3.1.2)
  - Format error messages: `{prefix} {detail}. {guidance}`
  - **Reference:** SPEC.md section 3.1
  - **Verification:** CLI invocation matches specification

- [ ] **6.4 Add error handling and exit codes**
  - Map exceptions to exit codes:
    - `InvalidInputError` → exit 1
    - `AdapterError` → exit 2
    - `SchemaValidationError` → exit 3
    - `NormalizationError` → exit 4
    - `FileIOError` → exit 5
  - Ensure error messages follow format
  - **Reference:** SPEC.md section 3.1.2
  - **Verification:** Test each error type manually

- [ ] **6.5 Write unit tests**
  - Create `tests/test_cli.py`
    - Test argument parsing
    - Test `--help` output
    - Test `--version` output
  - Create `tests/integration/test_cli_invocation.py`
    - Test successful execution
    - Test invalid input (file not found) → exit 1
    - Test adapter error → exit 2
  - **Tools:** `pytest`, `click.testing.CliRunner`
  - **Verification:** Run `pytest apps/cli/tests/ --cov=apps/cli/src --cov-report=term`
  - **Pass criteria:** Coverage ≥ 80%

- [ ] **6.6 Add console script entry point**
  - Update `apps/cli/pyproject.toml`
  - Add `[project.scripts]` with `living-doc = "living_doc_cli.main:cli"`
  - **Verification:** After install, `living-doc --help` works from command line

---

## Phase 7: Python CI/CD Workflow

**Goal:** Configure GitHub Actions workflows for static analysis, tests, and coverage.

### Tasks

- [ ] **7.1 Create static analysis workflow**
  - Create `.github/workflows/ci.yml`
  - Add Pylint job:
    - Set up Python 3.14
    - Install dependencies
    - Run `pylint` on all `*.py` files
    - Enforce score ≥ 9.5
  - Add Black format check job:
    - Run `black --check $(git ls-files '*.py')`
  - Add Mypy type check job:
    - Run `mypy .`
  - **Reference:** `living-doc-collector-gh/.github/workflows/static_analysis_and_tests.yml`
  - **Verification:** Workflow passes on clean code

- [ ] **7.2 Add unit test workflow**
  - Add pytest job to `.github/workflows/ci.yml`:
    - Set up Python 3.14
    - Install all packages (`pip install -e packages/*/` and `pip install -e apps/cli`)
    - Run `pytest --cov=. --cov-report=term --cov-fail-under=80`
  - **Reference:** `living-doc-collector-gh` pytest configuration
  - **Verification:** Tests pass with coverage ≥ 80%

- [ ] **7.3 Create integration test workflow**
  - Create `.github/workflows/integration.yml`
  - Add fixture verification job:
    - Run `verifications/verify_golden.py`
    - Run `verifications/verify_compatibility.py`
  - **Verification:** Integration tests pass in CI

- [ ] **7.4 Configure Python version pinning**
  - Pin Python 3.14 in all workflows
  - Use `actions/setup-python@v5` with `python-version: '3.14'`
  - Enable pip caching with `cache: 'pip'`
  - **Reference:** `living-doc-collector-gh` workflows

- [ ] **7.5 Add CI status badges to README**
  - Add badges for:
    - CI status (static analysis + tests)
    - Integration tests status
    - Coverage (optional, if using Codecov)
  - **Verification:** Badges display correctly on GitHub

---

## Phase 8: Fixture-Based Verification

**Goal:** Add comprehensive fixtures and manual verification scripts.

### Tasks

- [ ] **8.1 Add collector-gh fixtures**
  - Create `tests/fixtures/collector_gh/v1.0.0/input/doc-issues.json`
  - Create `tests/fixtures/collector_gh/v1.2.0/input/doc-issues.json`
  - Create `tests/fixtures/collector_gh/v2.0.0/input/doc-issues.json` (out-of-range)
  - Use realistic examples with:
    - 10-15 issues
    - Varied markdown (headings, lists, tables, links)
    - Different states (open, closed)
    - Multiple tags
  - **Verification:** Files are valid JSON and follow collector-gh format

- [ ] **8.2 Add golden output files**
  - Create `tests/fixtures/golden/v1.0.0/expected_output.json`
  - Create `tests/fixtures/golden/v1.2.0/expected_output.json`
  - Generate expected outputs manually (verified by SPEC)
  - **Verification:** Expected outputs validate against `PdfReadyV1` schema

- [ ] **8.3 Create golden file verification script**
  - Create `verifications/verify_golden.py`
  - For each fixture:
    - Run `living-doc normalize-issues --input {fixture} --output {temp}`
    - Load expected output
    - Compare (ignore `generated_at`, `started_at`, `finished_at`)
    - Print diff if mismatch
    - Exit 0 if all pass, exit 1 if any fail
  - **Verification:** Script passes with current implementation

- [ ] **8.4 Create compatibility verification script**
  - Create `verifications/verify_compatibility.py`
  - Test with v0.9.0 fixture (expect warnings)
  - Test with v1.0.0 fixture (expect success)
  - Test with v2.0.0 fixture (expect warnings)
  - Verify warnings appear in output and `audit.trace[].warnings[]`
  - **Verification:** Script detects version mismatches correctly

- [ ] **8.5 Add CI integration for verification scripts**
  - Update `.github/workflows/integration.yml`
  - Add steps to run verification scripts
  - Fail workflow if verification fails
  - **Verification:** CI fails if golden files don't match

---

## Phase 9: Cookbooks & Recipes

**Goal:** Write user-facing documentation with examples and ready-to-use recipes.

### Tasks

- [ ] **9.1 Write `normalize-issues` cookbook**
  - Create `docs/cookbooks/normalize-issues.md`
  - Sections:
    - What it does (overview)
    - How detection works (adapter selection)
    - How compatibility checking works (version ranges)
    - How audit is preserved and augmented (trace steps)
    - How to interpret warnings
    - Troubleshooting (common errors)
  - **Verification:** Documentation is clear and accurate

- [ ] **9.2 Create local usage recipe**
  - Create `docs/recipes/local-normalize-issues.md`
  - Include:
    - Prerequisites (Python 3.14, pip install)
    - Installation commands
    - Example CLI invocation (with real paths)
    - Expected output
    - How to verify output (schema validation)
  - **Reference:** SPEC.md section 3.1.1 for CLI examples
  - **Verification:** Recipe tested locally and works as documented

- [ ] **9.3 Create GitHub Actions recipe**
  - Create `docs/recipes/github-actions-normalize-issues.yml`
  - Include complete workflow example:
    - Checkout code
    - Set up Python 3.14
    - Install living-doc-toolkit
    - Run `living-doc normalize-issues`
    - Upload artifacts (pdf_ready.json)
  - Show chaining: collector → builder → generator
  - **Verification:** Recipe tested in CI and works as documented

- [ ] **9.4 Add troubleshooting guide**
  - Create `docs/troubleshooting.md`
  - Cover common issues:
    - "File not found" errors
    - "No compatible adapter found" errors
    - Version mismatch warnings
    - Schema validation failures
  - Provide actionable solutions for each
  - **Verification:** Guide covers all error codes from SPEC.md 3.1.2

- [ ] **9.5 Add architecture diagram** (optional)
  - Create `docs/architecture.md`
  - Include diagram showing:
    - Collector → Adapter → Service → Dataset → Generator
    - Monorepo package structure
    - Data flow
  - **Tools:** Mermaid, PlantUML, or draw.io
  - **Verification:** Diagram matches SPEC.md architecture

---

## Phase 10: Release Preparation

**Goal:** Prepare for first release (v0.1.0).

### Tasks

- [ ] **10.1 Set version numbers**
  - Update `version` in all `pyproject.toml` files to `0.1.0`
  - Ensure consistency across all packages
  - **Verification:** All version numbers match

- [ ] **10.2 Update `CHANGELOG.md`**
  - Move `[Unreleased]` items to `[0.1.0] - 2026-01-23`
  - Sections:
    - **Added:** Initial implementation of normalize-issues service, adapters, core utilities, CLI, etc.
    - **Changed:** N/A (initial release)
    - **Fixed:** N/A (initial release)
  - **Verification:** Changelog follows Keep a Changelog format

- [ ] **10.3 Write migration guide** (for future releases)
  - Create `docs/migration_guide.md`
  - Add template for future breaking changes
  - **Verification:** Template is ready for v0.2.0 updates

- [ ] **10.4 Run full test suite**
  - Run `pytest` on all packages
  - Run all verification scripts
  - Run CI workflows locally (using `act` or similar)
  - **Pass criteria:** All tests pass, coverage ≥ 80%

- [ ] **10.5 Review documentation**
  - Verify SPEC.md is up-to-date
  - Verify README.md is accurate
  - Verify all recipes work as documented
  - Check for broken links
  - **Verification:** Documentation review complete

- [ ] **10.6 Create release workflow**
  - Create `.github/workflows/release.yml`
  - Add steps:
    - Trigger on tag push (`v*`)
    - Run full test suite
    - Build packages
    - Create GitHub Release draft
    - Upload artifacts
  - **Reference:** `living-doc-collector-gh/.github/workflows/release_draft.yml`
  - **Verification:** Workflow tested with dry-run

- [ ] **10.7 Create GitHub Release draft**
  - Tag: `v0.1.0`
  - Title: "Living Documentation Toolkit v0.1.0 - Initial Release"
  - Body:
    - Summary of features
    - Link to SPEC.md
    - Link to cookbooks and recipes
    - Installation instructions
    - Known limitations
  - **Verification:** Release notes are complete and accurate

- [ ] **10.8 Run final pre-release checklist**
  - [ ] All CI workflows passing
  - [ ] Code coverage ≥ 80%
  - [ ] Pylint score ≥ 9.5
  - [ ] Black formatting applied
  - [ ] Mypy type checking passing
  - [ ] All verification scripts passing
  - [ ] Documentation complete and reviewed
  - [ ] CHANGELOG.md updated
  - [ ] Version numbers consistent
  - [ ] License headers present

- [ ] **10.9 Publish release**
  - Push tag `v0.1.0`
  - Trigger release workflow
  - Publish GitHub Release
  - **Verification:** Release is live on GitHub

---

## Post-Release Tasks

**These tasks are for ongoing maintenance after v0.1.0 release.**

- [ ] **Monitor issue tracker**
  - Triage new issues
  - Label bugs, enhancements, questions
  - Respond to user feedback

- [ ] **Plan v0.2.0 features**
  - Review SPEC.md "Future Extensions" (section 12.1)
  - Prioritize next service or feature
  - Update TASKS.md with new phases

- [ ] **Maintain compatibility**
  - Track `living-doc-collector-gh` releases
  - Update adapter confirmed range if needed
  - Test with new collector versions

- [ ] **Improve documentation**
  - Add more examples based on user feedback
  - Expand troubleshooting guide
  - Record common questions in FAQ

---

## Appendix: Tool Reference

### Testing Tools

- **pytest**: Testing framework
  - Run: `pytest`
  - Coverage: `pytest --cov=. --cov-report=term`
  - Coverage threshold: `--cov-fail-under=80`

- **pytest-cov**: Coverage plugin
  - Config: `[tool.coverage.run]` in `pyproject.toml`

### Code Quality Tools

- **Black**: Code formatter
  - Check: `black --check $(git ls-files '*.py')`
  - Format: `black $(git ls-files '*.py')`
  - Config: `[tool.black]` in `pyproject.toml` (line-length=120, py314)

- **Pylint**: Linter
  - Run: `pylint $(git ls-files '*.py')`
  - Threshold: Score ≥ 9.5
  - Config: `.pylintrc` or `pyproject.toml`

- **Mypy**: Type checker
  - Run: `mypy .`
  - Config: `[tool.mypy]` in `pyproject.toml` (check_untyped_defs, py314)

### CI/CD Tools

- **GitHub Actions**: CI/CD platform
  - Workflows: `.github/workflows/*.yml`
  - Python version: 3.14 (pinned)
  - Cache: `cache: 'pip'`

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-23 | Specification Master | Initial roadmap based on SPEC.md |

---

**End of Document**
