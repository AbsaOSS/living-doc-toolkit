# living-doc-service-coverage-matrix

The `coverage-matrix` transform: one `doc-source.json` and one `ui-tests.json`, as a collector wrote them, to
`coverage-matrix.json`, the file a generator reads. The three files are
[`living-doc-utilities`](https://github.com/AbsaOSS/living-doc-utilities) contracts, `doc-source-v1.0.0`,
`ui-tests-v1.0.0` and `coverage-matrix-v1.0.0`; this package keeps no copy of any of them.

| Module | What it holds |
|---|---|
| `living_doc_service_coverage_matrix.builder` | `build_coverage_matrix(documentation, tests, *, view, generated_at)`: the inputs' contract models to the output's. It reads and writes no file. |
| `living_doc_service_coverage_matrix.lineage` | `LINEAGE_TABLE`, the command's lineage table over both inputs |
| `living_doc_service_coverage_matrix.service` | `coverage_matrix(doc_inputs, tests_input, output_path, *, view)`, the command, and `check_no_field_loss(result)` |

The CLI registers it as `living-doc coverage-matrix` ([CLI README](../../../apps/cli/README.md#coverage-matrix)),
with the `--fail-under` gate, and the action runs it as `command: coverage-matrix`
([README](../../../README.md#github-action)).

Coverage is counted per declared aspect: a criterion that declares aspects or a keyword is `covered`,
`partially_covered` or `not_covered` from its aspects, and a scenario link the matrix does not count as written is a
warning in the file.

## What a run does

1. Both inputs go through the shared input validation, `validate_inputs("coverage-matrix", …)`, and nothing else
   reads them ([core README](../../core/README.md#shared-input-validation)). A failing step stops the run before
   anything is built.
   - A run reads exactly one documentation file, so a second one fails with `MULTIPLE_DOCUMENTATION_SOURCES`.
   - A repeated entity id, or a repeated criterion id under one entity, fails with `DUPLICATE_ENTITY_ID` or
     `DUPLICATE_AC_ID`, listing every place.
2. The builder builds the matrix from the validated models, and the command sets its `metadata.run` to the CI run.
3. `check_no_field_loss` compares the lineage table's paths against the documentation input
   ([Lineage](#lineage)); a lost field stops the run.
4. `write_artifact` writes the file. It fills `metadata.stats` and `producer.utilities_version`, and validates first.

Nothing is written when a step fails.

## Entities and rows

- There is one `entities[]` entry per User Story and per Functionality, whatever its state, and whether or not it
  has a counted criterion. Its `type`, `title` and `state` are the entity's own.
- There is no Feature entity.
- An entity has a row per `active` or `deprecated` criterion, with that criterion's `state`.
  - A `planned` or an `in_review` criterion has no row.
- A link matches a criterion by its `id`, whatever repository the scenario is in.
- A criterion that declares aspects, with `Aspect:` or a keyword, gets an `aspects[]` entry per declared value, in
  declared order.
  - An aspect lists the `scenario_id` of every scenario whose link names that aspect. A bare `@AC:<id>` link, with no
    aspect, lists its scenario under every aspect.
  - An aspect is `covered` with at least one scenario and `not_covered` with none. The row's `status` follows its
    aspects, and its own `scenario_ids` stays empty.
  - A keyword criterion's row carries `keyword`, the criterion's one `placeholder_values` key, as stored (`rule`); an
    `Aspect:` row carries none. The keyword's name in a scenario tag is not stored, so it is not checked.
  - A link to an aspect the criterion does not declare counts nowhere ([Warnings](#warnings)).
- A criterion without aspects gets a plain row: it lists the `scenario_id` of every scenario that links it, and is
  `covered` with at least one scenario and `not_covered` with none. It carries no aspect and no keyword.
  - A link with an aspect covers it too, as a bare one does, and is a warning: the scenario names the criterion, and
    the criterion has one thing to cover.
- A scenario is listed once per aspect, and once per plain row, however many of its links reach it.
- Order: every User Story, then every Functionality, each in input order. Rows follow the entity's own criteria,
  aspects the criterion's declared values, and the scenarios the tests input. Nothing is sorted.

Which criteria are counted, and what each status means, are the canon's
[rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md) page,
§ Coverage; how a keyword declares its values, the
[AC grammar](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/authoring/ac-grammar.md) page,
§ Variants.

## Summaries

- Each entity's `summary` comes from `CoverageSummary.from_rows` over its own rows, and the root `summary` over every
  row of every entity.
  - An entity without a row counts `0` criteria and has no percentage, `null`.
- `planned_summary` counts the `planned` criteria of User Stories and Functionalities: one with a `version` under
  `by_target_version`, in the order first met, and one without in `backlog`. `total` is their sum. An `in_review`
  criterion is in neither.

The rules are the [rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md)
page, § Coverage summary and § Planned work summary.

## View and gate

- `--view` sets `document.view`, `inner` by default, and nothing else: both views have the same rows and the same
  counts. What a view shows is the generator's.
- `--fail-under` is the CLI's gate, run after the file is written, on the root `coverage_pct`
  ([CLI README](../../../apps/cli/README.md#coverage-matrix)). The service has no gate.

## The envelope

| Field | Value |
|---|---|
| `metadata.producer` | `name` `AbsaOSS/living-doc-toolkit`; `version` the toolkit's one version, read from the installed `living-doc-core`; `build` `null`; `utilities_version` filled by `write_artifact` |
| `metadata.run` | the CI run the file is written in, from `living_doc_core.run_context`; empty outside GitHub Actions |
| `metadata.source` | the documentation input's, with each of the tests input's `systems` it does not name added once |
| `metadata.generated_at` | the write time, in UTC, to the second |
| `metadata.stats` | computed by `write_artifact` from the matrix's own entities |
| `metadata.source_inputs[]` | the documentation input's entry, then the tests input's, each with its `schema_version`, `producer`, `run`, `source`, `stats` and `selected_stats` |
| `document.view` | `--view` |

- Each input's own `run` stays in its `source_inputs[]` entry. The output's `sources_configured`, `sources_failed`,
  `unresolved_refs` and `entities_skipped` are `0`: this transform configures no source.
- The documentation entry's `selected_stats` are computed over the records the matrix counts: the User Stories and
  Functionalities, each with only its `active` and `deprecated` criteria, and no Feature. Its `stats` against its
  `selected_stats` shows what the matrix leaves out.
- The tests entry's `selected_stats` are computed over all its scenarios, so they equal its occupancy.
- The envelope follows `living-doc-utilities`' [artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md),
  § The metadata envelope, R6 and R7.

## Warnings

Every input warning reaches the output unchanged but for `context`: the documentation input's first, then the tests
input's, each in input order. The shared [`living_doc_core.envelope.forwarded`](../../core/README.md#shared-envelope)
helper starts each context with its own input, `source_input='doc-source-v1.0.0'` or
`source_input='ui-tests-v1.0.0'`, then keeps the warning's own context after a space. The rule is the
[errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md) page, § Forwarded
warnings.

After them, the command adds a warning for each scenario link it does not count as written:

| Code | The link names | The link |
|---|---|---|
| `STALE_AC_REF` | a criterion no User Story or Functionality in the documentation input has | counts nowhere |
| `STALE_AC_REF` | an aspect its criterion does not declare | counts nowhere; on a criterion without aspects, covers it |
| `PLANNED_AC_HAS_TESTS` | a `planned` criterion, whatever the aspect | counts nowhere; the criterion has no row |
| `IN_REVIEW_AC_HAS_TESTS` | an `in_review` criterion, whatever the aspect | counts nowhere; the criterion has no row |

- `ac_id` is the link's criterion, and `entity_id` that id without its last `-<n>`. `line_no`, `path` and
  `source_url` stay unset: a collector fills them.
- `message` names the scenario, the criterion and an undeclared aspect. `context` holds them as
  `scenario_id='<id>'`, with ` aspect='<value>'` for an undeclared aspect.
- There is one warning per scenario and criterion, and per scenario, criterion and aspect for an undeclared aspect,
  in scenario order, then link order.
- The run still succeeds, and no command logs a warning: the warnings are the file's.
- A scenario on a `planned` or `in_review` criterion keeps its link in `ui-test-catalog`
  ([`normalize-tests`](../normalize_tests/README.md)).

The codes and their fields are the
[errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md) page, § Codes and § How
codes are reported.

## Lineage

`LINEAGE_TABLE` is one table over both inputs: the 162 `doc-source-v1.0.0` paths and the 12 `ui-tests-v1.0.0` paths.
It is declared here, and `assert_complete(LINEAGE_TABLE, "doc-source-v1.0.0")` and
`assert_complete(LINEAGE_TABLE, "ui-tests-v1.0.0")` run in this package's tests only.

| Input path | Output path |
|---|---|
| `user_stories[]` and `functionalities[]`: `entity_id`, `type`, `title`, `state` | `entities[].entity_id`, `.type`, `.title`, `.state` |
| `user_stories[]` and `functionalities[]`: `acceptance_criteria[].id` | `entities[].acceptance_criteria[].ac_id` |
| `user_stories[]` and `functionalities[]`: `acceptance_criteria[].state` | `entities[].acceptance_criteria[].state` |
| `user_stories[]` and `functionalities[]`: `acceptance_criteria[].aspect[]` | `entities[].acceptance_criteria[].aspects[].aspect` |
| `user_stories[]` and `functionalities[]`: `acceptance_criteria[].placeholder_values` | `entities[].acceptance_criteria[].keyword` |
| `scenarios[].scenario_id` | `entities[].acceptance_criteria[].scenario_ids[]` |

Every other path is `Dropped`, with its reason: every `features[]` path, as the matrix has no Feature entity; the
other entity and criterion fields, as the matrix carries coverage, not content; each link's `id` and `aspect`, as
they decide which row, and which aspect of it, lists the scenario; and the other `scenarios[]` paths, as a row names
its scenarios by id.

### The run-time check

Before `write_artifact`, `check_no_field_loss` computes the matrix's stats as `write_artifact` will, and calls
`check_field_loss` once, with the documentation entry's `selected_stats`. The tests entry is never compared.

- Against the documentation input only, as the canon's
  [component checks](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/component-checks.md),
  § R11, says: the one documentation input makes the comparison well defined.
  - Why not the tests input as well: a tests file in which no scenario links a counted criterion would fail with
    `FIELD_LOSS` on `scenarios[].scenario_id`, though the matrix lost nothing.
- Against `selected_stats` over the counted records, not over the whole input.
  - Why: with the input's own stats, a documentation file whose criteria are all `planned` writes no row and would fail
    with `FIELD_LOSS` on `acceptance_criteria[].id` and `.state`, so a new project with only planned work would get
    no matrix. Over the counted records, that file gets its matrix, and a builder that empties every entity's rows
    still fails.
  - The [artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md),
    R7, define `selected_stats` by the view filter. This command's view filters nothing, and its count rule plays
    that part. The contract pages do not state that reading yet.
- It checks every mapped path, the criteria's declared aspects and keywords included: a builder that drops every
  row's aspects fails on `acceptance_criteria[].aspect[]` and `.placeholder_values`, and one that drops only the
  keywords on `.placeholder_values`.
- `user_stories[]` and `functionalities[]` map to the same output paths, so a criterion, or a criterion's aspects or
  keyword, lost from one list while the other fills its path is a partial drop. R11 compares aggregate occupancy, and
  does not detect it.
- `FIELD_LOSS` stays a hard error when the counted records have data in a mapped path and the matrix has none.

## Tests

- The fixture pair's matrix is compared with the committed [golden](tests/expected/README.md), masking only
  `metadata.generated_at`; the release view differs from it only in `document.view`.
- Built inputs cover counted and uncounted states, a `deprecated` row, rows with every, some and no aspect covered, a
  bare link on a criterion with aspects, a scenario that links a criterion twice, a keyword criterion beside an
  `Aspect:` one, each link warning with its fields and order, the planned-work counts, the merged `source`, both
  `source_inputs[]` entries and forwarding from both inputs.
- `full_sample("doc-source-v1.0.0")` and `full_sample("ui-tests-v1.0.0")` are written with `write_artifact` and run
  through the command in both views, shared input validation included. Their entities, every row, aspect, keyword and
  summary included, their root `summary` and their `planned_summary` equal `full_sample("coverage-matrix-v1.0.0")`'s,
  and they raise no warning. The entities are compared by id: that sample lists them in another order.
- A builder that drops a mapped field, the rows, the titles, the aspects or the keywords, fails with `FIELD_LOSS` and
  writes no file.

## Installation

```bash
pip install -e packages/services/coverage_matrix
```

## License

Apache License, Version 2.0
