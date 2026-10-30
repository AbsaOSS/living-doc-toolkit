# Living Documentation Core

## Purpose

This page defines what every command shares: the reader table, the shared input validation, the view filter, the CI
run context and the envelope. Developers who change a command read it.

Read before: [CLI](../../apps/cli/README.md) · Next: [normalize-docs](../services/normalize_docs/README.md)

## Contents

- [Modules](#modules)
- [The reader table](#the-reader-table)
- [Shared input validation](#shared-input-validation)
- [The view filter](#the-view-filter)
- [The CI run context](#the-ci-run-context)
- [Shared envelope](#shared-envelope)
- [Usage](#usage)

## Modules

| Module | What it holds |
|---|---|
| `living_doc_core.logging_config` | `setup_logging(verbose)`: the `living_doc` logger, `[LEVEL] message` on stderr |
| `living_doc_core.envelope` | The toolkit producer identity and `forwarded(warning, source)`, shared by every transform |
| `living_doc_core.readers` | The reader table, `READERS`, and the readers `read_documentation` and `read_tests` |
| `living_doc_core.input_validation` | `validate_inputs(command, inputs)`, which runs the shared input validation over one command's inputs |
| `living_doc_core.views` | `select_records(entities, view)`, the view filter |
| `living_doc_core.run_context` | `run_context()`, the CI run a file is written in, for `metadata.run` |

- It depends on `living-doc-utilities==0.8.0` and nothing else; the contract models and schemas are that package's
- `living_doc_core` itself exports only `setup_logging` and `__version__`; every other module loads the contract models, so it is imported by name
  - Why: it keeps the contract-model imports behind the module boundary that needs them.

## The reader table

`READERS` maps each contract the toolkit reads, by contract name, to its role and the producers known to write it:

| Contract | Role | Known producers |
|---|---|---|
| `doc-source` | documentation | `AbsaOSS/living-doc-collector-gh` |
| `ui-tests` | tests | `AbsaOSS/living-doc-collector-gh` |

- It is keyed by contract name, never by producer: the file's own `schema_version` says how it is read
- Every read goes through `read_artifact(path, expected=<the role's contract names>)`, which runs R5, and returns the contract's model: `read_documentation` a `DocSourceResult`, `read_tests` a `UITestsResult`; neither returns a `dict`
- The issue-tracker documentation contract, `doc-entities`, joins the documentation role in a later release, through a spec → [Reader-table spec](../../SPEC.md#3-reader-table-spec--required-contents)

## Shared input validation

Each command declares the roles it takes, one input each:

| Command | Documentation input | Tests input |
|---|---|---|
| `normalize-docs` | one | none |
| `normalize-tests` | none | one |
| `coverage-matrix` | one | one |

`validate_inputs(command, {Role.DOCUMENTATION: [...], Role.TESTS: [...]})` runs these steps in order:

1. `MISSING_INPUT`: a role the command takes with no path, or a path that names no file.
2. R5 per input, through `read_artifact`: `INVALID_CONTRACT_ID`, `CONTRACT_MISMATCH`, `SCHEMA_VALIDATION_FAILED`. A file that is not JSON fails here too, with a line that carries no code.
3. `UNKNOWN_PRODUCER`: `metadata.producer.name` is not a known producer of the file's contract.
4. `PROJECT_MISMATCH`: the inputs name different `metadata.source.project_id`s.
5. `MULTIPLE_DOCUMENTATION_SOURCES`: more than one documentation file; a run reads exactly one.
6. `DUPLICATE_ENTITY_ID`, `DUPLICATE_AC_ID`: an entity id twice in the documentation, or a criterion id twice under one entity, listing every place.

- The first failing step ends validation: `InputValidationError` carries every occurrence of that step, each an `InputProblem` with its code, the input it is in and a hint, and nothing from a later step
  - Why: a reader never gets a cascade of errors caused by the first one, and no precedence rule picks a winner.
- An `InputProblem` reads as `[CODE] <role> input '<path>': <what is wrong>; <hint>`
- Once every step passes, it returns `ValidatedInputs`: the documentation and tests as contract models, `None` for a role the command does not take
- `metadata.producer.version` is audit information: it is never compared, and an unfamiliar one passes silently
- `MIXED_DOCUMENTATION_SOURCES` needs a second documentation contract, so it arrives with `doc-entities` → [errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md)
- A command it does not know, a role the command does not take, or a second tests path is a `ValueError`: a command's own options rule them out
- The steps and codes are the [errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md) page's § Shared input validation order; the one-documentation-file rule is the pipeline rules' § One project, one pipeline, one documentation source → [pipeline rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/pipeline-rules.md)

## The view filter

`select_records(entities, view)` is the one view filter: a transform runs it to pick the records a view holds. It
returns the kept entities and the contract's own `SelectionSummary`:

- `inner` keeps every record.
- `release` drops `planned` and `in_review` entities and, of the entities it keeps, `planned` and `in_review` acceptance criteria; it keeps `deprecated` ones. A Feature is dropped by its derived state
- It selects records only and never edits a field: a kept entity is the input's own, or a copy without its dropped criteria
- The acceptance-criteria counts cover kept entities only; a dropped entity's criteria are not counted.
- A view other than `inner` or `release` is a `ValueError`.
- The rule is the [rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md) page's § Records and presentation; how a generator shows each view is `living-doc`'s guide → [document types](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-document-types.md)

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

- An unset or empty variable is `None`, so outside GitHub Actions every field is `None`
- A command sets it as its output's `metadata.run`. It is audit information: nothing reads it to decide anything → [Shared envelope](#shared-envelope)
- An input's own `run` stays in its `metadata.source_inputs[]` entry → [Shared envelope](#shared-envelope)
- `run` is defined on the artifact rules' § The metadata envelope → [artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md)

## Shared envelope

Every command's output carries these fields the same way; each command's page gives the rest:

| Field | Value |
|---|---|
| `metadata.producer` | `name` `AbsaOSS/living-doc-toolkit`, `PRODUCER_NAME`; `version` the toolkit's one version, `TOOLKIT_VERSION`, read from the installed `living-doc-core`; `build` `null`; `write_artifact` fills `producer.utilities_version` |
| `metadata.run` | the CI run the file is written in ([The CI run context](#the-ci-run-context)); empty outside GitHub Actions |
| `metadata.generated_at` | the write time, in UTC, to the second |
| `metadata.stats` | computed by `write_artifact` from the output's own records; `write_artifact` validates the output before it writes |

- `metadata.producer.build` stays `null`: the canon defines it as the writing tool's own build; the CI run is `metadata.run` → [artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md)
- Each input's own `run` and `stats` stay in its `metadata.source_inputs[]` entry → [artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md)
- The output's `sources_configured`, `sources_failed`, `unresolved_refs` and `entities_skipped` are `0`: a transform configures no source
- The canon's rules are the artifact rules' § The metadata envelope, R6 and R7 → [artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md)

`forwarded(warning, source)` copies an input warning unchanged but for `context`:

- `context` names the input first, `source_input='<schema_version>'`, the input's contract id, then keeps the warning's own context after a space: `source_input='doc-source-v1.0.0' entity_id='FEAT-003' target='FEAT-002'`.
  - Why the contract id: it is the `schema_version` of the input's own `metadata.source_inputs[]` entry, so the name points into the same file.
  - A run reads one input per contract, and a file name or path would depend on where the run happened.
  - Why `source_input=`: the key follows `metadata.source_inputs[]`. A collector's own context can already hold `input=`, naming its configuration input.
  - Such a context, e.g. `input='doc-source-repositories' entry=1 repository='org/repo'`, stays as it is after the forwarded name.
- A warning without a context gets only `source_input='<schema_version>'`.
- `code`, `message`, `entity_id`, `ac_id`, `line_no`, `path` and `source_url` are not touched.
- The rule is the errors page's § Forwarded warnings → [errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md#forwarded-warnings)

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
