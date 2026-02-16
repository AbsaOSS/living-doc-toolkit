# Living Doc Datasets PDF

Versioned Pydantic models and JSON schemas for `pdf_ready` and `audit` contracts used by the Living Documentation Toolkit.

## Overview

This package provides:
- **PDF Ready v1.0 models**: Pydantic models for the PDF-ready dataset contract
- **Audit Envelope v1.0 models**: Pydantic models for audit trail metadata
- **JSON Schemas**: Exported JSON Schema files for validation
- **Serialization helpers**: Utilities for deterministic JSON serialization

## Installation

```bash
pip install -e packages/datasets_pdf
```

## Usage

### Using PDF Ready Models

```python
from living_doc_datasets_pdf.pdf_ready.v1.models import PdfReadyV1, Meta, Content
from living_doc_datasets_pdf.pdf_ready.v1.serializer import to_json, from_json

# Create a model instance
pdf_ready = PdfReadyV1(
    schema_version="1.0",
    meta=Meta(...),
    content=Content(user_stories=[])
)

# Serialize to JSON
json_str = to_json(pdf_ready)

# Parse from JSON
pdf_ready2 = from_json(json_str)
```

### Using Audit Envelope Models

```python
from living_doc_datasets_pdf.audit.v1.models import AuditEnvelopeV1, Producer, Run, Source
from living_doc_datasets_pdf.audit.v1.serializer import to_json, from_json

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
from living_doc_datasets_pdf.pdf_ready.v1.schema import export_json_schema

# Export schema to file
schema = export_json_schema("output/schema.json")
```

## Development

### Running Tests

```bash
cd packages/datasets_pdf
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
