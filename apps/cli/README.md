# living-doc-cli

CLI wrapper for the Living Documentation Toolkit: the `living-doc` command group.

It registers `normalize-docs`, `normalize-tests` and `coverage-matrix`, every command the action runs.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Show help; it lists normalize-docs, normalize-tests and coverage-matrix
living-doc --help

# Show version
living-doc --version

# doc-source.json to generator-ready.json, in the inner view
living-doc normalize-docs --input doc-source.json --output generator-ready.json

# The release view, with the document's own title and version
living-doc normalize-docs --input doc-source.json --output generator-ready.json \
  --view release --document-title "Payments service" --document-version 2.3.0

# ui-tests.json to ui-test-catalog.json
living-doc normalize-tests --input ui-tests.json --output ui-test-catalog.json

# doc-source.json and ui-tests.json to coverage-matrix.json, failing below 80 % coverage
living-doc coverage-matrix --doc-input doc-source.json --tests-input ui-tests.json \
  --output coverage-matrix.json --fail-under 80
```

- `--verbose` is the group's option, so it goes before the command name: `living-doc --verbose normalize-docs …` logs
  at DEBUG. No command takes it, and the action passes it there.
- A command name the group does not register, such as `living-doc generate`, fails with click's "No such command"
  and exit code 2.

## normalize-docs

Reads one documentation file and writes `generator-ready.json`. What it builds, and how it proves no field is lost:
[`living-doc-service-normalize-docs`](../../packages/services/normalize_docs/README.md).

| Option | Required | Default | Description |
|---|---|---|---|
| `--input` | yes | | The documentation input, `doc-source.json`. |
| `--output` | yes | | The `generator-ready.json` to write; its directory is created when missing. |
| `--view` | no | `inner` | `inner` or `release`: the records the output holds. |
| `--document-title` | no | the input's `metadata.source.project_id` | `document.title`. |
| `--document-version` | no | `1.0.0` | `document.version`. |

A run that succeeds exits 0 and logs one line:
``[INFO] normalize-docs - written: `<output>` (<view> view; <kept> of <total> entities, <kept> of <total> acceptance criteria).``

A run that fails exits 1, writes no file, and leaves a file already at `--output` untouched:

| Failure | Error lines |
|---|---|
| The input fails the shared input validation | one per problem, before anything is built: ``[ERROR] [MISSING_INPUT] documentation input 'doc-source.json': no such file; …`` ([core README](../../packages/core/README.md#shared-input-validation)) |
| A field with data in the input is empty in the output | one: ``[ERROR] [FIELD_LOSS] '<input path>' had occupancy <n> on input but its mapped output path '<output path>' has occupancy 0`` |
| The output cannot be written | one: ``[ERROR] normalize-docs - the output cannot be written: <reason>`` |

- An option click rejects, such as a `--view` that is neither `inner` nor `release`, exits 2 with click's usage error.

## normalize-tests

Reads one tests file and writes `ui-test-catalog.json`. What it groups and how it checks that no scenario field is
lost: [`living-doc-service-normalize-tests`](../../packages/services/normalize_tests/README.md).

| Option | Required | Default | Description |
|---|---|---|---|
| `--input` | yes | | The tests input, `ui-tests.json`. |
| `--output` | yes | | The `ui-test-catalog.json` to write; its directory is created when missing. |

A run that succeeds exits 0 and logs one line:
``[INFO] normalize-tests - written: `<output>` (<feature files> feature files, <scenarios> scenarios).``

A run that fails exits 1 and writes no file. Input validation reports one `[ERROR]` line per problem before the
transform; `FIELD_LOSS` and output-write failures use one line each, as described for
[`normalize-docs`](#normalize-docs).

## coverage-matrix

Reads one documentation file and one tests file and writes `coverage-matrix.json`, counted per declared aspect of each
acceptance criterion. What it counts, in which order, the warnings it writes, and how it checks that no field is lost:
[`living-doc-service-coverage-matrix`](../../packages/services/coverage_matrix/README.md).

| Option | Required | Default | Description |
|---|---|---|---|
| `--doc-input` | yes | | The documentation input, `doc-source.json`. A run reads exactly one: given twice, the run fails. |
| `--tests-input` | yes | | The tests input, `ui-tests.json`. |
| `--output` | yes | | The `coverage-matrix.json` to write; its directory is created when missing. |
| `--view` | no | `inner` | `inner` or `release`: `document.view`. Both views count the same criteria. |
| `--fail-under` | no | | A finite number: the run fails when the matrix's root `coverage_pct` is below it, or is `null` because no criterion is counted. |

A run that succeeds exits 0 and logs one line:
``[INFO] coverage-matrix - written: `<output>` (<view> view; <n> counted acceptance criteria, <n> covered, <pct>%).``
With no counted criterion the line ends `no coverage percentage)` instead.

`--fail-under` is checked after the file is written: a run below it logs the success line, then one error line, and
exits 1 with the file left in place. At or above it, the run succeeds.

- The gate compares `coverage_pct` as written, rounded to one decimal, so `--fail-under 100` passes at 99.95 % or
  more. Rounding:
  [rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md#coverage-summary),
  § Coverage summary.

Any other failure exits 1, writes no file, and leaves a file already at `--output` untouched:

| Failure | Error lines |
|---|---|
| The inputs fail the shared input validation | one per problem, before anything is built ([core README](../../packages/core/README.md#shared-input-validation)): ``[ERROR] [MISSING_INPUT] tests input 'ui-tests.json': no such file; …``, one ``[ERROR] [MULTIPLE_DOCUMENTATION_SOURCES] documentation input '<path>': one of 2 documentation files; …`` per documentation file, and one ``[ERROR] [DUPLICATE_ENTITY_ID] …`` or ``[ERROR] [DUPLICATE_AC_ID] …`` per repeated id, listing every place it is at |
| A mapped field with data in the records the matrix counts is empty in the output | one: ``[ERROR] [FIELD_LOSS] '<input path>' had occupancy <n> on input but its mapped output path '<output path>' has occupancy 0`` |
| The output cannot be written | one: ``[ERROR] coverage-matrix - the output cannot be written: <reason>`` |

The gate's lines, after the file is written:

| Gate | Error line |
|---|---|
| The coverage percentage is below `--fail-under` | ``[ERROR] coverage-matrix - the coverage percentage, <pct>, is below --fail-under <n>.`` |
| No criterion is counted, so there is no percentage | ``[ERROR] coverage-matrix - no acceptance criterion is counted, so the matrix has no coverage percentage, which fails --fail-under <n>.`` |

- An option click rejects, such as a `--fail-under` that is not a finite number (`nan` and `inf` included), exits 2
  with click's usage error and writes no file.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
pylint src/living_doc_cli

# Run type checking
mypy src/living_doc_cli

# Format code
black src/ tests/
```
