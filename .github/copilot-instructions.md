# Copilot Instructions — Living Documentation Toolkit

This file tells a coding agent how to work in this repository. It describes this repo's
own layout, contracts, and workflow; it is not shared with or copied from other repos.

**Section order** — keep the sections below in exactly this order:
Overview → Repo specifics → Coding guidelines → Inputs → Language and style →
Logging and string formatting → Docstrings and comments → Patterns → Testing →
Tooling and quality gates → Common pitfalls → Learned rules.

**House rules for this file**

- Must write every guidance bullet as a constraint led by one of `Must`, `Must not`, `Prefer`, `Avoid`.
- Must not put a colon after the leading keyword, and Must not use any other keyword style such as `Do`, `Should`, or a two-keyword `Do` / `Avoid` variant.
- Prefer bullet lists over paragraphs.
- Must end the file with a single trailing newline.

## Overview

`Living Documentation Toolkit` is a **monorepo** of Python packages behind one CLI
(`living-doc`) and one composite GitHub Action. It sits between the upstream `living-doc-*`
collector actions and the downstream generator actions: it reads collector output as
`living-doc-utilities` contract artifacts, validates a command's inputs together, and
transforms them into the contracts the generators read. `normalize-docs`, `normalize-tests` and
`coverage-matrix` run.

- Must treat the `living-doc` CLI running as a step in a GitHub Actions workflow as the supported path; running `living-doc <command>` locally is a development and debugging affordance only.
- Must keep the whole collect → normalize → generate pipeline AI-free — deterministic Python only, no LLM call and no network call anywhere in that path.
- Must scope a change to a single package where possible; split a change that spans packages unless they must change together.
- Must respect the package dependency rules — `core` depends only on `living-doc-utilities`; a service package under `packages/services/` depends on `core` and `living-doc-utilities`; `apps/cli` depends on `click`, the services it registers, `core` and `living-doc-utilities`.

## Repo specifics

Module map — five packages under `packages/` and `apps/`, each with its own `pyproject.toml`,
`src/` layout, and `tests/` directory:

| Path | Package (`pip` name) | Responsibility |
|---|---|---|
| `packages/core` | `living-doc-core` | `logging_config.py` (`setup_logging`), `envelope.py` (`PRODUCER_NAME`, `TOOLKIT_VERSION`, `forwarded`, the producer identity and warning forwarding every transform shares), `readers.py` (the reader table, `read_documentation`, `read_tests`), `input_validation.py` (`validate_inputs`, the shared input validation), `views.py` (`select_records`, the view filter), `run_context.py` (`run_context`, the CI run for `metadata.run`). Depends on `living-doc-utilities==0.8.0`. |
| `packages/services/normalize_docs` | `living-doc-service-normalize-docs` | `builder.py` (`build_generator_ready`), `lineage.py` (`LINEAGE_TABLE`), `service.py` (`normalize_docs`, the command, and `check_no_field_loss`). |
| `packages/services/normalize_tests` | `living-doc-service-normalize-tests` | `builder.py` (`build_ui_test_catalog`), `lineage.py` (`LINEAGE_TABLE`), `service.py` (`normalize_tests`, the command, and the runtime field-loss check). |
| `packages/services/coverage_matrix` | `living-doc-service-coverage-matrix` | `builder.py` (`build_coverage_matrix`), `lineage.py` (`LINEAGE_TABLE`, over both inputs), `service.py` (`coverage_matrix`, the command, and `check_no_field_loss`, against the documentation input only). |
| `apps/cli` | `living-doc-cli` | CLI entry point — `main.py` (`cli()` click group), one module per command under `commands/`. Registers `normalize-docs`, `normalize-tests` and `coverage-matrix`; `coverage-matrix`'s `--fail-under` gate is the CLI's, after the write. |

