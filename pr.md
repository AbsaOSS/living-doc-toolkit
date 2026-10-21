## Overview

Adds `living-doc normalize-docs`, the first command the action runs. It reads one `doc-source.json` through the shared
input validation and writes `generator-ready.json` on the `living-doc-utilities` `0.7.0` contract, with every authored
field of every entity the view keeps, the metadata envelope and the input's warnings. It checks its field-lineage
table before it writes. A field that has data in the input and arrives empty stops the run with `FIELD_LOSS`.

**Mapping.** `doc-source`'s three lists share one entity model with `generator-ready`'s `content.entities[]`, so the
builder concatenates them in a fixed order, User Stories, then Features, then Functionalities, each in input order.
No field is translated. This is the order the canon groups entity types in, and the Markdown generator groups them the
same way. `build_generator_ready` is typed on the contract models in and out and does no I/O. The new package
`packages/services/normalize_docs` (`living-doc-service-normalize-docs` `0.1.0`) holds it, with the command's lineage
table.

**View filter.** `living_doc_core.views.select_records(entities, view)` is the one view filter and returns the
contract's own `SelectionSummary`. `inner` keeps everything. `release` drops `planned` and `in_review` entities, a
Feature by its derived state, and the `planned` and `in_review` criteria of the entities it keeps, and it keeps
`deprecated` ones. It selects records and never edits a field. `selected_stats` is computed over the kept records, so a
record the view drops is never a `FIELD_LOSS`.

**The action.** `command: normalize-docs` now runs, and `normalize-tests` and `coverage-matrix` still stop with one
line, ``Command `<name>` is not available yet.`` (the old "; no command runs yet" tail is gone). `action-run` is back
with a `normalize-docs` step over the fixture, and the venv jobs' `normalize-docs` runs now assert success and the
written file.

Other changes:

- **One version.** `living-doc-core` moves from `1.0.0` to `0.1.0`, so every package declares `0.1.0`.
  `metadata.producer.version` is read from the installed `living-doc-core`, never from a literal.
- **`--verbose` on the command too.** `main.py` passes `--verbose` after the command's options, so `normalize-docs`
  takes it as well as the group does. `living-doc --verbose normalize-docs …` still works.
- **Forwarded `context` format.** The context reads `input='<contract id>' <the warning's own context>`, for example
  `input='doc-source-v1.0.0' entity_id='FEAT-003' target='FEAT-002'`. The contract id is the `schema_version` of the
  input's own `source_inputs[]` entry, so the name points into the same file. A run reads one input per contract, and
  the name does not depend on where the run happened.
- **The output's own `sources_configured`, `sources_failed`, `unresolved_refs` and `entities_skipped` are `0`.** The
  canon puts the input's counts in the audit record, and they are in `source_inputs[0].stats`.
- **Registration.** The package is registered in `requirements.txt`, the `Makefile` (alias `normalize-docs`),
  `.github/dependabot.yml`, `DEVELOPER.md` § Monorepo Layout and the agent and Copilot docs that list the aliases.
- **Fixtures.** `utilities`' six golden entities are copied from `v0.7.0` (`8d0e244`) into
  `tests/fixtures/utilities-golden/`, with their source noted beside them.

### Rules implemented

| Rule | Page (`living-doc-utilities` `docs/contracts/` unless noted) | Where |
|---|---|---|
| Every authored field carried at its authored level | `rendering.md` § Records and presentation | `builder.py` concatenation; `test_authored_fields.py` |
| The view filter selects records only; release drops `planned` / `in_review` entities and criteria, a Feature by its derived state | `rendering.md` § Records and presentation | `living_doc_core/views.py` |
| A transform forwards every input warning unchanged, naming the input in the context | `errors.md` § Forwarded warnings; `pipeline-rules.md` (a transform copies the source counts into its audit record) | `builder.py::forwarded` |
| The envelope: the producer is the transform (R6); `source` copied from the one documentation input; the `document` block | `artifact-rules.md` § The metadata envelope, R6 | `builder.py` |
| One `source_inputs[]` entry with `schema_version`, `producer`, `run`, `source`, `stats` and `selected_stats` (R7) | `artifact-rules.md` R7 | `builder.py` |
| The lineage table in the transform's own package; `assert_complete` in tests; `FIELD_LOSS` at run time against `selected_stats` (R11) | `component-checks.md` § R11 | `lineage.py`, `service.py::check_no_field_loss` |
| One read path and one write path, typed on contract models (R12 check 2) | `component-checks.md` § Check 2 | `validate_inputs` → `read_artifact`; `write_artifact`; `test_builder.py` |
| The full-sample test in every view (R12 check 3) | `component-checks.md` § Check 3 | `test_full_sample.py` |
| No hand-written twin of a contract model | `living-doc` `docs/introduction/principles.md` § The frame, F7 | `select_records` returns `SelectionSummary` |

