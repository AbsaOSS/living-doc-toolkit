# Living Documentation Core

The package every toolkit command shares: logging, the reader table, the shared input validation, the view filter
and the CI run context.

## Overview

| Module | What it holds |
|---|---|
| `living_doc_core.logging_config` | `setup_logging(verbose)`: the `living_doc` logger, `[LEVEL] message` on stderr |
| `living_doc_core.readers` | The reader table, `READERS`, and the readers `read_documentation` and `read_tests` |
| `living_doc_core.input_validation` | `validate_inputs(command, inputs)`, which runs the shared input validation over one command's inputs |
| `living_doc_core.views` | `select_records(entities, view)`, the view filter |
| `living_doc_core.run_context` | `run_context()`, the CI run a file is written in, for `metadata.run` |

- It depends on `living-doc-utilities==0.8.0` and nothing else; the contract models and schemas are that package's.
- `living_doc_core` itself exports only `setup_logging` and `__version__`; `readers`, `input_validation`, `views` and
  `run_context` load the contract models, so they are imported by name.
- Its version is the toolkit's one version, which every package declares. `metadata.producer.version` of a file the
  toolkit writes reads it from the installed `living-doc-core`.

## The reader table

`READERS` maps each contract the toolkit reads, by contract name, to its role and the producers known to write it:

| Contract | Role | Known producers |
|---|---|---|
| `doc-source` | documentation | `AbsaOSS/living-doc-collector-gh` |
| `ui-tests` | tests | `AbsaOSS/living-doc-collector-gh` |

- It is keyed by contract name, never by producer: the file's own `schema_version` says how it is read.
- Every read goes through `read_artifact(path, expected=<the role's contract names>)`, which runs R5, and returns the
  contract's model: `read_documentation` a `DocSourceResult`, `read_tests` a `UITestsResult`. Neither returns a
  `dict`.
- The issue-tracker documentation contract, `doc-entities`, joins the documentation role in a later release.

## Shared input validation

Each command declares the roles it takes, one input each:

| Command | Documentation input | Tests input |
|---|---|---|
| `normalize-docs` | one | none |
| `normalize-tests` | none | one |
| `coverage-matrix` | one | one |

`validate_inputs(command, {Role.DOCUMENTATION: [...], Role.TESTS: [...]})` runs these steps in order:

1. `MISSING_INPUT`: a role the command takes with no path, or a path that names no file.
2. R5 per input, through `read_artifact`: `INVALID_CONTRACT_ID`, `CONTRACT_MISMATCH`, `SCHEMA_VALIDATION_FAILED`.
   A file that is not JSON fails here too, with a line that carries no code.
3. `UNKNOWN_PRODUCER`: `metadata.producer.name` is not a known producer of the file's contract.
4. `PROJECT_MISMATCH`: the inputs name different `metadata.source.project_id`s.
5. `MULTIPLE_DOCUMENTATION_SOURCES`: more than one documentation file.
6. `DUPLICATE_ENTITY_ID`, `DUPLICATE_AC_ID`: an entity id twice in the documentation, or a criterion id twice under one
   entity.

- The first failing step ends validation: `InputValidationError` carries every occurrence of that step, each an
  `InputProblem` with its code, the input it is in and a hint, and nothing from a later step.
  - Why: a reader never gets a cascade of errors caused by the first one, and no precedence rule picks a winner.
- An `InputProblem` reads as `[CODE] <role> input '<path>': <what is wrong>; <hint>`.
- Once every step passes, it returns `ValidatedInputs`: the documentation and tests as contract models, `None` for a
  role the command does not take.
- `metadata.producer.version` is audit information: it is never compared, and an unfamiliar one passes silently.
- `MIXED_DOCUMENTATION_SOURCES` needs a second documentation contract, so it arrives with `doc-entities`.
- A command it does not know, a role the command does not take, or a second tests path is a `ValueError`: a
  command's own options rule them out.

The steps and codes are `living-doc-utilities`' [errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md)
page, § Shared input validation order; the one-documentation-file rule is its
[pipeline rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/pipeline-rules.md) page,
§ One project, one pipeline, one documentation source.

## The view filter

`select_records(entities, view)` is the one view filter: a transform runs it to pick the records a view holds. It
returns the kept entities and the contract's own `SelectionSummary`.

- `inner` keeps every record.
- `release` drops `planned` and `in_review` entities and, of the entities it keeps, `planned` and `in_review`
  acceptance criteria; it keeps `deprecated` ones. A Feature is dropped by its derived state.
- It selects records only and never edits a field: a kept entity is the input's own, or a copy without its dropped
  criteria.
- The acceptance-criteria counts cover kept entities only; a dropped entity's criteria are not counted.
- A view other than `inner` or `release` is a `ValueError`.

The rule is `living-doc-utilities`' [rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md)
page, § Records and presentation; how a generator shows each view is `living-doc`'s
[document types](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-document-types.md) guide.

## The CI run context

`run_context()` returns the contract's `Run`, read from the GitHub Actions variables of the run the command runs in:

| Field | Variable |
|---|---|
| `run_id` | `GITHUB_RUN_ID` |
| `run_attempt` | `GITHUB_RUN_ATTEMPT` |
| `actor` | `GITHUB_ACTOR` |
| `workflow` | `GITHUB_WORKFLOW` |
| `ref` | `GITHUB_REF` |
| `sha` | `GITHUB_SHA` |

- An unset or empty variable is `None`, so outside GitHub Actions every field is.
- A command sets it as its output's `metadata.run`. It is audit information: nothing reads it to decide anything.
- An input's own `run` stays in its `metadata.source_inputs[]` entry.

`run` is defined on `living-doc-utilities`' [artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md)
page, § The metadata envelope.

## Installation

```bash
pip install -e packages/core
```

## Usage

```python
from living_doc_core import setup_logging
from living_doc_core.input_validation import InputValidationError, validate_inputs
from living_doc_core.readers import Role

logger = setup_logging(verbose=False)
try:
    inputs = validate_inputs("coverage-matrix", {Role.DOCUMENTATION: ["doc-source.json"], Role.TESTS: ["ui-tests.json"]})
except InputValidationError as error:
    for problem in error.problems:
        logger.error("%s", problem)
```

## License

Apache License, Version 2.0
