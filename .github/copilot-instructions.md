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

`Living Documentation Toolkit` is a **monorepo** of independent Python packages behind one
CLI (`living-doc`). It sits between the upstream `living-doc-*` collector actions and the
downstream generator actions: it detects the input producer, checks version compatibility,
normalizes collector output into canonical datasets, and validates that output against a
versioned contract.

- Must treat the `living-doc` CLI running as a step in a GitHub Actions workflow as the supported path; running `living-doc <service>` locally is a development and debugging affordance only.
- Must keep the whole collect → normalize → generate pipeline AI-free — deterministic Python only, no LLM call and no network call anywhere in that path.
- Must scope a change to a single package where possible; split a change that spans packages unless they must change together (an adapter and the contract it implements).
- Must respect the package dependency rules — `core` depends on nothing; `datasets_*` and `adapters/*` depend only on `core`; `services/*` depend on `core` and optionally `datasets_*` and specific `adapters/*`; `apps/cli` depends on `core` and the services.

## Repo specifics

Module map — six packages under `packages/` and `apps/`, each with its own `pyproject.toml`,
`src/` layout, and `tests/` directory:

| Path | Package (`pip` name) | Responsibility |
|---|---|---|
| `packages/core` | `living-doc-core` | Shared utilities — `json_utils.py`, `markdown_utils.py`, `logging_config.py`, `errors.py`. No dependencies. |
| `packages/datasets_pdf` | `living-doc-datasets-pdf` | Versioned PDF contract — `pdf_ready/v1/models.py` + `audit/v1/models.py` (Pydantic, source of truth), `schema.py` / `serializer.py`, `schemas/*.schema.json` exports. |
| `packages/adapters/collector_gh` | `living-doc-adapter-collector-gh` | Collector-gh adapter — `detector.py` (`can_handle`), `compatibility.py` (confirmed version range), `parser.py` (payload → `AdapterResult`), `models.py`, `schema_export.py`. |
| `packages/services/normalize_issues` | `living-doc-service-normalize-issues` | `normalize-issues` service — `service.py` (orchestration), `normalizer.py` (markdown → sections, pure), `builder.py` (PDF-ready JSON + audit envelope). |
| `packages/services/coverage_matrix` | `living-doc-service-coverage-matrix` | `coverage-matrix` service — `service.py` (orchestration + `--fail-under`), `loader.py` (pure I/O), `matcher.py` (pure transform), `summary.py` (pure tallying), `model/coverage_item.py` (output dataclasses), `schema_validation.py`. |
| `apps/cli` | `living-doc-cli` | CLI entry point — `main.py` (`cli()` click group), `commands/normalize_issues.py`, `commands/coverage_matrix.py`. |

- Must treat `apps/cli/src/living_doc_cli/main.py` `cli()` as the entry point — it registers each `commands/<name>.py` sub-command, which parses arguments and calls the service's `run_service(...)`.
- Must treat the pure modules — `normalizer.py`, `matcher.py`, `summary.py`, `loader.py`, the adapter `parser.py` — as I/O-free: they take parsed input and return structured data, with no file I/O, no logging setup, and no environment reads. Keep them that way.
- Must keep `service.py` (each service) as the only place that maps a failure to a CLI exit code.

Inputs — CLI arguments (full reference in [`docs/contracts.md`](../docs/contracts.md)):

| Command | Arguments |
|---|---|
| `living-doc normalize-issues` | `--input` (req), `--output` (req), `--source` (`auto` \| `collector-gh`, default `auto`), `--document-title`, `--document-version`, `--verbose` |
| `living-doc coverage-matrix` | `--doc-input` (req), `--tests-input` (req), `--output` (req), `--fail-under` (float), `--verbose` |

Contract-sensitive outputs (the *Stable* / *Requires review* items in `docs/contracts.md`):

- Must keep exit codes stable — `normalize-issues`: `0` success, `1` invalid input, `2` adapter detection failed, `3` schema validation failure, `4` normalization error, `5` file I/O error; `coverage-matrix`: `0` success, `1` any error (including coverage below `--fail-under`).
- Must keep error-message prefixes stable — `Invalid input:`, `Adapter error:`, `Schema validation failed:`, `Normalization failed:`, `File I/O error:` — tests assert exact prefixes.
- Must keep `schema_version` values stable — `pdf_ready` `"1.0"`, `coverage-matrix` `"coverage-matrix-v1.0.0"`, audit envelope `"1.0"`.
- Must keep the `pdf_ready.json` / `coverage-matrix.json` structure and the `AdapterResult` model signature in step with the Pydantic models / dataclasses that are their source of truth; a breaking change requires a major version bump of the affected package.
- Must keep CLI argument names and defaults stable.

QA commands — the per-package `Makefile` targets (`.github/workflows/test.yml` runs the same targets):

