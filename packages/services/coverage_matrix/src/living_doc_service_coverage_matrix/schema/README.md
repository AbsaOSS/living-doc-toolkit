# Input Schema Artifacts

This directory holds a **vendored, pinned copy** of the `doc-source.json` input-contract
schema, alongside the `coverage-matrix.json` output schema that this service owns itself.

## Schema Files

- **`doc-source-v1.0.0-schema.json`** — JSON Schema for the `doc-source.json` input
  (schema version `1.0.0`). **Vendored** — see Ownership below.
- **`coverage-matrix-v1.0.0-schema.json`** — JSON Schema for this service's own
  `coverage-matrix.json` output. **Owned by this repo** (`toolkit` is the producer), not
  vendored.

## Ownership

`living-doc-collector-gh` **owns** the `doc-source-v1.0.0` and `ui-tests-v1.0.0` input
contracts. It generates both schemas from its own Pydantic models and is the schema
**and** data producer for them. This service is a schema **and** data consumer for
`doc-source.json`: it vendors `doc-source-v1.0.0-schema.json` verbatim and keeps
`schema_validation.py` in step with it via the golden fixture tests
(`tests/integration/test_golden_files.py`).

A vendored `ui-tests-v1.0.0-schema.json` is not carried here today because this service
does not schema-validate `ui-tests.json` (`loader.load_tests_input()` only checks for an
`items` array). Add the vendored copy alongside this file if/when that validation is
introduced, taken byte-for-byte from `collector-gh` at the same time.

`coverage-matrix.json` and its schema are unaffected by this ownership split — `toolkit`
produces that output and remains its schema owner.

## How to Update

This is a manual sync until the pin-and-vendor automation lands (roadmap Phase 5). The
procedure mirrors `packages/adapters/collector_gh/SCHEMA_SYNC.md`:

1. Take `doc-source-v1.0.0-schema.json` from `living-doc-collector-gh` at the pinned
   commit / tag.
2. Copy it here byte-for-byte (do not reformat or re-key it).
3. Bring `../schema_validation.py` back into step with it and re-run this service's golden
   tests (`make qa-coverage`).
4. Commit the sync, recording the exact `living-doc-collector-gh` commit SHA or tag the
   copy came from in the commit message (e.g. `chore: re-sync vendored doc-source schema
   to collector-gh <pin>`) — mirrors `packages/adapters/collector_gh/SCHEMA_SYNC.md`.

## Usage

Downstream tooling can validate a `doc-source.json` against this file, e.g. with `ajv-cli`:

```bash
ajv validate -s doc-source-v1.0.0-schema.json -d /path/to/doc-source.json
```
