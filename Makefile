# ============================================================================
# Living Documentation Toolkit — QA command vocabulary
#
# Canonical targets (see living-doc/docs/specs/repo-conventions.md §7 "Command
# vocabulary"):  qa · lint · format · format-check · types · test · coverage
#
#   make qa                 Run format-check -> lint -> types -> test on every package
#   make qa-<alias>         Same, for one package
#   make lint-<alias>       One gate, one package  (also: format, format-check, types, test, coverage)
#   make <gate>             One gate, every package
#
# Package aliases:  core · datasets-pdf · collector-gh · normalize · coverage · cli
#
# The pre-Phase-0 names (py-qa, black, pylint, mypy, pytest-unit and their
# per-package forms) still work as deprecated aliases for one release — each
# prints a one-line notice.  .github/workflows/test.yml runs the same targets.
# ============================================================================

# --- Package map -----------------------------------------------------------
ALIASES := core datasets-pdf collector-gh normalize coverage cli

dir-core         := packages/core
dir-datasets-pdf := packages/datasets_pdf
dir-collector-gh := packages/adapters/collector_gh
dir-normalize    := packages/services/normalize_issues
dir-coverage     := packages/services/coverage_matrix
dir-cli          := apps/cli

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
DEPREC_TARGETS  := $(DEPRECATED) $(foreach g,$(DEPRECATED),$(addprefix $(g)-,$(ALIASES)))

.PHONY: help install qa $(GATES) $(QA_TARGETS) $(GATE_TARGETS) $(DEPREC_TARGETS)

# ============================================================================
# Help / install
# ============================================================================

help: ## Show this help message
	@echo "$(GREEN)Living Documentation Toolkit — QA commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup:$(NC)"
	@echo "  make install                 Install all packages with [dev] dependencies"
	@echo ""
	@echo "$(YELLOW)Every package:$(NC)"
	@echo "  make qa                      format-check -> lint -> types -> test, all packages"
	@echo "  make lint | format | format-check | types | test | coverage"
	@echo ""
	@echo "$(YELLOW)One package (alias: core datasets-pdf collector-gh normalize coverage cli):$(NC)"
	@echo "  make qa-<alias>              All gates for one package"
	@echo "  make lint-<alias> | format-<alias> | format-check-<alias> | types-<alias> | test-<alias> | coverage-<alias>"
	@echo ""
	@echo "$(YELLOW)Thresholds (match CI):$(NC) Pylint >= $(MIN_PYLINT_SCORE) · Black line length 120 · mypy clean · coverage >= $(MIN_COVERAGE)%"

install: ## Install all packages with [dev] dependencies (dependency order)
	@echo "$(YELLOW)Installing packages in dependency order...$(NC)"
	$(PYTHON) -m pip install -e packages/core[dev]
	$(PYTHON) -m pip install -e packages/datasets_pdf[dev]
	$(PYTHON) -m pip install -e packages/adapters/collector_gh[dev]
	$(PYTHON) -m pip install -e packages/services/normalize_issues[dev]
	$(PYTHON) -m pip install -e packages/services/coverage_matrix[dev]
	$(PYTHON) -m pip install -e "apps/cli[dev]"
	@echo "$(GREEN)✓ All packages installed$(NC)"

# ============================================================================
# Canonical aggregate targets — one gate across every package
# ============================================================================

qa: $(QA_TARGETS) ## format-check -> lint -> types -> test, every package
	@echo "$(GREEN)✓ QA passed for all packages$(NC)"

lint: $(addprefix lint-,$(ALIASES)) ## Ruff + Pylint (score >= 9.5), every package
	@echo "$(GREEN)✓ Ruff + Pylint passed for all packages (Pylint score >= $(MIN_PYLINT_SCORE))$(NC)"

format: $(addprefix format-,$(ALIASES)) ## Ruff autofix + Black (rewrite), every package
	@echo "$(GREEN)✓ Ruff + Black formatting complete for all packages$(NC)"

format-check: $(addprefix format-check-,$(ALIASES)) ## Black --check (no writes), every package
	@echo "$(GREEN)✓ Black check passed for all packages$(NC)"

types: $(addprefix types-,$(ALIASES)) ## mypy, every package
	@echo "$(GREEN)✓ mypy passed for all packages$(NC)"

test: $(addprefix test-,$(ALIASES)) ## pytest, every package
	@echo "$(GREEN)✓ Unit tests passed for all packages$(NC)"

coverage: $(addprefix coverage-,$(ALIASES)) ## pytest with coverage gate, every package
	@echo "$(GREEN)✓ Coverage passed for all packages (>= $(MIN_COVERAGE)%)$(NC)"

# ============================================================================
# Canonical per-package targets — <gate>-<alias> (static pattern rules)
# ============================================================================

$(QA_TARGETS): qa-%: format-check-% lint-% types-% test-%
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

$(addprefix test-,$(ALIASES)): test-%:
	@echo "$(YELLOW)→ Tests: $* ($(dir-$*))$(NC)"
	cd $(dir-$*) && $(PYTHON) -m pytest tests/

$(addprefix coverage-,$(ALIASES)): coverage-%:
	@echo "$(YELLOW)→ Coverage: $* ($(dir-$*), >= $(MIN_COVERAGE)%)$(NC)"
	cd $(dir-$*) && $(PYTHON) -m pytest tests/ --cov=src --cov-fail-under=$(MIN_COVERAGE)

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
