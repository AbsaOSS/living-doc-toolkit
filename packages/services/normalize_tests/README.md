# living-doc-service-normalize-tests

The `normalize-tests` transform: one `ui-tests.json`, as a collector wrote it, to `ui-test-catalog.json`, the file a
generator reads. Both files are [`living-doc-utilities`](https://github.com/AbsaOSS/living-doc-utilities) contracts,
`ui-tests-v1.0.0` and `ui-test-catalog-v1.0.0`; this package keeps no copy of either.

| Module | What it holds |
|---|---|
| `living_doc_service_normalize_tests.builder` | `build_ui_test_catalog(tests, *, generated_at)`: the input's contract model to the output's. It reads and writes no file. |
| `living_doc_service_normalize_tests.lineage` | `LINEAGE_TABLE`, the command's lineage table |
| `living_doc_service_normalize_tests.service` | `normalize_tests(input_path, output_path)`, the command, and the runtime field-loss check |

The CLI registers it as `living-doc normalize-tests` ([CLI README](../../../apps/cli/README.md#normalize-tests)), and
the action runs it as `command: normalize-tests` ([README](../../../README.md#github-action)).

## What a run does

1. The input goes through the shared input validation, `validate_inputs("normalize-tests", …)`, and nothing else
   reads it ([core README](../../core/README.md#shared-input-validation)). A failing step stops the run before
   anything is built.
2. The builder groups the validated scenarios and builds the output model; the command sets its `metadata.run` to
   the CI run.
3. The runtime field-loss check compares the input's selected occupancy with the sum of all three output groups
   ([Lineage](#lineage)); a lost field stops the run.
4. `write_artifact` writes the file. It fills `metadata.stats` and `producer.utilities_version`, and validates first.

Nothing is written when a step fails.

## Grouping and order

- There is one `feature_files[]` entry per feature file, named from the scenario's `scenario_id` up to its last `/`
  only when that prefix ends with `/<source_ref.native_id>` and exactly two non-empty path components (`<org>/<repo>`)
  precede the native path. Otherwise the key and name are `source_ref.native_id`.
  - Why exactly two: a `metadata.source.repositories[]` entry is `org/repo` on GitHub and `org/project` on Azure
    DevOps ([artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md),
    § The metadata envelope), so a prefix of any other length is not a repository the contracts name.
- The repository-qualified name relies on `collector-gh`'s `scenario_id` shape, which no contract defines. Until a
  contract field names the repository, other id shapes use the native path; the final repository identifier belongs
  in a future contract change.
- A `US-` acceptance-criterion link groups its scenario under the User Story id without the final `-<n>`; `FUNC-`
  links do the same under a Functionality. A scenario linking both appears in both groups, and several links to one
  entity place it there once.
- A scenario with no links goes in `unlinked[]`. Its complete `Scenario` model, including `acceptance_criteria[]`
  and `tags[]`, is carried unchanged.
- Feature files follow their first scenario in the input. Groups follow an entity's first link; scenarios within a
  group follow input order. Nothing is sorted.

## The envelope

| Field | Value |
|---|---|
| `metadata.producer` | `name` `AbsaOSS/living-doc-toolkit`; `version` the toolkit's one version, read from the installed `living-doc-core`; `build` `null`; `utilities_version` filled by `write_artifact` |
| `metadata.run` | the CI run the file is written in, from `living_doc_core.run_context`; empty outside GitHub Actions |
| `metadata.source` | the input's, copied |
| `metadata.generated_at` | the write time, in UTC, to the second |
| `metadata.stats` | computed by `write_artifact` from the output's own groups |
| `metadata.source_inputs[]` | one entry for the input: its `schema_version`, `producer`, `run`, `source`, and `stats`; `selected_stats` is computed over all input scenarios, with no view filter |
| `document.view` | `inner`; the catalog has no view-dependent field |

- The input's own `run` stays in `source_inputs[0].run`. The output's `sources_configured`, `sources_failed`,
  `unresolved_refs` and `entities_skipped` are `0`: this transform configures no source.
- The envelope follows `living-doc-utilities`' [artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md),
  § The metadata envelope, R6 and R7; the view follows its [rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md)
  page.

## Warnings

Every input warning reaches the output unchanged but for `context`, in input order. The shared
[`living_doc_core.envelope.forwarded`](../../core/README.md#shared-envelope) helper starts the context with
`source_input='ui-tests-v1.0.0'`, then keeps the warning's own context after a space. A warning without context gets
only that source name. The rule is the [errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md)
page, § Forwarded warnings.

## Lineage

`LINEAGE_TABLE` maps each of the 12 `ui-tests-v1.0.0` scenario paths to its twin under
`feature_files[].linked_to_user_story[].scenarios[]`. The table is declared here, and
`assert_complete(LINEAGE_TABLE, "ui-tests-v1.0.0")` runs in this package's tests only.

At run time, `check_no_field_loss` computes the catalog's own stats as `write_artifact` will, then adds the matching
occupancy under `linked_to_functionality[].scenarios[]` and `unlinked[]` to each mapped User Story path before calling
`check_field_loss`. Only the stats passed to the check are aggregated; the written file keeps its own counts.

The scenarios are routed among three groups, so mapping a field to one group alone reports false loss when that
group happens not to contain the field. For example, the fixture's four `acceptance_criteria[].aspect` values are
all on Functionality links. Summing the groups lets the fixture and the utilities full sample pass. A field lost
from one group while another still has it is a partial drop; this runtime check does not detect that, because R11
compares aggregate occupancy. `FIELD_LOSS` remains a hard error when the input has data and the union of the three
groups has none. The rules are the [component checks](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/component-checks.md)
page, R11 and R12 checks 2 and 3.

## Tests

- The fixture command output is compared with the committed [golden](tests/expected/README.md), masking only
  `metadata.generated_at`.
- Built inputs cover multiple linked entities, cross-group links, duplicate links to one entity, unlinked scenarios,
  input order, and two repositories with the same native path.
- `full_sample("ui-tests-v1.0.0")` is written with `write_artifact` and run through the command, shared input
  validation included.

## Installation

```bash
pip install -e packages/services/normalize_tests
```

## License

Apache License, Version 2.0
