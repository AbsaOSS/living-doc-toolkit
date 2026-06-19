# Schema Synchronization Guide

## Pattern: Pydantic-First (Schema Producer / Data Consumer)

This adapter uses the **Pydantic-First** pattern where **this repository** (living-doc-toolkit):
- **Receives data** from collector-gh (data consumer role)
- **Produces schema** as an artifact for collector-gh to validate against (schema producer role)

The Pydantic models in this repo are the **single source of truth** for the input contract.

```
┌────────────────────────────────────────────────┐
│ living-doc-toolkit (This Repo)                 │
│ SCHEMA PRODUCER / DATA CONSUMER                │
│                                                │
│ • Pydantic models (models.py)  ◄── SOURCE     │
│ • Export JSON Schema (schema_export.py)        │
│ • Save to: schemas/doc-issues-v1.0.0-schema.json │
│ • Publish schema as artifact                   │
└────────────────────────────────────────────────┘
                      │
                      │ Schema published as independent artifact
                      │ (no direct code dependency)
                      ▼
┌────────────────────────────────────────────────┐
│ Downstream Consumers (Independent)             │
│ SCHEMA CONSUMER / DATA PRODUCER                │
│                                                │
│ • Obtain published schema                      │
│ • Use it independently for validation          │
│ • Publishes validated data                     │
└────────────────────────────────────────────────┘
```

**Key:** No direct code dependency. The schema is a published artifact that each
repo uses independently within their own validation pipeline.


## Schema Version

- **Input Schema Version:** `1.0.0` (independent of adapter package version)
- **Adapter Package Version:** `1.0.0` (see `__init__.py`)
- **Producer Compatibility Range:** `>=1.0.0,<2.0.0` (see `compatibility.py`)

## Workflow: When Pydantic Models Change

### 1. Consumer (living-doc-toolkit) Updates Model

Edit [models.py](src/living_doc_adapter_collector_gh/models.py):

```python
class AdapterMetadataSource(BaseModel):
    """Source information for adapter metadata."""
    systems: list[str] = Field(min_length=1, description="At least one system")
    # ... other fields
```

### 2. Export Updated Schema

Schema is automatically saved with version in filename:

```bash
# From packages/adapters/collector_gh/
python -m living_doc_adapter_collector_gh.schema_export

# Schema is now in: schemas/doc-issues-v1.0.0-schema.json

# Or programmatically:
from living_doc_adapter_collector_gh import export_schema, SCHEMA_VERSION
schema = export_schema()  # Saved to default location with version
print(f"Schema version: {SCHEMA_VERSION}")  # 1.0.0
```

Or save to custom location:

```bash
python -m living_doc_adapter_collector_gh.schema_export /path/to/custom-schema.json
```

### 3. Validate Tests Pass

```bash
make pytest-unit-packages/adapters/collector_gh
```

### 4. Commit & Publish Schema as Artifact

Schema changes are committed and published with version in filename:

```bash
# Commit the updated schema (versioned filename)
git add packages/adapters/collector_gh/schemas/doc-issues-v1.0.0-schema.json
git commit -m "chore: update input schema to v1.0.0

- systems field now requires min_length=1
- See packages/adapters/collector_gh/SCHEMA_SYNC.md for details"

# Create release with schema as artifact
# or include schema in release notes / documentation
```

Schema is now available at: `packages/adapters/collector_gh/schemas/doc-issues-v1.0.0-schema.json`

### 5. Downstream Consumers Obtain & Use Schema

Consumers (e.g., collector-gh repo):
- Obtain published schema (from GitHub release, documentation, etc.)
- Integrate into their validation pipeline
- Use to validate data
- **No direct code dependency** on this repo

Example consumer workflow:

```yaml
# .github/workflows/validate-output.yml
- name: Download schema
  run: |
    curl -O https://github.com/AbsaOSS/living-doc-toolkit/releases/download/v1.0.0/doc-issues-schema.json

- name: Validate output against schema
  uses: ajv-validator/ajv-cli@v5
  with:
    schema: doc-issues-schema.json
    data: doc-issues.json
```

## Workflow: When Producer Version Increments

If producer releases `v1.1.0` or `v2.0.0`:

1. **Download their release notes**
2. **Identify breaking vs. non-breaking changes**
3. **If breaking:**
   - Update `CONFIRMED_MIN` or `CONFIRMED_MAX` in [compatibility.py](src/living_doc_adapter_collector_gh/compatibility.py)
   - Add test fixtures for the new version
   - Document in [README.md](README.md)

4. **If non-breaking:**
   - Add golden test fixture (no code changes needed)
   - Verify compatibility test passes

## File Locations

| File | Purpose |
|------|---------|
| [models.py](src/living_doc_adapter_collector_gh/models.py) | Pydantic models (source of truth) |
| [schema_export.py](src/living_doc_adapter_collector_gh/schema_export.py) | Export models to JSON Schema |
| [compatibility.py](src/living_doc_adapter_collector_gh/compatibility.py) | Version compatibility checking & schema version |
| [__init__.py](src/living_doc_adapter_collector_gh/__init__.py) | Package exports & documentation |
| [tests/test_parser.py](tests/test_parser.py) | Golden tests (fixture validation) |

## Key Constants

```python
# In compatibility.py
CONFIRMED_MIN = "0.1.0"  # Min producer version
CONFIRMED_MAX = "2.0.0"  # Max producer version (exclusive)
SCHEMA_VERSION = "1.0.0" # Input contract schema version
```

## Testing

### Golden Tests (Verify Fixtures Match Model)

```bash
# Run golden tests
make pytest-unit-packages/adapters/collector_gh

# Specific test
pytest packages/adapters/collector_gh/tests/test_parser.py::TestParser::test_metadata_source_mapping
```

### Schema Export

```bash
# Verify schema can be generated
python -m living_doc_adapter_collector_gh.schema_export

# Write to file
python -m living_doc_adapter_collector_gh.schema_export schema.json
```

## Links

- **Producer Repo:** https://github.com/AbsaOSS/living-doc-collector-gh
- **Consumer (This Repo):** https://github.com/AbsaOSS/living-doc-toolkit
- **Input Contract Docs:** [../../docs/contracts.md](../../docs/contracts.md#input-contract-doc-issuesjson)
