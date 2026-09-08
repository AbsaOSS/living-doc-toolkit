# Living Doc Datasets Generator-Ready

Versioned Pydantic models and JSON schemas for the `generator-ready` and `audit` contracts used by the Living Documentation Toolkit.

## Overview

This package provides:
- **Generator-ready v1.0.0 models**: Pydantic models for the canonical `generator-ready.json` dataset contract
- **Audit Envelope v1.0 models**: Pydantic models for audit trail metadata
- **JSON Schemas**: Exported JSON Schema files for validation
- **Serialization helpers**: Utilities for deterministic JSON serialization

## Installation

```bash
pip install -e packages/datasets_generator_ready
```

## Usage

### Using Generator-Ready Models

```python
from living_doc_datasets_generator_ready.generator_ready.v1.models import (
    Content,
    GeneratorReadyV1,
    Meta,
    SelectionSummary,
)
from living_doc_datasets_generator_ready.generator_ready.v1.serializer import to_json, from_json

# Create a model instance
generator_ready = GeneratorReadyV1(
    schema_version="generator-ready-v1.0.0",
    meta=Meta(
        document_title="Product Requirements",
        document_version="1.0.0",
        generated_at="2026-01-23T12:00:00Z",
        source_set=["github:AbsaOSS/project"],
        selection_summary=SelectionSummary(total_items=0, included_items=0, excluded_items=0),
    ),
    content=Content(user_stories=[]),
)

# Serialize to JSON
json_str = to_json(generator_ready)

# Parse from JSON
generator_ready2 = from_json(json_str)
```

The superseded `schema_version` value `"1.0"` is still accepted on read for one or two
minor versions and emits a `DeprecationWarning`.

### Using Audit Envelope Models

```python
from living_doc_datasets_generator_ready.audit.v1.models import AuditEnvelopeV1, Producer, Run, Source
from living_doc_datasets_generator_ready.audit.v1.serializer import to_json, from_json

# Create an audit envelope
audit = AuditEnvelopeV1(
    schema_version="1.0",
    producer=Producer(name="test", version="1.0.0"),
    run=Run(),
    source=Source(systems=["GitHub"]),
    trace=[]
)

# Serialize to JSON
json_str = to_json(audit)
```

### Exporting JSON Schemas

```python
from living_doc_datasets_generator_ready.generator_ready.v1.schema import export_json_schema

# Export schema to file
schema = export_json_schema("output/schema.json")
```

## Development

### Running Tests

```bash
cd packages/datasets_generator_ready
pytest tests/ -v --cov=src
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
pylint src/
```

## License

Apache License 2.0
