# Living Documentation Toolkit

[![CI](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/test.yml)
[![Integration Tests](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/integration.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/integration.yml)

A monorepo of Python packages that transform and enrich machine-readable artifacts produced by upstream collectors (e.g., [living-doc-collector-gh](https://github.com/AbsaOSS/living-doc-collector-gh)) into datasets consumable by downstream actions (e.g., [living-doc-generator-pdf](https://github.com/AbsaOSS/living-doc-generator-pdf)).

> *This is a monorepo of multiple packages and follows a different README shape than the single-purpose `living-doc-*` action repos (per the fleet-wide `repo-conventions.md`). If you arrived from an action repo, the `Understand / Use / Maintain` layout below is deliberate.*

---

- [Overview](#overview)
- [Quickstart](#quickstart)
- [GitHub Action](#github-action)
- [Documentation](#documentation)
- [License](#license)

---

## Overview

**Expected usage: GitHub Actions first.** The `living-doc` CLI is invoked as a step in a GitHub Actions workflow, chained between the upstream `living-doc-*` collector actions and the downstream generator actions. Running `living-doc <command>` locally — the pattern documented in [DEVELOPER.md](DEVELOPER.md) — is a development and debugging affordance only, not a second supported deployment target.

**The Living Documentation pipeline runs AI-free.** Every step — collect → normalize → generate — is deterministic tooling (Python, JSON Schema validation, Jinja2/Markdown templates) with no LLM call anywhere in that path. [`AbsaOSS/agentic-toolkit`](https://github.com/AbsaOSS/agentic-toolkit) can accelerate the upstream *authoring* of GitHub Issues and `.feature` files, but it is never a runtime dependency of this pipeline: a human writing the same input by hand is a fully supported, identical path.

The Living Documentation Toolkit is a **generic builder** designed to:
- Run one command per GitHub Actions step, through the composite action at the repository root
- Read only contract artifacts, through [`living-doc-utilities`](https://github.com/AbsaOSS/living-doc-utilities)' `read_artifact`, and validate a command's inputs together before it transforms them
- Keep no copy of a contract: the models and schemas come from the installed `living-doc-utilities` (`==0.8.0`)
- Offer core utilities shared across commands

## Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/AbsaOSS/living-doc-toolkit.git
cd living-doc-toolkit

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install all packages
pip install --upgrade pip
pip install -r requirements.txt
```

### CLI

```bash
living-doc --version
living-doc --help      # lists normalize-docs, normalize-tests and coverage-matrix

# doc-source.json, as a collector wrote it, to generator-ready.json for a generator
living-doc normalize-docs --input doc-source.json --output generator-ready.json
living-doc normalize-docs --input doc-source.json --output generator-ready.json --view release
living-doc normalize-tests --input ui-tests.json --output ui-test-catalog.json
living-doc coverage-matrix --doc-input doc-source.json --tests-input ui-tests.json \
  --output coverage-matrix.json --fail-under 80
```

The command's options, error lines and exit codes are in the [CLI README](apps/cli/README.md).

## GitHub Action

The repository root is a composite action. One step runs one command over its input files
and writes the file the command produces.

```yaml
- uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
  with:
    python-version: '3.14'

- name: Normalize the collected documentation
  id: normalize
  uses: AbsaOSS/living-doc-toolkit@<ref>
  with:
    command: normalize-docs
    input: doc-source.json
    output: output/generator-ready.json
    view: release
    document-title: Payments service

- name: Normalize the collected tests
  id: normalize-tests
  uses: AbsaOSS/living-doc-toolkit@<ref>
  with:
    command: normalize-tests
    input: ui-tests.json
    output: output/ui-test-catalog.json

- name: Compute the coverage matrix
  id: coverage
  uses: AbsaOSS/living-doc-toolkit@<ref>
  with:
    command: coverage-matrix
    input: doc-source.json
    tests-input: ui-tests.json
    output: output/coverage-matrix.json
    fail-under: 80
```

- **Python:** the action uses the Python on `PATH`, 3.10 or later, so put `actions/setup-python`
  before it. Below 3.10 it fails with one line before it installs anything.
- **Runner:** Linux only. The action assumes the venv's POSIX `bin/` layout.
- It installs the toolkit into a venv of its own under `$RUNNER_TEMP` and leaves the job's
  `python` unchanged. [DEVELOPER.md](DEVELOPER.md#action-venv) holds the venv's rules.

### Commands

Every command the action declares runs.

| Command | Reads | Writes |
|---|---|---|
| `normalize-docs` | one documentation file (`doc-source.json`) | `generator-ready.json`, in the `inner` or `release` view |
| `normalize-tests` | one tests file (`ui-tests.json`) | `ui-test-catalog.json` |
| `coverage-matrix` | one documentation file (`doc-source.json`) and one tests file (`ui-tests.json`) | `coverage-matrix.json`, with `document.view` `inner` or `release` |

- `normalize-docs` carries every authored field of every entity the view keeps, and forwards the input's warnings.
  How it maps the input and checks that no field is lost: [its package README](packages/services/normalize_docs/README.md).
- `normalize-tests` groups each scenario by feature file and every User Story or Functionality it links to, carrying
  the scenario unchanged. How it groups records and checks lineage: [its package README](packages/services/normalize_tests/README.md).
- `coverage-matrix` counts each `active` or `deprecated` acceptance criterion of every User Story and Functionality as
  covered or not by the scenarios that link it, and adds a summary per entity, for the whole matrix and for the
  planned work. How it counts and checks lineage: [its package README](packages/services/coverage_matrix/README.md).
  - It reads exactly one documentation file: a second one fails with `MULTIPLE_DOCUMENTATION_SOURCES`. A repeated
    entity id, or a repeated criterion id under one entity, fails with `DUPLICATE_ENTITY_ID` or `DUPLICATE_AC_ID`,
    listing every place.
  - With `fail-under`, a coverage percentage below the number, or none, fails the step after the file is written, and
    `output-path` is not set.

### Inputs

| Input | Required | Default | Taken by | Description |
|---|---|---|---|---|
| `command` | yes | | | `normalize-docs`, `normalize-tests` or `coverage-matrix`; every one runs. |
| `input` | yes | | every command | Path to the input JSON file: the documentation file for `normalize-docs` and `coverage-matrix` (`--doc-input`), the tests file for `normalize-tests`. |
| `output` | yes | | every command | Path of the JSON file the command writes. |
| `view` | no | `''` | `normalize-docs`, `coverage-matrix` | `inner` (the CLI default) or `release`. |
| `document-title` | no | `''` | `normalize-docs` | The document title; the input's `metadata.source.project_id` when empty. |
| `tests-input` | for `coverage-matrix` | `''` | `coverage-matrix` | Path to the tests JSON file (`--tests-input`). |
| `fail-under` | no | `''` | `coverage-matrix` | Fail the step when the coverage percentage is below this number, or there is none (`--fail-under`); the file is written first. |
| `verbose-logging` | no | `'false'` | every command | `'true'` logs at DEBUG, the command line included. A re-run with debug logging (`RUNNER_DEBUG=1`) does the same without it. |

- An input left empty is not passed, so the CLI's default applies.
- A non-empty input the command does not take fails the step with one line naming the input
  and the command; so does an empty required one, and a `fail-under` that is not a number.
- An unknown `command` fails with one line listing the valid commands.
- A failed command fails the step with the CLI's own error lines and exit code.

### Output

| Output | Description |
|---|---|
| `output-path` | Absolute path of the file the command wrote; set once the command succeeds. |

A later step reads it as `${{ steps.normalize.outputs.output-path }}`, for example as a
generator's input file.

## Documentation

### Understand
- **[Core package](packages/core/README.md)** — The reader table, the shared input validation, the view filter and the CI run context every command uses
- **[normalize-docs package](packages/services/normalize_docs/README.md)** — How `normalize-docs` builds `generator-ready.json`, and its lineage table
- **[normalize-tests package](packages/services/normalize_tests/README.md)** — How `normalize-tests` builds `ui-test-catalog.json`, groups scenarios, and checks lineage
- **[coverage-matrix package](packages/services/coverage_matrix/README.md)** — How `coverage-matrix` builds `coverage-matrix.json`, counts criteria, and checks lineage
- **[CLI package](apps/cli/README.md)** — The `living-doc` command group and its commands
- **[SPEC.md](SPEC.md)** — How a new command or package is specced before it is built (the prospective-spec process for this monorepo)
- **[`living-doc-utilities` contracts](https://github.com/AbsaOSS/living-doc-utilities/tree/master/docs/contracts)** — The contracts, error codes and pipeline rules the toolkit implements

### Maintain
- **[Developer Guide](DEVELOPER.md)** — Environment setup, testing, linting, branch conventions
- **[Contribution Guidelines](CONTRIBUTING.md)** — How to report bugs, propose features, and open a PR

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for full details.