Nothing added contradicts a page.

### Found during the work

- **The full sample cannot pass the command's own input step, so the R12 check 3 test starts after it.**
  - **What the sample holds.** `living_doc_utilities/contracts/testing.py::_doc_source_sample` (`v0.7.0`, lines
    307-314) puts one list of four entities, US-001, US-002, FEAT-001 and FUNC-001, into each of `user_stories[]`,
    `features[]` and `functionalities[]`.
    - This is deliberate. R11 counts occupancy per list, so each list needs every entity shape to fill all 54 of its
      paths. `user_stories[].stub_reason`, for one, can only be filled by a Feature.
  - **What the toolkit does with it.** Written to a file and run through `normalize-docs`, the sample stops at step 6
    of the shared input validation ([errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md),
    § Shared input validation order). There are four problems, one per id, for example
    `[DUPLICATE_ENTITY_ID] … entity id 'US-001' at user_stories[0], features[0], functionalities[0]`. Nothing is
    built.
  - **Where the two pages pull apart.** [Component checks](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/component-checks.md)
    § Check 3 says "a transform runs over it in every view", and that the sample "stays something a real pipeline
    could produce". The errors page has the toolkit reject that same sample before any transform. Both rules are
    right on their own; the sample just does not meet the second.
  - **What the test does instead.** `test_full_sample.py` hands the sample to `build_generator_ready` as the model
    `validate_inputs` would have returned. From there it runs exactly what the command runs: the view filter, the
    field-loss check, `write_artifact` and a read back. Only the input step is skipped, and the fixture and golden
    tests cover it.
  - **The fix belongs upstream.** `living-doc-utilities` would give the copies in `features[]` and
    `functionalities[]` their own ids, for example US-101 and US-201. The shapes, and so the per-list occupancy, stay
    as they are, and the sample then passes the input step. Once it does, the test can run the whole command.
  - **Not yet raised on #87**: the owner raises it there, and upstream on `living-doc-utilities` if wanted.
- No lineage path is dropped: all 162 `doc-source-v1.0.0` paths map one to one onto the 54 `content.entities[]`
  paths.
- `check_field_loss` is per path, and three input paths map to each output path. So a field lost from one list while
  another list still fills it counts as a partial drop, which R11 does not stop at run time. The package README says
  so.

### Results

- `make qa`: every package gate passes.
  - `core`, `normalize-docs` and `cli`: Black, ruff, Pylint 10.00/10, mypy and deptry clean; tests 55, 69 and 17
    passed, at 100 %, 100 % and 97.92 % coverage.
  - Root: format, lint and types clean, coverage 98.82 %.
  - `no-vendored-schemas`: clean.
  - Locally, three `tests/test_action_yml.py` tests fail on Windows only, as they do on `master` (they compare POSIX
    paths that the bash venv step writes); this PR does not touch them.
- The fixture's `selection_summary` (entities total / included / excluded, then criteria):

  | View | Entities | Acceptance criteria |
  |---|---|---|
  | `inner` | 5 / 5 / 0 | 8 / 8 / 0 |
  | `release` | 5 / 3 / 2 (FEAT-003 and FUNC-002 dropped) | 7 / 6 / 1 (US-001-03 dropped) |

- The new `action-run` job needs adding to the required checks, as every `integration.yml` job is.

