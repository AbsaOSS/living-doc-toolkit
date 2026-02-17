# living-doc-service-normalize-issues

Normalization service for the Living Documentation Toolkit.

## Overview

This service transforms collector-gh output (`doc-issues.json`) into PDF-ready canonical JSON (`pdf_ready.json`). It is the core normalization component of the Living Documentation Toolkit pipeline.

## Features

- **Markdown Normalization**: Parses and normalizes issue body markdown into canonical sections
- **Heading Synonym Mapping**: Maps various heading synonyms to standard section names (e.g., "Overview", "Summary" → "description")
- **PDF-Ready Output**: Generates validated JSON conforming to the PDF-ready v1.0 schema
- **Audit Trail**: Maintains full audit trail from collection through normalization

## Installation

```bash
pip install living-doc-service-normalize-issues
```

## Usage

```python
from living_doc_service_normalize_issues.service import run_service

# Run normalization service
run_service(
    input_path="doc-issues.json",
    output_path="pdf_ready.json",
    options={
        "document_title": "My Living Documentation",
        "document_version": "1.0.0"
    }
)
```

## Architecture

The service consists of three main components:

1. **normalizer.py**: Markdown parsing and section normalization
2. **builder.py**: PDF-ready JSON construction from adapter results
3. **service.py**: Pipeline orchestration and error handling

## Dependencies

- `living-doc-core`: Core utilities (JSON, markdown, logging, errors)
- `living-doc-datasets-pdf`: PDF-ready and audit schemas (Pydantic models)
- `living-doc-adapter-collector-gh`: Collector-GH adapter models

## License

Apache License 2.0. Copyright 2026 ABSA Group Limited.
