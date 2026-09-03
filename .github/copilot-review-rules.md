# Copilot Review Rules — Living Documentation Toolkit

This file defines how Copilot reviews pull requests in this repository. It describes this
repo's own risk areas and review expectations; it is not shared with other repos.

**House rules for this file**

- Must write every guidance bullet as a constraint led by one of `Must`, `Must not`, `Prefer`, `Avoid`.
- Must not put a colon after the leading keyword, and Must not use any other keyword style.
- Prefer short headings and bullet lists over prose.
- Prefer verifiable checks — a reviewer can point to the code and the impact.
- Avoid long audit reports unless they are explicitly requested.

## Review modes

- Must support two modes — Default review for standard PR risk, and Double-check review for elevated-risk PRs.

## Mode — Default review

- Must treat the change as a single PR with normal risk.
- Must prioritise in this order — correctness, security, tests, maintainability, style.

**Checks**

- Must flag logic bugs, missing edge cases, regressions, and unintended contract changes.
- Must flag unsafe input handling, path traversal on `--input` / `--output`, and insecure defaults.
- Must check that tests exist for changed logic and cover the success and failure paths.
- Must check that a change stays within the package dependency rules and, where practical, touches one package.
- Prefer calling out unnecessary complexity, duplication, and unclear naming or structure.
- Avoid style notes unless they reduce readability or break a repo convention.

**Response format**

- Must use short bullet points.
- Prefer referencing files and line ranges.
- Must group comments by severity — Blocker (must fix), Important (should fix), Nit (optional).
- Prefer actionable suggestions over rewrites.
- Must not rewrite the whole PR or produce a long report.

## Mode — Double-check review

- Must treat the change as higher risk — schema or contract changes (`datasets_pdf` models, `coverage-matrix` dataclasses, `AdapterResult`, the audit envelope), CLI argument or exit-code changes, adapter interface changes, wide refactors, and anything touching the golden fixtures.

**Additional focus**

- Prefer confirming that previous review comments were addressed correctly.
- Must re-check high-risk areas — the adapter `detector.py` / `compatibility.py` version logic, `parser.py` payload mapping, `normalizer.py` section mapping, `matcher.py` / `summary.py` coverage maths, JSON Schema validation, and the failure-to-exit-code mapping in each `service.py`.
- Prefer looking for hidden side effects — backward compatibility of the output contract, behaviour on missing or malformed input, deprecated-AC handling, and version-mismatch warning paths.
- Prefer validating safe defaults — `--source auto` detection, safe error messages, predictable behaviour when an input file is empty or a producer version is out of range.
- Must confirm the version impact of any contract change is stated — additive (no bump) vs breaking (major bump of the affected package) per `docs/contracts.md`.

**Response format**

- Prefer commenting only where risk or impact is non-trivial.
- Avoid repeating minor style notes already covered by Default review.
- Prefer stating risk acceptance explicitly when something is left as-is — the risk, why it is acceptable, and the mitigation that exists.

## Commenting rules — all modes

- Must include for every comment — what the issue is (one line), why it matters (impact or risk), and how to fix it (a minimal actionable suggestion).
- Prefer linking to an existing pattern in the repo over introducing a new one.
- Must ask a targeted question instead of assuming when context is missing.

## Non-goals

- Must not request refactors unrelated to the PR's intent.
- Must not bikeshed formatting that Black or Pylint already enforces.
- Avoid proposing architectural rewrites unless they are explicitly requested.

## Repo specifics

- Must treat these as high-risk areas — the adapter version-compatibility logic (`packages/adapters/collector_gh/detector.py`, `compatibility.py`), the payload → `AdapterResult` mapping in `parser.py`, markdown section normalization in `normalize_issues/normalizer.py`, the coverage maths in `coverage_matrix/matcher.py` / `summary.py`, JSON Schema validation in `schema_validation.py` / `datasets_pdf`, and the exit-code mapping in each service's `service.py`.
- Must treat these as contract-sensitive — CLI argument names and defaults, the exit-code taxonomies (`normalize-issues` `0`–`5`, `coverage-matrix` `0`/`1`), the error-message prefixes, `schema_version` values (`pdf_ready` `"1.0"`, `coverage-matrix` `"coverage-matrix-v1.0.0"`, audit `"1.0"`), the `pdf_ready.json` / `coverage-matrix.json` structure, and the `AdapterResult` signature. Tests and golden fixtures assert exact content.
- Must expect the whole collect → normalize → generate pipeline to stay AI-free and offline — flag any LLM call or network request introduced into the runtime path.
- Must expect unit tests in each package's `tests/` mirroring its `src/`, with golden fixtures under `tests/fixtures/golden/v*` and collector-gh compatibility fixtures under `tests/fixtures/collector_gh/v*` (discovered, never hard-coded).
- Must expect QA to run through the per-package `Makefile` targets — `make qa` / `make qa-<alias>` cover `format-check`, `lint`, `types`, and `test`, and `.github/workflows/test.yml` calls the same targets.
