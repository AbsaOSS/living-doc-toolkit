# Contracts & Interfaces Reference

Quick reference for all external-facing contracts. Changes to items below require review (see [Change Control](#change-control)).

---

- [CLI Interface](#cli-interface)
- [Generator Inputs by `document-type`](#generator-inputs-by-document-type)
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
| `--view` | enum | No | `inner` | Content view: `inner` (comprehensive) or `release` (public-facing, filtered) — see [Content Views](#content-views) |
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

## Generator Inputs by `document-type`

Design rule: **a generator's input is always an artifact with an owned, versioned schema —
never raw, unschematized scraping.** Usually that artifact is toolkit-produced (a
`normalize-*` pass does real work, as for `user-stories`); where a collector already emits a
first-class, schema-versioned ecosystem contract, the generator consumes it directly and no
toolkit copy step is added (see `ui-test-catalog` below). The table below is the
authoritative statement of which artifact + schema is the generator input for each
`document-type`.

| `document-type` | Generator input artifact | Schema (`schema_version`) | Producer | Provenance envelope |
|-----------------|--------------------------|---------------------------|----------|---------------------|
| `user-stories` | `generator-ready.json` | `generator-ready-v1.0.0` | `living-doc normalize-issues` (this repo) | `meta.audit` — see [Audit Envelope](#audit-envelope-v10) |
| `ui-test-catalog` | `ui-tests.json` | `ui-tests-v1.0.0` | `living-doc-collector-gh` `ui-tests` mode | none — see rationale below |
| `coverage-matrix` | `coverage-matrix.json` | `coverage-matrix-v1.0.0` | `living-doc coverage-matrix` (this repo) | none today — see rationale below |

### `user-stories`

`doc-issues.json` (collector output) → `living-doc normalize-issues` → `generator-ready.json`.
The normalize step does real work — heading-synonym normalization, restructuring, and audit
enrichment (see [Output Contract: `generator-ready.json`](#output-contract-generator-readyjson)).
This is the reference shape for the rule.

### `ui-test-catalog` — `ui-tests.json` is generator-ready as-is (no toolkit pass)

**Decision: option (a).** No `normalize-test-catalog` service is added. The generator input
for `document-type: ui-test-catalog` is `ui-tests.json` exactly as `living-doc-collector-gh`
emits it. `living-doc-collector-gh` owns the `ui-tests-v1.0.0` schema; this repo does not
vendor it and does not schema-validate `ui-tests.json` — `coverage-matrix`'s
`loader.load_tests_input()` only checks for an `items` array. See
[`packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/schema/README.md`](../packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/schema/README.md)
for the ownership split and the condition under which a vendored copy would be added.

Rationale:

- `ui-tests.json` is a **flat `items[]` catalog** of test scenarios with a single owned,
  versioned schema. There is no multi-surface-form input to canonicalize — nothing analogous
  to the `Description` / `Overview` / `Summary` heading-synonym problem that justifies
  `normalize-issues`.
- It is **not raw scraping**: `ui-tests.json` is already a first-class, schema-versioned
  ecosystem contract that this repo's `coverage-matrix` service consumes directly as
  `--tests-input`. The "toolkit is in the path" intent — a stable, owned contract between
  collector and generator — is satisfied by the schema, not by an extra copy step.
- A `normalize-test-catalog` pass with no normalization rule to apply would only re-wrap
  identical bytes in a `meta` envelope. That is ceremony, not provenance: it adds a service,
  a CLI command, a schema, and a test surface for zero transformation.

If a concrete catalog-level normalization need appears later (e.g. tag-grammar canonicalization,
cross-source ID reconciliation), revisit as option (b): a thin `normalize-test-catalog` service
producing a `test-catalog-ready.json` with a `meta.audit` envelope consistent with
`generator-ready.json`.

### `coverage-matrix` — `coverage-matrix.json` is toolkit-produced (rule satisfied)

`doc-source.json` + `ui-tests.json` → `living-doc coverage-matrix` → `coverage-matrix.json`.
The artifact is produced by this repo's `coverage_matrix` service, so a generator consuming it
for `document-type: coverage-matrix` never touches a collector output — the rule is satisfied.

**Provenance-envelope decision: not added in v1.0.0.** `coverage-matrix.json` carries
`schema_version` and `generated_at` but no `meta.audit` envelope. It is not added now because:

- the output is a deterministic join of two already-provenanced inputs; the useful provenance
  (collector producer/version, run context) lives in those inputs, and no generator consumes
  an upstream-provenance envelope from `coverage-matrix.json` today;
- adding `meta.audit` is a **purely additive** change (new optional object — *Safe to change*
  under [Change Control](#change-control)), so it can be introduced without a major bump the
  moment a consumer needs upstream provenance parity with `generator-ready.json`.

Tracked as a follow-up: add a `meta.audit` envelope to `coverage-matrix.json` (mapping
`doc-source.json` / `ui-tests.json` producer metadata + a `coverage-matrix` `trace[]` step)
when a generator requires it. This is net-new work — the loader, the `coverage_matrix` model,
and the output schema/serializer carry no provenance fields today.

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
│   ├── view (optional) { view, filtered_user_stories, filtered_acceptance_criteria }
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

### Content Views

`normalize-issues` renders one of two views, selected with `--view` (default `inner`).
The view is a toolkit-level decision, not a per-generator input — the same
`generator-ready.json` contract is produced either way.

| View | Purpose | Filtering |
|------|---------|-----------|
| `inner` (default) | Comprehensive internal documentation | None — every entity and acceptance criterion from the input is kept |
| `release` | Public-facing documentation | Drop rules below are applied |

**`release` drop rules** (state comparison is case-insensitive; `-` and spaces fold to `_`,
so `In Review` == `in-review` == `in_review`):

- **Entities** (`content.user_stories[]`) whose `state` is `planned` or `in_review` are
  removed entirely, along with their acceptance criteria.
- **Acceptance criteria** (`sections.acceptance_criteria[]`) whose `state` is `planned` or
  `in_review` are dropped from entities that are kept.
- `deprecated` acceptance criteria are **kept** — they describe behaviour that shipped and
  is still part of the solution. Likewise a `deprecated` **entity** is not dropped (only
  `planned` / `in_review` entities are), so its acceptance criteria survive `release`. Only
  not-yet-real content (`planned` / `in_review`) is release-hidden.

**Provenance.** Every output records the applied view at `meta.view`:

| Field | Type | Description |
|-------|------|-------------|
| `view` | string | `inner` or `release` |
| `filtered_user_stories` | int ≥ 0 | Entities removed by the view (`0` for `inner`) |
| `filtered_acceptance_criteria` | int ≥ 0 | Acceptance criteria removed from kept entities (`0` for `inner`) |

`meta.selection_summary.excluded_items` also reflects entities removed by the view
(`total_items` counts the input entities, `included_items` the ones written).

---

## Output Contract: `coverage-matrix.json`

**Schema version:** `"coverage-matrix-v1.0.0"` (field `schema_version`)

Produced by `living-doc coverage-matrix`. Consumed by downstream PDF / reporting generators,
which read the coverage data only — none consumes an upstream-provenance envelope from it
today (see [Generator Inputs by `document-type`](#generator-inputs-by-document-type)).

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
