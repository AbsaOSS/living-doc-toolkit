# living-doc-service-coverage-matrix

Coverage matrix generator for the Living Documentation Toolkit.

Cross-references two collector outputs to produce an AC-level test coverage matrix
per User Story, ready for PDF report generation.

## Inputs

| Input | Source | Description |
|---|---|---|
| `doc-source.json` | living-doc-collector-gh `doc-source` mode | User Stories with acceptance criteria |
| `ui-tests.json` | living-doc-collector-gh `ui-tests` mode | UI/E2E test scenarios with `us_id` / `ac_ids` |

The doc input may be a bare JSON array of User Story objects, a legacy collector
envelope exposing an `items` array, or a `doc-source` envelope exposing
`user_stories`, `functionalities`, and `features` arrays. The tests input must be an
envelope with an `items` array.

Only a full `doc-source` envelope (one carrying `metadata` and `warnings`) is validated
against a vendored, pinned copy of
[`doc-source-v1.0.0-schema.json`](src/living_doc_service_coverage_matrix/schema/doc-source-v1.0.0-schema.json);
a bare JSON array or a legacy `items` envelope is accepted without schema validation.
`living-doc-collector-gh` owns and generates that schema; this service is a vendoring
consumer only — see [`schema/README.md`](src/living_doc_service_coverage_matrix/schema/README.md)
for the ownership split and re-sync procedure.

## Output

`coverage-matrix.json`, conforming to
[`coverage-matrix-v1.0.0-schema.json`](src/living_doc_service_coverage_matrix/schema/coverage-matrix-v1.0.0-schema.json).
It groups results into `user_stories`, `functionalities`, and `features`.
This service **owns** that output schema — it is not vendored from anywhere else.

## CLI

```
living-doc coverage-matrix \
  --doc-input   doc-source.json \
  --tests-input ui-tests.json \
  --output      coverage-matrix.json \
  [--fail-under 80]
```

| Argument | Required | Description |
|---|---|---|
| `--doc-input` | yes | Path to the US+AC doc JSON file |
| `--tests-input` | yes | Path to the ui-tests JSON file |
| `--output` | yes | Destination path for the coverage matrix JSON |
| `--fail-under` | no | Exit with code 1 if `coverage_pct < N` |

## Matching logic

- A scenario links to a User Story when `scenario.us_id` equals the US short id
  (the numeric suffix of `us.id`, e.g. `org/repo/US-27` -> `US-27`).
- When two User Stories share a short id across sources, the scenario's
  `source.org` / `source.repo` picks the matching one. A scenario whose `source` matches
  none of the colliding User Stories is left unresolved (it becomes an unlinked test); a
  scenario with no usable `source` falls back to the first in document order so the
  output stays deterministic.
- A scenario covers an AC when the `ac_id` appears in `scenario.ac_ids` and matches a
  known `acceptance_criteria[].id` on the resolved User Story.
- `coverage_pct` counts only Active ACs, so deprecated ACs never inflate it.
- Scenarios with an unresolved `us_id` land in `unlinked_tests`; `ac_ids` that do not
  exist on the resolved US land in `stale_ac_refs`.

## Module layout

- `loader.py` — pure I/O: `load_doc_input()`, `load_tests_input()`
- `matcher.py` — pure: `build_coverage_matrix()`
- `summary.py` — pure: `compute_summary()`, `compute_us_summary()`
- `service.py` — orchestration: `run_service()`
- `model/coverage_item.py` — output dataclasses
- `schema/` — shipped JSON Schema (`doc-source-v1.0.0` vendored from `collector-gh`, `coverage-matrix-v1.0.0` owned here — see `schema/README.md`)

## Testing

The golden integration fixtures (`tests/fixtures/golden/`) are **real
`living-doc-collector-gh` output** — the `.feature` corpus in `tests/fixtures/corpus/` is
mined by the collector's `doc-source` and `ui-tests` modes, so a schema/parser change in
`collector-gh` that alters the mined output surfaces here as a failing golden test.
Hand-authored fixtures under `tests/fixtures/synthetic/` cover shapes the corpus does not
produce (empty inputs, a cross-source User Story id collision). See
[`tests/fixtures/README.md`](tests/fixtures/README.md) for the two-step golden-refresh
procedure.
