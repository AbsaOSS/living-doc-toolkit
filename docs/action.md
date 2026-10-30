# Action reference

## Purpose

This page is the action's full reference: what the runner needs, the commands, every input and which command takes
it, the output, and the run-level errors. Workflow authors who configure the toolkit step read it.

Read before: [README](../README.md) · Next: [CLI](../apps/cli/README.md)

## Contents

- [Prerequisites](#prerequisites)
- [Commands](#commands)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Errors](#errors)

## Prerequisites

- Python 3.10 or later is on `PATH` as `python3`, or as `python` when there is no `python3`; the caller prepares it
  - Below 3.10, or with no Python, the step fails with one line before it creates anything ([Errors](#errors)).
- The action brings its own venv: it installs `requirements.txt` into `$RUNNER_TEMP/living-doc-toolkit-venv` and runs there
  - It never changes the job's interpreter, `PATH` or environment, and writes nothing to `$GITHUB_ENV` or `$GITHUB_PATH`.
  - How it builds, checks and reuses the venv: [Action venv](../DEVELOPER.md#action-venv).
- The runner reaches a package index: each run installs the pinned requirements with `pip`
- It runs on Linux runners only: the venv's POSIX `bin/` layout is assumed
- The input files are on the runner, for example written by a collector step earlier in the job
- Every command reads local files only and makes no network call, so the action takes no token

Put `actions/setup-python` before the step:

```yaml
- uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
  with:
    python-version: '3.14'
```

## Commands

One step runs one command over its input files and writes the file the command produces; every command the action
declares runs.

| Command | Reads | Writes | What a run does |
|---|---|---|---|
| `normalize-docs` | one documentation file, `doc-source.json` | `generator-ready.json`, in the `inner` or `release` view | [normalize-docs](../packages/services/normalize_docs/README.md) |
| `normalize-tests` | one tests file, `ui-tests.json` | `ui-test-catalog.json` | [normalize-tests](../packages/services/normalize_tests/README.md) |
| `coverage-matrix` | one documentation file and one tests file | `coverage-matrix.json`, with `document.view` `inner` or `release` | [coverage-matrix](../packages/services/coverage_matrix/README.md) |

The three commands chained, one step each; the first one's `id` lets a later step read its output:

```yaml
- id: normalize
  uses: AbsaOSS/living-doc-toolkit@v0.1.0
  with:
    command: normalize-docs
    input: doc-source.json
    output: output/generator-ready.json
- uses: AbsaOSS/living-doc-toolkit@v0.1.0
  with:
    command: normalize-tests
    input: ui-tests.json
    output: output/ui-test-catalog.json
- uses: AbsaOSS/living-doc-toolkit@v0.1.0
  with:
    command: coverage-matrix
    input: doc-source.json
    tests-input: ui-tests.json
    output: output/coverage-matrix.json
    fail-under: 80
```

## Inputs

Every input `action.yml` declares, in its order; a test keeps this table equal to it, and `Taken by` equal to the
commands `main.py` passes each input to.

<!-- over limit: one row per input; the meanings are the one-line option-list entries the page rules ask for -->
| Input | Required | Default | Taken by | Meaning |
|---|---|---|---|---|
| `command` | yes | — | — | The command to run: `normalize-docs`, `normalize-tests` or `coverage-matrix` ([Commands](#commands)) |
| `input` | yes | — | `normalize-docs`, `normalize-tests`, `coverage-matrix` | Path to the input JSON file: the documentation file for `normalize-docs` and `coverage-matrix` (`--doc-input`), the tests file for `normalize-tests` |
| `output` | yes | — | `normalize-docs`, `normalize-tests`, `coverage-matrix` | Path of the JSON file the command writes |
| `view` | no | `''` | `normalize-docs`, `coverage-matrix` | `inner` (the CLI default) or `release` |
| `document-title` | no | `''` | `normalize-docs` | The document title; the input's `metadata.source.project_id` when empty |
| `tests-input` | no | `''` | `coverage-matrix` | Path to the tests JSON file (`--tests-input`); `coverage-matrix` requires it |
| `fail-under` | no | `''` | `coverage-matrix` | Fail the step when the coverage percentage is below this number, or there is none (`--fail-under`); the file is written first ([Outputs](#outputs)) |
| `verbose-logging` | no | `false` | every command, as the group's `--verbose` | `true`, in any case, logs at DEBUG, the command line included; a re-run with debug logging (`RUNNER_DEBUG=1`) does the same without it |

- An input left empty is not passed, so the CLI's default applies
  - Why: `action.yml` passes every input on every run, an unset one as its empty default.
- Each input goes only to the commands that take it, as `--<option>=<value>`, so a value starting with `-` stays the option's value
- `output` reaches the CLI as an absolute path
- Verbose logging adds the group's `--verbose` before the command name, so it applies to every command and no command declares it
  - Why `--verbose`: the CLI reads no `INPUT_*` variable, so `main.py` reads `INPUT_VERBOSE_LOGGING` and passes an option.
  - The variable also stays in the CLI's environment; `living-doc-utilities`' own logging reads it.
- The only variables the CLI reads are the `GITHUB_*` run context, recorded in an output's `metadata.run` for audit only → [The CI run context](../packages/core/README.md#the-ci-run-context)

## Outputs

| Output | Meaning |
|---|---|
| `output-path` | Absolute path of the file the command wrote; set once the command succeeds |

- A later step reads it as `${{ steps.normalize.outputs.output-path }}`, for example as a generator's input file
- A `coverage-matrix` run below `fail-under` writes its file, then fails with the CLI's line and exit code 1, so `output-path` is not set

## Errors

The step fails at the first check that does not pass, in this order:

| Where | Situation | The step fails with |
|---|---|---|
| venv | no Python 3.10 or later on `PATH` | `::error::living-doc-toolkit needs Python >= 3.10 on PATH. Add actions/setup-python before this step.` |
| venv | `python -m venv` fails | `::error::living-doc-toolkit: '<python> -m venv' failed; install the venv module.` |
| venv | the import check fails: the packages did not land in the venv | one `::error::` line pointing at the runner's pip configuration, for a `target` or `prefix` setting |
| input | `command` is empty or unknown | one line listing the valid commands |
| input | a non-empty input the command does not take | one line naming the input and the command |
| input | an empty input the command requires, `tests-input` for `coverage-matrix` included | one line naming it |
| input | `output` holds a line break, which `output-path` cannot carry | one line naming it |
| input | `fail-under` is not a finite number | one line naming it |
| command | the command fails | the CLI's own error lines and exit code ([Exit codes](../apps/cli/README.md#exit-codes)) |
| output | `output-path` cannot be written | one line |

- The venv step's checks run before it creates or installs anything that depends on them
- `main.py` checks in the order of the `input` rows above: the command, an untaken input, an empty required input, `output`, then `fail-under`; it stops at the first failure, with exit code 1
- A failed command ends the step with the command's own exit code; any other failure here ends it with exit code 1
