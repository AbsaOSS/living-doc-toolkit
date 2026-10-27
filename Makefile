# ============================================================================
# Living Documentation Toolkit — QA command vocabulary
#
# Canonical targets (see living-doc/docs/specs/repo-conventions.md §7 "Command
# vocabulary"):  qa · lint · format · format-check · types · test · coverage
#
#   make qa                 Run format-check -> lint -> types -> deptry -> test on every package, then the root
#                           checks, then no-vendored-schemas
#   make qa-<alias>         Same, for one package
#   make qa-root            The root checks: main.py and tests/
#   make lint-<alias>       One gate, one package  (also: format, format-check, types, deptry, test, coverage)
#   make <gate>             One gate, every package and the root (deptry: every package)
#   make no-vendored-schemas  R12 check 1 over the whole repository
#
# Package aliases:  core · normalize-docs · normalize-tests · coverage-matrix · cli
#
# The pre-Phase-0 names (py-qa, black, pylint, mypy, pytest-unit and their
# per-package forms) still work as deprecated aliases for one release — each
# prints a one-line notice.  .github/workflows/test.yml runs the same targets.
# ============================================================================

# --- Package map -----------------------------------------------------------
ALIASES := core normalize-docs normalize-tests coverage-matrix cli

dir-core           := packages/core
dir-normalize-docs := packages/services/normalize_docs
dir-normalize-tests := packages/services/normalize_tests
dir-coverage-matrix := packages/services/coverage_matrix
dir-cli            := apps/cli

# --- Root: the action's entry point and its tests ----------------------------
ROOT_SRC := main.py
ROOT_PY  := $(ROOT_SRC) tests

# --- Tools / thresholds ------------------------------------------------------
PYTHON ?= python3
MIN_PYLINT_SCORE := 9.5
MIN_COVERAGE := 80

GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

GATES := lint format format-check types test coverage
DEPRECATED := py-qa black pylint mypy pytest-unit

# Concrete target lists (static pattern rules — GNU Make 3.81 compatible)
QA_TARGETS      := $(addprefix qa-,$(ALIASES))
GATE_TARGETS    := $(foreach g,$(GATES),$(addprefix $(g)-,$(ALIASES)))
DEPTRY_TARGETS  := $(addprefix deptry-,$(ALIASES))
DEPREC_TARGETS  := $(DEPRECATED) $(foreach g,$(DEPRECATED),$(addprefix $(g)-,$(ALIASES)))
ROOT_TARGETS    := qa-root $(addsuffix -root,$(GATES))

.PHONY: help install qa deptry no-vendored-schemas $(GATES) $(QA_TARGETS) $(GATE_TARGETS) $(DEPTRY_TARGETS) \
	$(DEPREC_TARGETS) $(ROOT_TARGETS)

# ============================================================================
# Help / install
# ============================================================================

help: ## Show this help message
	@echo "$(GREEN)Living Documentation Toolkit — QA commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup:$(NC)"
	@echo "  make install                 Install requirements-dev.txt, then every package editable with [dev]"
	@echo ""
	@echo "$(YELLOW)Every package:$(NC)"
	@echo "  make qa                      format-check -> lint -> types -> deptry -> test, all packages, then qa-root"
	@echo "                               and no-vendored-schemas"
	@echo "  make lint | format | format-check | types | deptry | test | coverage"
	@echo ""
	@echo "$(YELLOW)Root (main.py, tests/):$(NC)"
	@echo "  make qa-root                 All gates for the root"
	@echo ""
	@echo "$(YELLOW)Whole repository:$(NC)"
	@echo "  make no-vendored-schemas     Fail on a committed contract schema file (R12 check 1)"
	@echo ""
	@echo "$(YELLOW)One package (alias: core normalize-docs normalize-tests coverage-matrix cli):$(NC)"
	@echo "  make qa-<alias>              All gates for one package"
	@echo "  make lint-<alias> | format-<alias> | format-check-<alias> | types-<alias> | deptry-<alias> | test-<alias>"
	@echo "  make coverage-<alias>"
	@echo ""
	@echo "$(YELLOW)Thresholds (match CI):$(NC) Pylint >= $(MIN_PYLINT_SCORE) · Black line length 120 · mypy clean · coverage >= $(MIN_COVERAGE)%"

install: ## Install requirements-dev.txt, then every package editable with [dev] (dependency order)
	@echo "$(YELLOW)Installing requirements-dev.txt, then the packages editable in dependency order...$(NC)"
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -e packages/core[dev]
	$(PYTHON) -m pip install -e "packages/services/normalize_docs[dev]"
	$(PYTHON) -m pip install -e "packages/services/normalize_tests[dev]"
	$(PYTHON) -m pip install -e "packages/services/coverage_matrix[dev]"
	$(PYTHON) -m pip install -e "apps/cli[dev]"
	@echo "$(GREEN)✓ All packages installed$(NC)"

