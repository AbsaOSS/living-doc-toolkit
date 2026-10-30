# normalize-tests

## Purpose

This page defines how `normalize-tests` turns one `ui-tests.json` into `ui-test-catalog.json`: grouping and order,
envelope, warnings and lineage. Developers who change the command, and readers of its output, read it.

Read before: [normalize-docs](../normalize_docs/README.md) · Next: [coverage-matrix](../coverage_matrix/README.md)

## Contents

- [Modules](#modules)
- [What a run does](#what-a-run-does)
- [Grouping and order](#grouping-and-order)
- [The envelope](#the-envelope)
- [Warnings](#warnings)
- [Lineage](#lineage)
- [Tests](#tests)

## Modules

`living-doc-service-normalize-tests` turns one `ui-tests.json`, as a collector wrote it, into `ui-test-catalog.json`,
the file a generator reads.

| Module | What it holds |
|---|---|
| `living_doc_service_normalize_tests.builder` | `build_ui_test_catalog(tests, *, generated_at)`: the input's contract model to the output's. It reads and writes no file. |
| `living_doc_service_normalize_tests.lineage` | `LINEAGE_TABLE`, the command's lineage table |
| `living_doc_service_normalize_tests.service` | `normalize_tests(input_path, output_path)`, the command, and the runtime field-loss check |

- Both files are `living-doc-utilities` contracts, `ui-tests-v1.0.0` and `ui-test-catalog-v1.0.0`; this package keeps no copy of either
- The CLI registers it as `living-doc normalize-tests`, and the action runs it as `command: normalize-tests` → [CLI](../../../apps/cli/README.md#normalize-tests), [Commands](../../../docs/action.md#commands)

## What a run does

A run takes these steps; nothing is written when one fails:

1. The input goes through the shared input validation, `validate_inputs("normalize-tests", …)`, and nothing else reads it ([Shared input validation](../../core/README.md#shared-input-validation)). A failing step stops the run before anything is built.
2. The builder groups the validated scenarios and builds the output model; the command sets its `metadata.run` to the CI run.
3. The runtime field-loss check compares the input's selected occupancy with the sum of all three output groups ([Lineage](#lineage)); a lost field stops the run.
4. `write_artifact` validates the catalog, then writes it.

## Grouping and order

The builder groups each scenario by feature file and by every entity it links:

- There is one `feature_files[]` entry per feature file
  - Its key and name are the scenario's `scenario_id` up to its last `/`, when that prefix ends with `/<source_ref.native_id>` and exactly two non-empty path components (`<org>/<repo>`) precede the native path.
  - Otherwise the key and name are `source_ref.native_id`.
  - Why exactly two: a `metadata.source.repositories[]` entry is `org/repo` or `org/project`; another length names no repository.
  - `org/repo` is GitHub's form, `org/project` Azure DevOps' ([artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md), § The metadata envelope).
- The repository-qualified name relies on `living-doc-collector-gh`'s `scenario_id` shape, which no contract defines; other id shapes use the native path
  - The final repository identifier belongs in a future contract change, once a contract field names the repository.
- A `US-` acceptance-criterion link groups its scenario under the User Story id without the final `-<n>`; `FUNC-` links do the same under a Functionality
  - A scenario linking both appears in both groups, and several links to one entity place it there once.
- A scenario with no links goes in `unlinked[]`. Its complete `Scenario` model, including `acceptance_criteria[]` and `tags[]`, is carried unchanged.
- Feature files follow their first scenario in the input. Groups follow an entity's first link; scenarios within a group follow input order. Nothing is sorted.

## The envelope

The fields `normalize-tests` fills its own way; every command fills the rest the same way, as the core's [Shared envelope](../../core/README.md#shared-envelope) says:

| Field | Value |
|---|---|
| `metadata.source` | the input's, copied |
| `metadata.stats` | from the output's own groups |
| `metadata.source_inputs[]` | one entry for the input: its `schema_version`, `producer`, `run`, `source`, and `stats`; `selected_stats` is computed over all input scenarios, with no view filter |
| `document.view` | `inner`; the catalog has no view-dependent field |

- The input's own `run` stays in `source_inputs[0].run`
- The view follows the rendering page → [rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md)

## Warnings

Every input warning reaches the output through the core's [`forwarded`](../../core/README.md#shared-envelope), in input order, its `context` starting with `source_input='ui-tests-v1.0.0'`.

## Lineage

`LINEAGE_TABLE` maps each of the 12 `ui-tests-v1.0.0` scenario paths to its twin under
`feature_files[].linked_to_user_story[].scenarios[]`.

- The table is declared here, and `assert_complete(LINEAGE_TABLE, "ui-tests-v1.0.0")` runs in this package's tests only
- At run time, `check_no_field_loss` computes the catalog's own stats as `write_artifact` will. It adds the occupancy under `linked_to_functionality[].scenarios[]` and `unlinked[]` to each mapped User Story path, then calls `check_field_loss`
  - Only the stats passed to the check are aggregated; the written file keeps its own counts.
  - Why: scenarios are split among three groups, so one group alone reports a false loss when it lacks the field.
  - For example, the fixture's four `acceptance_criteria[].aspect` values are all on Functionality links. Summing the groups lets the fixture and the utilities full sample pass.
- A field lost from one group while another still has it is a partial drop; this check does not detect it, because R11 compares aggregate occupancy
- `FIELD_LOSS` remains a hard error when the input has data and the union of the three groups has none
- The runtime check is R11; this package's tests carry R12 checks 2 and 3 → [component checks](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/component-checks.md)

## Tests

- The fixture command output is compared with the committed [golden](tests/expected/README.md), masking only `metadata.generated_at`
- Built inputs cover multiple linked entities, cross-group links, duplicate links to one entity, unlinked scenarios, input order, and two repositories with the same native path
- `full_sample("ui-tests-v1.0.0")` is written with `write_artifact` and run through the command, shared input validation included
