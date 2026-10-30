# living-doc-cli

Parent: `../../CONTEXT.md`

The `living-doc` command group. Its behaviour is [README.md](README.md); this file maps that page to the code.

## Code map

What realises each fact of [README.md](README.md):

- The `living-doc` script → `apps/cli/pyproject.toml::living-doc`
- The group, its commands, `--version` and `--verbose` → `apps/cli/src/living_doc_cli/main.py::cli`
- `[LEVEL] message` on stderr → `packages/core/src/living_doc_core/logging_config.py::setup_logging`
- `normalize-docs`, its options and its success line → `apps/cli/src/living_doc_cli/commands/normalize_docs.py::normalize_docs`
- `normalize-tests`, its options and its success line → `apps/cli/src/living_doc_cli/commands/normalize_tests.py::normalize_tests`
- `coverage-matrix`, its options, its success line and the `--fail-under` gate → `apps/cli/src/living_doc_cli/commands/coverage_matrix.py::coverage_matrix`
- `--fail-under` takes only a finite number → `apps/cli/src/living_doc_cli/commands/coverage_matrix.py::_finite`
- The error lines and exit code 1; no file written, an existing one untouched → `apps/cli/src/living_doc_cli/failures.py::exit_on_failure`
- Exit code 2 and the usage error → `apps/cli/src/living_doc_cli/main.py::cli`