# ============================================================================
# Canonical aggregate targets — one gate across every package
# ============================================================================

qa: $(QA_TARGETS) qa-root no-vendored-schemas ## every package's gates, then the root checks, then R12 check 1
	@echo "$(GREEN)✓ QA passed for all packages and the root$(NC)"

lint: $(addprefix lint-,$(ALIASES)) lint-root ## Ruff + Pylint (score >= 9.5), every package
	@echo "$(GREEN)✓ Ruff + Pylint passed for all packages (Pylint score >= $(MIN_PYLINT_SCORE))$(NC)"

format: $(addprefix format-,$(ALIASES)) format-root ## Ruff autofix + Black (rewrite), every package
	@echo "$(GREEN)✓ Ruff + Black formatting complete for all packages$(NC)"

format-check: $(addprefix format-check-,$(ALIASES)) format-check-root ## Black --check (no writes), every package
	@echo "$(GREEN)✓ Black check passed for all packages$(NC)"

types: $(addprefix types-,$(ALIASES)) types-root ## mypy, every package
	@echo "$(GREEN)✓ mypy passed for all packages$(NC)"

deptry: $(DEPTRY_TARGETS) ## deptry, every package: no undeclared or unused dependency
	@echo "$(GREEN)✓ deptry passed for all packages$(NC)"

test: $(addprefix test-,$(ALIASES)) test-root ## pytest, every package
	@echo "$(GREEN)✓ Unit tests passed for all packages$(NC)"

coverage: $(addprefix coverage-,$(ALIASES)) coverage-root ## pytest with coverage gate, every package
	@echo "$(GREEN)✓ Coverage passed for all packages (>= $(MIN_COVERAGE)%)$(NC)"

# ============================================================================
# Canonical per-package targets — <gate>-<alias> (static pattern rules)
# ============================================================================

$(QA_TARGETS): qa-%: format-check-% lint-% types-% deptry-% test-%
	@echo "$(GREEN)✓ QA passed for $* ($(dir-$*))$(NC)"

$(addprefix lint-,$(ALIASES)): lint-%:
	@echo "$(YELLOW)→ Ruff + Pylint: $* ($(dir-$*), Pylint threshold >= $(MIN_PYLINT_SCORE))$(NC)"
	cd $(dir-$*) && $(PYTHON) -m ruff check .
	cd $(dir-$*) && $(PYTHON) -m pylint --fail-under=$(MIN_PYLINT_SCORE) $$(git ls-files '*.py' | grep -v '^tests/')

$(addprefix format-,$(ALIASES)): format-%:
	@echo "$(YELLOW)→ Ruff autofix + Black: $* ($(dir-$*))$(NC)"
	cd $(dir-$*) && $(PYTHON) -m ruff check --fix .
	cd $(dir-$*) && $(PYTHON) -m black .

$(addprefix format-check-,$(ALIASES)): format-check-%:
	@echo "$(YELLOW)→ Black --check: $* ($(dir-$*))$(NC)"
	cd $(dir-$*) && $(PYTHON) -m black --check .

$(addprefix types-,$(ALIASES)): types-%:
	@echo "$(YELLOW)→ mypy: $* ($(dir-$*))$(NC)"
	cd $(dir-$*) && $(PYTHON) -m mypy .

# Each import is a declared dependency of its package, and each declared dependency is imported ([tool.deptry]).
$(DEPTRY_TARGETS): deptry-%:
	@echo "$(YELLOW)→ deptry: $* ($(dir-$*))$(NC)"
	cd $(dir-$*) && $(PYTHON) -m deptry .

$(addprefix test-,$(ALIASES)): test-%:
	@echo "$(YELLOW)→ Tests: $* ($(dir-$*))$(NC)"
	cd $(dir-$*) && $(PYTHON) -m pytest tests/

$(addprefix coverage-,$(ALIASES)): coverage-%:
	@echo "$(YELLOW)→ Coverage: $* ($(dir-$*), >= $(MIN_COVERAGE)%)$(NC)"
	cd $(dir-$*) && $(PYTHON) -m pytest tests/ --cov=src --cov-fail-under=$(MIN_COVERAGE)

# ============================================================================
# Whole repository — R12 check 1 (living-doc-utilities docs/contracts/component-checks.md)
# ============================================================================