- Full gate, every package: `make qa` (runs `format-check` → `lint` → `types` → `test`, failing on the first).
- Per package: `make qa-<alias>` where `<alias>` is one of `core`, `datasets-pdf`, `collector-gh`, `normalize`, `coverage`, `cli`.
- Individual gate per package: `make lint-<alias>`, `make format-<alias>`, `make format-check-<alias>`, `make types-<alias>`, `make test-<alias>`, `make coverage-<alias>`.
- `lint-<alias>` runs ruff (`E` / `F` / `I` / `B`, `tests` / `verifications` excluded per each package's `[tool.ruff]`) then Pylint; `format-<alias>` runs `ruff check --fix` then Black.
- Must not use repo-root `pylint $(git ls-files '*.py')` / `pytest tests/` as the QA command — CI gates changes per package from inside each package directory.

## Coding guidelines

- Must keep changes small and scoped to one package where possible.
- Prefer explicit code over clever constructs.
- Must keep externally visible behaviour stable unless the task is an intentional contract change.
- Must not change existing error messages, error prefixes, or log texts without a stated reason.
- Prefer pure functions for parsing, matching, and tallying logic, and Avoid adding I/O or environment reads to the modules that are pure today.

## Inputs

- Must parse CLI arguments only in the `apps/cli/commands/<name>.py` layer and pass typed values into the service.
- Must centralise input-file loading and validation in the service's `loader.py` / `service.py`, not scattered across the transform modules.
- Avoid duplicating validation across packages — the adapter validates the input contract, the dataset package validates the output contract.

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
- Prefer the clearest formatting for exception and failure messages, and Must keep the contract-sensitive error prefixes exact.

## Docstrings and comments

- Must match the existing module docstring style — a short summary of what the module contains.
- Prefer a one-line docstring summary for functions, expanding only where it adds information.
- Prefer self-explanatory code, and Prefer comments only for intent, edge cases, and the "why".
- Avoid tutorial-style prose or long examples in docstrings.

## Patterns

- Prefer leaf modules raising the typed errors in `living_doc_core.errors`.
- Must let each service's `service.py` be the only place that translates a failure into a CLI exit code.
- Prefer the adapter pattern for new input producers — `detector.can_handle(payload)`, a confirmed compatibility range, `parser.parse(payload) -> AdapterResult` — added without modifying the services.
- Must keep integration boundaries — file I/O, JSON Schema validation, the adapter registry — explicit and mockable.
- Must append a `trace[]` step to the audit envelope for each transformation stage (`step`, `tool`, `tool_version`, `warnings`).

## Testing

- Must use `pytest` with `pytest-mock` / `pytest-cov`, and Must not use `unittest`.
- Must keep tests in each package's own `tests/` directory, mirroring its `src/` layout; cross-package golden and compatibility checks live in the repo-root `tests/` and per-service `verifications/`.
- Must test behaviour — return values, raised errors, error prefixes, exit codes, serialized JSON keys.
- Must isolate file I/O and the adapter registry behind mocks; the pure modules (`matcher`, `summary`, `normalizer`, `loader`) need no mocks.
- Must add a golden fixture directory under `tests/fixtures/collector_gh/v<X.Y.Z>/` for a new collector-gh schema version — the parametrized compatibility tests discover it automatically; Must not hard-code the version list.
- Prefer shared fixtures in each package's `tests/conftest.py`.

## Tooling and quality gates

- Must run `make qa` (or `make qa-<alias>` for the package you touched) before finishing a code change — it runs `format-check` → `lint` → `types` → `test` and fails on the first failing gate.
- Must use the individual per-package targets while iterating — `make format-<alias>`, `make lint-<alias>`, `make types-<alias>`, `make test-<alias>`, `make coverage-<alias>`.
- Must keep `lint` clean per package — it runs ruff (`E` / `F` / `I` / `B`, `tests` / `verifications` excluded) then Pylint, and Pylint must score 9.5 or higher.
- Must keep `format-check` (Black, line length 120, config in each `pyproject.toml`) clean, and Prefer `make format-<alias>` (ruff autofix + Black) to fix import order and formatting in one step.
- Must keep `types` (mypy, config in each `pyproject.toml`) clean, and Prefer fixing types over adding ignores.
- Must keep `coverage` (pytest, `--cov-fail-under=80`) passing per package.
- Must expect `.github/workflows/test.yml` and `.github/workflows/integration.yml` to call the same `make` targets, so local and CI never drift.

## Common pitfalls

- Must verify a new dependency supports Python 3.10 before adding it, and Must add it to the owning package's `pyproject.toml` (there is no root `requirements.txt` of pinned deps — `requirements.txt` only lists the editable packages).
- Must keep a change within the package dependency rules — Avoid importing a service from `core`, or an adapter from another adapter.
- Must remove unused imports and variables in the same change, and Avoid leaving dead code.
- Avoid changing externally visible strings, exit codes, `schema_version` values, or schema structure unless the task calls for it and the version impact is stated.
- Must keep the Pydantic models / dataclasses and their exported JSON Schemas in step — regenerate the schema export when a model changes.

## Learned rules

- Must keep the five `normalize-issues` error prefixes and the exit-code taxonomy (`0`–`5`) stable — tests assert exact prefixes and codes.
- Must keep deprecated ACs counted in the coverage matrix but excluded from `coverage_pct` — they must not inflate the score.
- Must keep the golden-fixture discovery dynamic — `tests/fixtures/collector_gh/v*` and `tests/fixtures/golden/v*` are enumerated, never hard-coded.
