# Living Documentation Toolkit — Developer Guide

- [Get Started](#get-started)
- [Monorepo Layout](#monorepo-layout)
- [QA Automation with Make](#qa-automation-with-make)
- [Running Static Code Analysis](#running-static-code-analysis)
- [Run Black Tool Locally](#run-black-tool-locally)
- [Run mypy Tool Locally](#run-mypy-tool-locally)
- [Running Unit Tests](#running-unit-tests)
- [Running Integration Tests](#running-integration-tests)
- [Code Coverage](#code-coverage)
- [Run CLI Locally](#run-cli-locally)
- [Branch Naming Convention (PID:H-1)](#branch-naming-convention-pidh-1)

## Get Started

Clone the repository and navigate to the project directory:

```shell
git clone https://github.com/AbsaOSS/living-doc-toolkit.git
cd living-doc-toolkit
```

### Set Up Python Environment

The supported floor is **Python 3.10** (`requires-python = ">=3.10"` in every package's
`pyproject.toml`); CI runs the `3.10`–`3.14` matrix. Use any interpreter in that range.

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### Install All Packages (editable mode)

Packages must be installed in dependency order. The following commands install every
package together with the `[dev]` extras needed for tooling:

```shell
pip install -e packages/core[dev]
pip install -e packages/datasets_pdf[dev]
pip install -e packages/adapters/collector_gh[dev]
pip install -e packages/services/normalize_issues[dev]
pip install -e packages/services/coverage_matrix[dev]
pip install -e "apps/cli[dev]"
```

> **Note:** No `requirements.txt` exists — all dependencies are declared in per-package
> `pyproject.toml` files.

## Monorepo Layout

| Path | Package | Description |
|---|---|---|
| `packages/core` | `living-doc-core` | Shared utilities (logging, JSON, markdown, errors) |
| `packages/datasets_pdf` | `living-doc-datasets-pdf` | Pydantic models and JSON schemas for PDF contracts |
| `packages/adapters/collector_gh` | `living-doc-adapter-collector-gh` | Detector and parser for collector-gh output |
| `packages/services/normalize_issues` | `living-doc-service-normalize-issues` | Issue normalization service |
| `packages/services/coverage_matrix` | `living-doc-service-coverage-matrix` | AC-level test coverage matrix generator |
| `apps/cli` | `living-doc-cli` | CLI entry point (`living-doc` command) |

Each package has its own `pyproject.toml`, `src/` layout, and `tests/` directory.
All quality-gate commands below are designed to run **per-package** from within the
package directory, matching how CI executes them.

## QA Automation with Make

This project includes a `Makefile` exposing the shared **command vocabulary**
([`repo-conventions.md` §7](https://github.com/AbsaOSS/living-doc/blob/master/docs/specs/repo-conventions.md)).
Use the Make targets instead of manual loops — `.github/workflows/test.yml` runs the same
targets, so local and CI never drift.

### Quick Start

First, install all packages with dev dependencies:

```shell
make install
```

Then run every QA gate (`format-check` → `lint` → `types` → `test`) on all packages:

```shell
make qa
```

Show all available commands:

```shell
make help
```

### Canonical targets

Seven targets. Each has an **aggregate** form (every package) and a **per-package** form
`<target>-<alias>`.

| Target | Runs | Gate |
|--------|------|------|
| `qa` | `format-check` → `lint` → `types` → `test`, failing on the first | all of the below |
| `lint` | Pylint over tracked `*.py` (tests excluded) | score ≥ **9.5** / 10 |
| `format` | Black, rewriting files | line length **120** |
| `format-check` | Black `--check` (no writes) | line length **120** |
| `types` | mypy | clean |
| `test` | pytest | pass |
| `coverage` | pytest with coverage measurement | `--cov-fail-under=80` |

### Run QA for a specific package

Package aliases: `core`, `datasets-pdf`, `collector-gh`, `normalize`, `coverage`, `cli`.

```shell
make qa-core                  # all gates for packages/core
make qa-datasets-pdf          # packages/datasets_pdf
make qa-collector-gh          # packages/adapters/collector_gh
make qa-normalize             # packages/services/normalize_issues
make qa-coverage              # packages/services/coverage_matrix
make qa-cli                   # apps/cli
```

Run one gate on one package:

```shell
make format-core              # Black on packages/core
make lint-core                # Pylint on packages/core
make types-core               # mypy on packages/core
make test-core                # tests on packages/core
make coverage-core            # tests + coverage gate on packages/core
```

### Deprecated target names

The pre-Phase-0 names still work for one release and print a deprecation notice:
`py-qa` → `qa`, `black` → `format`, `pylint` → `lint`, `mypy` → `types`,
`pytest-unit` → `test`, and their `-<alias>` per-package forms.

## Running Static Code Analysis

This project uses [Pylint](https://pylint.readthedocs.io/) for static code analysis.
Pylint displays a global evaluation score rated out of 10.0. We aim to keep our code
quality at or above **9.5**.

Each package's `pyproject.toml` configures Pylint. CI runs Pylint per-package and
excludes test files.

### Run Pylint

One package (`make lint-<alias>`) or all of them (`make lint`):

```shell
make lint-core          # wraps: cd packages/core && pylint --fail-under=9.5 $(git ls-files '*.py' | grep -v '^tests/')
make lint               # every package
```

To run Pylint on a specific file, from inside the package directory:

```shell
cd packages/core && pylint src/living_doc_core/json_utils.py
```

## Run Black Tool Locally

This project uses [Black](https://github.com/psf/black) for code formatting.
Line length is set to **120 characters** (configured in each package's `pyproject.toml`).

### Run Black

Rewrite one package (`make format-<alias>`) or all of them (`make format`):

```shell
make format-normalize        # wraps: cd packages/services/normalize_issues && black .
make format                  # every package
```

### Check-only mode (no changes)

```shell
make format-check-core       # wraps: cd packages/core && black --check .
make format-check            # every package
```

### Expected Output
```
All done! ✨ 🍰 ✨
1 file reformatted.
```

## Run mypy Tool Locally

This project uses [mypy](https://mypy.readthedocs.io/en/stable/) for static type
checking. Configuration is in each package's `pyproject.toml`.

### Run mypy

One package (`make types-<alias>`) or all of them (`make types`):

```shell
make types-core              # wraps: cd packages/core && mypy .
make types                   # every package
```

Configuration (`[tool.mypy]` in each `pyproject.toml`) sets `python_version = "3.10"` — the
supported floor — so type checks catch 3.11+-only stdlib use.

## Running Unit Tests

Unit tests are written using [pytest](https://docs.pytest.org/) and live in each
package's `tests/` directory.

### Run tests

One package (`make test-<alias>`) or all of them (`make test`):

```shell
make test-normalize          # wraps: cd packages/services/normalize_issues && pytest tests/
make test                    # every package
```

`make coverage` / `make coverage-<alias>` adds the explicit `--cov=src --cov-fail-under=80`
gate that CI enforces.

## Running Integration Tests

Integration tests are executed in a separate CI workflow
(`.github/workflows/integration.yml`). They run golden-file and compatibility
verifications across the installed packages.

### Run locally

With all packages installed (see [Get Started](#get-started)):

```shell
# Golden-file verification (normalize-issues)
python packages/services/normalize_issues/verifications/verify_golden.py

# Compatibility verification (normalize-issues)
python packages/services/normalize_issues/verifications/verify_compatibility.py
```

Per-package integration tests (where they exist):

```shell
cd packages/services/normalize_issues
pytest tests/integration/ -v
```

## Code Coverage

Code coverage is collected with `pytest-cov`. The minimum threshold is **80 %**.

### Check coverage

```shell
make coverage-core           # wraps: cd packages/core && pytest tests/ --cov=src --cov-fail-under=80
make coverage                # every package
```

### Generate HTML report

Each package's `pyproject.toml` sets `--cov-report=html`, so `make coverage-core` also
writes `packages/core/htmlcov/index.html`:

```shell
make coverage-core
open packages/core/htmlcov/index.html
```

## Run CLI Locally

After installing all packages (see [Get Started](#get-started)), the `living-doc`
command is available:

```shell
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --source auto \
  --document-title "Sprint 42 Report" \
  --document-version "1.0.0"

living-doc coverage-matrix \
  --doc-input  doc-source.json \
  --tests-input ui-tests.json \
  --output coverage-matrix.json \
  --fail-under 80
```

## Branch Naming Convention (PID:H-1)

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the canonical rules — this is a summary.

Every branch is `<prefix>/<issue>-<scope>`: an allowed prefix, then the issue number
**immediately** after it, then a lowercase kebab-case scope. The `check-pr-requirements`
CI check rejects a branch with no issue number.

Allowed prefixes:
- `feature/` : new functionality & enhancements
- `fix/`     : bug fixes / defect resolutions
- `docs/`    : documentation-only updates
- `chore/`   : maintenance, CI, dependency bumps, non-behavioral refactors

Examples:
- `feature/123-add-hierarchy-support`
- `fix/456-null-title-parsing`
- `docs/203-update-readme-quickstart`
- `chore/318-upgrade-pydantic`

Rules:
- Prefix and issue number mandatory; rename before pushing (`git branch -m <prefix>/<issue>-<scope>`).
- Scope lowercase kebab-case; hyphens only; avoid vague terms (`update`, `changes`).
- Align scope: a docs-only PR MUST use `docs/`, not `feature/`.

Verification tip:
```shell
git rev-parse --abbrev-ref HEAD | grep -E '^(feature|fix|docs|chore)/[0-9]+-' \
  || echo 'Branch naming violation (expected <prefix>/<issue>-<scope>)'
```
Future possible prefixes (not enforced yet): `refactor/`, `perf/`.
