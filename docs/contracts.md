# Contracts & Interfaces Reference

Quick reference for all external-facing contracts. Changes to items below require review (see [Change Control](#change-control)).

---

- [CLI Interface](#cli-interface)
- [Input Contract: `doc-issues.json`](#input-contract-doc-issuesjson)
- [Output Contract: `generator-ready.json`](#output-contract-generator-readyjson)
- [Output Contract: `coverage-matrix.json`](#output-contract-coverage-matrixjson)
- [Audit Envelope (v1.0)](#audit-envelope-v10)
- [JSON Schemas](#json-schemas)
- [Change Control](#change-control)
- [Performance Budgets](#performance-budgets)

---

## CLI Interface

### `living-doc normalize-issues`

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--input` | path | Yes | — | Path to input JSON (e.g., `doc-issues.json`) |
| `--output` | path | Yes | — | Path for output JSON (e.g., `generator-ready.json`; `pdf_ready.json` still accepted, deprecated) |
| `--source` | enum | No | `auto` | Adapter selection: `auto`, `collector-gh` |
| `--document-title` | string | No | from input | Override `meta.document_title` |
| `--document-version` | string | No | from input | Override `meta.document_version` |
| `--verbose` | flag | No | `false` | Enable verbose logging |

### Exit Codes (`normalize-issues`)

| Code | Condition | Error Prefix |
|------|-----------|--------------|
| 0 | Success | — |
| 1 | Invalid input (missing file, malformed JSON) | `Invalid input:` |
| 2 | Adapter detection failed | `Adapter error:` |
| 3 | Schema validation failure | `Schema validation failed:` |
| 4 | Normalization error | `Normalization failed:` |
| 5 | File I/O error | `File I/O error:` |

Error format: `{prefix} {detail}. {guidance}`

---

### `living-doc coverage-matrix`

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--doc-input` | path | Yes | — | Path to US+AC doc JSON (`doc-source.json` / `doc-issues.json`) |
| `--tests-input` | path | Yes | — | Path to ui-tests JSON (`ui-tests.json`) |
| `--output` | path | Yes | — | Destination path for `coverage-matrix.json` |
| `--fail-under` | float | No | disabled | Exit code 1 if `coverage_pct < N` |
| `--verbose` | flag | No | `false` | Enable verbose logging |

### Exit Codes (`coverage-matrix`)

| Code | Condition |
|------|-----------|
| 0 | Success |
| 1 | Any error (invalid input, I/O failure, coverage below `--fail-under`) |

---

## Input Contract: `doc-issues.json`

Produced by [living-doc-collector-gh](https://github.com/AbsaOSS/living-doc-collector-gh).

### Producer Detection

Adapter auto-detection checks:
- `metadata.producer.name` == `"AbsaOSS/living-doc-collector-gh"`
- `metadata.producer.version` — semver format

### Compatibility Policy

**Confirmed range:** `>=0.1.1,<2.0.0`

The floor tracks `living-doc-collector-gh`'s current released package version (`0.1.1`), so
the range already covers the whole `1.x` line. It is raised to the originally-intended
`>=1.0.0` once collector-gh tags a real `v1.0.0` (see
`packages/adapters/collector_gh/SCHEMA_SYNC.md`).

| Scenario | Behavior |
|----------|----------|
| Within range | Proceed silently |
| Outside range | Log warning, add to `audit.trace[].warnings[]`, attempt processing |
| Unrecognizable schema | Exit with `Adapter error:` |

Warning format in audit:
```json
{
  "code": "VERSION_MISMATCH",
  "message": "Producer version 2.1.0 is outside confirmed range >=0.1.1,<2.0.0",
  "context": "metadata.producer.version"
}
```

---

## Output Contract: `generator-ready.json`

Target: any generator that consumes the canonical dataset — today
[`living-doc-generator-pdf`](https://github.com/AbsaOSS/living-doc-generator-pdf) and
[`living-doc-generator-markdown`](https://github.com/AbsaOSS/living-doc-generator-markdown).
The schema has no format-specific field; `generator-pdf` is one consumer, not the owner.

**Schema version:** `"generator-ready-v1.0.0"` (field `schema_version`; the superseded `"1.0"` is still accepted on read, deprecated)

The legacy output name `pdf_ready.json` is still accepted as a deprecated alias for one or two minor versions.

### Structure

```
generator-ready.json
├── schema_version: "generator-ready-v1.0.0"
├── meta
│   ├── document_title, document_version, generated_at
│   ├── source_set[]
│   ├── selection_summary { total_items, included_items, excluded_items }
│   └── audit (optional) → see Audit Envelope below
└── content
    └── user_stories[]
        ├── id, title, state, tags[], url
        ├── timestamps { created, updated }
        └── sections { description, business_value, … }
```

### Section Mapping (Heading Synonyms)

Issue body `##` headings map to canonical section keys (case-insensitive):

| Canonical Key | Accepted Synonyms |
|---------------|-------------------|
| `description` | Description, Overview, Summary |
| `business_value` | Business Value, Value, Why |
| `preconditions` | Preconditions, Prerequisites, Setup |
| `acceptance_criteria` | Acceptance Criteria, AC, Done Criteria |
| `user_guide` | User Guide, How To, Instructions |
| `connections` | Connections, Related, Links |
| `last_edited` | Last Edited, History, Changes |

**Edge cases:**
- Unknown headings → appended to `description` as `### {Heading}\n{content}`
- Content before first heading → assigned to `description`
- Multiple occurrences of same heading → concatenated with separator
- Missing sections → `null` or `""`

### Stable ID Format

`github:{owner}/{repo}#{number}` (e.g., `github:AbsaOSS/project#42`)

---

## Output Contract: `coverage-matrix.json`

**Schema version:** `"coverage-matrix-v1.0.0"` (field `schema_version`)

Produced by `living-doc coverage-matrix`. Consumed by downstream PDF / reporting generators.

### Structure

```
coverage-matrix.json
├── schema_version: "coverage-matrix-v1.0.0"
├── generated_at: ISO-8601 timestamp
├── summary { total_user_stories, total_functionalities, total_features, total_acs, active_acs, covered_acs, coverage_pct }
├── user_stories[]
│   ├── id, full_id, title, state
│   ├── summary { total_acs, active_acs, covered_acs, coverage_pct }
│   └── acceptance_criteria[]
│       ├── id, state, version, description
│       └── coverage { status, test_count, tests[] }
├── functionalities[]
│   ├── id, full_id, title, state, parent, func_type
│   ├── summary { total_acs, active_acs, covered_acs, coverage_pct }
│   └── acceptance_criteria[]  ← same shape as user_stories
├── features[]               ← registry surfaces (no acceptance criteria)
│   └── id, full_id, title, state, surface_type, route, owners, purpose,
│       user_stories[], functionalities[], external_dependencies, page_object
├── unlinked_tests[]      ← scenarios with null/unresolved us_id and func_id
└── stale_ac_refs[]       ← ac_ids that don't exist on the resolved US/Functionality
```

### Coverage Status

| Status | Condition |
|--------|-----------|
| `covered` | ≥1 scenario references this `ac_id` |
| `not_covered` | 0 scenarios reference this `ac_id` |

### Coverage Percentage

`coverage_pct = covered_active_acs / active_acs * 100` rounded to 1 dp.  
Deprecated ACs (`state != "Active"`) are included in the matrix but **excluded from `coverage_pct`** so they cannot inflate scores.  
`coverage_pct` is `null` when `active_acs == 0`.

---

## Audit Envelope (v1.0)

Lives at `meta.audit`. Preserves upstream provenance and tracks transformation steps.

### Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | Yes | Fixed `"1.0"` |
| `producer.name` | string | Yes | e.g., `"AbsaOSS/living-doc-collector-gh"` |
| `producer.version` | string | Yes | Semver |
| `producer.build` | string \| null | No | Build identifier |
| `run.*` | object | No | CI run context (run_id, actor, workflow, ref, sha) |
| `source.systems` | string[] | Yes | Non-empty (e.g., `["GitHub"]`) |
| `source.repositories` | string[] | No | e.g., `["AbsaOSS/project"]` |
| `trace[]` | array | Yes | Ordered transformation steps |
| `extensions` | object | No | Namespaced extra data |

### Trace Step

Each pipeline stage appends a trace entry:
```json
{
  "step": "normalization",
  "tool": "living-doc-toolkit",
  "tool_version": "0.1.0",
  "started_at": "2026-01-23T12:00:00Z",
  "finished_at": "2026-01-23T12:00:05Z",
  "warnings": []
}
```

### Metadata Mapping (Collector → Audit)

| Collector field | Audit field |
|-----------------|-------------|
| `metadata.producer.*` | `audit.producer.*` |
| `metadata.run.*` | `audit.run.*` |
| `metadata.source.*` | `audit.source.*` |
| Full original `metadata` | `audit.extensions["collector-gh"].original_metadata` |

---

## JSON Schemas

Machine-readable schemas are at:
- `packages/datasets_generator_ready/schemas/generator-ready-v1.0.0-schema.json`
- `packages/datasets_generator_ready/schemas/audit_envelope_v1.schema.json`
- `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/schema/doc-source-v1.0.0-schema.json` (validates a full `doc-source.json` envelope only, not a bare array or legacy `items` envelope; a vendored, pinned copy owned and generated by `living-doc-collector-gh` — see `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/schema/README.md`)
- `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/schema/coverage-matrix-v1.0.0-schema.json` (owned by this repo)

Pydantic models (source of truth for the generator-ready contracts):
- `packages/datasets_generator_ready/src/living_doc_datasets_generator_ready/generator_ready/v1/models.py`
- `packages/datasets_generator_ready/src/living_doc_datasets_generator_ready/audit/v1/models.py`

Dataclasses (source of truth for coverage-matrix contract):
- `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/model/coverage_item.py`

---

## Change Control

### Stable (breaking changes require major version bump)

- Schema field names, types, and meanings (`generator-ready` v1.0.0, `coverage-matrix` v1.0.0)
- `AdapterResult` model signature
- CLI argument names and defaults
- Exit codes and error message prefixes

### Safe to change (no version bump needed)

- Internal refactoring (preserving behavior)
- New optional fields in schemas
- New optional CLI arguments
- Test, doc, and logging improvements

### Requires review before changing

- Schema modifications (`datasets_generator_ready`)
- Adapter interface changes
- Error message text
- Performance budgets

---

## Performance Budgets

| Operation | Target | Maximum |
|-----------|--------|---------|
| JSON parsing (10 MB) | < 1 s | 5 s |
| Adapter detection | < 0.1 s | 1 s |
| Markdown normalization (100 issues) | < 2 s | 10 s |
| Output validation | < 1 s | 5 s |
| Total (100 issues) | < 10 s | 30 s |
