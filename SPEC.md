# Living Documentation Toolkit — System Specification

**Version:** 1.0  
**Last Updated:** 2026-01-23  
**Status:** Active  
**Python Runtime:** 3.14

---

## 1. Overview & Scope

### 1.1 Purpose

The Living Documentation Toolkit is a **generic builder** hosting multiple independent Python services that transform and enrich machine-readable artifacts produced by upstream collectors (e.g., `AbsaOSS/living-doc-collector-gh`) into datasets consumable by downstream actions (e.g., `AbsaOSS/living-doc-generator-pdf`).

It is designed as a **monorepo** containing:
- **Multiple services**: Independent, runnable entrypoints (pipelines/capabilities)
- **Adapters**: Input producer detection and parsing (collector action compatibility)
- **Reusable core utilities**: Shared helpers used by all services
- **Versioned contracts**: JSON Schema + Pydantic models for dataset validation
- **Cookbooks and recipes**: Ready-to-use workflow examples for GitHub Actions

### 1.2 Scope

**Current Scope (Service #1):**
- **Service:** `normalize-issues`
- **Goal:** Convert collector output `doc-issues.json` into PDF-ready canonical JSON (`pdf_ready.json`) compliant with `AbsaOSS/living-doc-generator-pdf` SPEC v1.0.

**In Scope:**
- Adapter-based input detection and version compatibility checking
- Markdown normalization into canonical `sections.*` fields
- Enterprise-grade audit trail preservation and augmentation
- JSON Schema validation and Pydantic model enforcement
- CLI wrapper exposing multiple services via subcommands
- Fixture-based verification and golden file testing
- GitHub Actions CI/CD with static analysis and test coverage

**Out of Scope:**
- PDF rendering (belongs to `living-doc-generator-pdf`)
- Source collection and labeling (belongs to collectors)
- "Smart" content generation (analytics, coverage matrices) unless it becomes a new service

### 1.3 Design Principles

1. **Adapter-Driven Input Detection**: Detect producer action by metadata, not file format
2. **Fail-Safe Compatibility**: Warn and attempt when producer version is outside confirmed range
3. **Audit Transparency**: Preserve enterprise-level audit; augment with builder trace
4. **Schema Stability**: Canonical datasets follow versioned contracts
5. **Deterministic Output**: Same input always produces same output (excluding timestamps)
6. **Modular Architecture**: Clear separation of concerns (services, adapters, core, contracts)

---

## 2. Glossary & Invariants

### 2.1 Key Terms

- **Service**: An independent, runnable entrypoint that orchestrates a complete transformation pipeline
- **Adapter**: A module that detects and parses input from a specific producer action (e.g., `collector-gh`)
- **Producer**: An upstream action that generates input artifacts (e.g., `AbsaOSS/living-doc-collector-gh`)
- **Dataset Contract**: A versioned JSON schema + Pydantic model defining canonical output structure
- **Audit Envelope**: Standardized metadata structure preserving provenance and transformation trace
- **Canonical JSON**: Normalized, schema-validated JSON ready for downstream consumption
- **Fixture**: Test input file (e.g., `doc-issues.json`) used for verification and golden file testing
- **Golden File**: Expected output file used for regression testing

### 2.2 Invariants

1. **Adapter Independence**: Services depend on adapters via stable `AdapterResult` interface, not implementation details
2. **Schema Version Stability**: Once published, schema version 1.0 field meanings never change
3. **Audit Preservation**: Original producer audit metadata must never be lost or corrupted
4. **Compatibility Transparency**: Version mismatches produce warnings, not failures (unless critically incompatible)
5. **Output Determinism**: Same input JSON produces same output structure (timestamps excluded)

---

## 3. Interfaces & Contracts

### 3.1 CLI Interface

#### 3.1.1 CLI Name

**Command:** `living-doc`

#### 3.1.2 Service: `normalize-issues`

**Command:**
```bash
living-doc normalize-issues \
  --input <path> \
  --output <path> \
  [--source auto|collector-gh] \
  [--document-title <string>] \
  [--document-version <string>] \
  [--verbose]
```

**Arguments:**

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--input` | path | **Yes** | - | Path to input JSON file (e.g., `doc-issues.json`) |
| `--output` | path | **Yes** | - | Path for output JSON file (e.g., `pdf_ready.json`) |
| `--source` | enum | No | `auto` | Producer adapter selection (`auto`, `collector-gh`) |
| `--document-title` | string | No | _(from input)_ | Override document title in `meta.document_title` |
| `--document-version` | string | No | _(from input)_ | Override document version in `meta.document_version` |
| `--verbose` | flag | No | `false` | Enable verbose logging |

**Exit Codes:**

| Exit Code | Condition | Error Message Prefix |
|-----------|-----------|---------------------|
| 0 | Success | - |
| 1 | Invalid input (missing file, malformed JSON) | `Invalid input:` |
| 2 | Adapter detection failed | `Adapter error:` |
| 3 | Schema validation failure (output) | `Schema validation failed:` |
| 4 | Normalization error (parsing failure) | `Normalization failed:` |
| 5 | File I/O error (write failure) | `File I/O error:` |

**Error Message Format:**
```
{prefix} {specific_detail}. {actionable_guidance}
```

**Examples:**
```
Invalid input: File 'doc-issues.json' not found. Ensure --input points to a valid file.
Adapter error: No compatible adapter found for input. Check metadata.generator.name field.
Schema validation failed: Missing required field 'schema_version' in output. This is a builder bug.
Normalization failed: Unable to parse markdown in issue #42 body. Check for malformed content.
```

#### 3.1.3 Verification Commands (Future)

**Command:**
```bash
living-doc verify normalize-issues --fixture <path>
```

**Purpose:** Run verification against golden fixtures for manual testing and CI validation.

### 3.2 Input Contract: `doc-issues.json` (Collector-GH)

#### 3.2.1 Producer Detection

**Detection Logic:**
```python
if payload.get("metadata", {}).get("generator", {}).get("name") == "AbsaOSS/living-doc-collector-gh":
    adapter = CollectorGhAdapter()
```

**Required Fields for Detection:**
- `metadata.generator.name` (string, non-empty)
- `metadata.generator.version` (string, semver format)

#### 3.2.2 Compatibility Policy

**Adapter:** `collector_gh`

**Confirmed Compatible Range:** `>=1.0.0,<2.0.0`

**Behavior:**
- **Within Range:** Proceed silently
- **Outside Range:** Log warning, add to `audit.trace[].warnings[]`, attempt processing with newest logic
- **Critically Incompatible:** Exit with `Adapter error:` if schema is unrecognizable

**Warning Format:**
```json
{
  "code": "VERSION_MISMATCH",
  "message": "Producer version 2.1.0 is outside confirmed range >=1.0.0,<2.0.0",
  "context": "metadata.generator.version"
}
```

#### 3.2.3 Input Schema (Collector-GH v1.x)

**Example Structure (Minimal):**
```json
{
  "metadata": {
    "generator": {
      "name": "AbsaOSS/living-doc-collector-gh",
      "version": "1.2.0",
      "build": "abc123"
    },
    "run": {
      "run_id": "123456",
      "run_attempt": "1",
      "actor": "user@example.com",
      "workflow": "collect-docs",
      "ref": "refs/heads/main",
      "sha": "abc123def456"
    },
    "source": {
      "systems": ["GitHub"],
      "repositories": ["AbsaOSS/project"],
      "organization": "AbsaOSS",
      "enterprise": null
    }
  },
  "issues": [
    {
      "number": 42,
      "title": "User login with SSO",
      "state": "open",
      "labels": ["documentation", "priority:high"],
      "html_url": "https://github.com/AbsaOSS/project/issues/42",
      "created_at": "2026-01-10T08:00:00Z",
      "updated_at": "2026-01-20T14:30:00Z",
      "body": "## Description\nAs a user, I want to..."
    }
  ]
}
```

### 3.3 Output Contract: `pdf_ready.json` (Generator-PDF v1.0)

**Reference:** [`AbsaOSS/living-doc-generator-pdf` SPEC.md](https://github.com/AbsaOSS/living-doc-generator-pdf/blob/master/SPEC.md)

#### 3.3.1 Schema Version

**Field:** `schema_version`  
**Type:** String  
**Required:** Yes  
**Allowed Values:** `"1.0"`

#### 3.3.2 Metadata Section

**Field:** `meta`  
**Type:** Object  
**Required:** Yes

**Required Fields:**
```json
{
  "document_title": "string (non-empty, 1-200 chars)",
  "document_version": "string (non-empty, 1-50 chars, semver recommended)",
  "generated_at": "ISO 8601 UTC timestamp",
  "source_set": ["array of source identifiers, non-empty"],
  "selection_summary": {
    "total_items": "integer >= 0",
    "included_items": "integer >= 0",
    "excluded_items": "integer >= 0"
  }
}
```

**Optional Fields:**
```json
{
  "run_context": {
    "ci_run_id": "string",
    "triggered_by": "string",
    "branch": "string",
    "commit_sha": "string"
  },
  "audit": {
    "schema_version": "string",
    "producer": {},
    "run": {},
    "source": {},
    "trace": [],
    "extensions": {}
  }
}
```

#### 3.3.3 Content Section

**Field:** `content`  
**Type:** Object  
**Required:** Yes

**Required Fields:**
```json
{
  "user_stories": [
    {
      "id": "string (canonical stable ID, e.g., 'github:owner/repo#123')",
      "title": "string (non-empty, 1-500 chars)",
      "state": "string (e.g., 'open', 'closed')",
      "tags": ["array of strings"],
      "url": "string (valid URL)",
      "timestamps": {
        "created": "ISO 8601 timestamp",
        "updated": "ISO 8601 timestamp"
      },
      "sections": {
        "description": "string (Markdown)",
        "business_value": "string (Markdown, optional)",
        "preconditions": "string (Markdown, optional)",
        "acceptance_criteria": "string (Markdown, optional)",
        "user_guide": "string (Markdown, optional)",
        "connections": "string (Markdown, optional)",
        "last_edited": "string (Markdown, optional)"
      }
    }
  ]
}
```

**Section Mapping Rules:**
- All headings in issue body are considered; mapping must be deterministic
- Known heading synonyms map to canonical keys (case-insensitive):
  - `Description`, `Overview`, `Summary` → `description`
  - `Business Value`, `Value`, `Why` → `business_value`
  - `Preconditions`, `Prerequisites`, `Setup` → `preconditions`
  - `Acceptance Criteria`, `AC`, `Done Criteria` → `acceptance_criteria`
  - `User Guide`, `How To`, `Instructions` → `user_guide`
  - `Connections`, `Related`, `Links` → `connections`
  - `Last Edited`, `History`, `Changes` → `last_edited`
- Unknown headings: Append to `description` in structured form (e.g., `### Unknown Heading\n{content}`)
- Missing sections: Represented as `null` or empty string
- Preserve Markdown formatting (tables, links, lists) for template rendering

#### 3.3.4 Output Example

```json
{
  "schema_version": "1.0",
  "meta": {
    "document_title": "Product Requirements - Release 2.1",
    "document_version": "2.1.0",
    "generated_at": "2026-01-23T12:00:00Z",
    "source_set": ["github:AbsaOSS/project"],
    "selection_summary": {
      "total_items": 15,
      "included_items": 12,
      "excluded_items": 3
    },
    "audit": {
      "schema_version": "1.0",
      "producer": {
        "name": "AbsaOSS/living-doc-collector-gh",
        "version": "1.2.0",
        "build": "abc123"
      },
      "run": {
        "run_id": "123456",
        "run_attempt": "1",
        "actor": "user@example.com",
        "workflow": "collect-docs",
        "ref": "refs/heads/main",
        "sha": "abc123def456"
      },
      "source": {
        "systems": ["GitHub"],
        "repositories": ["AbsaOSS/project"],
        "organization": "AbsaOSS",
        "enterprise": null
      },
      "trace": [
        {
          "step": "collection",
          "tool": "living-doc-collector-gh",
          "tool_version": "1.2.0",
          "started_at": "2026-01-23T11:50:00Z",
          "finished_at": "2026-01-23T11:55:00Z",
          "warnings": []
        },
        {
          "step": "normalization",
          "tool": "living-doc-toolkit",
          "tool_version": "0.1.0",
          "started_at": "2026-01-23T12:00:00Z",
          "finished_at": "2026-01-23T12:00:05Z",
          "warnings": []
        }
      ],
      "extensions": {
        "collector-gh": {
          "original_metadata": {}
        }
      }
    }
  },
  "content": {
    "user_stories": [
      {
        "id": "github:AbsaOSS/project#42",
        "title": "User login with SSO",
        "state": "open",
        "tags": ["authentication", "priority:high"],
        "url": "https://github.com/AbsaOSS/project/issues/42",
        "timestamps": {
          "created": "2026-01-10T08:00:00Z",
          "updated": "2026-01-20T14:30:00Z"
        },
        "sections": {
          "description": "As a user, I want to log in using SSO...",
          "business_value": "Reduces friction for enterprise users",
          "preconditions": "SSO provider configured",
          "acceptance_criteria": "- User can click SSO button\n- Redirect to provider\n- Return with session",
          "user_guide": null,
          "connections": "Related to #41, #43",
          "last_edited": "Updated by alice@example.com on 2026-01-20"
        }
      }
    ]
  }
}
```

### 3.4 Audit Envelope Standard (v1.0)

#### 3.4.1 Purpose

Enterprise-grade audit trail that:
- Preserves collector-level provenance and metadata
- Tracks builder transformation steps
- Records warnings and compatibility issues
- Supports extensibility via namespaced extensions

#### 3.4.2 Schema Structure

**Field:** `meta.audit` (optional in PDF-ready contract)  
**Type:** Object

**Required Fields:**
```json
{
  "schema_version": "string (fixed: '1.0')",
  "producer": {
    "name": "string (required, e.g., 'AbsaOSS/living-doc-collector-gh')",
    "version": "string (required, semver)",
    "build": "string | null"
  },
  "run": {
    "run_id": "string | null",
    "run_attempt": "string | null",
    "actor": "string | null",
    "workflow": "string | null",
    "ref": "string | null",
    "sha": "string | null"
  },
  "source": {
    "systems": ["array of strings, non-empty"],
    "repositories": ["array of strings"],
    "organization": "string | null",
    "enterprise": "string | null"
  },
  "trace": [
    {
      "step": "string (e.g., 'collection', 'normalization')",
      "tool": "string (e.g., 'living-doc-collector-gh')",
      "tool_version": "string (semver)",
      "started_at": "ISO 8601 timestamp | null",
      "finished_at": "ISO 8601 timestamp | null",
      "warnings": [
        {
          "code": "string (e.g., 'VERSION_MISMATCH')",
          "message": "string (human-readable)",
          "context": "string | null (e.g., field path)"
        }
      ]
    }
  ],
  "extensions": {
    "collector-gh": {},
    "builder": {},
    "absa.enterprise": {}
  }
}
```

**Validation Rules:**
- `schema_version`: Required, fixed `"1.0"`
- `producer.name`: Required, non-empty string
- `source.systems`: Required, non-empty array
- `extensions`: Keys must be namespaced strings; values must be JSON objects

#### 3.4.3 Mapping Collector-GH Metadata

**Adapter Responsibility:**
- Map `metadata.generator.*` → `audit.producer.*`
- Map `metadata.run.*` → `audit.run.*`
- Map `metadata.source.*` → `audit.source.*`
- Store full original `metadata` in `audit.extensions["collector-gh"].original_metadata`

**Service Responsibility:**
- Append trace step for normalization:
  ```json
  {
    "step": "normalization",
    "tool": "living-doc-toolkit",
    "tool_version": "{version}",
    "started_at": "{iso_timestamp}",
    "finished_at": "{iso_timestamp}",
    "warnings": []
  }
  ```

---

## 4. Data & Storage Schemas

### 4.1 Repository Layout (Final Structure)

```
repo-root/
  README.md
  SPEC.md                        # This document
  TASKS.md                       # Implementation roadmap
  LICENSE
  pyproject.toml                 # Shared tooling config (ruff/black/mypy)
  
  .github/
    workflows/
      ci.yml                     # Static analysis and tests
      integration.yml            # Fixture-based verification
      release.yml                # Release automation
  
  docs/
    cookbooks/                   # Explainers and guides
      normalize-issues.md
    recipes/                     # Ready-to-use examples
      local-normalize-issues.md
      github-actions-normalize-issues.yml
  
  packages/
    datasets_pdf/                # Dataset contract for PDF generator
      pyproject.toml
      src/living_doc_datasets_pdf/
        __init__.py
        pdf_ready/
          v1/
            __init__.py
            models.py            # Pydantic models
            schema.py            # Schema export helpers
        audit/
          v1/
            __init__.py
            models.py
      schemas/
        pdf_ready_v1.schema.json
        audit_envelope_v1.schema.json
      tests/
        test_pdf_ready_models.py
        test_audit_models.py
    
    core/                        # Shared utilities
      pyproject.toml
      src/living_doc_core/
        __init__.py
        json_utils.py            # JSON read/write helpers
        logging_config.py        # Logging setup
        markdown_utils.py        # Markdown parsing primitives
        errors.py                # Common error types
      tests/
        test_json_utils.py
        test_markdown_utils.py
    
    adapters/
      collector_gh/              # Collector-GH adapter
        pyproject.toml
        src/living_doc_adapter_collector_gh/
          __init__.py
          detector.py            # Producer detection
          parser.py              # Input parsing
          models.py              # AdapterResult models
        tests/
          test_detector.py
          test_parser.py
          fixtures/
            collector_v1.0.0/
              input/
                doc-issues.json
    
    services/
      normalize_issues/          # Normalize-issues service
        pyproject.toml
        src/living_doc_service_normalize_issues/
          __init__.py
          service.py             # Main service logic
          normalizer.py          # Markdown normalization
          builder.py             # PDF-ready JSON builder
        tests/
          test_service.py
          test_normalizer.py
          test_builder.py
        verifications/           # Manual verification scripts
          verify_golden.py
          verify_compatibility.py
  
  apps/
    cli/                         # CLI wrapper
      pyproject.toml
      src/living_doc_cli/
        __init__.py
        main.py                  # CLI entrypoint
        commands/
          normalize_issues.py
      tests/
        test_cli.py
  
  outputs/                       # Gitignored runtime artifacts
    pdf_ready.json
    reports/
```

### 4.2 Output Artifact Location

**Directory:** `outputs/` (gitignored)

**Artifacts:**
- `outputs/pdf_ready.json` - Canonical output
- `outputs/reports/` - Service-specific diagnostic reports (optional)

---

## 5. Algorithms & Rules

### 5.1 Service Pipeline: `normalize-issues`

```
1. Load and parse input JSON
2. Detect producer adapter (auto or explicit)
3. Check version compatibility (warn if outside range)
4. Parse input into AdapterResult
5. Normalize markdown sections
6. Build pdf_ready.json structure
7. Augment audit envelope with builder trace
8. Validate output against schema
9. Write output file
10. Log summary and warnings
```

### 5.2 Adapter Selection Logic

**Mode: `auto`**
```python
for adapter in registered_adapters:
    if adapter.can_handle(payload):
        return adapter
raise AdapterNotFoundError("No compatible adapter found")
```

**Mode: `collector-gh`**
```python
return CollectorGhAdapter()
```

### 5.3 Markdown Normalization Rules

**Input:** Raw markdown string (issue body)  
**Output:** Dictionary of section keys → markdown content

**Algorithm:**
1. Split markdown by `##` headings (H2 level)
2. For each heading:
   - Normalize heading text (lowercase, strip whitespace)
   - Match against known synonyms (see 3.3.3)
   - If match: Assign content to canonical section key
   - If no match: Append to `description` as structured content
3. Preserve Markdown formatting (tables, lists, links)
4. Handle edge cases:
   - Empty sections: `null` or `""`
   - Content before first heading: Assign to `description`
   - Multiple occurrences of same heading: Concatenate with separator

**Determinism:**
- Same markdown input always produces same section mapping
- Order of sections in output dictionary is stable (alphabetical)

### 5.4 Compatibility Warning Logic

**Trigger:** Producer version outside confirmed range

**Action:**
1. Log warning at `WARNING` level
2. Add to `audit.trace[].warnings[]`:
   ```json
   {
     "code": "VERSION_MISMATCH",
     "message": "Producer version X.Y.Z is outside confirmed range A.B.C-D.E.F",
     "context": "metadata.generator.version"
   }
   ```
3. Continue processing with newest adapter logic
4. If parsing fails: Exit with `Adapter error:`

### 5.5 Performance Budgets

| Operation | Target | Maximum |
|-----------|--------|---------|
| JSON parsing (10 MB) | < 1 second | 5 seconds |
| Adapter detection | < 0.1 seconds | 1 second |
| Markdown normalization (100 issues) | < 2 seconds | 10 seconds |
| Output validation | < 1 second | 5 seconds |
| Total service runtime (100 issues) | < 10 seconds | 30 seconds |

**Note:** Budgets assume typical collector-gh output (~500 KB - 10 MB JSON)

---

## 6. Phase-by-Phase Acceptance Criteria

### Phase 1: Repository Structure & Scaffolding

**Acceptance Criteria:**
- [ ] Monorepo directory structure created (packages/, apps/, docs/, outputs/)
- [ ] Root `pyproject.toml` configured with black, mypy, pytest settings
- [ ] `.gitignore` configured (outputs/, `__pycache__`, `.pytest_cache`, etc.)
- [ ] `README.md` updated with project overview and quickstart
- [ ] License file (Apache 2.0) present
- [ ] CODEOWNERS file configured

**Verification:**
- Directory structure matches SPEC section 4.1
- `pyproject.toml` lint checks pass (black --check, mypy .)

### Phase 2: Dataset/Contract Package (`datasets_pdf`)

**Acceptance Criteria:**
- [ ] Pydantic models for `pdf_ready` v1.0 created
- [ ] Pydantic models for `audit` v1.0 created
- [ ] JSON Schema files exported and validated
- [ ] Serialization helpers (deterministic JSON output)
- [ ] Unit tests for model validation (valid/invalid inputs)
- [ ] Test coverage ≥ 80%

**Verification:**
- `tests/packages/datasets_pdf/test_pdf_ready_models.py`
- `tests/packages/datasets_pdf/test_audit_models.py`
- JSON schemas validate correctly against reference examples

### Phase 3: Core Utilities Package

**Acceptance Criteria:**
- [ ] JSON read/write helpers implemented
- [ ] Logging configuration module created
- [ ] Markdown parsing primitives (heading splitter, list parser)
- [ ] Common error types defined
- [ ] Unit tests for all utilities
- [ ] Test coverage ≥ 80%

**Verification:**
- `tests/packages/core/test_json_utils.py`
- `tests/packages/core/test_markdown_utils.py`
- Utilities are reusable and do not encode service-specific logic

### Phase 4: Adapter Package (`collector_gh`)

**Acceptance Criteria:**
- [ ] Producer detection logic implemented
- [ ] Version extraction and compatibility checking
- [ ] Input parsing into `AdapterResult` model
- [ ] Audit metadata mapping (metadata → audit envelope)
- [ ] Unit tests with fixture files (collector v1.0.0, v1.2.0)
- [ ] Test coverage ≥ 80%

**Verification:**
- `tests/packages/adapters/collector_gh/test_detector.py`
- `tests/packages/adapters/collector_gh/test_parser.py`
- Fixture files in `tests/packages/adapters/collector_gh/fixtures/`

### Phase 5: Service Package (`normalize_issues`)

**Acceptance Criteria:**
- [ ] Service orchestration logic implemented
- [ ] Markdown normalization with heading mapping
- [ ] PDF-ready JSON builder with audit augmentation
- [ ] Output schema validation
- [ ] Unit tests for normalization rules
- [ ] Integration tests with golden files
- [ ] Test coverage ≥ 80%

**Verification:**
- `tests/packages/services/normalize_issues/test_service.py`
- `tests/packages/services/normalize_issues/test_normalizer.py`
- Golden file comparison tests

### Phase 6: CLI Wrapper

**Acceptance Criteria:**
- [ ] CLI entrypoint (`living-doc`) implemented
- [ ] `normalize-issues` subcommand with argument parsing
- [ ] Exit codes match specification
- [ ] Error messages follow format (prefix + detail + guidance)
- [ ] Verbose logging option functional
- [ ] Unit tests for CLI argument parsing
- [ ] Integration tests for CLI invocation

**Verification:**
- `tests/apps/cli/test_cli.py`
- Manual CLI invocation tests
- Help text (`--help`) is clear and accurate

### Phase 7: Python CI/CD Workflow

**Acceptance Criteria:**
- [ ] CI workflow configured (`.github/workflows/ci.yml`)
- [ ] Pylint analysis with score threshold ≥ 9.5
- [ ] Black format check
- [ ] Mypy type checking
- [ ] Pytest with coverage ≥ 80%
- [ ] Python 3.14 pinned in workflows
- [ ] Workflows modeled after `living-doc-collector-gh`

**Verification:**
- CI passes on all commits
- All quality gates enforced automatically

### Phase 8: Fixture-Based Verification

**Acceptance Criteria:**
- [ ] Golden fixtures added (collector v1.0.0, v1.2.0)
- [ ] Manual verification scripts (`verifications/verify_golden.py`)
- [ ] Integration test workflow (`.github/workflows/integration.yml`)
- [ ] Verification scripts runnable in CI
- [ ] Compatibility warnings tested with out-of-range versions

**Verification:**
- `verifications/verify_golden.py` runs successfully
- Integration tests pass with multiple collector versions

### Phase 9: Cookbooks & Recipes

**Acceptance Criteria:**
- [ ] Cookbook: `docs/cookbooks/normalize-issues.md` written
- [ ] Recipe: `docs/recipes/local-normalize-issues.md` created
- [ ] Recipe: `docs/recipes/github-actions-normalize-issues.yml` created
- [ ] All recipes tested and verified
- [ ] Documentation includes examples of:
  - Local CLI usage
  - GitHub Actions workflow integration
  - Chaining collector → builder → generator

**Verification:**
- Recipes execute successfully in local and CI environments
- Documentation is clear and includes expected outputs

### Phase 10: Release Preparation

**Acceptance Criteria:**
- [ ] `CHANGELOG.md` created with v0.1.0 notes
- [ ] Version number set in all `pyproject.toml` files
- [ ] Release workflow configured (`.github/workflows/release.yml`)
- [ ] GitHub Release draft created
- [ ] All tests passing
- [ ] Documentation reviewed and complete

**Verification:**
- Release checklist completed
- Version tags consistent across repository
- Release notes include breaking changes and migration guide

---

## 7. Change Control

### 7.1 Versioned Contracts

**Schema Version 1.0 (Immutable):**
- Field names, types, and meanings are **stable**
- New optional fields may be added (backwards compatible)
- Breaking changes require new schema version (2.0)

**Adapter Interface (Stable):**
- `AdapterResult` model signature is stable
- New fields may be added as optional
- Removing fields requires major version bump

**CLI Interface (Stable):**
- Argument names and defaults are stable
- New optional arguments may be added
- Removing arguments requires major version bump

### 7.2 Approval Requirements

**Changes Requiring Review:**
- Schema modifications (datasets_pdf contract)
- Adapter interface changes
- CLI argument changes
- Error message text changes
- Exit code changes
- Performance budget changes

**Changes Not Requiring Special Approval:**
- Internal refactoring (preserving behavior)
- Test additions
- Documentation updates
- Logging improvements

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Coverage Target:** ≥ 80%

**Focus:**
- JSON schema validation
- Markdown normalization rules
- Adapter detection and parsing
- Pydantic model validation
- Error handling and messages

**Tools:**
- `pytest` (testing framework)
- `pytest-cov` (coverage reporting)

### 8.2 Integration Tests

**Focus:**
- End-to-end service execution
- Golden file comparison
- Fixture-based compatibility testing
- CLI invocation and exit codes

### 8.3 Verification Scripts

**Purpose:** Manual validation and CI quality gates

**Scripts:**
- `verifications/verify_golden.py` - Golden file comparison
- `verifications/verify_compatibility.py` - Version compatibility checks
- `verifications/verify_schema.py` - Schema validation against examples

---

## 9. Dependencies

### 9.1 Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic` | `^2.10.0` | Data validation and models |
| `jsonschema` | `^4.20.0` | JSON schema validation |
| `click` | `^8.1.0` | CLI framework |

### 9.2 Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | `^9.0.0` | Testing framework |
| `pytest-cov` | `^7.0.0` | Coverage reporting |
| `black` | `^26.0.0` | Code formatting |
| `pylint` | `^4.0.0` | Code quality |
| `mypy` | `^1.19.0` | Type checking |

**Note:** Version constraints follow patterns from `living-doc-collector-gh`

---

## 10. Security Considerations

### 10.1 Input Validation

- **JSON Injection:** All inputs validated against strict schemas
- **Path Traversal:** File paths validated to prevent directory traversal
- **Resource Exhaustion:** File size limits enforced (50 MB soft limit)

### 10.2 Secrets

- **No Secrets in JSON:** Input/output files must not contain secrets or credentials
- **No API Calls:** Toolkit operates offline (no network calls)

---

## 11. Monitoring & Observability

### 11.1 Logging Levels

| Level | Purpose | Examples |
|-------|---------|----------|
| DEBUG | Detailed diagnostics | "Detected adapter: collector-gh", "Parsed 12 issues" |
| INFO | Normal operation | "Normalization complete", "Output written to pdf_ready.json" |
| WARNING | Non-fatal issues | "Producer version outside confirmed range" |
| ERROR | Fatal failures | "Adapter detection failed", "Schema validation failed" |

### 11.2 Audit Trail

All transformations tracked in `meta.audit.trace[]`:
- Step name (e.g., "normalization")
- Tool name and version
- Start/finish timestamps
- Warnings (compatibility, parsing issues)

---

## 12. Future Extensions

- **Adapter Registry:** Plugin system for new producer adapters
- **Normalizer Plugins:** Custom markdown parsing rules
- **Output Validators:** Pluggable schema validators for different versions

---

## 13. References

### 13.1 Related Specifications

- [Living Documentation PDF Generator SPEC v1.0](https://github.com/AbsaOSS/living-doc-generator-pdf/blob/master/SPEC.md)
- Living Documentation Toolkit Issue #1 (Draft Specification)

### 13.2 External Standards

- [JSON Schema Specification](https://json-schema.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Semantic Versioning](https://semver.org/)
- [ISO 8601 Date/Time Format](https://www.iso.org/iso-8601-date-and-time-format.html)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-23 | Specification Master | Initial specification based on draft and references |

---

**End of Specification**
