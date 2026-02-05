# Living Documentation Toolkit

A monorepo hosting multiple independent Python services that transform and enrich machine-readable artifacts produced by upstream collectors (e.g., [living-doc-collector-gh](https://github.com/AbsaOSS/living-doc-collector-gh)) into datasets consumable by downstream actions (e.g., [living-doc-generator-pdf](https://github.com/AbsaOSS/living-doc-generator-pdf)).

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

# Install dependencies (once available)
pip install -e .
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
```

## Documentation

- **[SPEC.md](SPEC.md)** - System specification and architecture details
- **[TASKS.md](TASKS.md)** - Implementation roadmap and task tracking
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and notable changes

## Services

### `normalize-issues`
Converts collector output (`doc-issues.json`) into PDF-ready canonical JSON (`pdf_ready.json`) compliant with the PDF generator specification.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for full details.