- Must treat the repository root as the action — `action.yml`, its entry point `main.py` (input checks, `COMMAND_INPUTS`), and the root `tests/`.
- Must treat `apps/cli/src/living_doc_cli/main.py` `cli()` as the CLI entry point — each command is registered there as it lands.
- Must read every contract artifact through `living_doc_core.readers`, which calls `living-doc-utilities`' `read_artifact`, and must write one only through `write_artifact` (R12 check 2).
- Must run `living_doc_core.input_validation.validate_inputs` over a command's inputs before it transforms them.
- Must select view records only through `living_doc_core.views.select_records`, and Must keep each command's lineage table in its own service package, checked by `assert_complete` in its tests and never at run time; `normalize-tests` has no view input and always writes `document.view` as `inner`.
- Must declare the toolkit's one version in every package, and Must read `metadata.producer.version` from the installed `living-doc-core`, never from a literal.

Inputs — the action's inputs (full reference in [`README.md`](../README.md#inputs)):

| Command | Inputs |
|---|---|
| `normalize-docs` | `input` (req, documentation), `output` (req), `view`, `document-title` |
| `normalize-tests` | `input` (req, tests), `output` (req) |
| `coverage-matrix` | `input` (req, documentation, `--doc-input`), `output` (req), `view`, `tests-input` (req), `fail-under` |

Contract-sensitive outputs:

- Must keep the action's input names, its `output-path` output, and `main.py`'s one-line error messages stable — `tests/test_main.py` asserts them exactly.
- Must keep the shared input validation's codes and order those of `living-doc-utilities`' `docs/contracts/errors.md` § Shared input validation order.
- Must not define a contract model or commit a contract schema — the models and schemas are `living-doc-utilities`'; `make no-vendored-schemas` fails on a committed `*-schema.json` / `*.schema.json`.
- Must keep CLI argument names and defaults stable once a command ships.

QA commands — the per-package `Makefile` targets (`.github/workflows/test.yml` runs the same targets):

