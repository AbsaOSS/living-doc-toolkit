## Overview

Re-baselines the `coverage-matrix` service's golden integration fixtures on **real
`living-doc-collector-gh` output** instead of hand-authored JSON, so "schema as specced"
and "schema as shipped" can no longer silently diverge.

- **New `.feature` corpus** — `packages/services/coverage_matrix/tests/fixtures/corpus/us/`
  holds a small, committed corpus (User Login / View Dashboard / Delete Domain plus an
  orphan and an unknown-story file) that exercises the full matrix: a covered AC, an
  uncovered AC, a deprecated AC, a stale `@AC:` reference, an unlinked scenario and a
  scenario for an unresolved User Story.
- **`generate_golden_inputs.py`** — a developer tool that runs `collector-gh`'s
  `doc-source` and `ui-tests` modes over the corpus and writes the mined JSON to
  `tests/fixtures/golden/doc_source.json` / `ui_tests.json`. The only post-processing is
  determinism normalisation (the dynamic `generated_at` timestamp and GitHub-Actions env
  fields are pinned; the source URL is made repo-relative). It records the exact
  `collector-gh` commit it was run against (`b6c935d`).
- **`golden/doc_source.json` / `golden/ui_tests.json`** regenerated as real collector
  output — they now carry the full collector envelope (three named lists for doc-source,
  flat `items[]` for ui-tests, `AdapterMetadata`, the new AC fields `aspect` /
  `preconditions` / deprecation metadata, `ac_links`, step bodies).
- **`golden/expected_coverage_matrix.json`** regenerated from the real inputs via
  `golden/regenerate_expected.py`. Coverage facts are unchanged (3 US, 5 ACs, 4 active,
  3 covered, 75 %); only ordering and the added `source.line` differ.
- **`synthetic/` fixtures kept** — hand-authored inputs for shapes the corpus can't
  produce: empty inputs, and a cross-source `US-1` id collision that also contains an
  unmatched AC and an unresolved User Story.
- **New tests** — `test_golden_inputs_are_real_collector_output` guards that the golden
  inputs are collector output and that the `@AC:` → AC-ID join resolves;
  `test_synthetic_empty_inputs` and `test_synthetic_cross_source_collision` cover the
  edge cases.
- **Docs** — `tests/fixtures/README.md` (fixture map + two-step refresh procedure),
  `tests/fixtures/synthetic/README.md`, and a Testing section in the package README.

No production code, CLI contract, schema, or `coverage-matrix.json` structure changed.

### Follow-up (not in this PR)

The vendored `schema/doc-source-v1.0.0-schema.json` predates the AC fields `collector-gh`
added in its P2-CGH1/CGH2 work; the real golden output still validates against it (the
schema has no `additionalProperties: false`), but a byte-for-byte re-sync per
`schema/README.md` is a separate `P2-TK1`-style chore.

## Release Notes

- The `coverage-matrix` service's golden tests now run against real
  `living-doc-collector-gh` output mined from a committed `.feature` corpus, so a
  collector schema or parser change that alters the mined `doc-source.json` /
  `ui-tests.json` is caught here instead of drifting silently.

## Related

Closes #71

## Acceptance criteria

| # | Criterion | Proof |
|---|---|---|
| 1 | Golden tests consume `doc-source.json` / `ui-tests.json` from `collector-gh`'s actual modes | `tests/fixtures/generate_golden_inputs.py`; `tests/fixtures/golden/doc_source.json:133` + `ui_tests.json:256` (`"name": "AbsaOSS/living-doc-collector-gh"`); `tests/integration/test_golden_files.py:49` |
| 2 | Synthetic fixtures replaced/supplemented; expected goldens regenerated | `tests/fixtures/golden/{doc_source,ui_tests,expected_coverage_matrix}.json` regenerated; `tests/fixtures/golden/regenerate_expected.py`; `tests/fixtures/synthetic/` added |
| 3 | ≥ 1 synthetic fixture for edge cases (empty, unmatched AC, cross-source) | `tests/fixtures/synthetic/empty_*.json`, `tests/fixtures/synthetic/collision_*.json`; `test_golden_files.py:105` and `:120` |
| 4 | AC-ID join validation: real `@AC:<id>` tags produce correct AC IDs | `test_golden_files.py:56-61` (declared vs scenario `ac_ids`); `test_golden_files.py:63` `test_golden_summary_and_buckets` asserts coverage from the real tags |
| 5 | `make qa` / `make integration` green for `coverage_matrix` | `make qa-coverage`: ruff clean, pylint 9.85/10 (≥ 9.5), mypy clean, black clean, pytest 37 passed / 97.65 % cov; `make integration` passes |
| 6 | Test docs updated; golden-refresh process clear | `tests/fixtures/README.md`, `tests/fixtures/synthetic/README.md`, `packages/services/coverage_matrix/README.md` Testing section |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
