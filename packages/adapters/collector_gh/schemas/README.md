# Input Schema Artifacts

This directory holds a **vendored, pinned copy** of the `doc-issues.json` input-contract
schema.

## Schema File

- **`doc-issues-v1.0.0-schema.json`** — JSON Schema for `doc-issues.json` input data
  (schema version `1.0.0`).

## Ownership

`living-doc-collector-gh` **owns** this contract. It generates
`doc-issues-v1.0.0-schema.json` from its own Pydantic models (`doc_issues/models.py`) and is
the schema **and** data producer. This repository is the schema **and** data consumer: it
vendors the file below
verbatim and keeps `src/living_doc_adapter_collector_gh/models.py` in step with it via the
golden-fixture tests.

## How to Update

This is a manual sync until the pin-and-vendor automation lands (roadmap Phase 5):

1. Take `doc_issues/schema/doc-issues-v1.0.0-schema.json` from `living-doc-collector-gh` at
   the pinned commit / tag.
2. Copy it here byte-for-byte (do not reformat or re-key it).
3. Bring `../src/living_doc_adapter_collector_gh/models.py` back into step with it and
   re-run the adapter golden tests (`make qa-collector-gh`).

See `../SCHEMA_SYNC.md` for the full consumer-side synchronization workflow.

## Usage

Downstream tooling can validate a `doc-issues.json` against this file, e.g. with `ajv-cli`:

```bash
ajv validate -s doc-issues-v1.0.0-schema.json -d /path/to/doc-issues.json
```