- Full gate, every package: `make qa` (runs `format-check` → `lint` → `types` → `deptry` → `test` per package, then the root checks, then `no-vendored-schemas`, failing on the first).
- Per package: `make qa-<alias>` where `<alias>` is one of `core`, `normalize-docs`, `normalize-tests`, `coverage-matrix`, `cli`.
- Individual gate per package: `make lint-<alias>`, `make format-<alias>`, `make format-check-<alias>`, `make types-<alias>`, `make deptry-<alias>`, `make test-<alias>`, `make coverage-<alias>`.
- `lint-<alias>` runs ruff (`E` / `F` / `I` / `B`, `tests` excluded per each package's `[tool.ruff]`) then Pylint; `format-<alias>` runs `ruff check --fix` then Black.
- Must not use repo-root `pylint $(git ls-files '*.py')` / `pytest tests/` as the QA command — CI gates changes per package from inside each package directory.

## Coding guidelines

- Must keep changes small and scoped to one package where possible.
- Prefer explicit code over clever constructs.
- Must keep externally visible behaviour stable unless the task is an intentional contract change.
- Must not change existing error messages or log texts without a stated reason.
- Prefer pure functions for parsing, matching, and tallying logic, and Avoid adding I/O or environment reads to the modules that are pure today.

## Inputs

- Must parse CLI arguments only in the command layer of `apps/cli` and pass typed values on.
- Must read input files only through `living_doc_core.readers` and validate them only through `living_doc_core.input_validation`, not scattered across the transform modules.
- Avoid duplicating validation that `living-doc-utilities` already runs — R5 belongs to `read_artifact`.

## Language and style

- Must target Python 3.10+ — the ecosystem floor set by `requires-python = ">=3.10"` and the `3.10 → 3.14` CI matrix.
- Must keep `X | Y` union annotations and other 3.10-native syntax; Must guard any 3.11+ standard-library use (`tomllib`, `datetime.UTC`, `enum.StrEnum`, `match`/`case` is fine on 3.10) behind a `sys.version_info` fallback.
- Must add type hints for new public functions and classes.
- Must keep imports at module top — no imports inside functions or methods.
- Must not disable a linter rule inline unless this file records the exception under Learned rules.

## Logging and string formatting

- Must use `logging` via `living_doc_core.logging_config`, never `print`.
- Must use lazy `%` formatting in logging calls — `logger.info("msg %s", value)`.
- Must not use f-strings inside logging calls.
- Prefer the clearest formatting for exception and failure messages, and Must keep the contract-sensitive error lines exact.

## Docstrings and comments

- Must match the existing module docstring style — a short summary of what the module contains.
- Prefer a one-line docstring summary for functions, expanding only where it adds information.
- Prefer self-explanatory code, and Prefer comments only for intent, edge cases, and the "why".
- Avoid tutorial-style prose or long examples in docstrings.

## Patterns

- Prefer the contract models of `living-doc-utilities` over any local representation of a contract.
- Must key a new input contract in the reader table by its contract name, never by its producer.
- Must report every occurrence of the first failing validation step, never the first occurrence only, and never pick a winner between two occurrences.
- Must keep integration boundaries — file I/O, contract reads and writes, the CLI the action runs — explicit and mockable.

## Testing

- Must use `pytest` with `pytest-cov`, and Must not use `unittest`.
- Must keep tests in each package's own `tests/` directory, mirroring its `src/` layout; the action's entry point and venv step are tested in the repo-root `tests/`.
- Must test behaviour — return values, the contract model a read returns, raised errors, each `InputProblem`'s code and message, exit codes, error lines.
- Must read contract inputs from the one fixture copy under the repo-root `tests/fixtures/`, or from a changed copy of it under `tmp_path`.
- Prefer shared fixtures in each package's `tests/conftest.py`.

## Tooling and quality gates

- Must run `make qa` (or `make qa-<alias>` for the package you touched) before finishing a code change — it runs `format-check` → `lint` → `types` → `deptry` → `test` and fails on the first failing gate.
- Must use the individual per-package targets while iterating — `make format-<alias>`, `make lint-<alias>`, `make types-<alias>`, `make deptry-<alias>`, `make test-<alias>`, `make coverage-<alias>`.
- Must keep `lint` clean per package — it runs ruff (`E` / `F` / `I` / `B`, `tests` excluded) then Pylint, and Pylint must score 9.5 or higher.
- Must keep `format-check` (Black, line length 120, config in each `pyproject.toml`) clean, and Prefer `make format-<alias>` (ruff autofix + Black) to fix import order and formatting in one step.
- Must keep `types` (mypy, config in each `pyproject.toml`) clean, and Prefer fixing types over adding ignores.
- Must keep `deptry` clean per package — every import declared in its `pyproject.toml`, every declared dependency imported.
- Must keep `coverage` (pytest, `--cov-fail-under=80`) passing per package.
- Must expect `.github/workflows/test.yml` to call the same `make` targets, so local and CI never drift.

## Common pitfalls

- Must verify a new dependency supports Python 3.10 before adding it, and Must add it to the owning package's `pyproject.toml` (the root `requirements.txt` lists the package directories, not their dependencies; `requirements-dev.txt` adds the development tools).
- Must keep a change within the package dependency rules — Avoid importing `apps/cli` from `core`.
- Must remove unused imports and variables in the same change, and Avoid leaving dead code.
- Avoid changing externally visible strings or exit codes unless the task calls for it and the version impact is stated.
- Must not pin `living-doc-utilities` to another version in one package only — every package that imports it pins the same version.

## Learned rules

- Must keep `main.py`'s check order — a known command, then an input it does not take, then an empty required input, then `output`, then `fail-under` — so each run fails on the first wrong input with one line.
- Prefer the inline `# pylint: disable=too-many-arguments,too-many-positional-arguments` on a click command function only — click passes each of its options as one parameter.
- Must keep `--verbose` the group's option only — `main.py` passes it before the command name, so no command declares its own.
- Must treat `metadata.producer.version` as audit information — never compare it, and never warn on an unfamiliar one.
