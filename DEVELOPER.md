# Living Documentation Toolkit — Developer Guide

- [Get Started](#get-started)
- [Monorepo Layout](#monorepo-layout)
- [QA Automation with Make](#qa-automation-with-make)
- [Running Static Code Analysis](#running-static-code-analysis)
- [Run Black Tool Locally](#run-black-tool-locally)
- [Run mypy Tool Locally](#run-mypy-tool-locally)
- [Dependency and Contract Checks](#dependency-and-contract-checks)
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
pip install -e "packages/services/normalize_docs[dev]"
pip install -e "apps/cli[dev]"
```

| File | What it holds | Who installs it |
|---|---|---|
| `requirements.txt` | Runtime only: the three package directories, each after the ones it depends on (`./packages/core`, `./packages/services/normalize_docs`, `./apps/cli`) | `action.yml`, into its venv, on every run; the README Quickstart |
| `requirements-dev.txt` | `-r requirements.txt`, the gate and test tools pinned, and `PyYAML` for `tests/test_action_yml.py` | `make install` and CI |

- Each package declares its own runtime dependencies in its `pyproject.toml`; `requirements.txt`
  names the packages, not their dependencies.
  - Every package declares `living-doc-utilities==0.7.0`, from PyPI, as each imports it; one pin, the same in each.
- Every package declares the toolkit's one version, `0.1.0`, the version the action's release tag carries.
  - `metadata.producer.version` of a file the toolkit writes is read from the installed `living-doc-core`, so a
    release changes every package's version together.
- The development tools live in both places. Each package's `[dev]` extra keeps the ranges that
  package needs on its own; `requirements-dev.txt` pins the versions `make install` and CI use.
- Run both installs from the repository root: pip reads `./packages/...` against the directory
  it runs in, not against the file.
- `requirements.txt` carries no `-e`. `make install` gives the editable install for development;
  the action and the Quickstart need a plain one.
  - Why the order in `make install`: a later `pip install -r requirements.txt` would reinstall the
    packages non-editable, and one call holding both `./packages/core` and `-e packages/core`
    does not resolve.
- A plain install builds each package in place and leaves a `build/` directory beside its `src/`.
  Each package's mypy `exclude` skips `build/`.
  - Why: `make types-<alias>` runs `mypy .`, which would otherwise find every module twice.
- A new package under `packages/` or `apps/` goes into `requirements.txt` after the packages it
  depends on, and a development tool goes into `requirements-dev.txt`, never `requirements.txt`.
  - Why: the toolkit's own packages are not on PyPI, so a package that depends on an unlisted one fails
    the install with "No matching distribution found"; and the action installs `requirements.txt` on
    every run.
- Dependabot covers both files from its `pip` entry on `/`, beside one entry per package
  directory, in `.github/dependabot.yml`.

## Monorepo Layout

| Path | Package | Description |
|---|---|---|
| `packages/core` | `living-doc-core` | Logging, the reader table, the shared input validation and the view filter ([README](packages/core/README.md)) |
| `packages/services/normalize_docs` | `living-doc-service-normalize-docs` | The `normalize-docs` transform and its lineage table ([README](packages/services/normalize_docs/README.md)) |
| `apps/cli` | `living-doc-cli` | CLI entry point (`living-doc` command group); registers `normalize-docs` ([README](apps/cli/README.md)) |

- A package directory `packages/<group>/<name>` is the distribution `living-doc-<group>-<name>` and the import
  `living_doc_<group>_<name>`.
- Each command's transform is a package of its own under `packages/services/`, with its lineage table in it.
- The toolkit's packages ship no `py.typed`, so a package that imports another reads its annotations through a
  mypy `follow_untyped_imports` override in its `pyproject.toml`, as the root does for `living_doc_core`.

Each package has its own `pyproject.toml`, `src/` layout, and `tests/` directory.
All quality-gate commands below are designed to run **per-package** from within the
package directory, matching how CI executes them.

The repository root holds the action: `action.yml`, its entry point `main.py`, and the root
`tests/` for both. The root gates run from the repository root with the root `pyproject.toml`
(see [Root checks](#root-checks)).

`tests/fixtures/collector-gh/` holds the one copy of `living-doc`'s example `doc-source.json` and
`ui-tests.json`, with their source noted beside them; every package's tests and `integration.yml`
read it. `tests/fixtures/utilities-golden/` holds `living-doc-utilities`' six golden entities, which
`packages/services/normalize_docs`' tests read.

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

Then run every QA gate (`format-check` → `lint` → `types` → `deptry` → `test`) on all packages,
then the [root checks](#root-checks), then `no-vendored-schemas`:

```shell
make qa
```

Show all available commands:

```shell
make help
```

### Canonical targets

Eight package targets, each with an **aggregate** form (every package) and a **per-package**
form `<target>-<alias>`, and one repository-wide target.

| Target | Runs | Gate |
|--------|------|------|
| `qa` | `format-check` → `lint` → `types` → `deptry` → `test` per package, then `qa-root`, then `no-vendored-schemas`, failing on the first | all of the below |
| `lint` | Pylint over tracked `*.py` (tests excluded) | score ≥ **9.5** / 10 |
| `format` | Black, rewriting files | line length **120** |
| `format-check` | Black `--check` (no writes) | line length **120** |
| `types` | mypy | clean |
| `deptry` | deptry, per package (no root form) | no undeclared, unused or transitive dependency |
| `test` | pytest | pass |
| `coverage` | pytest with coverage measurement | `--cov-fail-under=80` |
| `no-vendored-schemas` | R12 check 1 over the whole repository (no per-package form) | no tracked `*-schema.json` / `*.schema.json` outside `tests/` |

### Run QA for a specific package

Package aliases: `core`, `normalize-docs`, `cli`.

```shell
make qa-core                  # all gates for packages/core
make qa-normalize-docs        # packages/services/normalize_docs
make qa-cli                   # apps/cli
```

Run one gate on one package:

```shell
make format-core              # Black on packages/core
make lint-core                # Pylint on packages/core
make types-core               # mypy on packages/core
make deptry-core              # deptry on packages/core
make test-core                # tests on packages/core
make coverage-core            # tests + coverage gate on packages/core
```

### Root checks

`make qa-root` runs the gates over the root's own files. `make qa` runs it after the packages,
and each aggregate target (`make lint`, `make test`, …) except `deptry` includes its `-root` form.

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
cd packages/core && pylint src/living_doc_core/input_validation.py
```

## Run Black Tool Locally

This project uses [Black](https://github.com/psf/black) for code formatting.
Line length is set to **120 characters** (configured in each package's `pyproject.toml`).

### Run Black

Rewrite one package (`make format-<alias>`) or all of them (`make format`):

```shell
make format-core             # wraps: cd packages/core && black .
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

## Dependency and Contract Checks

```shell
make deptry-core             # wraps: cd packages/core && python -m deptry .
make deptry                  # every package
make no-vendored-schemas     # wraps: python -m living_doc_utilities.contracts.check_no_vendored_schemas
```

- `deptry` fails on an import its package does not declare, on a declared dependency nothing imports, and on an
  import that only arrives through another package. Each package configures it under `[tool.deptry]`:
  `optional_dependencies_dev_groups = ["dev"]`, because the `[dev]` extra holds only tools, and `known_first_party`,
  its own `src/` package.
  - It has no root form: the root declares no package, and `main.py` imports only the standard library and
    `living_doc_core`, which `requirements.txt` installs.
- `no-vendored-schemas` is R12 check 1 of `living-doc-utilities`' [component checks](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/component-checks.md):
  no repository but `living-doc-utilities` commits a contract schema. It reads git's index, so a file not yet added
  is not seen, and it skips anything under a `tests/` directory.
  - Why: the contract models and schemas come from the installed `living-doc-utilities`; a committed copy stops
    tracking it, and nothing reports that.
- R12 check 2, one read path and one write path, is the code's: every read goes through `read_artifact` and returns a
  contract model ([core README](packages/core/README.md#the-reader-table)), and every write goes through
  `write_artifact` from a contract model ([normalize-docs README](packages/services/normalize_docs/README.md#what-a-run-does)).
- R12 check 3 and R11 are each transform's own tests: the full-sample test, and `assert_complete` over its lineage
  table ([normalize-docs README](packages/services/normalize_docs/README.md#lineage)).

## Running Unit Tests

Unit tests are written using [pytest](https://docs.pytest.org/) and live in each
package's `tests/` directory.

### Run tests

One package (`make test-<alias>`) or all of them (`make test`):

```shell
make test-core               # wraps: cd packages/core && pytest tests/
make test                    # every package
```

`make coverage` / `make coverage-<alias>` adds the explicit `--cov=src --cov-fail-under=80`
gate that CI enforces.

## Running Integration Tests

`.github/workflows/integration.yml` runs the action itself, through `uses: ./`, on real
interpreters ([CI](#ci)). It has no local form: it needs a GitHub runner.

- Locally, `normalize-docs` runs end to end over the fixtures in `packages/services/normalize_docs`'
  tests, against committed goldens, and through the entry point in `tests/test_main.py`.
- Each command's change brings its own end-to-end tests and its step in `action-run`.

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
command is available. It registers `normalize-docs`:

```shell
living-doc --version
living-doc --help
living-doc --verbose normalize-docs --input tests/fixtures/collector-gh/doc-source.json \
  --output output/generator-ready.json --view release
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
- The import check imports `living_doc_cli.main`, which imports `click`, the CLI package and each
  command it registers, with the packages that command imports: for `normalize-docs`, its service,
  `living-doc-core` and `living-doc-utilities`.
- pip rebuilds a local directory on every install, so each run reinstalls the three packages into the
  reused venv; their dependencies stay installed.

### The entry point

`main.py` checks the inputs, then runs `python -I -m living_doc_cli.main <command> --<option>=<value> …`
on the venv's interpreter. The CLI's exit code is the step's.

- `action.yml` declares three commands, and `main.py`'s `COMMAND_INPUTS` maps each one's inputs to its
  CLI options. An unknown `command` fails with one line listing the valid commands.
- Each input goes only to the commands that take it. A non-empty input the command does not take
  fails with one line naming the input and the command. An empty one is not passed, so the CLI's
  default applies.
  - Why: `action.yml` passes every input on every run, an unset one as its empty default.
- `tests-input` and `fail-under` are `coverage-matrix`'s own inputs, as decided on issue #81; `view`
  is taken by `normalize-docs` and `coverage-matrix`, `document-title` by `normalize-docs`.
  An empty required input, `tests-input` for `coverage-matrix` included, fails with one line naming
  it, and so does a `fail-under` that is not a finite number.
- Only once the inputs pass is a command in `NOT_AVAILABLE_YET` refused, with one line:
  ``Command `<command>` is not available yet.`` `normalize-tests` and `coverage-matrix` are in it today.
  - Why last: an input the command does not take is rejected the same way for a command not available yet.
- `verbose-logging: 'true'`, in any case, adds `--verbose` after the command's options, which every
  command takes as the group does, and logs the command line at DEBUG. `INPUT_VERBOSE_LOGGING` stays
  in the run step's `env:`.
  - Why: the CLI reads no environment variable, so `--verbose` is the way in. The variable is there
    for when the toolkit reads it, as `living-doc-utilities`' logging does.
- Once the command succeeds, `output-path` is set to the absolute path of `output`.
- `tests/test_main.py` replaces the CLI to test the run itself: the command line, the exit code passed
  through, and `output-path`; it empties `NOT_AVAILABLE_YET` to test it for the two commands not
  available yet. It also runs `normalize-docs` through the entry point over the fixture, for real.

A debug run, from the repository root after `make install`:

```shell
export INPUT_COMMAND=normalize-docs
export INPUT_INPUT=tests/fixtures/collector-gh/doc-source.json
export INPUT_OUTPUT=output/generator-ready.json
export INPUT_VERBOSE_LOGGING=true      # optional: --verbose and DEBUG lines; default false
python3 main.py                        # writes output/generator-ready.json
```

- Each input is an `INPUT_<NAME>` variable, upper case with `_` for `-`, as `action.yml` passes it.
- Without `GITHUB_OUTPUT`, as outside GitHub Actions, the run sets no `output-path` output and logs
  that once.

## CI

`test.yml` runs the gates, `integration.yml` runs the action itself, and `link-check.yml` checks
the Markdown links.

- The checks to mark as required are `QA Gate` and every `integration.yml` job.
  - `QA Gate` always runs, passes over a skipped job and fails on a failed or cancelled one. Why: a
    required check must report on every pull request, also on one that changed no Python.
  - `integration.yml` runs on every pull request to `master`, so its jobs always report. Why: its
    jobs are the only ones that run the action itself; without them a broken action merges green.
- The gates run when a Python-related file changed: `*.py`, `requirements.txt`,
  `requirements-dev.txt`, a `pyproject.toml`, a `tests/fixtures/` file, a `*-schema.json` or
  `*.schema.json` file, `Makefile`, `action.yml` or `test.yml`.
  - The fixtures are in the list because `packages/core`'s tests read them.
  - Schema files are in the list because `no-vendored-schemas` fails on one.
  - `action.yml` is in the list because `tests/test_action_yml.py` reads it.
  - On a pull request a renamed file counts by its old path too, so moving a file out of that set
    still runs the tests.
- A manual run runs every gate, and a manual run of `link-check.yml` checks every page.
  - Why: a manual run is a request to re-check the branch, whatever its last commit touched.
- `format-check`, `lint`, `types`, `deptry` and `no-vendored-schemas` run once, on Python 3.10, over
  every package and the root.
  - Why: they give the same result on every interpreter, and on the floor a syntax newer than 3.10
    fails.
- `make coverage` runs on Python 3.10 to 3.14.
  - Why: the action runs on whatever Python ≥ 3.10 the caller puts on `PATH`.
- `integration.yml`'s jobs run the action through `uses: ./` over the committed fixtures.
- `action-run` runs each command the action runs and checks what it wrote: `normalize-docs` over
  `doc-source.json` in the release view.
  - It reads the file with `read_artifact` on the action's venv, checks `document.view` and the
    `selection_summary`, and checks that `output-path` is the file's absolute path.
  - `normalize-tests` and `coverage-matrix` each add their step when they land.
- The venv jobs run `normalize-docs`, which writes its file, and the isolation job also runs
  `coverage-matrix`, which fails on the "not available yet" line.
  - Each run step has `continue-on-error`, and the job asserts its `outcome`: `success` for
    `normalize-docs`, `failure` for `coverage-matrix`.
  - A step cannot read another step's log, so each job then replays the run's inputs on the action's
    venv, as the run step runs `main.py`. A `normalize-docs` replay asserts exit code 0, `output-path`
    and the file; the `coverage-matrix` one asserts exit code 1 and the "not available yet" line.
    - Why: a failed install would fail the step too; the replay shows the venv imports and the run
      ends where it should.
  - Each job reads the files the run steps wrote too, with `read_artifact`: valid `generator-ready`
    files, and in the isolation job with the view and title the step gave.
- The jobs need only `contents: read`: they run the repository's code and make no GitHub API call.
- The isolation job installs `pydantic<2` into the runner's interpreter and compares its `python`,
  version and pydantic before and after. It runs on 3.12, a version pydantic 1.x publishes wheels for.
  - Why: the toolkit's packages need pydantic 2, through `living-doc-utilities`, so an action on that
    interpreter would fail its import check, and an action installing into it would replace that
    pydantic.
- It proves the reuse by `pyvenv.cfg`'s mtime, unchanged across its runs of the action.
  - Why: `python -m venv` without `--clear` keeps the files already in the directory, so a marker
    file survives a re-create; `pyvenv.cfg` is rewritten on every create.
- It runs `normalize-docs`, then `coverage-matrix`, then `normalize-docs` again with `view` and
  `document-title`, and replays all three.
- The rebuild job runs the action on 3.12, switches `setup-python` to 3.11, runs it again, and asks
  the venv's own interpreter for its version after each run.
  - Why: the isolation job runs on one Python, so it cannot see the interpreter comparison; a reused
    venv would still report 3.12, so the version proves the rebuild, where an mtime would not.
- The 3.9 job runs the action with `continue-on-error` and asserts the failure, and that no venv
  exists. It asserts that `PATH`'s Python is 3.9 before it checks the failure.
  - Why: otherwise it would also pass if `setup-python` resolved something newer and the action
    failed for another reason.
- The 3.9 job runs on `ubuntu-24.04`; every other job runs on `ubuntu-latest`.
  - Why: `setup-python` publishes no 3.9 for `ubuntu-latest` (26.04), so the job would fail setting
    up Python before the action runs.

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
