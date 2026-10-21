# living-doc-cli

CLI wrapper for the Living Documentation Toolkit: the `living-doc` command group.

It registers `normalize-docs`. `normalize-tests` and `coverage-matrix` are added to the group as each lands.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Show help; it lists normalize-docs
living-doc --help

# Show version
living-doc --version

# doc-source.json to generator-ready.json, in the inner view
living-doc normalize-docs --input doc-source.json --output generator-ready.json

# The release view, with the document's own title and version
living-doc normalize-docs --input doc-source.json --output generator-ready.json \
  --view release --document-title "Payments service" --document-version 2.3.0
```

- `--verbose` is a group option, and every command takes it too: `living-doc --verbose normalize-docs …` and
  `living-doc normalize-docs … --verbose` both log at DEBUG.
  - Why both: the action passes `--verbose` after the command's own options.
- A command name the group does not register yet, such as `living-doc normalize-tests`, fails with click's
  "No such command" and exit code 2.

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
| `--verbose` | no | off | Log at DEBUG. |

A run that succeeds exits 0 and logs one line:
``[INFO] normalize-docs - written: `<output>` (<view> view; <kept> of <total> entities, <kept> of <total> acceptance criteria).``

A run that fails exits 1, writes no file, and leaves a file already at `--output` untouched:

| Failure | Error lines |
|---|---|
| The input fails the shared input validation | one per problem, before anything is built: ``[ERROR] [MISSING_INPUT] documentation input 'doc-source.json': no such file; …`` ([core README](../../packages/core/README.md#shared-input-validation)) |
| A field with data in the input is empty in the output | one: ``[ERROR] [FIELD_LOSS] '<input path>' had occupancy <n> on input but its mapped output path '<output path>' has occupancy 0`` |
| The output cannot be written | one: ``[ERROR] normalize-docs - the output cannot be written: <reason>`` |

- An option click rejects, such as a `--view` that is neither `inner` nor `release`, exits 2 with click's usage error.

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
