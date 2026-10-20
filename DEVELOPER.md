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
- [Action venv](#action-venv)
- [CI](#ci)
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

Run `make install` from the repository root. It installs `requirements-dev.txt`, then
reinstalls every package editable with its `[dev]` extra, in dependency order:

```shell
pip install -r requirements-dev.txt
pip install -e packages/core[dev]
pip install -e packages/datasets_generator_ready[dev]
pip install -e packages/adapters/collector_gh[dev]
pip install -e packages/services/normalize_issues[dev]
pip install -e packages/services/coverage_matrix[dev]
pip install -e "apps/cli[dev]"
```

| File | What it holds | Who installs it |
|---|---|---|
| `requirements.txt` | Runtime only: the six package directories, each after the ones it depends on (`./packages/core` … `./apps/cli`) | `action.yml`, into its venv, on every run; the README Quickstart |
| `requirements-dev.txt` | `-r requirements.txt`, the gate and test tools pinned, and `PyYAML` for `tests/test_action_yml.py` | `make install` and CI |

- Each package declares its own runtime dependencies in its `pyproject.toml`; `requirements.txt`
  names the packages, not their dependencies.
- The development tools live in both places. Each package's `[dev]` extra keeps the ranges that
  package needs on its own; `requirements-dev.txt` pins the versions `make install` and CI use.
- Run both installs from the repository root: pip reads `./packages/...` against the directory
  it runs in, not against the file.
- `requirements.txt` carries no `-e`. `make install` gives the editable install for development;
  the action and the Quickstart need a plain one.
  - Why the order in `make install`: a later `pip install -r requirements.txt` would reinstall the
    six packages non-editable, and one call holding both `./packages/core` and `-e packages/core`
    does not resolve.
- A plain install builds each package in place and leaves a `build/` directory beside its `src/`.
  Each package's mypy `exclude` skips `build/`.
  - Why: `make types-<alias>` runs `mypy .`, which would otherwise find every module twice.
- A new package under `packages/` or `apps/` goes into `requirements.txt` after the packages it
  depends on, and a development tool goes into `requirements-dev.txt`, never `requirements.txt`.
  - Why: `apps/cli` depends on the other packages by name and none of them is on PyPI, so an
    unlisted package fails the install with "No matching distribution found"; and the action
    installs `requirements.txt` on every run.
- Dependabot covers both files from its `pip` entry on `/`, beside one entry per package
  directory, in `.github/dependabot.yml`.

## Monorepo Layout

| Path | Package | Description |
|---|---|---|
| `packages/core` | `living-doc-core` | Shared utilities (logging, JSON, markdown, errors) |
| `packages/datasets_generator_ready` | `living-doc-datasets-generator-ready` | Pydantic models and JSON schemas for the generator-ready and audit contracts |
| `packages/adapters/collector_gh` | `living-doc-adapter-collector-gh` | Detector and parser for collector-gh output |
| `packages/services/normalize_issues` | `living-doc-service-normalize-issues` | Issue normalization service |
| `packages/services/coverage_matrix` | `living-doc-service-coverage-matrix` | AC-level test coverage matrix generator |
| `apps/cli` | `living-doc-cli` | CLI entry point (`living-doc` command) |

Each package has its own `pyproject.toml`, `src/` layout, and `tests/` directory.
All quality-gate commands below are designed to run **per-package** from within the
package directory, matching how CI executes them.

The repository root holds the action: `action.yml`, its entry point `main.py`, and the root
`tests/` for both. The root gates run from the repository root with the root `pyproject.toml`
(see [Root checks](#root-checks)).

## QA Automation with Make

This project includes a `Makefile` exposing the shared **command vocabulary**
(the fleet-wide `repo-conventions.md` §7 "Command vocabulary").
Use the Make targets instead of manual loops — `.github/workflows/test.yml` runs the same
targets, so local and CI never drift.

### Quick Start

First, install all packages with dev dependencies:

```shell
make install
```

Then run every QA gate (`format-check` → `lint` → `types` → `test`) on all packages, then
the [root checks](#root-checks):

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
| `qa` | `format-check` → `lint` → `types` → `test` per package, then `qa-root`, failing on the first | all of the below |
| `lint` | Pylint over tracked `*.py` (tests excluded) | score ≥ **9.5** / 10 |
| `format` | Black, rewriting files | line length **120** |
| `format-check` | Black `--check` (no writes) | line length **120** |
| `types` | mypy | clean |
| `test` | pytest | pass |
| `coverage` | pytest with coverage measurement | `--cov-fail-under=80` |

### Run QA for a specific package

Package aliases: `core`, `datasets-generator-ready`, `collector-gh`, `normalize`, `coverage`, `cli`.

```shell
make qa-core                  # all gates for packages/core
make qa-datasets-generator-ready   # packages/datasets_generator_ready
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

### Root checks

`make qa-root` runs the gates over the root's own files. `make qa` runs it after the packages,
and each aggregate target (`make lint`, `make test`, …) includes its `-root` form.

| Target | Runs | Gate |
|---|---|---|
| `format-check-root` / `format-root` | Black over `main.py` and `tests/` | line length **120** |
| `lint-root` | ruff over `main.py` and `tests/`, then Pylint over `main.py` | score ≥ **9.5** / 10 |
| `types-root` | mypy over `main.py` | clean |
| `test-root` / `coverage-root` | pytest over `tests/`, measuring `main.py` | ≥ **80 %** |

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
verifications across the installed packages; the same workflow runs the action
itself ([CI](#ci)).

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
  --output generator-ready.json \
  --source auto \
  --document-title "Sprint 42 Report" \
  --document-version "1.0.0"

living-doc coverage-matrix \
  --doc-input  doc-source.json \
  --tests-input ui-tests.json \
  --output coverage-matrix.json \
  --fail-under 80
```

## Action venv

`action.yml` runs the toolkit in a venv of its own, built from the caller's Python. The rules
are `living-doc-generator-markdown`'s; what differs here follows them.

- The action uses the Python on `PATH`; the caller prepares it, for example with `actions/setup-python`.
- Below 3.10 it fails before creating anything, with one line:
  `::error::living-doc-toolkit needs Python >= 3.10 on PATH. Add actions/setup-python before this step.`
- It installs `requirements.txt` into `$RUNNER_TEMP/living-doc-toolkit-venv`. It never changes the
  caller's interpreter, `PATH` or environment, and writes nothing to `$GITHUB_ENV` or `$GITHUB_PATH`.
- `PIP_TARGET`, `PIP_PREFIX`, `PIP_USER`, `PIP_ROOT`, `PIP_PYTHON` and `PYTHONPATH` are unset before
  the install.
  - Why: pip reads them as configuration, so a caller exporting one would empty or shadow the venv,
    or (`PIP_PYTHON`) install into the caller's own interpreter.
- The venv is reused only when the interpreter now on `PATH` built it, compared as `sys.base_prefix`
  plus version; otherwise it is rebuilt.
- After the install, one import of `living_doc_cli.main` through the venv's interpreter proves the
  packages landed there. Its failure is one line pointing at the runner's pip configuration.
- `main.py` runs with `-E`, so a caller's `PYTHONPATH` cannot shadow the venv. Every input reaches it
  through the run step's `env:`; no `run:` script holds `${{ inputs.* }}`.
- `main.py` runs the CLI with `-I`, which is `-E` that also keeps the working directory off `sys.path`.
  - Why: the run step runs in the caller's checkout, and `python -m` searches the working directory
    first, so a `click.py` or `json.py` there would replace the venv's module.
- Linux runners only: the venv's POSIX `bin/` layout is assumed.
- `tests/test_action_yml.py` runs the venv step against a fake interpreter. `integration.yml` shows
  the reuse, the rebuild on an interpreter change, and the rejection of Python 3.9 on real ones
  ([CI](#ci)).

What differs from `living-doc-generator-markdown`:

- The install and the import check run from the action's own directory, `$GITHUB_ACTION_PATH`.
  - Why: `requirements.txt` names `./packages/...`, which pip reads against the directory it runs
    in; from the caller's workspace the paths do not exist.
  - Why the variable, not `${{ github.action_path }}`: in a `container:` job the expression gives
    the runner host's path, which does not exist inside the container.
- The import check imports `living_doc_cli.main`, which imports the other five packages through the
  two commands.
- pip rebuilds a local directory on every install, so each run reinstalls the six packages into the
  reused venv; their dependencies stay installed.

### The entry point

`main.py` checks the inputs, then runs `python -I -m living_doc_cli.main <command> --<option>=<value> …`
on the venv's interpreter. The CLI's exit code is the step's.

- An unknown `command` fails with one line listing the valid commands. `normalize-tests` fails with
  one line saying it is not available yet: `action.yml` declares it, and no CLI command runs it yet.
- Each input goes only to the commands that take it. A non-empty input the command does not take
  fails with one line naming the input and the command. An empty one is not passed, so the CLI's
  default applies.
  - Why: `action.yml` passes every input on every run, an unset one as its empty default.
- `tests-input` and `fail-under` are `coverage-matrix`'s own inputs, as decided on issue #81.
  An empty required input, `tests-input` for `coverage-matrix` included, fails with one line naming
  it, and so does a `fail-under` that is not a finite number.
- `verbose-logging: 'true'`, in any case, adds `--verbose` and logs the command line at DEBUG.
  `INPUT_VERBOSE_LOGGING` stays in the run step's `env:`.
  - Why: the CLI reads no environment variable, so `--verbose` is the way in. The variable is there
    for when the toolkit reads it, as `living-doc-utilities`' logging does.
  - Under `--verbose` the services log at DEBUG level but emit no DEBUG line of their own today, so
    the DEBUG lines are the entry point's.
- Once the command succeeds, `output-path` is set to the absolute path of `output`.

A debug run, from the repository root after `make install`:

```shell
export INPUT_COMMAND=normalize-issues
export INPUT_INPUT=tests/fixtures/collector_gh/v1.2.0/input/doc-issues.json
export INPUT_OUTPUT=output/generator-ready.json
export INPUT_VERBOSE_LOGGING=true      # optional: --verbose and DEBUG lines; default false
python3 main.py
```

- Each input is an `INPUT_<NAME>` variable, upper case with `_` for `-`, as `action.yml` passes it.
- Without `GITHUB_OUTPUT`, as outside GitHub Actions, the run sets no `output-path` output and logs
  that once.

## CI

`test.yml` runs the gates, `integration.yml` runs the verifications and the action itself, and
`link-check.yml` checks the Markdown links.

- The checks to mark as required are `QA Gate` and every `integration.yml` job.
  - `QA Gate` always runs, passes over a skipped job and fails on a failed or cancelled one. Why: a
    required check must report on every pull request, also on one that changed no Python.
  - `integration.yml` runs on every pull request to `master`, so its jobs always report. Why: its
    action jobs are the only ones that run the action itself; without them a broken action merges
    green.
- The gates run when a Python-related file changed: `*.py`, `requirements.txt`,
  `requirements-dev.txt`, a `pyproject.toml`, a `tests/fixtures/` file, a JSON file under
  `packages/`, `Makefile`, `action.yml` or `test.yml`.
  - The fixtures are in the list because the golden tests compare against them.
  - JSON under `packages/` is in the list because the services load their JSON schemas at run time
    and the tests check them.
  - `action.yml` is in the list because `tests/test_action_yml.py` reads it.
  - On a pull request a renamed file counts by its old path too, so moving a file out of that set
    still runs the tests.
- A manual run runs every gate, and a manual run of `link-check.yml` checks every page.
  - Why: a manual run is a request to re-check the branch, whatever its last commit touched.
- `format-check`, `lint` and `types` run once, on Python 3.10, over every package and the root.
  - Why: they give the same result on every interpreter, and on the floor a syntax newer than 3.10
    fails.
- `make coverage` runs on Python 3.10 to 3.14.
  - Why: the action runs on whatever Python ≥ 3.10 the caller puts on `PATH`.
- `integration.yml`'s action jobs run the action through `uses: ./` over the committed fixtures, so
  a failed run fails the job, then assert on the files written and on the `output-path` output.
  - `Action - Commands Over the Fixtures` runs `normalize-issues` and `coverage-matrix` and uploads
    what they wrote as the `action-output` artifact.
  - It checks the repository out under `toolkit/`, runs the action as `uses: ./toolkit`, and puts a
    `click.py` that exits in the workspace. Why: with `uses: ./` the action's directory is the
    working directory, so the job would still pass without the `cd` into `$GITHUB_ACTION_PATH` or
    without the CLI's `-I`.
  - The 3.9 job runs the action with `continue-on-error` and asserts the failure.
  - Why: a run that passed without writing its file would be a broken action.
- The jobs need only `contents: read`: they run the repository's code and make no GitHub API call.
- The isolation job installs `pydantic<2` into the runner's interpreter and compares its `python`,
  version and pydantic before and after. It runs on 3.12, a version pydantic 1.x publishes wheels for.
  - Why: the toolkit's packages need pydantic 2, so an action on that interpreter would fail its
    import check, and an action installing into it would replace that pydantic.
- It proves the reuse by `pyvenv.cfg`'s mtime, unchanged across its runs of the action.
  - Why: `python -m venv` without `--clear` keeps the files already in the directory, so a marker
    file survives a re-create; `pyvenv.cfg` is rewritten on every create.
- It runs `normalize-issues`, then `coverage-matrix`, then `normalize-issues` again with `view` and
  `document-title`. It then replays `main.py` on the action's venv, as the action runs it, and
  expects the command's success line and the `output-path` line.
  - Why: a failed install would stop on an import, and a wrong input on reading it.
- The rebuild job runs the action on 3.12, switches `setup-python` to 3.11, runs it again, and asks
  the venv's own interpreter for its version.
  - Why: the isolation job runs on one Python, so it cannot see the interpreter comparison; a reused
    venv would still report 3.12, so the version proves the rebuild, where an mtime would not.
- The 3.9 job asserts that `PATH`'s Python is 3.9 before it checks the failure.
  - Why: otherwise it would also pass if `setup-python` resolved something newer and the action
    failed for another reason.

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
