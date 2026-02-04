Purpose
- Must keep this file portable across repos (only “Repo additions” is repo-specific).
- Must define constraints for code changes, reviews, and Copilot output.

Structure
- Must keep sections in this order to reduce scanning time.
- Prefer bullets over paragraphs.
- Must write rules as constraints using “Must / Must not / Prefer / Avoid”.
- Must keep one blank line at end of file.

Context
- Must assume components may run locally and/or on GitHub Actions runners.
- If implementing GitHub Actions, must read inputs from environment variables with the `INPUT_` prefix.

Coding guidelines
- Must keep changes small and focused.
- Prefer clear, explicit code over clever tricks.
- Must keep externally-visible behavior stable unless intentionally updating the contract.
- Must not change existing error messages or log texts without a strong reason (tests may assert exact strings).
- Prefer keeping pure logic free of I/O and environment access; route I/O and env through dedicated boundaries.

Output discipline (reduce review time)
- Must default to concise final recaps (aim ≤ 10 lines).
- Must not restate large file contents/configs/checklists; prefer linking files and summarizing deltas.
- Prefer actionable bullets over prose; avoid repeating unchanged plan sections.
- When making code changes, must end with:
  - What changed
  - Why
  - How to verify (commands/tests)
- Prefer deep rationale, alternatives, or long examples only when explicitly requested.

PR Body Management
- Must treat the PR description as a changelog.
- Must not rewrite/replace the entire PR body; always append updates.
- Prefer this structure:
  - Keep the original description at the top.
  - Append new sections chronologically below.
  - Use headings like `## Update YYYY-MM-DD`.
  - Each update references the commit hash that introduced the change.

Inputs
- If running as a GitHub Action, must read inputs via environment variables with the `INPUT_` prefix.
- Must centralize input validation in one dedicated layer.
- Avoid duplicating validation rules across modules.

Language and style
- Must target Python 3.14+.
- Must add type hints for new public functions and classes.
- Must use logging, not `print`.
- Must place all Python imports at the top of the file (no imports inside methods/functions).
- Must not disable linter rules inline unless the repo documents an exception process.

String formatting
- Logging:
  - Must use lazy `%` formatting (e.g., `logger.info("msg %s", value)`).
  - Must not use f-strings for logging interpolation.
- User-visible strings:
  - Must keep externally-visible strings stable unless intentionally updating the contract.
  - Prefer the clearest formatting approach for exceptions/errors while keeping messages stable.

Docstrings and comments
- Prefer self-explanatory code over comments.
- Comments:
  - Prefer intent/edge-case “why” comments only.
  - Avoid blocks that restate what the code already says.
- Docstrings:
  - Prefer a short summary line.
  - Avoid tutorials/long prose/doctest-style examples.

Patterns
- Error handling contract:
  - Prefer leaf modules raise exceptions.
  - Prefer entry points translate failures into exit codes / action failure output.
- Testability:
  - Must keep integration boundaries explicit and mockable.
  - Must not call external APIs in unit tests.
- Internal helpers:
  - Prefer private helpers for internal behavior (e.g., `_helper_name`).

Testing
- Must use pytest with tests located in `tests/`.
- Must test behavior: return values, raised errors, log messages, and exit codes.
- Must mock environment variables in unit tests.
- Prefer mirrored structure between source and tests.

Tooling
- Formatting: must use Black (configured via `pyproject.toml` if present).
- Linting: must run Pylint on tracked Python files (excluding `tests/`) and prefer fixing warnings.
- Type checking: must run mypy and prefer fixing types over ignoring them.
- Coverage: must use pytest-cov and keep coverage at or above 80%.

Quality gates
- Must run after changes; fix only if below threshold:
  - Tests: `pytest tests/unit/` (or the relevant test directory)
  - Formatting: `black $(git ls-files '*.py')`
  - Linting: `pylint --ignore=tests $(git ls-files '*.py')` (target score ≥ 9.5/10)
  - Type checking: `mypy .` (or `mypy <changed_files>`)
  - Coverage: `pytest --ignore=tests/integration --cov=. tests/ --cov-fail-under=80 --cov-report=html`

Common pitfalls to avoid
- Dependencies:
  - Must verify compatibility with the target Python version before adding.
  - Prefer testing imports locally before committing.
  - For untyped libraries, prefer adding `# type: ignore[import-untyped]` with a brief justification.
- Logging:
  - Must follow the lazy `%` formatting rule; avoid “workarounds”.
- Cleanup:
  - Must remove unused variables/imports promptly.
  - Avoid leaving dead code.
- Stability:
  - Must not change externally-visible strings/outputs unless intentional.

Learned rules
- Must keep error messages stable (tests may assert exact strings).
- Must not change exit codes for existing failure scenarios unless intentionally updating the contract.

Repo additions
- Project name: living-doc-toolkit
- Log prefix (if any): <none defined>
- Entry points: `.github/workflows/*` and any `main.py` / `action.yml` if present
- Inputs: GitHub Actions inputs via `INPUT_*` environment variables
- Contract-sensitive outputs: error messages, log texts, exit codes
- Commands (if different from defaults): <none>
- Allowed exceptions to this template: <none>

