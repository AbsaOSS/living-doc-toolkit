# coverage-matrix

## Purpose

This page defines how `coverage-matrix` turns one `doc-source.json` and one `ui-tests.json` into
`coverage-matrix.json`: entities and rows, summaries, view, envelope, warnings and lineage. Developers who change the
command, and readers of its output, read it.

Read before: [normalize-tests](../normalize_tests/README.md) · Next: [Action reference](../../../docs/action.md)

## Contents

- [Modules](#modules)
- [What a run does](#what-a-run-does)
- [Entities and rows](#entities-and-rows)
- [Summaries](#summaries)
- [View and gate](#view-and-gate)
- [The envelope](#the-envelope)
- [Warnings](#warnings)
- [Lineage](#lineage)
- [Tests](#tests)

## Modules

`living-doc-service-coverage-matrix` turns one `doc-source.json` and one `ui-tests.json`, as a collector wrote them,
into `coverage-matrix.json`, the file a generator reads.

| Module | What it holds |
|---|---|
| `living_doc_service_coverage_matrix.builder` | `build_coverage_matrix(documentation, tests, *, view, generated_at)`: the inputs' contract models to the output's. It reads and writes no file. |
| `living_doc_service_coverage_matrix.lineage` | `LINEAGE_TABLE`, the command's lineage table over both inputs |
| `living_doc_service_coverage_matrix.service` | `coverage_matrix(doc_inputs, tests_input, output_path, *, view)`, the command, and `check_no_field_loss(result)` |

- The three files are `living-doc-utilities` contracts, `doc-source-v1.0.0`, `ui-tests-v1.0.0` and `coverage-matrix-v1.0.0`; this package keeps no copy of any of them
- The CLI registers it as `living-doc coverage-matrix`, with the `--fail-under` gate, and the action runs it as `command: coverage-matrix` → [CLI](../../../apps/cli/README.md#coverage-matrix), [Commands](../../../docs/action.md#commands)
- Coverage is counted per declared aspect, and a scenario link the matrix does not count as written is a warning in the file → [Entities and rows](#entities-and-rows), [Warnings](#warnings)

## What a run does

A run takes these steps; nothing is written when one fails:

1. Both inputs go through the shared input validation, `validate_inputs("coverage-matrix", …)`, and nothing else reads them ([Shared input validation](../../core/README.md#shared-input-validation)). A failing step stops the run before anything is built; a second documentation file, or a repeated entity or criterion id, fails there.
2. The builder builds the matrix from the validated models, and the command sets its `metadata.run` to the CI run.
3. `check_no_field_loss` compares the lineage table's paths against the documentation input ([Lineage](#lineage)); a lost field stops the run.
4. `write_artifact` validates the matrix, then writes it.

## Entities and rows

The builder gives each User Story and Functionality an entry and a row per counted criterion:

- There is one `entities[]` entry per User Story and per Functionality, whatever its state, and whether or not it has a counted criterion. Its `type`, `title` and `state` are the entity's own
- There is no Feature entity
- An entity has a row per `active` or `deprecated` criterion, with that criterion's `state`; a `planned` or an `in_review` criterion has no row
- A link matches a criterion by its `id`, whatever repository the scenario is in
- A criterion that declares aspects, with `Aspect:` or a keyword, gets an `aspects[]` entry per declared value, in declared order
  - An aspect lists the `scenario_id` of every scenario whose link names that aspect. A bare `@AC:<id>` link, with no aspect, lists its scenario under every aspect.
  - An aspect is `covered` with at least one scenario and `not_covered` with none. The row's `status` follows its aspects, `covered`, `partially_covered` or `not_covered`, and its own `scenario_ids` stays empty.
  - A keyword criterion's row carries `keyword`, the criterion's one `placeholder_values` key, as stored (`rule`); an `Aspect:` row carries none.
  - The keyword's name in a scenario tag is not stored, so it is not checked.
  - A link to an aspect the criterion does not declare counts nowhere ([Warnings](#warnings)).
- A criterion without aspects gets a plain row: it lists the `scenario_id` of every scenario that links it, and is `covered` with at least one scenario and `not_covered` with none. It carries no aspect and no keyword
  - A link with an aspect covers it too, as a bare one does, and is a warning: the scenario names the criterion, and the criterion has one thing to cover.
- A scenario is listed once per aspect, and once per plain row, however many of its links reach it
- Order: every User Story, then every Functionality, each in input order. Rows follow the entity's own criteria, aspects the criterion's declared values, and the scenarios the tests input. Nothing is sorted
- Which criteria are counted, and what each status means, are the rendering page's § Coverage → [rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md)
- How a keyword declares its values is the AC grammar page's § Variants → [AC grammar](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/authoring/ac-grammar.md)

## Summaries

- Each entity's `summary` comes from `CoverageSummary.from_rows` over its own rows, and the root `summary` over every row of every entity
  - An entity without a row counts `0` criteria and has no percentage, `null`.
- `planned_summary` counts the `planned` criteria of User Stories and Functionalities
  - One with a `version` goes under `by_target_version`, in the order first met, and one without in `backlog`; `total` is their sum.
  - An `in_review` criterion is in neither.
- The rules are the rendering page's § Coverage summary and § Planned work summary → [rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md)

## View and gate

- `--view` sets `document.view`, `inner` by default, and nothing else: both views have the same rows and the same counts. What a view shows is the generator's
- `--fail-under` is the CLI's gate on the root `coverage_pct`, run after the file is written; the service has no gate → [CLI](../../../apps/cli/README.md#coverage-matrix)

## The envelope

The fields `coverage-matrix` fills its own way; every command fills the rest the same way, as the core's [Shared envelope](../../core/README.md#shared-envelope) says:

| Field | Value |
|---|---|
| `metadata.source` | the documentation input's, with each of the tests input's `systems` it does not name added once |
| `metadata.stats` | from the matrix's own entities |
| `metadata.source_inputs[]` | the documentation input's entry, then the tests input's, each with its `schema_version`, `producer`, `run`, `source`, `stats` and `selected_stats` |
| `document.view` | `--view` |

- `metadata.source` merges the tests input's `systems` into the documentation input's
- Each input's own `run` stays in its `source_inputs[]` entry
- The documentation entry's `selected_stats` are computed over the records the matrix counts: the User Stories and Functionalities, each with only its `active` and `deprecated` criteria, and no Feature
  - Its `stats` against its `selected_stats` shows what the matrix leaves out.
- The tests entry's `selected_stats` are computed over all its scenarios, so they equal its occupancy

## Warnings

Every input warning reaches the output through the core's [`forwarded`](../../core/README.md#shared-envelope): the documentation input's first, then the tests input's, each in input order, its `context` starting with `source_input='doc-source-v1.0.0'` or `source_input='ui-tests-v1.0.0'`.

After them, the command adds a warning for each scenario link it does not count as written:

| Code | The link names | The link |
|---|---|---|
| `STALE_AC_REF` | a criterion no User Story or Functionality in the documentation input has | counts nowhere |
| `STALE_AC_REF` | an aspect its criterion does not declare | counts nowhere; on a criterion without aspects, covers it |
| `PLANNED_AC_HAS_TESTS` | a `planned` criterion, whatever the aspect | counts nowhere; the criterion has no row |
| `IN_REVIEW_AC_HAS_TESTS` | an `in_review` criterion, whatever the aspect | counts nowhere; the criterion has no row |

- `ac_id` is the link's criterion, and `entity_id` that id without its last `-<n>`. `line_no`, `path` and `source_url` stay unset: a collector fills them
- `message` names the scenario, the criterion and an undeclared aspect. `context` holds them as `scenario_id='<id>'`, then a space and `aspect='<value>'` for an undeclared aspect
- There is one warning per scenario and criterion, and per scenario, criterion and aspect for an undeclared aspect, in scenario order, then link order
- The run still succeeds, and no command logs a warning: the warnings are the file's
- A scenario on a `planned` or `in_review` criterion keeps its link in `ui-test-catalog` → [normalize-tests](../normalize_tests/README.md)
- The codes and their fields are the errors page's § Codes and § How codes are reported → [errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md)

## Lineage

`LINEAGE_TABLE` is one table over both inputs: the 162 `doc-source-v1.0.0` paths and the 12 `ui-tests-v1.0.0` paths.

| Input path | Output path |
|---|---|
| `user_stories[]` and `functionalities[]`: `entity_id`, `type`, `title`, `state` | `entities[].entity_id`, `.type`, `.title`, `.state` |
| `user_stories[]` and `functionalities[]`: `acceptance_criteria[].id` | `entities[].acceptance_criteria[].ac_id` |
| `user_stories[]` and `functionalities[]`: `acceptance_criteria[].state` | `entities[].acceptance_criteria[].state` |
| `user_stories[]` and `functionalities[]`: `acceptance_criteria[].aspect[]` | `entities[].acceptance_criteria[].aspects[].aspect` |
| `user_stories[]` and `functionalities[]`: `acceptance_criteria[].placeholder_values` | `entities[].acceptance_criteria[].keyword` |
| `scenarios[].scenario_id` | `entities[].acceptance_criteria[].scenario_ids[]` |

- It is declared here, and `assert_complete(LINEAGE_TABLE, "doc-source-v1.0.0")` and `assert_complete(LINEAGE_TABLE, "ui-tests-v1.0.0")` run in this package's tests only
- Every other path is `Dropped`, with its reason
  - Every `features[]` path, as the matrix has no Feature entity.
  - The other entity and criterion fields, as the matrix carries coverage, not content.
  - Each link's `id` and `aspect`, as they decide which row, and which aspect of it, lists the scenario.
  - The other `scenarios[]` paths, as a row names its scenarios by id.

### The run-time check

Before `write_artifact`, `check_no_field_loss` computes the matrix's stats as `write_artifact` will, and calls
`check_field_loss` once, with the documentation entry's `selected_stats`; the tests entry is never compared.

- It compares against the documentation input only, as the component checks' § R11 says: the one documentation input makes the comparison well defined → [component checks](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/component-checks.md)
  - Why not the tests input: a tests file linking no counted criterion would falsely fail with `FIELD_LOSS` on `scenarios[].scenario_id`.
- It compares against `selected_stats` over the counted records, not over the whole input
  - Why: over the input's own stats, an all-`planned` file writes no row and fails with `FIELD_LOSS` on `acceptance_criteria[].id` and `.state`.
  - So a new project with only planned work would get no matrix. Over the counted records, that file gets its matrix, and a builder that empties every entity's rows still fails.
  - The artifact rules' R7 defines `selected_stats` by the view filter. This command's view filters nothing, and its count rule plays that part; the contract pages do not state that reading yet → [artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md)
- It checks every mapped path, the criteria's declared aspects and keywords included: a builder that drops every row's aspects fails on `acceptance_criteria[].aspect[]` and `.placeholder_values`, and one that drops only the keywords on `.placeholder_values`
- `user_stories[]` and `functionalities[]` map to the same output paths, so a criterion, or its aspects or keyword, lost from one list while the other fills its path is a partial drop; R11 compares aggregate occupancy and does not detect it
- `FIELD_LOSS` stays a hard error when the counted records have data in a mapped path and the matrix has none

## Tests

- The fixture pair's matrix is compared with the committed [golden](tests/expected/README.md), masking only `metadata.generated_at`; the release view differs from it only in `document.view`
- Built inputs cover counted and uncounted states, a `deprecated` row, rows with every, some and no aspect covered, a bare link on a criterion with aspects, a scenario that links a criterion twice, a keyword criterion beside an `Aspect:` one, each link warning with its fields and order, the planned-work counts, the merged `source`, both `source_inputs[]` entries and forwarding from both inputs
- `full_sample("doc-source-v1.0.0")` and `full_sample("ui-tests-v1.0.0")` are written with `write_artifact` and run through the command in both views, shared input validation included
  - Their entities, every row, aspect, keyword and summary included, their root `summary` and their `planned_summary` equal `full_sample("coverage-matrix-v1.0.0")`'s, and they raise no warning.
  - The entities are compared by id: that sample lists them in another order.
- A builder that drops a mapped field, the rows, the titles, the aspects or the keywords, fails with `FIELD_LOSS` and writes no file
