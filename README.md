# Living Documentation Toolkit

[![CI](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/test.yml)
[![Integration Tests](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/integration.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/integration.yml)

A monorepo hosting multiple independent Python services that transform and enrich machine-readable artifacts produced by upstream collectors (e.g., [living-doc-collector-gh](https://github.com/AbsaOSS/living-doc-collector-gh)) into datasets consumable by downstream actions (e.g., [living-doc-generator-pdf](https://github.com/AbsaOSS/living-doc-generator-pdf)).

---

- [Overview](#overview)
- [Quickstart](#quickstart)
- [Documentation](#documentation)
- [Services](#services)
- [License](#license)

---

## Overview

The Living Documentation Toolkit is a **generic builder** designed to:
- Host multiple independent services with CLI entrypoints
- Transform and normalize collector outputs into canonical datasets
- Provide adapters for input producer detection and parsing
- Offer reusable core utilities shared across services
- Enforce versioned contracts via JSON Schema and Pydantic models

## Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/AbsaOSS/living-doc-toolkit.git
cd living-doc-toolkit

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install all packages
pip install --upgrade pip
pip install -r requirements.txt
```

### Example CLI Usage

```bash
# Normalize issues from collector output to PDF-ready format
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --source auto \
  --document-title "Sprint 42 Report" \
  --document-version "1.0.0"

# Generate an AC-level test coverage matrix
living-doc coverage-matrix \
  --doc-input  doc-source.json \
  --tests-input ui-tests.json \
  --output coverage-matrix.json \
  --fail-under 80
```

## Documentation

### Understand
- **[Architecture](docs/architecture.md)** — System overview, data flow pipeline, package structure
- **[Contracts & Interfaces](docs/contracts.md)** — CLI reference, input/output schemas, audit envelope, change control

### Use

Each service below has a **Cookbook** (explains *how* it works — detection logic, compatibility rules, normalization behavior) and **Recipes** (step-by-step guides to run it in a specific environment). See [Services](#services) for the full list.

### Maintain
- **[Troubleshooting](docs/troubleshooting.md)** — Exit codes, common errors, FAQ
- **[Developer Guide](DEVELOPER.md)** — Environment setup, testing, linting, branch conventions
- **[Changelog](CHANGELOG.md)** — Version history and notable changes

## Services

### `normalize-issues`
Converts collector output (`doc-issues.json`) into PDF-ready canonical JSON (`pdf_ready.json`) compliant with the PDF generator specification.

- [Cookbook](docs/cookbooks/normalize-issues.md) — How detection, compatibility, and normalization work
- [Recipe: Local usage](docs/recipes/local-normalize-issues.md) — Run the CLI on your machine
- [Recipe: GitHub Actions](docs/recipes/github-actions-normalize-issues.md) — CI/CD workflow integration

### `coverage-matrix`
Cross-references a `doc-source.json` (User Stories + acceptance criteria) with a `ui-tests.json` (E2E test scenarios) and produces `coverage-matrix.json`: an AC-level test coverage matrix per User Story.

- [Package README](packages/services/coverage_matrix/README.md) — Matching logic, CLI reference, module layout

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for full details.
