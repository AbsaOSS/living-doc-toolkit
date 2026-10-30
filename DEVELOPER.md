# Living Documentation Toolkit: developer guide

## Purpose

This page is how to change this repository: setup, the layout, the quality gates, the test data, the local runs,
the action's venv, CI, and the rules for writing documentation. Anyone who changes the code or the pages reads it.

Read before: [README](README.md) · Next: [Contributing](CONTRIBUTING.md)

## Contents

- [Setup](#setup)
- [Layout](#layout)
- [Gates](#gates)
- [Test data](#test-data)
- [CLI run](#cli-run)
- [Debug run](#debug-run)
- [Local Integration Run](#local-integration-run)
- [Action venv](#action-venv)
- [CI](#ci)
- [Writing documentation](#writing-documentation)

## Setup

1. Clone the repository: `git clone https://github.com/AbsaOSS/living-doc-toolkit.git`, then `cd living-doc-toolkit`.
2. Use Python 3.10 or later; create and activate a venv: `python3 -m venv .venv`, then `source .venv/bin/activate`.
3. Run `make install`: `requirements-dev.txt`, then every package editable with its `[dev]` extra, in dependency order → `Makefile::install`

- The supported floor is 3.10, `requires-python = ">=3.10"` in every package; CI runs 3.10 to 3.14 → `packages/core/pyproject.toml::requires-python`
- Run every install from the repository root: pip reads `./packages/...` against the directory it runs in, not against the file.
- To install the toolkit as the action does, not editable: `pip install -r requirements.txt` in a fresh venv.

<!-- over limit: one row per file; the columns are what each file holds and who installs it -->
| File | What it holds | Who installs it |
|---|---|---|
| `requirements.txt` | Runtime only: the `living-doc-utilities==0.8.0` pin, then `./packages/core`, `./packages/services/normalize_docs`, `./packages/services/normalize_tests`, `./packages/services/coverage_matrix`, `./apps/cli`, in dependency order | `action.yml`, into its venv, on every run; a plain install, above |
| `requirements-dev.txt` | `-r requirements.txt`, the gate and test tools pinned, and `PyYAML` for the root tests | `make install` and CI |

- Each package declares its own runtime dependencies in its `pyproject.toml`; `requirements.txt` names the packages, not their dependencies, with one exception: the `living-doc-utilities` pin.
  - Every package declares `living-doc-utilities==0.8.0`, from PyPI, as each imports it; one pin, the same in each.
  - `requirements.txt` pins the same version, so the file the action installs names the contract version it runs on.
- Every package declares the toolkit's one version, `0.1.0`, the version the action's release tag carries → `packages/core/src/living_doc_core/__init__.py::__version__`
  - `metadata.producer.version` of a file the toolkit writes is read from the installed `living-doc-core`, so a release changes every package's version together.
- The development tools live in both places. Each package's `[dev]` extra keeps the ranges that package needs on its own; `requirements-dev.txt` pins the versions `make install` and CI use.
- `requirements.txt` carries no `-e`. `make install` gives the editable install for development; the action and a plain install need a plain one.
  - Why the order in `make install`: a later `pip install -r requirements.txt` would reinstall the packages non-editable.
  - Why two calls: one call holding both `./packages/core` and `-e packages/core` does not resolve.
- A plain install builds each package in place and leaves a `build/` directory beside its `src/`; each package's mypy `exclude` skips it → `packages/core/pyproject.toml::build/`
  - Why: `make types-<alias>` runs `mypy .`, which would otherwise find every module twice.
- A new package under `packages/` or `apps/` goes into `requirements.txt` after the packages it depends on.
  - Why: the toolkit's packages are not on PyPI; a package depending on an unlisted one fails with "No matching distribution found".
- A development tool goes into `requirements-dev.txt`, never `requirements.txt`.
  - Why: the action installs `requirements.txt` on every run.
- Dependabot covers both files from its `pip` entry on `/`, beside one entry per package directory → `.github/dependabot.yml::pip-root`
  - Each package entry, and the root entry, ignores `living-doc-utilities`: its pin moves by hand, in every package and in the root `requirements.txt`, in one change.
    - Why: an entry updates only its own directory, so its bump moves one pin and the five packages stop installing together.
    - A new `living-doc-utilities` is also a contract change, made in its own issue.

## Layout

| Path | Package | What it holds |
|---|---|---|
| `packages/core` | `living-doc-core` | Logging, the shared envelope, reader table, input validation, view filter and CI run context ([README](packages/core/README.md)) |
| `packages/services/normalize_docs` | `living-doc-service-normalize-docs` | The `normalize-docs` transform and its lineage table ([README](packages/services/normalize_docs/README.md)) |
| `packages/services/normalize_tests` | `living-doc-service-normalize-tests` | The `normalize-tests` transform and its lineage table ([README](packages/services/normalize_tests/README.md)) |
| `packages/services/coverage_matrix` | `living-doc-service-coverage-matrix` | The `coverage-matrix` transform and its lineage table over both inputs ([README](packages/services/coverage_matrix/README.md)) |
| `apps/cli` | `living-doc-cli` | The `living-doc` command group; registers `normalize-docs`, `normalize-tests` and `coverage-matrix` ([README](apps/cli/README.md)) |

- A package directory `packages/<group>/<name>` is named by the group's singular and its name: the distribution `living-doc-<kind>-<name>`, with `-` for `_`, and the import `living_doc_<kind>_<name>` → `packages/services/normalize_docs/pyproject.toml::living-doc-service-normalize-docs`
  - So `packages/services/normalize_docs` is `living-doc-service-normalize-docs`, imported as `living_doc_service_normalize_docs`.
  - The packages ship only inside the action's release, never on PyPI.
  - Why the prefix: the packages share the action's venv with `living_doc_utilities` and its dependencies; `living_doc_` keeps them apart.
  - `<kind>` is this repository's convention.
- Each command's transform is a package of its own under `packages/services/`, with its lineage table in it.
- Each package has its own `pyproject.toml`, `src/` layout and `tests/` directory; its gates run from inside its directory, as CI runs them → `Makefile::dir-core`
- The toolkit's packages ship no `py.typed`, so a package that imports another reads its annotations through a mypy `follow_untyped_imports` override in its `pyproject.toml`, as the root does for `living_doc_core` → `pyproject.toml::follow_untyped_imports`
- The repository root holds the action: `action.yml`, its entry point `main.py`, the local run's `local-integration.sh` and `tools/`, and the root `tests/` for them. The root gates run from the root with the root `pyproject.toml` → `Makefile::ROOT_PY`

## Gates

`make qa` runs `format-check`, `lint`, `types`, `deptry` and `test` on every package, then the root's gates (`qa-root`),
then `no-vendored-schemas`, and stops at the first failure → `Makefile::qa`. Run it before opening a pull request.

<!-- over limit: one row per target; the columns are what each gate needs and cannot be shortened -->
| Target | Runs | Gate | One package | The root | Old name |
|---|---|---|---|---|---|
| `make qa` | the five package gates, then `qa-root`, then `no-vendored-schemas` | every gate below | `qa-<alias>` | `qa-root`: every root gate, no `deptry` | `py-qa` |
| `make format` | ruff autofix, then Black, rewriting files | line length 120 | `format-<alias>` | `format-root`: `main.py`, `tools/`, `tests/` | `black` |
| `make format-check` | Black in check mode, no writes | line length 120 | `format-check-<alias>` | `format-check-root`: `main.py`, `tools/`, `tests/` | — |
| `make lint` | ruff, then Pylint over the tracked `*.py` outside `tests/` | Pylint ≥ 9.5 / 10 | `lint-<alias>` | `lint-root`: ruff over `main.py`, `tools/`, `tests/`; Pylint over `main.py`, `tools/` | `pylint` |
| `make types` | mypy, `[tool.mypy]` `python_version = "3.10"` | clean | `types-<alias>` | `types-root`: `main.py`, `tools/` | `mypy` |
| `make deptry` | deptry | no undeclared, unused or transitive dependency | `deptry-<alias>` | none | — |
| `make test` | pytest over `tests/`; each `pyproject.toml` adds coverage with `pytest-cov` | pass, coverage ≥ 80 % | `test-<alias>` | `test-root`: `tests/`, measuring `main.py` and `tools/` | `pytest-unit` |
| `make coverage` | pytest with `--cov=src --cov-fail-under=80` on the command line; `--cov-report=html` writes `<package>/htmlcov/index.html` | coverage ≥ 80 % | `coverage-<alias>` | `coverage-root` | — |
| `make no-vendored-schemas` | `living-doc-utilities`' vendored-schema check over the whole repository | no tracked `*-schema.json` or `*.schema.json` outside a `tests/` directory | none | none | — |

- The aliases are `core`, `normalize-docs`, `normalize-tests`, `coverage-matrix` and `cli` → `Makefile::ALIASES`
- Each aggregate target but `deptry` and `no-vendored-schemas` runs its root form too → `Makefile::ROOT_TARGETS`
- An old name, and its `-<alias>` form, prints a deprecation notice and runs the new target; they stay for one release → `Makefile::DEPRECATED`
- `test.yml` runs the same targets, so local runs and CI never drift → `.github/workflows/test.yml::coverage`
- `make help` lists every target → `Makefile::help`
- Black, ruff, Pylint, mypy and pytest read their settings from each package's `pyproject.toml`; one file: `cd packages/core && pylint src/living_doc_core/input_validation.py` → `packages/core/pyproject.toml::tool.pylint`
- mypy checks against the 3.10 floor, so a standard-library use newer than 3.10 fails → `packages/core/pyproject.toml::python_version`
- `deptry` fails on an import its package does not declare, on a declared dependency nothing imports, and on an import that only arrives through another package → `packages/core/pyproject.toml::tool.deptry`
  - Each package sets `optional_dependencies_dev_groups = ["dev"]`, because the `[dev]` extra holds only tools, and `known_first_party`, its own `src/` package.
  - It has no root form: the root declares no package, and `main.py` imports only the standard library and `living_doc_core`, which `requirements.txt` installs.
- `no-vendored-schemas` is R12 check 1 of `living-doc-utilities`' [component checks](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/component-checks.md): no repository but `living-doc-utilities` commits a contract schema → `Makefile::check_no_vendored_schemas`
  - It reads git's index, so a file not yet added is not seen, and it skips anything under a `tests/` directory.
  - Why: the contract models and schemas come from the installed `living-doc-utilities`; a committed copy stops tracking it, and nothing reports that.
- R12 check 2, one read path and one write path, is the code's. Every read goes through `read_artifact` and returns a contract model → [The reader table](packages/core/README.md#the-reader-table)
  - Every write goes through `write_artifact` from a contract model: each command's § What a run does, [normalize-docs](packages/services/normalize_docs/README.md#what-a-run-does), [normalize-tests](packages/services/normalize_tests/README.md#what-a-run-does), [coverage-matrix](packages/services/coverage_matrix/README.md#what-a-run-does).
- R12 check 3 and R11 are each transform's own tests: the full-sample test, and `assert_complete` over its lineage table → each command's § Lineage, [normalize-docs](packages/services/normalize_docs/README.md#lineage), [normalize-tests](packages/services/normalize_tests/README.md#lineage), [coverage-matrix](packages/services/coverage_matrix/README.md#lineage)
- The page checks in `tests/docs/` are root tests, so `make test` and `make qa` run them → [Checks](#checks)

## Test data

- `tests/fixtures/collector-gh/` holds the one copy of `living-doc`'s example `doc-source.json` and `ui-tests.json`, with their source noted beside them; every package's tests and `integration.yml` read it → [README](tests/fixtures/collector-gh/README.md)
- `tests/fixtures/utilities-golden/` holds `living-doc-utilities`' six golden entities, which `packages/services/normalize_docs`' tests read → [README](tests/fixtures/utilities-golden/README.md)
- Each command's golden output is in its package's `tests/expected/`, with how to regenerate it → [normalize-docs](packages/services/normalize_docs/tests/expected/README.md), [normalize-tests](packages/services/normalize_tests/tests/expected/README.md), [coverage-matrix](packages/services/coverage_matrix/tests/expected/README.md)
- Each command runs end to end over the fixtures against its golden, and through the entry point → `tests/test_main.py::test_the_entry_point_runs_coverage_matrix_over_the_fixture_pair_and_sets_the_output_path`
- Each command's change brings its own end-to-end tests and its step in `integration.yml`'s `action-run` → [CI](#ci)

## CLI run

After `make install`, `living-doc` runs the commands over the fixtures; every option is in the [CLI reference](apps/cli/README.md).

```shell
living-doc --version
living-doc --help
living-doc --verbose normalize-docs --input tests/fixtures/collector-gh/doc-source.json \
  --output output/generator-ready.json --view release
living-doc normalize-tests --input tests/fixtures/collector-gh/ui-tests.json \
  --output output/ui-test-catalog.json
living-doc coverage-matrix --doc-input tests/fixtures/collector-gh/doc-source.json \
  --tests-input tests/fixtures/collector-gh/ui-tests.json --output output/coverage-matrix.json --fail-under 50
```

## Debug run

The run of `main.py` as the action runs it, in the development venv, from the repository root after `make install`.
What it checks and the lines it fails with: [Errors](docs/action.md#errors).

```shell
export INPUT_COMMAND=normalize-docs
export INPUT_INPUT=tests/fixtures/collector-gh/doc-source.json
export INPUT_OUTPUT=output/generator-ready.json
export INPUT_VERBOSE_LOGGING=true      # optional: --verbose and DEBUG lines; default false; RUNNER_DEBUG=1 too
python3 main.py                        # writes output/generator-ready.json
```

- Each input is an `INPUT_<NAME>` variable, upper case with `_` for `-`, as `action.yml` passes it → `action.yml::INPUT_DOCUMENT_TITLE`
- Without `GITHUB_OUTPUT`, as outside GitHub Actions, the run sets no `output-path` output and logs that once → `tests/test_main.py::test_a_run_outside_github_actions_sets_no_output_and_says_so`
- `tests/test_main.py` replaces the CLI to test the run itself: the command line, the exit code passed through, and `output-path` → `tests/test_main.py::test_a_failed_command_ends_the_run_with_its_exit_code_and_sets_no_output`
  - It also runs `normalize-docs`, `normalize-tests` and `coverage-matrix` through the entry point over their fixtures, for real.

## Local Integration Run

`local-integration.sh` runs the real toolkit over a given `doc-source.json` and `ui-tests.json`, on the machine that
has them, outside any workflow. It runs the three commands through `main.py` in a venv of its own, re-reads every
output with `read_artifact`, and prints what ran and what came out. No workflow runs it; like any local run, it is a
development and operator-check affordance, not a second supported deployment target.

- The usual inputs are the two files a `living-doc-collector-gh` run wrote: its [Local Integration Run](https://github.com/AbsaOSS/living-doc-collector-gh/blob/master/DEVELOPER.md#local-integration-run) says where they land. The script never derives another component's paths; you configure both files → `.env.local.example::DOC_INPUT`

### What You Prepare

The script checks the Python version, `git` and the two inputs, and nothing else of the environment → `local-integration.sh::--check`. The rest is yours:

- **Python ≥ 3.10**, with its `venv` module. The script uses `PYTHON` from `.env.local` when set, else `python3`, else `python` from `PATH`, the order `action.yml` uses.
  - On Git Bash for Windows, `python3` may be the Microsoft Store alias, which does not run: set `PYTHON=python`.
- **`git`** on `PATH`: the report's header names this repository's commit.
- **Network and pip configuration** that lets `pip install -r requirements.txt` succeed: `pip.conf`, `PIP_INDEX_URL`, `PIP_FIND_LINKS`, a proxy. The script leaves them as they are.
- **A POSIX shell**: bash 3.2 or later; Linux, macOS, or Git Bash on Windows.

No token: every command reads local files and calls no API, so the script reads no credential.

- It unsets `GITHUB_TOKEN`, `GH_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN` and every inherited `INPUT_*` before it starts anything → `local-integration.sh::GH_TOKEN`
- `.env.local` is read as data, never sourced. A token left in it is ignored; the script reports its line by number, never its text.

### Configure It

```shell
cp .env.local.example .env.local      # .env.local is git-ignored
```

As committed, the example runs over the fixture pair in `tests/fixtures/collector-gh/`, unchanged.

| Key | Required | What it sets |
|---|---|---|
| `DOC_INPUT` | yes | the documentation input, a `doc-source` artifact: `normalize-docs` and `coverage-matrix` `input` |
| `TESTS_INPUT` | yes | the tests input, a `ui-tests` artifact: `normalize-tests` `input`, `coverage-matrix` `tests-input` |
| `VIEW` | no | `view` for `normalize-docs` and `coverage-matrix`: `inner` (the default) or `release` |
| `OUT_DIR` | no | the output root, default `./output` (git-ignored) |
| `PYTHON` | no | the interpreter the venv is built from |

- A relative path resolves against this repository's root; `~/` is the home directory.
- One `KEY=value` per line; a line starting with `#` is a comment, and values are taken literally.

### Run It

```shell
./local-integration.sh --check   # Python, git, the configuration and both inputs; creates no venv, runs nothing
./local-integration.sh           # the run
```

A run, in order:

1. **Checks** what `--check` checks. A missing setting or input file, an input inside a directory the run clears, a `VIEW` other than `inner` or `release`, or a Python below 3.10 stops it with one line that names it.
2. **Builds its venv**, `.venv-local-integration/` (git-ignored), separate from the development `.venv`. It installs only `requirements.txt` (`pip install -r`), from the repository root: a runtime requirement missing from that file fails here, as on a runner.
   - It follows [Action venv](#action-venv): the same six variables unset, the same import check after the install, and `main.py` run with `-E`.
   - The venv is reused only when the same interpreter built it from the same `requirements.txt`.
3. **Prints what runs**: this repository's commit, the installed `living-doc-utilities` version, the Python version, both inputs, the view and the output directory. The commit is marked when tracked files differ from it.
4. **Runs `normalize-docs`, `normalize-tests`, then `coverage-matrix`**, each as its own `main.py` run with only the inputs it takes ([Inputs](docs/action.md#inputs)), into `$OUT_DIR/toolkit/<command>/`, having cleared the three directories first. Each command is echoed before it runs.
   - A command that fails stops the run with one line naming it, after the toolkit's own error lines. A `DOC_INPUT` that is not a `doc-source` artifact stops `normalize-docs` with `[CONTRACT_MISMATCH]`.
5. **Validates and reports** each output → `tools/local_integration.py::report`
   - It re-reads the output with `read_artifact` against its contract, then prints its producer, run time, size and `metadata.stats.cardinality`, and for `coverage-matrix` the root `summary`.
   - It prints each `metadata.source_inputs[]` entry: the input's contract, the producer that wrote it, `source.project_id` and `source.repositories`.
   - It prints the warnings by code: each code's count and its first ten occurrences.
   - Per input, it matches each of the input's warnings to one the output carries unchanged, every field the same but the context, which names the input first. It prints how many matched beside the input's own count; one that does not match fails the run ([`errors.md` § Forwarded warnings](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md#forwarded-warnings)).
   - In the report, text from the files is printed with control characters spelled out (`\n`, `\x1b`), so an input cannot forge a report line. The toolkit's own log lines above it are printed as the toolkit writes them.

- It exits non-zero when a check, the install, a command or a validation fails → `tools/local_integration.py::main`
- Outside GitHub Actions every `metadata.run` field is empty; the inputs' producers in `metadata.source_inputs[]` say where the run's data came from.
- For an issue or a report, keep the whole output: `set -o pipefail; ./local-integration.sh 2>&1 | tee local-integration.log`.

## Action venv

`action.yml` runs the toolkit in a venv of its own, built from the caller's Python. The rules are
`living-doc-generator-markdown`'s; what differs here follows them. What the caller provides, and the lines the step
fails with: [Prerequisites](docs/action.md#prerequisites), [Errors](docs/action.md#errors).

- `PIP_TARGET`, `PIP_PREFIX`, `PIP_USER`, `PIP_ROOT`, `PIP_PYTHON` and `PYTHONPATH` are unset before the install → `action.yml::PIP_TARGET`
  - Why: pip reads them as configuration; an exported one would empty or shadow the venv, or (`PIP_PYTHON`) target the caller's interpreter.
- The venv is reused only when the interpreter now on `PATH` built it, compared as `sys.base_prefix` plus version; otherwise it is rebuilt → `action.yml::IDENTITY`
- After the install, one import of `living_doc_cli.main` through the venv's interpreter proves the packages landed there → `action.yml::living_doc_cli.main`
- `main.py` runs with `-E`, so a caller's `PYTHONPATH` cannot shadow the venv → `action.yml::-E`
- Every input reaches `main.py` through the run step's `env:`; no `run:` script holds `${{ inputs.* }}` → `action.yml::INPUT_COMMAND`
- `main.py` runs `python -I -m living_doc_cli.main <command> --<option>=<value> …` on the venv's interpreter; `-I` is `-E` that also keeps the working directory off `sys.path` → `main.py::run`
  - Why: the step runs in the caller's checkout, which `python -m` searches first; a `click.py` or `json.py` would shadow the venv's.
- `tests/test_action_yml.py` runs the venv step against a fake interpreter; `integration.yml` shows the reuse, the rebuild on an interpreter change, and the rejection of Python 3.9 on real ones ([CI](#ci)) → `tests/test_action_yml.py::test_the_venv_is_reused_when_the_interpreter_on_path_built_it`

What differs from `living-doc-generator-markdown`:

- The install and the import check run from the action's own directory, `$GITHUB_ACTION_PATH` → `action.yml::GITHUB_ACTION_PATH`
  - Why: pip reads `requirements.txt`'s `./packages/...` against its working directory; from the caller's workspace they do not exist.
  - Why the variable, not `${{ github.action_path }}`: in a `container:` job the expression gives the runner host's path, which does not exist inside the container.
- The import check imports `living_doc_cli.main`, which imports `click`, the CLI package and each command it registers, with the packages those commands import: the three services, `living-doc-core` and `living-doc-utilities`.
- pip rebuilds a local directory on every install, so each run reinstalls the five packages into the reused venv; their dependencies stay installed.

## CI

`test.yml` runs the gates, `integration.yml` runs the action itself, and `link-check.yml` checks the Markdown links.

- The checks to mark as required are `QA Gate` and every `integration.yml` job.
  - `QA Gate` always runs, passes over a skipped job and fails on a failed or cancelled one. Why: a required check must report on every pull request, also on one that changed no Python.
  - `integration.yml` runs on every pull request to `master`, so its jobs always report. Why: its jobs are the only ones that run the action itself; without them a broken action merges green.
- The static checks and the tests run when a Python-related file changed: `*.py`, `requirements.txt`, `requirements-dev.txt`, a `pyproject.toml`, a `tests/fixtures/` file, a `*-schema.json` or `*.schema.json` file, `Makefile`, `action.yml` or `test.yml` → `.github/workflows/test.yml::python_changed`
  - The fixtures are in the list because `packages/core`'s tests read them.
  - Schema files are in the list because `no-vendored-schemas` fails on one.
  - `action.yml` is in the list because `tests/test_action_yml.py` reads it.
- The tests also run when a page, `action.yml`, a shell script, an `.example` file, `dependabot.yml` or a workflow changed → `.github/workflows/test.yml::docs_changed`
  - Why: `tests/docs/` checks every page against the code, and the root tests read the local run's script and its example configuration.
- On a pull request a renamed file counts by its old path too, so moving a file out of either set still runs the tests → `tests/docs/test_ci_filter.py::test_a_rename_lists_its_old_path_too`
- A manual run runs every gate, and a manual run of `link-check.yml` checks every page.
  - Why: a manual run is a request to re-check the branch, whatever its last commit touched.
- `format-check`, `lint`, `types`, `deptry` and `no-vendored-schemas` run once, on Python 3.10, over every package and the root.
  - Why: they give the same result on every interpreter, and on the floor a syntax newer than 3.10 fails.
- `make coverage` runs on Python 3.10 to 3.14.
  - Why: the action runs on whatever Python ≥ 3.10 the caller puts on `PATH`.
- `integration.yml`'s jobs run the action through `uses: ./` over the committed fixtures; they have no local form, as they need a GitHub runner.
- `action-run` runs each command the action runs and checks what it wrote: `normalize-docs` over `doc-source.json` in the release view, `normalize-tests` over `ui-tests.json`, and `coverage-matrix` over both in the release view.
  - It reads the file with `read_artifact` on the action's venv, checks `document.view`, the `selection_summary`, the feature files or the root coverage summary and a keyword row's status and keyword, and that `metadata.run.run_id` is the job's `GITHUB_RUN_ID` and `producer.build` is `null`, and checks that `output-path` is the file's absolute path.
- The venv jobs run `normalize-docs`, and the isolation job also runs `coverage-matrix`; each writes its file.
  - Each run step has `continue-on-error`, and the job asserts its `outcome`: `success` for each.
  - A step cannot read another step's log, so each job then replays the run's inputs on the action's venv, as the run step runs `main.py`. Each replay asserts exit code 0, `output-path` and the file.
    - Why: a failed install fails the step too; the replay shows the venv imports and the run ends where it should.
  - Each job reads the files the run steps wrote too, with `read_artifact`: valid `generator-ready` files, in the isolation job with the view and title the step gave, and a `coverage-matrix` file with the fixture pair's counted criteria.
- The jobs need only `contents: read`: they run the repository's code and make no GitHub API call.
- The isolation job installs `pydantic<2` into the runner's interpreter and compares its `python`, version and pydantic before and after. It runs on 3.12, a version pydantic 1.x publishes wheels for.
  - Why: the packages need pydantic 2, through `living-doc-utilities`; on that interpreter the action's import check would fail.
  - An action installing into that interpreter would replace its pydantic.
- It proves the reuse by `pyvenv.cfg`'s mtime, unchanged across its runs of the action.
  - Why: `python -m venv` without `--clear` keeps existing files, so a marker survives a re-create; `pyvenv.cfg` is rewritten every time.
- It runs `normalize-docs`, then `coverage-matrix`, then `normalize-docs` again with `view` and `document-title`, and replays all three.
- The rebuild job runs the action on 3.12, switches `setup-python` to 3.11, runs it again, and asks the venv's own interpreter for its version after each run.
  - Why: the isolation job has one Python, so it cannot test the interpreter comparison.
  - A reused venv would still report 3.12, so the version proves the rebuild, where an mtime would not.
- The 3.9 job runs the action with `continue-on-error` and asserts the failure, and that no venv exists. It asserts that `PATH`'s Python is 3.9 before it checks the failure.
  - Why: otherwise it would also pass if `setup-python` resolved something newer and the action failed for another reason.
- The 3.9 job runs on `ubuntu-24.04`; every other job runs on `ubuntu-latest`.
  - Why: `setup-python` publishes no 3.9 for `ubuntu-latest` (26.04), so the job would fail setting up Python before the action runs.

## Writing documentation

> **Provisional.** These rules are a pilot; the owner tunes them after this first rebuild, and a skill may replace
> this section. This section is their only copy in the repository.

### Depth

Depth is where a page sits in the folder tree. Deeper means more detail.

| Depth | Pages | Rule |
|---|---|---|
| 1 | `README.md`; `DEVELOPER.md`, `CONTRIBUTING.md` and `SPEC.md` | `README.md` is the entry: what the action is for, overview, usage tip, inputs and outputs at a glance, "where next". The other three are solo: one page each, no child pages |
| 2 | `docs/<topic>.md` | a hub: principle, decision list, routing to depth 3; it names and links facts, and defines none |
| 2 leaf | `docs/<topic>.md` with no `docs/<topic>/` folder; a package's `README.md`, beside its `pyproject.toml` | a leaf may define, like a depth-3 page |
| 3 | `docs/<topic>/<page>.md` | detail: fact lists, option lists, examples |

- One fact, one page: define a fact on the deepest page that needs it; shallower pages name it and link.

### Every page

1. `# Title`.
2. `## Purpose`: 1 to 3 sentences, who reads the page and what they get; then `Read before:` and `Next:` links where the page sits on a reading path.
   - `README.md` is the exception: its Purpose says what the action does and where it sits in the pipeline.
     Why: GitHub shows the README as the repository's front page, so it opens with the action, not the page.
3. `## Contents`: links to every other `##` chapter of the page, and nothing else.
4. Only the parts the page needs.

### Parts

| Part | Form | Checked against |
|---|---|---|
| Principle | at most 5 short sentences: the core idea | review |
| Decision list | one line per decision; the page's code map names where the code realises it | code, through the code map |
| Fact list | one line per fact the code relies on; the page's code map names its `path::symbol`, or a test | code, through the code map |
| Why | one indented `Why:` line under a rule, decision or fact, at most 20 words | review |
| Option list | every available option with a one-line meaning; complete | the input, output, command, option or code list in code |
| Example | at most 20 lines; run or parsed by a test | tests |
| Prose | only in Purpose, Principle and one-line list lead-ins; a block is at most 4 lines | review |
| Language | sentences of at most 20 words; active voice; one term per idea, the glossary's | review |

### Limits

- The limits (prose block 4 lines, sentence 20 words, example 20 lines) are targets, not hard caps.
- Exceed one only with a reason, stated next to the block: `<!-- over limit: <reason> -->`.
- Keep the overrun small; split the block when you can.

### Anchors

- A page states facts for people and carries no `path::symbol`. The `CONTEXT.md` beside the code holds the page's code map.
  - A code map is a `## Code map` chapter, one line per fact: `fact → path::symbol`. `tests/docs/pages.py::CODE_MAPS` pairs each depth-2 page with its map.
  - Why: an agent needs the anchor; a reader needs the fact.
- `DEVELOPER.md` may carry anchors: its readers work in the `Makefile`, the workflows and the scripts.
- A changed fact changes the page and its code map together.
- `path` is relative to the repository root, through a package's `src/`: `packages/core/src/living_doc_core/readers.py::READERS`.
- `symbol` is a module-level name, or a dotted one for a member: `InputProblem.__str__`.
- A test is `tests/<path>.py::test_name`; a non-Python file names a text it contains: `Makefile::qa`.
- Never use line numbers; they drift.
- A rule another component must realise names that component instead of an anchor: `→ utilities`, `→ collector-gh`.
- Every code-map item ends in `→` and an anchor, a component or a link.
- `README.md` is no PyPI description, so it links repository files relatively: `docs/action.md`.
  - A package's `README.md` is its `pyproject.toml` `readme`, but the packages never reach PyPI, so it links relatively too.

### Examples

- A `yaml` block must parse; every `with:` key it gives this action must be an `action.yml` input.
- Every `uses:` of this action names the same release, so a release bump changes them all.
- A `json` block must parse; a test runs every `python` block, each in a fresh namespace and a temporary directory.
- A `shell` block is a command line, not an example; it is not run.

### Checks

| Check | Where |
|---|---|
| page list and depths, `Purpose` then `Contents`, Contents links, no orphan page, README links relative | `tests/docs/test_page_structure.py` |
| every `path::symbol` on a page or in a code map resolves; no line-number anchor; no anchor on a page but `DEVELOPER.md`; every depth-2 page has a code map, each item saying where it is realised | `tests/docs/test_anchors.py` |
| every example parses or runs; every `with:` key is an `action.yml` input; one release named | `tests/docs/test_examples.py` |
| the input and output lists equal `action.yml`; each input's commands equal `main.py::COMMAND_INPUTS`; the command list equals it and the CLI's; each command's options equal the CLI's; every code a page names is in `ALL_CODES` | `tests/docs/test_option_lists.py` |
| links and `#fragments` resolve | `.github/workflows/link-check.yml::lychee` |
| a pull request that changes only a page, a code map, `action.yml`, the local run's script or a file an anchor names still runs these tests | `.github/workflows/test.yml::docs_changed`, `tests/docs/test_ci_filter.py` |

To add a page: put it at its depth, add it to `tests/docs/pages.py::APPROVED_PAGES`, and link it from `README.md`; at
depth 2, add its code map and pair the two in `tests/docs/pages.py::CODE_MAPS`.
