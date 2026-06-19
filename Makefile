.PHONY: help black pylint mypy pytest-unit py-qa \
        black-all pylint-all mypy-all pytest-unit-all \
        install \
        $(patsubst %,black-%,$(PACKAGES) $(APPS)) \
        $(patsubst %,pylint-%,$(PACKAGES) $(APPS)) \
        $(patsubst %,mypy-%,$(PACKAGES) $(APPS)) \
        $(patsubst %,pytest-unit-%,$(PACKAGES) $(APPS))

# Packages and apps
PACKAGES := packages/core \
            packages/datasets_pdf \
            packages/adapters/collector_gh \
            packages/services/normalize_issues
APPS := apps/cli
ALL_TARGETS := $(PACKAGES) $(APPS)

# Python and tools
PYTHON ?= python
MIN_PYLINT_SCORE := 9.5
MIN_COVERAGE := 80

# Color output
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

install: ## Install all packages with [dev] dependencies
	@echo "$(YELLOW)Installing packages in dependency order...$(NC)"
	$(PYTHON) -m pip install -e packages/core[dev]
	$(PYTHON) -m pip install -e packages/datasets_pdf[dev]
	$(PYTHON) -m pip install -e packages/adapters/collector_gh[dev]
	$(PYTHON) -m pip install -e packages/services/normalize_issues[dev]
	$(PYTHON) -m pip install -e "apps/cli[dev]"
	@echo "$(GREEN)✓ All packages installed$(NC)"

help: ## Show this help message
	@echo "$(GREEN)Living Documentation Toolkit - QA Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup:$(NC)"
	@echo "  make install            Install all packages with [dev] dependencies"
	@echo ""
	@echo "$(YELLOW)Run all QA checks:$(NC)"
	@echo "  make py-qa              Run all QA gates on all packages"
	@echo ""
	@echo "$(YELLOW)Run QA by check type:$(NC)"
	@echo "  make black              Run Black formatter on all packages"
	@echo "  make pylint             Run Pylint on all packages"
	@echo "  make mypy               Run mypy on all packages"
	@echo "  make pytest-unit        Run unit tests on all packages"
	@echo ""
	@echo "$(YELLOW)Run QA by package:$(NC)"
	@echo "  make py-qa-core         Run all QA on packages/core"
	@echo "  make py-qa-datasets-pdf Run all QA on packages/datasets_pdf"
	@echo "  make py-qa-collector-gh Run all QA on packages/adapters/collector_gh"
	@echo "  make py-qa-normalize    Run all QA on packages/services/normalize_issues"
	@echo "  make py-qa-cli          Run all QA on apps/cli"
	@echo ""
	@echo "$(YELLOW)Run individual checks by package:$(NC)"
	@echo "  make black-core         Run Black on packages/core"
	@echo "  make pylint-core        Run Pylint on packages/core"
	@echo "  make mypy-core          Run mypy on packages/core"
	@echo "  make pytest-unit-core   Run tests on packages/core"
	@echo ""
	@echo "$(YELLOW)Package shortcuts (replace 'core' with any package):$(NC)"
	@echo "  - datasets_pdf, collector_gh, normalize, cli"

# ============================================================================
# ALL PACKAGES: Aggregated QA targets
# ============================================================================

black: black-all ## Run Black on all packages

pylint: pylint-all ## Run Pylint on all packages

mypy: mypy-all ## Run mypy on all packages

pytest-unit: pytest-unit-all ## Run unit tests on all packages

py-qa: black pylint mypy pytest-unit ## Run all QA gates on all packages
	@echo "$(GREEN)✓ All QA checks passed!$(NC)"

# ============================================================================
# Aggregated targets for all packages
# ============================================================================

black-all: $(patsubst %,black-%,$(ALL_TARGETS))
	@echo "$(GREEN)✓ Black formatting complete for all packages$(NC)"

pylint-all: $(patsubst %,pylint-%,$(ALL_TARGETS))
	@echo "$(GREEN)✓ Pylint checks passed for all packages (score >= $(MIN_PYLINT_SCORE))$(NC)"

mypy-all: $(patsubst %,mypy-%,$(ALL_TARGETS))
	@echo "$(GREEN)✓ mypy type checks passed for all packages$(NC)"

pytest-unit-all: $(patsubst %,pytest-unit-%,$(ALL_TARGETS))
	@echo "$(GREEN)✓ Unit tests passed for all packages (coverage >= $(MIN_COVERAGE)%)$(NC)"

# ============================================================================
# PER-PACKAGE QA targets (all checks for one package)
# ============================================================================

py-qa-core: black-core pylint-core mypy-core pytest-unit-core
	@echo "$(GREEN)✓ All QA checks passed for packages/core$(NC)"

py-qa-datasets-pdf: black-packages/datasets_pdf pylint-packages/datasets_pdf mypy-packages/datasets_pdf pytest-unit-packages/datasets_pdf
	@echo "$(GREEN)✓ All QA checks passed for packages/datasets_pdf$(NC)"

py-qa-collector-gh: black-packages/adapters/collector_gh pylint-packages/adapters/collector_gh mypy-packages/adapters/collector_gh pytest-unit-packages/adapters/collector_gh
	@echo "$(GREEN)✓ All QA checks passed for packages/adapters/collector_gh$(NC)"

py-qa-normalize: black-packages/services/normalize_issues pylint-packages/services/normalize_issues mypy-packages/services/normalize_issues pytest-unit-packages/services/normalize_issues
	@echo "$(GREEN)✓ All QA checks passed for packages/services/normalize_issues$(NC)"

py-qa-cli: black-apps/cli pylint-apps/cli mypy-apps/cli pytest-unit-apps/cli
	@echo "$(GREEN)✓ All QA checks passed for apps/cli$(NC)"

# ============================================================================
# BLACK FORMATTER
# ============================================================================

$(patsubst %,black-%,$(ALL_TARGETS)): black-%:
	@echo "$(YELLOW)→ Black: $*$(NC)"
	cd $* && $(PYTHON) -m black .

# ============================================================================
# PYLINT LINTER
# ============================================================================

$(patsubst %,pylint-%,$(ALL_TARGETS)): pylint-%:
	@echo "$(YELLOW)→ Pylint: $* (threshold >= $(MIN_PYLINT_SCORE))$(NC)"
	cd $* && $(PYTHON) -m pylint --fail-under=$(MIN_PYLINT_SCORE) $$(git ls-files '*.py' | grep -v '^tests/')

# ============================================================================
# MYPY TYPE CHECKER
# ============================================================================

$(patsubst %,mypy-%,$(ALL_TARGETS)): mypy-%:
	@echo "$(YELLOW)→ mypy: $*$(NC)"
	cd $* && $(PYTHON) -m mypy .

# ============================================================================
# PYTEST UNIT TESTS
# ============================================================================

$(patsubst %,pytest-unit-%,$(ALL_TARGETS)): pytest-unit-%:
	@echo "$(YELLOW)→ Tests: $* (coverage >= $(MIN_COVERAGE)%)$(NC)"
	cd $* && $(PYTHON) -m pytest tests/ --cov=src --cov-fail-under=$(MIN_COVERAGE)