### Acceptance criteria

- [x] Input only through `validate_inputs`, and an invalid input fails with its code before any transform:
      `service.py:61`; `test_service.py:112`, `:126`, `:142`; CLI lines `test_normalize_docs.py:132`, `:150`
- [x] Typed builder with an `isinstance` test: `builder.py:68-75`; `test_builder.py:36`, `:42`. Valid output in both
      views without `FIELD_LOSS`, equal to the goldens: `test_service.py:43`. Release 5 / 3 / 2 and 7 / 6 / 1:
      `test_service.py:59`
- [x] Title and version defaults: `builder.py:115-116`; `test_builder.py:101`, `:109`; `test_service.py:89`, `:97`
- [x] Producer and one version: `builder.py:31-33`; all three `pyproject.toml:7` are `0.1.0`;
      `test_builder.py:120`. `source` and `source_inputs[0]`: `builder.py:98-110`; `test_builder.py:130`, `:139`,
      `:156`, `:165`
- [x] `select_records` is the only view filter (its one caller is `builder.py:88`) and returns `SelectionSummary`:
      `views.py:31`; `test_views.py:89`, `:97`, `:106`, `:121`. The fixture's FEAT-003: `test_builder.py:80`
- [x] Forwarding: `builder.py:54-65`, `:112`; `test_service.py:184` (`SOURCE_UNAVAILABLE`, `MISSING_STATUS`,
      `NO_SOURCE_URL`, `MALFORMED_AC`), `:203` (all five location fields), `:80` (the fixture's two)
- [x] The lineage table is in the command's package: `lineage.py:74`; `assert_complete` runs in
      `test_lineage.py:21`, and no source module calls it; `test_lineage.py:49`. Registered: `requirements.txt:4`,
      `Makefile:23`, `:26`, `:87`, `dependabot.yml:68`
- [x] `full_sample`: no `FIELD_LOSS` in either view, occupancy > 0 for every mapped path, no planned record in
      release: `test_full_sample.py:42`, `:47`, `:56`
- [x] Named fields: `test_authored_fields.py:33`, `:76`
- [x] `utilities`' goldens field by field: `test_authored_fields.py:146`; copies in `tests/fixtures/utilities-golden/`
- [x] `FIELD_LOSS` from a dropping builder, with no file written: `test_service.py:224`; the CLI's line,
      `test_normalize_docs.py:166`. Release with no `FIELD_LOSS`: `test_service.py:268`, `test_lineage.py:70`
- [x] The action: `main.py:61`, `:151`; `integration.yml:36` (`action-run`), `:65` (`output-path`), `:149`, `:181`
      (isolation), `:225`, `:254` (rebuild); `tests/test_main.py:114`, `:129`, `:419`, `:438`, `:454`
- [x] `make qa` green, except the three Windows-only root tests noted above
- [x] In sync with the canon: see *Rules implemented*. The `full_sample` finding is still to be raised on #87
- [x] No planning id in the diff or in this body
- [x] `## Framework` written by hand, below

## Release Notes

- New command `normalize-docs`: reads one `doc-source.json` and writes `generator-ready.json` on the
  `living-doc-utilities` contract, in the `inner` or `release` view, with `--document-title` and `--document-version`.
- The action runs `command: normalize-docs`; `normalize-tests` and `coverage-matrix` are not available yet, and their
  refusal now reads ``Command `<name>` is not available yet.``
- `normalize-docs` checks its field-lineage table before it writes: a field with data in the input that arrives empty
  stops the run with `FIELD_LOSS`, and no file is written.
- Every input warning reaches `generator-ready.json` unchanged, with the input named in its `context`.
- Every toolkit package now declares the one toolkit version, `0.1.0`, which `metadata.producer.version` records.

## Framework

- [x] Stays inside the frame: the toolkit normalises, validates and filters (F3), and reads and writes only
      `living-doc-utilities`' contract models, with no hand-written twin (F7). No row is bent.

## Related

Closes #87

🤖 Generated with [Claude Code](https://claude.com/claude-code)