# The contract schemas come from the installed living-doc-utilities; no copy of one is committed here.
no-vendored-schemas: ## Fail on any committed *-schema.json / *.schema.json outside a tests/ directory
	@echo "$(YELLOW)→ No vendored schemas (R12 check 1)$(NC)"
	$(PYTHON) -m living_doc_utilities.contracts.check_no_vendored_schemas

# ============================================================================
# Root targets — main.py and tests/, run from the repository root
# ============================================================================

qa-root: format-check-root lint-root types-root test-root
	@echo "$(GREEN)✓ QA passed for the root$(NC)"

lint-root:
	@echo "$(YELLOW)→ Ruff + Pylint: root (Ruff: $(ROOT_PY); Pylint: $(ROOT_SRC), threshold >= $(MIN_PYLINT_SCORE))$(NC)"
	$(PYTHON) -m ruff check $(ROOT_PY)
	$(PYTHON) -m pylint --fail-under=$(MIN_PYLINT_SCORE) $(ROOT_SRC)

format-root:
	@echo "$(YELLOW)→ Ruff autofix + Black: root ($(ROOT_PY))$(NC)"
	$(PYTHON) -m ruff check --fix $(ROOT_PY)
	$(PYTHON) -m black $(ROOT_PY)

format-check-root:
	@echo "$(YELLOW)→ Black --check: root ($(ROOT_PY))$(NC)"
	$(PYTHON) -m black --check $(ROOT_PY)

types-root:
	@echo "$(YELLOW)→ mypy: root ($(ROOT_SRC))$(NC)"
	$(PYTHON) -m mypy $(ROOT_SRC)

test-root:
	@echo "$(YELLOW)→ Tests: root (tests/)$(NC)"
	$(PYTHON) -m pytest tests/

coverage-root:
	@echo "$(YELLOW)→ Coverage: root (tests/, >= $(MIN_COVERAGE)%)$(NC)"
	$(PYTHON) -m pytest tests/ --cov=main --cov-fail-under=$(MIN_COVERAGE)

# ============================================================================
# Deprecated aliases — pre-Phase-0 names, kept for one release (§7.5)
# Each prints a one-line notice, then delegates to the canonical target.
# ============================================================================

py-qa:
	@echo "$(YELLOW)⚠ 'make py-qa' is deprecated — use 'make qa' (repo-conventions.md §7)$(NC)"
	@$(MAKE) --no-print-directory qa
black:
	@echo "$(YELLOW)⚠ 'make black' is deprecated — use 'make format' (repo-conventions.md §7)$(NC)"
	@$(MAKE) --no-print-directory format
pylint:
	@echo "$(YELLOW)⚠ 'make pylint' is deprecated — use 'make lint' (repo-conventions.md §7)$(NC)"
	@$(MAKE) --no-print-directory lint
mypy:
	@echo "$(YELLOW)⚠ 'make mypy' is deprecated — use 'make types' (repo-conventions.md §7)$(NC)"
	@$(MAKE) --no-print-directory types
pytest-unit:
	@echo "$(YELLOW)⚠ 'make pytest-unit' is deprecated — use 'make test' (repo-conventions.md §7)$(NC)"
	@$(MAKE) --no-print-directory test

$(addprefix py-qa-,$(ALIASES)): py-qa-%:
	@echo "$(YELLOW)⚠ 'make py-qa-$*' is deprecated — use 'make qa-$*' (repo-conventions.md §7)$(NC)"
	@$(MAKE) --no-print-directory qa-$*
$(addprefix black-,$(ALIASES)): black-%:
	@echo "$(YELLOW)⚠ 'make black-$*' is deprecated — use 'make format-$*' (repo-conventions.md §7)$(NC)"
	@$(MAKE) --no-print-directory format-$*
$(addprefix pylint-,$(ALIASES)): pylint-%:
	@echo "$(YELLOW)⚠ 'make pylint-$*' is deprecated — use 'make lint-$*' (repo-conventions.md §7)$(NC)"
	@$(MAKE) --no-print-directory lint-$*
$(addprefix mypy-,$(ALIASES)): mypy-%:
	@echo "$(YELLOW)⚠ 'make mypy-$*' is deprecated — use 'make types-$*' (repo-conventions.md §7)$(NC)"
	@$(MAKE) --no-print-directory types-$*
$(addprefix pytest-unit-,$(ALIASES)): pytest-unit-%:
	@echo "$(YELLOW)⚠ 'make pytest-unit-$*' is deprecated — use 'make test-$*' (repo-conventions.md §7)$(NC)"
	@$(MAKE) --no-print-directory test-$*
