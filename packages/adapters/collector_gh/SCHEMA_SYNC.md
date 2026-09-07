# Schema Synchronization Guide

## Pattern: Vendored Pinned Copy (Schema Consumer / Data Consumer)

`living-doc-collector-gh` is the repository that **produces `doc-issues.json`**, and since
its PR #110 it also **owns and generates** the contract for it:
`doc-issues-v1.0.0-schema.json` is exported from `collector-gh`'s own Pydantic models
(`doc_issues/models.py`) by a generator utility in that repo. That makes `collector-gh` the
**schema producer and the data producer**.

This adapter is the **schema consumer and the data consumer**:

- It **vendors a pinned copy** of `doc-issues-v1.0.0-schema.json` under `schemas/`, copied
  byte-for-byte from `collector-gh` at a known commit / tag.
- Its `models.py` is a **consumer-side representation** of that vendored schema — a
  convenience for parsing, not the authority for what a valid `doc-issues.json` looks like.
- The vendored schema and `models.py` are kept in step with each other by the golden
  fixture tests (`tests/test_parser.py`), not by re-generating anything in this repo.

This mirrors the "producers own and publish, consumers vendor a pinned copy" mechanism
planned for roadmap Phase 5 — the pin-and-vendor automation itself is later work; today the
copy is manual.

```
┌────────────────────────────────────────────────────────┐
│ living-doc-collector-gh                                 │
│ SCHEMA PRODUCER  +  DATA PRODUCER                       │
│                                                        │
│ • Pydantic models (doc_issues/models.py)  ◄── SOURCE    │
│ • Generates doc-issues-v1.0.0-schema.json from them      │
│ • Emits doc-issues.json at run time                     │
└────────────────────────────────────────────────────────┘
                      │
                      │ schema copied in at a pinned commit / tag
                      │ (manual vendor step — no code dependency)
                      ▼
┌────────────────────────────────────────────────────────┐
│ living-doc-toolkit — collector_gh adapter (This Repo)   │
│ SCHEMA CONSUMER  +  DATA CONSUMER                       │
│                                                        │
│ • Vendored copy: schemas/doc-issues-v1.0.0-schema.json  │
│ • Consumer-side models.py mirrors the vendored schema   │
│ • compatibility.py checks producer.version in range     │
│ • Golden tests keep models.py ↔ vendored schema in step │
└────────────────────────────────────────────────────────┘
```

**Key:** No direct code dependency. The schema travels as a file copied in at a pin; each
repo runs its own validation pipeline.


## Schema Version

- **Input Schema Version:** `1.0.0` (independent of adapter package version)
- **Adapter Package Version:** `1.0.0` (see `__init__.py`)
- **Producer Compatibility Range:** `>=0.1.1,<2.0.0` (see `compatibility.py`)

## Workflow: When `collector-gh` Changes the Contract

This is a manual sync until the pin-and-vendor automation lands (roadmap Phase 5).

### 1. Obtain `collector-gh`'s Regenerated Schema

`collector-gh` regenerates `doc_issues/schema/doc-issues-v1.0.0-schema.json` from its own
Pydantic models whenever the contract changes. Take that generated file at the commit / tag
you want to pin to.

### 2. Replace the Vendored Copy

Copy it here **byte-for-byte** — do not reformat or re-key it:

```bash
cp <collector-gh>/doc_issues/schema/doc-issues-v1.0.0-schema.json \
   packages/adapters/collector_gh/schemas/doc-issues-v1.0.0-schema.json
```

### 3. Update the Consumer-Side `models.py`

Bring [models.py](src/living_doc_adapter_collector_gh/models.py) into line with the new
vendored schema — same field list as `collector-gh`'s `doc_issues/models.py`. `models.py`
is a mirror, so this is a mechanical edit, not a design decision.

### 4. Re-Check the Compatibility Range

If `collector-gh` released a new version, re-check `CONFIRMED_MIN` / `CONFIRMED_MAX` in
[compatibility.py](src/living_doc_adapter_collector_gh/compatibility.py) against
`collector-gh`'s release notes:

- **Breaking change** → bump `CONFIRMED_MIN` or `CONFIRMED_MAX`, add a test fixture for the
  new version, note it in [README.md](README.md).
- **Non-breaking change** → add a golden test fixture; no code change.

### 5. Run the Golden Tests

```bash
make qa-collector-gh
# or just the golden tests:
pytest packages/adapters/collector_gh/tests/test_parser.py
```

The golden tests fail if the vendored schema and `models.py` have drifted apart.

### 6. Commit the Sync

```bash
git add packages/adapters/collector_gh/schemas/doc-issues-v1.0.0-schema.json \
        packages/adapters/collector_gh/src/living_doc_adapter_collector_gh/models.py
git commit -m "chore: re-sync vendored doc-issues schema to collector-gh <pin>"
```

Record which `collector-gh` commit / tag the copy came from in the commit message.

## File Locations

| File | Purpose |
|------|---------|
| [schemas/doc-issues-v1.0.0-schema.json](schemas/doc-issues-v1.0.0-schema.json) | Vendored, pinned copy of `collector-gh`'s generated schema |
| [models.py](src/living_doc_adapter_collector_gh/models.py) | Consumer-side representation of the vendored schema |
| [compatibility.py](src/living_doc_adapter_collector_gh/compatibility.py) | Producer version-compatibility checking & schema version |
| [__init__.py](src/living_doc_adapter_collector_gh/__init__.py) | Package exports & documentation |
| [tests/test_parser.py](tests/test_parser.py) | Golden tests (vendored schema ↔ `models.py`) |

## Key Constants

```python
# In compatibility.py
CONFIRMED_MIN = "0.1.1"  # Min producer version
CONFIRMED_MAX = "2.0.0"  # Max producer version (exclusive)
SCHEMA_VERSION = "1.0.0" # Input contract schema version
```

## Testing

### Golden Tests (Vendored Schema ↔ `models.py`)

```bash
# Run golden tests
make qa-collector-gh

# Specific test
pytest packages/adapters/collector_gh/tests/test_parser.py::TestParser::test_metadata_source_mapping
```

## Links

- **Producer Repo (owns the schema):** https://github.com/AbsaOSS/living-doc-collector-gh
- **Consumer (This Repo):** https://github.com/AbsaOSS/living-doc-toolkit
- **Input Contract Docs:** [../../../docs/contracts.md](../../../docs/contracts.md#input-contract-doc-issuesjson)
