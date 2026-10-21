# living-doc-service-normalize-docs

The `normalize-docs` transform: one `doc-source.json`, as a collector wrote it, to `generator-ready.json`, the file a
generator reads. Both files are [`living-doc-utilities`](https://github.com/AbsaOSS/living-doc-utilities) contracts,
`doc-source-v1.0.0` and `generator-ready-v1.0.0`; this package keeps no copy of either.

| Module | What it holds |
|---|---|
| `living_doc_service_normalize_docs.builder` | `build_generator_ready(documentation, *, view, generated_at, title, version)`: the input's contract model to the output's. It reads and writes no file. |
| `living_doc_service_normalize_docs.lineage` | `LINEAGE_TABLE`, the command's lineage table |
| `living_doc_service_normalize_docs.service` | `normalize_docs(input_path, output_path, *, view, document_title, document_version)`, the command, and `check_no_field_loss(result)` |

The CLI registers it as `living-doc normalize-docs` ([CLI README](../../../apps/cli/README.md#normalize-docs)), and
the action runs it as `command: normalize-docs` ([README](../../../README.md#github-action)).

## What a run does

1. The input goes through the shared input validation, `validate_inputs("normalize-docs", …)`, and nothing else
   reads it ([core README](../../core/README.md#shared-input-validation)). A failing step stops the run before
   anything is built.
2. The builder builds the output from the validated model.
3. `check_no_field_loss` compares the lineage table's paths ([Lineage](#lineage)); a lost field stops the run.
4. `write_artifact` writes the file. It fills `metadata.stats` and `producer.utilities_version`, and validates first.

Nothing is written when a step fails.

## Content

- `doc-source`'s three entity lists share one entity model with `generator-ready`'s `content.entities[]`, so the
  builder concatenates them and translates no field:
  1. `user_stories[]`;
  2. `features[]`, each with its derived `state` and its `stub_reason`;
  3. `functionalities[]`.
- Each list keeps its input order. This is the order the canon groups entity types in, User Stories, Features,
  Functionalities, and it stays stable.
- Every authored field is carried at its authored level, as the canon's
  [rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md) page,
  § Records and presentation, requires.

## View

`--view` selects the records the output holds, through `living_doc_core.views.select_records`
([core README](../../core/README.md#the-view-filter)), once per list:

- `inner` keeps every record.
- `release` drops the records the canon's release view drops, a Feature by its derived state, and keeps
  `deprecated` ones.
- `document.selection_summary` sums the three lists' counts. Its acceptance-criteria counts cover kept entities only.

## The document block

| Field | Value |
|---|---|
| `document.view` | `--view`, `inner` by default |
| `document.title` | `--document-title`, otherwise the input's `metadata.source.project_id` |
| `document.version` | `--document-version`, otherwise `1.0.0` |
| `document.selection_summary` | what the view kept and dropped |

- The action passes no document version: a real one needs an input and a source of truth, which come later.

## The envelope

| Field | Value |
|---|---|
| `metadata.producer` | `name` `AbsaOSS/living-doc-toolkit`; `version` the toolkit's one version, read from the installed `living-doc-core`; `utilities_version` filled by `write_artifact` |
| `metadata.run` | empty |
| `metadata.source` | the input's, copied |
| `metadata.generated_at` | the write time, in UTC, to the second |
| `metadata.stats` | computed by `write_artifact` from the output |
| `metadata.source_inputs[]` | one entry, the input: its `schema_version`, `producer`, `run` and `source`; `stats`, the input's own `metadata.stats`; `selected_stats`, the same counts over the records the view kept |

- The four counts a caller reports, `sources_configured`, `sources_failed`, `unresolved_refs` and `entities_skipped`,
  are the input's in `source_inputs[0].stats`. The output's own are `0`: a transform configures no source.
- The canon's rules are the [artifact rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/artifact-rules.md)
  page: § The metadata envelope, R6 and R7.

## Warnings

Every input warning reaches the output's `warnings[]` unchanged but for `context`, in input order, also in the
release view and also when it names an entity the view dropped
([errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md) page, § Forwarded
warnings):

- `context` names the input first, by its contract id, then keeps the warning's own context after a space:
  `input='doc-source-v1.0.0' entity_id='FEAT-003' target='FEAT-002'`.
  - Why the contract id: it is the `schema_version` of the input's own `metadata.source_inputs[]` entry, so the name
    points into the same file, and a run reads one input per contract. A file name or path would depend on where
    the run happened.
- A warning without a context gets `input='doc-source-v1.0.0'`.
- `code`, `message`, `entity_id`, `ac_id`, `line_no`, `path` and `source_url` are not touched.

## Lineage

`LINEAGE_TABLE` is a `living_doc_utilities.contracts.lineage.LineageTable`. It maps each of `doc-source-v1.0.0`'s
162 field paths to its `generator-ready-v1.0.0` path, and drops none:

| Input path | Output path |
|---|---|
| `user_stories[].<field>` | `content.entities[].<field>` |
| `features[].<field>` | `content.entities[].<field>` |
| `functionalities[].<field>` | `content.entities[].<field>` |

- `<field>` is each of the 54 entity paths `lineage.ENTITY_PATHS` lists, from `entity_id` to
  `acceptance_criteria[].placeholder_values` and `rationale`.
- The table is declared here, not read from the contract.
  - Why: a field a later contract version adds fails `assert_complete(LINEAGE_TABLE, "doc-source-v1.0.0")` in this
    package's tests until the table maps it.
- The command never calls `assert_complete`, so a field the table does not know never stops a run.
- At run time, `check_no_field_loss` computes the output's stats as `write_artifact` will, and runs `check_field_loss`
  against `source_inputs[0].selected_stats`. It compares the table's mapped paths only.
  - A mapped path with data in the kept records and none in the output is `FIELD_LOSS`, and the run stops.
  - A record the view drops is not a loss: `selected_stats` counts kept records only.
  - Three input paths map to each output path, so a field lost from one list while another still fills it is a
    partial drop, which R11 does not stop at run time.
- The canon's rules are the [component checks](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/component-checks.md)
  page: R11, and R12 checks 2 and 3.

## Tests

- `test_full_sample.py`: R12 check 3, over `full_sample("doc-source-v1.0.0")` unfiltered, in both views.
  - The sample repeats its four entities in each list, which the shared input validation stops with
    `DUPLICATE_ENTITY_ID`, so the test hands the model to the builder and runs the rest as the command does.
- `test_service.py`: the command over the repository's fixture, against the goldens in [`tests/expected/`](tests/expected/README.md).
- `test_authored_fields.py`: each named authored field, and `living-doc-utilities`' six golden entities
  ([`tests/fixtures/utilities-golden/`](../../../tests/fixtures/utilities-golden/README.md)) compared field by field.

## Installation

```bash
pip install -e packages/services/normalize_docs
```

## License

Apache License, Version 2.0
