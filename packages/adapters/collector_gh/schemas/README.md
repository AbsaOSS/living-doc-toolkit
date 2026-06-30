# Input Schema Artifacts

This directory contains the exported JSON Schema for the input contract.

## Schema File

- **`doc-issues-v1.0.0-schema.json`** — JSON Schema for doc-issues.json input data (schema version 1.0.0)

## How to Generate

From the package root (`packages/adapters/collector_gh/`):

```bash
# Generate and save to default location (this directory)
python -m living_doc_adapter_collector_gh.schema_export

# Or specify a custom output location
python -m living_doc_adapter_collector_gh.schema_export /path/to/custom-schema.json
```

## Usage

Downstream consumers (e.g., collector-gh repo) independently:
1. Obtain the published schema from this directory
2. Use it in their validation pipeline
3. Validate input data against the schema

Example with `ajv-cli`:

```bash
ajv validate -s doc-issues-v1.0.0-schema.json -d /path/to/doc-issues.json
```

## Schema Updates

When Pydantic models change:

1. Pydantic models in `src/living_doc_adapter_collector_gh/models.py` are updated
2. Run `python -m living_doc_adapter_collector_gh.schema_export` to regenerate
3. New versioned file is created: `doc-issues-v{VERSION}-schema.json`
4. Commit updated schema
5. Release as new version
6. Downstream consumers obtain and use updated schema

See `SCHEMA_SYNC.md` for complete synchronization workflow.
