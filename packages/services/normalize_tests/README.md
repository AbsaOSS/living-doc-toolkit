# normalize-tests

## Purpose

This page defines how `normalize-tests` turns one `doc-source.json` and one `ui-tests.json` into
`ui-test-catalog.json`: grouping and order, link states and the view, envelope, warnings and lineage. Developers who
change the command, and readers of its output, read it.

Read before: [normalize-docs](../normalize_docs/README.md) · Next: [coverage-matrix](../coverage_matrix/README.md)

## Contents

- [Modules](#modules)
- [What a run does](#what-a-run-does)
- [Grouping and order](#grouping-and-order)
- [Link states and the view](#link-states-and-the-view)
- [The envelope](#the-envelope)
- [Warnings](#warnings)
- [Lineage](#lineage)
- [Tests](#tests)

## Modules

`living-doc-service-normalize-tests` turns one `doc-source.json` and one `ui-tests.json`, as a collector wrote them,
into `ui-test-catalog.json`, the file a generator reads.

| Module | What it holds |
|---|---|
| `living_doc_service_normalize_tests.builder` | `build_ui_test_catalog(documentation, tests, *, view, generated_at)`: the inputs' contract models to the output's. It reads and writes no file. |
| `living_doc_service_normalize_tests.lineage` | `LINEAGE_TABLE`, the command's lineage table |
| `living_doc_service_normalize_tests.service` | `normalize_tests(doc_inputs, tests_input, output_path, *, view)`, the command, and the runtime field-loss check |

- The three files are `living-doc-utilities` contracts, `doc-source-v1.0.0`, `ui-tests-v1.0.0` and `ui-test-catalog-v1.0.0`; this package keeps no copy of any of them
- The CLI registers it as `living-doc normalize-tests`, and the action runs it as `command: normalize-tests` → [CLI](../../../apps/cli/README.md#normalize-tests), [Commands](../../../docs/action.md#commands)

## What a run does

A run takes these steps; nothing is written when one fails:

1. Both inputs go through the shared input validation, `validate_inputs("normalize-tests", …)`, and nothing else reads them ([Shared input validation](../../core/README.md#shared-input-validation)). A failing step stops the run before anything is built.
   - It takes one documentation input; a second one fails the run with `MULTIPLE_DOCUMENTATION_SOURCES`.
2. The builder groups the validated scenarios, gives each link its criterion's state, applies the view, and builds the output model; the command sets its `metadata.run` to the CI run.
3. The runtime field-loss check compares the tests input's selected occupancy with the sum of all three output groups ([Lineage](#lineage)); a lost field stops the run.
4. `write_artifact` validates the catalog, then writes it.

## Grouping and order

The builder groups each scenario by feature file and by every entity it links:

- There is one `feature_files[]` entry per feature file
  - Its key and name are the scenario's `scenario_id` up to its last `/`. That prefix must end with `/<source_ref.native_id>`, after exactly two non-empty path components (`<org>/<repo>`).
  - Otherwise the key and name are `source_ref.native_id`.
  - Why exactly two: a `metadata.source.repositories[]` entry is `org/repo` or `org/project`; another length names no repository.
  - `org/repo` is GitHub's form, `org/project` Azure DevOps' ([artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md), § The metadata envelope).
- The repository-qualified name relies on `living-doc-collector-gh`'s `scenario_id` shape, which no contract defines; other id shapes use the native path
  - The final repository identifier belongs in a future contract change, once a contract field names the repository.
- A feature file's `background` is its first scenario's `background`, once
  - Why: the collector writes a file's `Background:` on each of its scenarios.
  - Two files that share a native path under a fallback key keep the first one's background.
- A `US-` acceptance-criterion link groups its scenario under the User Story id without the final `-<n>`; `FUNC-` links do the same under a Functionality
  - A scenario linking both appears in both groups, and several links to one entity place it there once.
- A scenario with no links goes in `unlinked[]`
- Each scenario is a `CatalogScenario`: every field of the input's, `line`, `rule`, `rule_background[]` and `steps[]` included, unchanged, without its `background`
- Feature files follow their first scenario in the input. Groups follow an entity's first link; scenarios within a group follow input order. Nothing is sorted.

## Link states and the view

- Each link carries `state`, its criterion's state in the documentation input; a link to a criterion no User Story or Functionality holds carries none
- `document.view` is the view the command was given, `inner` by default
- The inner view keeps every link
- The release view drops each link to a `planned` or `in_review` criterion, and keeps `deprecated` ones
  - Why: the release view of every other document leaves such criteria out.
- A dropped link never moves its scenario: the groups come from every link the input gives
  - A scenario whose every link is dropped stays in its groups with no link.
- The rules are the rendering page's → [Test catalog](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md#test-catalog)

## The envelope

The fields `normalize-tests` fills its own way; every command fills the rest the same way, as the core's [Shared envelope](../../core/README.md#shared-envelope) says:

| Field | Value |
|---|---|
| `metadata.source` | the tests input's, copied |
| `metadata.stats` | from the output's own groups |
| `metadata.source_inputs[]` | the documentation input's entry, then the tests input's, each with its `schema_version`, `producer`, `run`, `source`, `stats` and `selected_stats` |
| `document.view` | the view given: `inner` or `release` |

- The documentation entry's `selected_stats` covers every record: every criterion's state is read, in both views
- The tests entry's `selected_stats` covers every scenario, with only the links the view keeps
- Each input's own `run` stays in its `source_inputs[]` entry

## Warnings

Every input warning reaches the output through the core's [`forwarded`](../../core/README.md#shared-envelope): the documentation input's first, then the tests input's, each in input order, its `context` starting with `source_input='doc-source-v1.0.0'` or `source_input='ui-tests-v1.0.0'`.

- The command adds no warning of its own; `coverage-matrix` reports the links it does not count → [coverage-matrix](../coverage_matrix/README.md#warnings)

## Lineage

`LINEAGE_TABLE` is one table over both inputs: the 17 `ui-tests-v1.0.0` paths and the 162 `doc-source-v1.0.0` paths.

| Input path | Output path |
|---|---|
| `scenarios[].background[]` | `feature_files[].background[]` |
| every other `scenarios[]` path | its twin under `feature_files[].linked_to_user_story[].scenarios[]` |
| `user_stories[]` and `functionalities[]`: `acceptance_criteria[].state` | `feature_files[].linked_to_user_story[].scenarios[].acceptance_criteria[].state` |

- Every other `doc-source` path is `Dropped`: the catalog reads only the state of each criterion a scenario can link
- The table is declared here, and `assert_complete` over both input contracts runs in this package's tests only
- At run time, `check_no_field_loss` compares against the tests input, the one whose records the catalog carries
  - Why: the documentation input holds none of the catalog's scenario fields, so a check against it would guard nothing.
  - It departs from the canon's "against the one documentation input" → [utilities#233](https://github.com/AbsaOSS/living-doc-utilities/issues/233)
- `check_no_field_loss` computes the catalog's own stats as `write_artifact` will. It adds the occupancy under `linked_to_functionality[].scenarios[]` and `unlinked[]` to each mapped User Story path, then calls `check_field_loss`
  - Only the stats passed to the check are aggregated; the written file keeps its own counts.
  - Why: scenarios are split among three groups, so one group alone reports a false loss when it lacks the field.
  - For example, the fixture's four `acceptance_criteria[].aspect` values are all on Functionality links. Summing the groups lets the fixture and the utilities full sample pass.
- The tests input's `selected_stats` leave out the links the view drops, so a release view that drops every link reports no loss
- A field lost from one group while another still has it is a partial drop; this check does not detect it, because R11 compares aggregate occupancy
- `FIELD_LOSS` remains a hard error when the input has data and the union of the three groups has none
- The runtime check is R11; this package's tests carry R12 checks 2 and 3 → [component checks](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/component-checks.md)

## Tests

- The fixture pair's command output is compared with the committed [golden](tests/expected/README.md), masking only `metadata.generated_at`; the release view differs from it only in `document.view`
- Built inputs cover multiple entities, cross-group and duplicate links, unlinked scenarios, input order, and repositories sharing a native path
- Built inputs also cover each link's state, the release view's drop of `planned` and `in_review` links, the new scenario fields and a file's background
- `full_sample("doc-source-v1.0.0")` and `full_sample("ui-tests-v1.0.0")` are written with `write_artifact` and run through the command, shared input validation included
