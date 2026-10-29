# Services

Parent: `../../CONTEXT.md`

## Purpose

One package per command, each a transform from validated input contracts to one output contract:
`normalize_docs` (`normalize-docs`), `normalize_tests` (`normalize-tests`), `coverage_matrix` (`coverage-matrix`).

Not responsible for: option parsing and error lines (`apps/cli`), reading and validating inputs (`packages/core`),
the contract models (`living-doc-utilities`).

## How it fits

Every package has the same three modules:

| Module | Holds | Rule |
|---|---|---|
| `builder.py` | `build_<output>(…)`: contract models in, the output model out | No I/O, no environment reads; leaves `metadata.run` empty and the caller counts in `metadata.stats` at 0 |
| `lineage.py` | `LINEAGE_TABLE`: every input field path mapped to an output path, or `Dropped` with a reason | Paths are declared literally, never read from the contract |
| `service.py` | The command function and `check_no_field_loss` | `validate_inputs` → builder → `run_context()` → `check_no_field_loss` → `write_artifact` |

- Depends on `living-doc-core` and `living-doc-utilities` only; `apps/cli` imports the service module.
- Each package README holds its rules and the canon sections it implements; read it before changing the package.

## Conventions

- Forward every input warning with `living_doc_core.envelope.forwarded`, in input order, before the command's own.
- `assert_complete(LINEAGE_TABLE, "<contract-id>")` runs in the package's tests only, never at run time.
- `check_no_field_loss` computes the output's stats as `write_artifact` will, then calls `check_field_loss` against
  a `source_inputs[]` entry's `selected_stats`; each README § Lineage says which entry and what it aggregates.
- Tests read `tests/fixtures/collector-gh/` through `conftest.py`, and build edge cases with `model_copy(update=…)`
  on the fixture models.
- A `FIELD_LOSS` test monkeypatches the `service` module (`build_<output>` wrapped to drop a field, or
  `LINEAGE_TABLE`) and asserts the lost path is named and no file is written.
- R12 check 3: `full_sample("<input-contract>")`, written with `write_artifact`, runs through the command.

## Invariants and gotchas

- `model_copy` skips validation: a built input or a dropped field passes until `write_artifact` validates the output.
- Several input lists mapped to one output path make a loss from one list undetectable (a partial drop): R11 compares
  aggregate occupancy.
- Each `tests/expected/README.md` says how to regenerate the golden: run the command over the fixture pair with no
  `GITHUB_*` variable set, review the diff, replace the file. The comparison masks `metadata.generated_at` only.
- `coverage-matrix` counts per declared aspect and writes its own link warnings (`STALE_AC_REF`,
  `PLANNED_AC_HAS_TESTS`, `IN_REVIEW_AC_HAS_TESTS`) after the forwarded ones; the rules are its
  [README](coverage_matrix/README.md).
- `coverage-matrix` checks field loss against the documentation input only, over the counted criteria.
- `full_sample("coverage-matrix-v1.0.0")` lists its entities in another order than the command and names another
  input: compare it by entity id, never by position or `source_inputs`.
