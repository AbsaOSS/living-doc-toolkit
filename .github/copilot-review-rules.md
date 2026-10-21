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

- Must treat the change as higher risk — a change to the reader table or the shared input validation, a `living-doc-utilities` pin change, CLI argument, action input or exit-code changes, wide refactors, and anything touching the committed fixtures.

**Additional focus**

- Prefer confirming that previous review comments were addressed correctly.
- Must re-check high-risk areas — the step order and the every-occurrence reporting in `living_doc_core/input_validation.py`, the reader table in `living_doc_core/readers.py`, and `main.py`'s input checks and their order.
- Prefer looking for hidden side effects — behaviour on a missing or malformed input file, a step that stops at its first occurrence instead of listing every one, and a read that bypasses `read_artifact`.
- Prefer validating safe defaults — safe error messages, and predictable behaviour when an input file is empty or names an unknown producer.
- Must confirm the version impact of any contract change is stated — additive (no bump) vs breaking (major bump of the affected package), per `SPEC.md` § Cross-cutting contract changes.

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

- Must treat these as high-risk areas — the shared input validation in `packages/core/src/living_doc_core/input_validation.py` (its step order, and every occurrence of a step reported), the reader table in `readers.py`, and the action's input checks in `main.py`.
- Must treat these as contract-sensitive — CLI argument names and defaults, the action's inputs and `output-path` output, `main.py`'s error lines, and the shared input validation's codes and order (`living-doc-utilities`' `docs/contracts/errors.md`). Tests assert exact content.
- Must expect the whole collect → normalize → generate pipeline to stay AI-free and offline — flag any LLM call or network request introduced into the runtime path.
- Must expect unit tests in each package's `tests/` mirroring its `src/`, reading the one fixture copy under the repo-root `tests/fixtures/`.
- Must flag any committed contract schema or local contract model — the contracts are `living-doc-utilities`' (`make no-vendored-schemas`).
- Must expect QA to run through the per-package `Makefile` targets — `make qa` / `make qa-<alias>` cover `format-check`, `lint`, `types`, `deptry`, and `test`, `make qa` adds `no-vendored-schemas`, and `.github/workflows/test.yml` calls the same targets.
