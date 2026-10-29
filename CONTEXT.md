# Living Documentation Toolkit

## Purpose

Python monorepo behind one CLI (`living-doc`) and one composite GitHub Action. It sits between the `living-doc-*`
collectors and the generators: it reads collector output as `living-doc-utilities` contract artifacts, validates a
command's inputs together, and writes the contract a generator reads.

- Commands: `normalize-docs`, `normalize-tests`, `coverage-matrix`.
- Not responsible for: collecting (collectors), rendering (generators), contract models and schemas
  (`living-doc-utilities`).
- AI-free: deterministic Python only, no LLM and no network call in the pipeline (`CONTRIBUTING.md` § AI-free
  Principle).

## Tech stack

- Python `>=3.10`; CI runs 3.10 to 3.14.
- `living-doc-utilities==0.8.0`: the contract models (pydantic 2), schemas, `read_artifact` / `write_artifact`,
  lineage and stats helpers.
- `click` for the CLI; a bash composite action that builds its own venv (`action.yml`).
- pytest + pytest-cov, ruff, Black, Pylint, mypy, deptry.

## Structure

| Path | What it is |
|---|---|
| `packages/core/` | `living-doc-core`: logging, reader table, shared input validation, view filter, run context, envelope helpers ([README](packages/core/README.md)) |
| `packages/services/` | One package per command: builder, lineage table, command ([CONTEXT](packages/services/CONTEXT.md)) |
| `apps/cli/` | `living-doc-cli`: the click group and one module per command under `commands/` ([README](apps/cli/README.md)) |
| `main.py`, `action.yml` | The action: `action.yml` builds the venv, `main.py` checks `INPUT_*` and runs `living-doc <command>` with `-I` |
| `local-integration.sh`, `tools/` | The operator's run of the three commands outside any workflow; `tools/local_integration.py` validates and reports each output |
| `tests/` | The root tests (`test_main.py`, `test_action_yml.py`, `test_local_integration.py`) and the one fixture copy under `tests/fixtures/` |
| `.github/workflows/` | `test.yml` runs the `make` targets; `integration.yml` runs the action through `uses: ./` |
| `SPEC.md` | Process document with the pending-specifications list; specs move out as they ship |

## How it fits together

```mermaid
flowchart LR
  C[living-doc-collector-gh] -->|doc-source.json| ND[normalize-docs]
  C -->|ui-tests.json| NT[normalize-tests]
  C -->|doc-source.json + ui-tests.json| CM[coverage-matrix]
  ND -->|generator-ready.json| G[generators]
  NT -->|ui-test-catalog.json| G
  CM -->|coverage-matrix.json| G
```

- Each command: `validate_inputs` → builder → `metadata.run = run_context()` → `check_no_field_loss` →
  `write_artifact`. Nothing is written when a step fails.
- The CLI calls the service; the action calls the CLI. `--fail-under` is the CLI's gate, after the write.

## Domain

- Entities: User Story (`US-<n>`), Feature, Functionality (`FUNC-<n>`), each with acceptance criteria
  (`<entity_id>-<n>`, pattern `^(?:US|FUNC)-\d+-\d+$`).
- Criterion states: `active`, `deprecated`, `planned`, `in_review`. Coverage counts `active` and `deprecated` only.
- A criterion may declare variants: `Aspect:` values or one keyword, both stored in `aspect[]`; a keyword's name is
  the one `placeholder_values` key.
- Scenarios link criteria with `@AC:<id>` or `@AC:<id>/<param>:<value>` tags, stored as `AcLink(id, aspect)`.
- Views: `inner` keeps every record; `release` drops `planned` and `in_review` ones (`living_doc_core.views`).

## Contracts

All owned by `living-doc-utilities`; this repo defines none and commits no schema.

| Command | Reads | Writes |
|---|---|---|
| `normalize-docs` | `doc-source-v1.0.0` | `generator-ready-v1.0.0` |
| `normalize-tests` | `ui-tests-v1.0.0` | `ui-test-catalog-v1.0.0` |
| `coverage-matrix` | `doc-source-v1.0.0`, `ui-tests-v1.0.0` | `coverage-matrix-v1.0.0` |

- The canon: `living-doc-utilities` `docs/contracts/` (rendering, errors, artifact rules, component checks) and
  `docs/authoring/`; `living-doc` `docs/guides/`. Each package README links the sections it implements.
- Codes and warning fields: `living-doc-utilities` `docs/contracts/errors.md`.

## Running it

- Commands: `AGENTS.md` § This project (`make install`, `make qa`, `make test-<alias>`).
- `PYTHON` passed to `make` must be an absolute path (unverified).
- The action's entry point: `python3 main.py` with `INPUT_*` variables; `metadata.run` reads `GITHUB_RUN_ID`,
  `GITHUB_RUN_ATTEMPT`, `GITHUB_ACTOR`, `GITHUB_WORKFLOW`, `GITHUB_REF`, `GITHUB_SHA`.
- `./local-integration.sh [--check]`: the three commands through `main.py` over `.env.local`'s `DOC_INPUT` and
  `TESTS_INPUT`, in `.venv-local-integration/` built from `requirements.txt` alone, into `$OUT_DIR/toolkit/`; then
  `python -m tools.local_integration report` re-reads each output and fails on an input warning not forwarded
  (`DEVELOPER.md` § Local Integration Run). No workflow runs it.

## Conventions

- `.github/copilot-instructions.md`: the agent rules for this repo (dependency rules, logging, tests, gates).
- Read a contract only through `living_doc_core.readers`, validate only through `validate_inputs`, write only through
  `write_artifact`.
- Every package is version `0.1.0` and pins the same `living-doc-utilities`; `metadata.producer.version` comes from
  the installed `living-doc-core`, never a literal.
- `SPEC.md` content moves to the live docs in the PR that ships it (`.claude/rules/docs-lifecycle.md`).

## Key decisions

- No contract models or schemas here (R12); `make no-vendored-schemas` fails on a committed `*-schema.json`.
- Each command's lineage table is declared in its own package and checked by `assert_complete` in tests only, so a
  field a later contract adds fails the tests, not a user's run.
- Shared input validation stops at the first failing step and reports every occurrence of it
  ([core README](packages/core/README.md#shared-input-validation)).

## Invariants and gotchas

- `tests/fixtures/collector-gh/` is the one fixture copy every package, the root tests and `integration.yml` read;
  refresh it as its [README](tests/fixtures/collector-gh/README.md) says.
- Each service's golden lives in its `tests/expected/`, with a README saying how to regenerate it; a change to the
  fixture pair's numbers also touches the CLI tests, `tests/test_main.py` and `integration.yml`.
- `make lint` reads `git ls-files`: `git add` a new file before linting it.
- `main.py`'s input checks run in a fixed order, and `tests/test_main.py` asserts its one-line errors exactly.
- `tests/test_action_yml.py`'s bash tests fail on Windows only; CI runs them on ubuntu (unverified).
- `tests/test_local_integration.py` runs the real script in a copy whose venv is pre-seeded with the test's own
  interpreter, so no test installs from the network; `.env.local.example`'s keys must equal the script's `KEYS`.
- `.local_context/` is private and never committed.
