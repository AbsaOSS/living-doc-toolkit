# normalize-docs

## Purpose

This page defines how `normalize-docs` turns one `doc-source.json` into `generator-ready.json`: content, view,
document block, envelope, warnings and lineage. Developers who change the command, and readers of its output, read it.

Read before: [Core](../../core/README.md) · Next: [normalize-tests](../normalize_tests/README.md)

## Contents

- [Modules](#modules)
- [What a run does](#what-a-run-does)
- [Content](#content)
- [View](#view)
- [The document block](#the-document-block)
- [The envelope](#the-envelope)
- [Warnings](#warnings)
- [Lineage](#lineage)
- [Tests](#tests)

## Modules

`living-doc-service-normalize-docs` turns one `doc-source.json`, as a collector wrote it, into `generator-ready.json`,
the file a generator reads.

| Module | What it holds |
|---|---|
| `living_doc_service_normalize_docs.builder` | `build_generator_ready(documentation, *, view, generated_at, title, version)`: the input's contract model to the output's. It reads and writes no file. |
| `living_doc_service_normalize_docs.lineage` | `LINEAGE_TABLE`, the command's lineage table |
| `living_doc_service_normalize_docs.service` | `normalize_docs(input_path, output_path, *, view, document_title, document_version)`, the command, and `check_no_field_loss(result)` |

- Both files are `living-doc-utilities` contracts, `doc-source-v1.0.0` and `generator-ready-v1.0.0`; this package keeps no copy of either
- The CLI registers it as `living-doc normalize-docs`, and the action runs it as `command: normalize-docs` → [CLI](../../../apps/cli/README.md#normalize-docs), [Commands](../../../docs/action.md#commands)

## What a run does

A run takes these steps; nothing is written when one fails:

1. The input goes through the shared input validation, `validate_inputs("normalize-docs", …)`, and nothing else reads it ([Shared input validation](../../core/README.md#shared-input-validation)). A failing step stops the run before anything is built.
2. The builder builds the output from the validated model, and the command sets its `metadata.run` to the CI run.
3. `check_no_field_loss` compares the lineage table's paths ([Lineage](#lineage)); a lost field stops the run.
4. `write_artifact` validates the output, then writes it.

## Content

The builder concatenates `doc-source`'s three entity lists into `content.entities[]`, in this order:

1. `user_stories[]`;
2. `features[]`, each with its derived `state` and its `stub_reason`;
3. `functionalities[]`.

- The three lists share one entity model with `content.entities[]`, so no field is translated.
- Each list keeps its input order. This is the order the canon groups entity types in, User Stories, Features, Functionalities, and it stays stable.
- Every authored field is carried at its authored level, as the rendering page's § Records and presentation requires → [rendering](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/rendering.md)

## View

`--view` selects the records the output holds through the core [view filter](../../core/README.md#the-view-filter), once per list:

- `release` drops the records the canon's release view drops, a Feature by its derived state, and keeps `deprecated` ones.
- `document.selection_summary` sums the three lists' counts; its acceptance-criteria counts cover kept entities only

## The document block

| Field | Value |
|---|---|
| `document.view` | `--view`, `inner` by default |
| `document.title` | `--document-title`, otherwise the input's `metadata.source.project_id` |
| `document.version` | `--document-version`, otherwise `1.0.0` |
| `document.selection_summary` | what the view kept and dropped |

- The default version is `1.0.0`
- The action passes no document version: a real one needs an input and a source of truth, which come later

## The envelope

The fields `normalize-docs` fills its own way; every command fills the rest the same way, as the core's [Shared envelope](../../core/README.md#shared-envelope) says:

| Field | Value |
|---|---|
| `metadata.source` | the input's, copied |
| `metadata.source_inputs[]` | one entry, the input: its `schema_version`, `producer`, `run` and `source`; `stats`, the input's own `metadata.stats`; `selected_stats`, the same counts over the records the view kept |

- The four counts a caller reports, `sources_configured`, `sources_failed`, `unresolved_refs` and `entities_skipped`, are the input's in `source_inputs[0].stats`
- The input's own run stays in `source_inputs[0].run`

## Warnings

Every input warning reaches the output's `warnings[]` through the core's [`forwarded`](../../core/README.md#shared-envelope), in input order:

- It is forwarded in the release view too, also when it names an entity the view dropped.
- Its `context` starts with `source_input='doc-source-v1.0.0'`.

## Lineage

`LINEAGE_TABLE` is a `living_doc_utilities.contracts.lineage.LineageTable`. It maps each of `doc-source-v1.0.0`'s 162
field paths to its `generator-ready-v1.0.0` path, and drops none.

| Input path | Output path |
|---|---|
| `user_stories[].<field>` | `content.entities[].<field>` |
| `features[].<field>` | `content.entities[].<field>` |
| `functionalities[].<field>` | `content.entities[].<field>` |

- `<field>` is each of the 54 entity paths, from `entity_id` to `acceptance_criteria[].placeholder_values` and `rationale`
- The table is declared here, not read from the contract
  - Why: a field a later contract version adds fails `assert_complete(LINEAGE_TABLE, "doc-source-v1.0.0")` in this package's tests until the table maps it.
- The command never calls `assert_complete`, so a field the table does not know never stops a run
- At run time, `check_no_field_loss` computes the output's stats as `write_artifact` will, and runs `check_field_loss` against `source_inputs[0].selected_stats`; it compares the table's mapped paths only
  - A mapped path with data in the kept records and none in the output is `FIELD_LOSS`, and the run stops.
  - A record the view drops is not a loss: `selected_stats` counts kept records only.
  - Three input paths map to each output path, so a field lost from one list while another still fills it is a partial drop, which R11 does not stop at run time.
- The canon's rules are the component checks: R11, and R12 checks 2 and 3 → [component checks](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/component-checks.md)

## Tests

- R12 check 3: `full_sample("doc-source-v1.0.0")`, unfiltered, is written with `write_artifact` and run through the command, the shared input validation included, in both views; the release view's expected counts are derived from the sample
- The command over the repository's fixture, against the goldens in [`tests/expected/`](tests/expected/README.md)
- Each named authored field, and `living-doc-utilities`' six golden entities ([`tests/fixtures/utilities-golden/`](../../../tests/fixtures/utilities-golden/README.md)) compared field by field
