# Living Documentation Toolkit

[![CI](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/test.yml)
[![Integration Tests](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/integration.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/integration.yml)

A monorepo hosting multiple independent Python services that transform and enrich machine-readable artifacts produced by upstream collectors (e.g., [living-doc-collector-gh](https://github.com/AbsaOSS/living-doc-collector-gh)) into datasets consumable by downstream actions (e.g., [living-doc-generator-pdf](https://github.com/AbsaOSS/living-doc-generator-pdf)).

> *This is a monorepo of multiple services and follows a different README shape than the single-purpose `living-doc-*` action repos ([convention](https://github.com/AbsaOSS/living-doc/blob/master/docs/specs/repo-conventions.md)). If you arrived from an action repo, the `Understand / Use / Maintain` layout below is deliberate.*

---

- [Overview](#overview)
- [Quickstart](#quickstart)
- [Documentation](#documentation)
- [Services](#services)
- [License](#license)

---

## Overview

**Expected usage: GitHub Actions first.** The `living-doc` CLI is invoked as a step in a GitHub Actions workflow, chained between the upstream `living-doc-*` collector actions and the downstream generator actions. Running `living-doc <service>` locally — the pattern documented in [DEVELOPER.md](DEVELOPER.md) — is a development and debugging affordance only, not a second supported deployment target.

**The Living Documentation pipeline runs AI-free.** Every step — collect → normalize → generate — is deterministic tooling (Python, JSON Schema validation, Jinja2/Markdown templates) with no LLM call anywhere in that path. [`AbsaOSS/agentic-toolkit`](https://github.com/AbsaOSS/agentic-toolkit) can accelerate the upstream *authoring* of GitHub Issues and `.feature` files, but it is never a runtime dependency of this pipeline: a human writing the same input by hand is a fully supported, identical path.

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
- **[SPEC.md](SPEC.md)** — How a new service or adapter is specced before it is built (the prospective-spec process for this monorepo)

### Use

Each service below has a **Cookbook** (explains *how* it works — detection logic, compatibility rules, normalization behavior) and **Recipes** (step-by-step guides to run it in a specific environment). See [Services](#services) for the full list.

### Maintain
- **[Troubleshooting](docs/troubleshooting.md)** — Exit codes, common errors, FAQ
- **[Developer Guide](DEVELOPER.md)** — Environment setup, testing, linting, branch conventions
- **[Contribution Guidelines](CONTRIBUTING.md)** — How to report bugs, propose features, and open a PR

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
