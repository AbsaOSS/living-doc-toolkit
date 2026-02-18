# Living Documentation Toolkit — Developer Guide

- [Get Started](#get-started)
- [Monorepo Layout](#monorepo-layout)
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
| `apps/cli` | `living-doc-cli` | CLI entry point (`living-doc` command) |

Each package has its own `pyproject.toml`, `src/` layout, and `tests/` directory.
All quality-gate commands below are designed to run **per-package** from within the
package directory, matching how CI executes them.

## Running Static Code Analysis

This project uses [Pylint](https://pylint.readthedocs.io/) for static code analysis.
Pylint displays a global evaluation score rated out of 10.0. We aim to keep our code
quality at or above **9.5**.

Each package's `pyproject.toml` configures Pylint. CI runs Pylint per-package and
excludes test files.

### Run Pylint (per-package)

From the **package directory** (e.g., `packages/core`):

```shell
cd packages/core
pylint $(git ls-files '*.py' | grep -v '^tests/')
```

To run Pylint on a specific file:

```shell
pylint src/living_doc_core/json_utils.py
```

### Run Pylint (all packages)

From the **repository root**:

```shell
for pkg in packages/core packages/datasets_pdf packages/adapters/collector_gh packages/services/normalize_issues apps/cli; do
  echo "=== Pylint: $pkg ==="
  (cd "$pkg" && pylint $(git ls-files '*.py' | grep -v '^tests/'))
done
```

## Run Black Tool Locally

This project uses [Black](https://github.com/psf/black) for code formatting.
Line length is set to **120 characters** (configured in each package's `pyproject.toml`).

### Run Black (per-package)

From the **package directory**:

```shell
cd packages/services/normalize_issues
black $(git ls-files '*.py')
```

### Run Black (all packages)

From the **repository root**:

```shell
for pkg in packages/core packages/datasets_pdf packages/adapters/collector_gh packages/services/normalize_issues apps/cli; do
  echo "=== Black: $pkg ==="
  (cd "$pkg" && black $(git ls-files '*.py'))
done
```

### Check-only mode (no changes)

```shell
cd packages/core
black --check $(git ls-files '*.py')
```

### Expected Output
```
All done! ✨ 🍰 ✨
1 file reformatted.
```

## Run mypy Tool Locally

This project uses [mypy](https://mypy.readthedocs.io/en/stable/) for static type
checking. Configuration is in each package's `pyproject.toml`.

### Run mypy (per-package)

From the **package directory**:

```shell
cd packages/core
mypy .
```

### Run mypy (all packages)

From the **repository root**:

```shell
for pkg in packages/core packages/datasets_pdf packages/adapters/collector_gh packages/services/normalize_issues apps/cli; do
  echo "=== mypy: $pkg ==="
  (cd "$pkg" && mypy .)
done
```

To type-check a specific file:

```shell
mypy packages/core/src/living_doc_core/json_utils.py
```

## Running Unit Tests

Unit tests are written using [pytest](https://docs.pytest.org/) and live in each
package's `tests/` directory.

### Run tests (per-package)

From the **package directory**:

```shell
cd packages/services/normalize_issues
pytest --cov=src -v tests/ --cov-fail-under=80
```

### Run tests (all packages)

From the **repository root**:

```shell
for pkg in packages/core packages/datasets_pdf packages/adapters/collector_gh packages/services/normalize_issues apps/cli; do
  echo "=== Tests: $pkg ==="
  (cd "$pkg" && pytest --cov=src -v tests/ --cov-fail-under=80)
done
```

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

### Check coverage (per-package)

```shell
cd packages/core
pytest --cov=src -v tests/ --cov-fail-under=80
```

### Generate HTML report

```shell
cd packages/core
pytest --cov=src -v tests/ --cov-fail-under=80 --cov-report=html
open htmlcov/index.html
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
```

## Branch Naming Convention (PID:H-1)
All work branches MUST use an allowed prefix followed by a concise kebab-case descriptor (optional numeric ID):
Allowed prefixes:
- feature/ : new functionality & enhancements
- fix/     : bug fixes / defect resolutions
- docs/    : documentation-only updates
- chore/   : maintenance, CI, dependency bumps, non-behavioral refactors
Examples:
- feature/add-hierarchy-support
- fix/456-null-title-parsing
- docs/update-readme-quickstart
- chore/upgrade-pygithub
Rules:
- Prefix mandatory; rename non-compliant branches before PR (`git branch -m feature/<new-name>` etc.).
- Descriptor lowercase kebab-case; hyphens only; avoid vague terms (`update`, `changes`).
- Align scope: a docs-only PR MUST use docs/ prefix, not feature/.
Verification Tip:
```shell
git rev-parse --abbrev-ref HEAD | grep -E '^(feature|fix|docs|chore)/' || echo 'Branch naming violation (expected allowed prefix)'
```
Future possible prefixes (not enforced yet): `refactor/`, `perf/`.
