# Normalize-Issues Service — Cookbook

**Service:** `normalize-issues`  
**Command:** `living-doc normalize-issues`  
**Purpose:** Convert collector output (`doc-issues.json`) into PDF-ready canonical JSON (`pdf_ready.json`)

---

## What It Does (Overview)

The `normalize-issues` service transforms machine-readable artifacts produced by upstream collectors (e.g., `AbsaOSS/living-doc-collector-gh`) into a canonical, PDF-ready JSON format compliant with `AbsaOSS/living-doc-generator-pdf` SPEC v1.0.

**Pipeline Overview (SPEC.md §1.2, §5.1):**
1. Load and parse input JSON (`doc-issues.json`)
2. Detect producer adapter (auto-detection or explicit selection)
3. Check version compatibility (warn if outside confirmed range)
4. Parse input into internal representation (`AdapterResult`)
5. Normalize markdown sections using heading synonyms
6. Build `pdf_ready.json` structure with canonical fields
7. Augment audit envelope with builder trace step
8. Validate output against JSON Schema
9. Write output file
10. Log summary and warnings

**Key Features:**
- **Adapter-driven input detection**: Automatically identifies producer based on metadata
- **Version compatibility checking**: Warns about version mismatches but attempts processing
- **Markdown normalization**: Maps issue body headings to canonical section keys
- **Audit trail preservation**: Maintains enterprise-level provenance tracking
- **Schema validation**: Ensures output conforms to generator contract

---

## How Detection Works (Adapter Selection)

### Auto-Detection (SPEC.md §3.2.1, §5.2)

When `--source auto` is used (default), the service automatically detects the producer by examining the `metadata.generator.name` field in the input JSON:

```python
if payload["metadata"]["generator"]["name"] == "AbsaOSS/living-doc-collector-gh":
    adapter = CollectorGhAdapter()
```

**Required Fields for Detection:**
- `metadata.generator.name` — Producer identifier (e.g., `"AbsaOSS/living-doc-collector-gh"`)
- `metadata.generator.version` — Producer version (semver format, e.g., `"1.2.0"`)

### Explicit Adapter Selection

Use `--source collector-gh` to explicitly select the collector-gh adapter without auto-detection:

```bash
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --source collector-gh
```

This is useful when:
- You know the input format in advance
- You want to skip detection overhead
- You're debugging adapter-specific behavior

---

## How Compatibility Checking Works (Version Ranges)

### Confirmed Compatible Range (SPEC.md §3.2.2, §5.4)

**Adapter:** `collector-gh`  
**Confirmed Range:** `>=1.0.0,<2.0.0`

The service uses semantic versioning to determine compatibility:

| Producer Version | Behavior |
|------------------|----------|
| `1.0.0` - `1.99.99` | ✅ Proceed silently (within confirmed range) |
| `0.9.0` or earlier | ⚠️ Log warning, add to `audit.trace[].warnings[]`, attempt processing |
| `2.0.0` or later | ⚠️ Log warning, add to `audit.trace[].warnings[]`, attempt processing |

**Fail-Safe Policy:**
- Versions **within range**: Proceed silently
- Versions **outside range**: Log warning, add warning to audit trace, **still attempt processing** with newest adapter logic
- **Critically incompatible**: Exit with `Adapter error:` if schema is unrecognizable

This policy ensures:
- Collectors can be updated without breaking existing pipelines
- Version mismatches are visible in audit trail
- Processing continues unless fundamentally incompatible

---

## How Audit Is Preserved and Augmented (Trace Steps)

### Adapter Mapping (SPEC.md §3.4.3)

The adapter maps collector metadata to the audit envelope:

```
metadata.generator.*   → audit.producer.*
metadata.run.*         → audit.run.*
metadata.source.*      → audit.source.*
```

**Example:**
```json
{
  "metadata": {
    "generator": {
      "name": "AbsaOSS/living-doc-collector-gh",
      "version": "1.2.0",
      "build": "abc123"
    }
  }
}
```

Becomes:
```json
{
  "meta": {
    "audit": {
      "producer": {
        "name": "AbsaOSS/living-doc-collector-gh",
        "version": "1.2.0",
        "build": "abc123"
      }
    }
  }
}
```

### Original Metadata Preservation

The full original `metadata` object is stored in the audit extensions:

```json
{
  "meta": {
    "audit": {
      "extensions": {
        "collector-gh": {
          "original_metadata": { /* full original metadata */ }
        }
      }
    }
  }
}
```

### Builder Trace Step

The service appends a normalization trace step to `audit.trace[]`:

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

This creates a complete audit trail from collection → normalization → generation.

---

## How to Interpret Warnings

### VERSION_MISMATCH Warning (SPEC.md §3.2.2, §5.4)

When the producer version is outside the confirmed range, a warning is logged and added to the audit trace:

```json
{
  "code": "VERSION_MISMATCH",
  "message": "Producer version 2.1.0 is outside confirmed range >=1.0.0,<2.0.0",
  "context": "metadata.generator.version"
}
```

**What to do:**
1. **Check the output**: Verify that the normalized data is correct
2. **Review the audit trail**: Inspect `audit.trace[].warnings[]` for details
3. **Consider upgrading**: Update to a compatible collector version if possible
4. **Report issues**: If processing fails or produces incorrect output, report to the toolkit maintainers

**Example Warning Output:**
```
[WARNING] Producer version 2.1.0 is outside confirmed range >=1.0.0,<2.0.0
[WARNING] Attempting processing with newest adapter logic
```

---

## Troubleshooting (Common Errors)

### Exit Code 1: Invalid Input (SPEC.md §3.1.2)

**Error Prefix:** `Invalid input:`

**Common Causes:**
- File not found: `--input` path does not exist
- Malformed JSON: Syntax errors in input file
- Missing required fields: Input lacks `metadata.generator.name`

**Example:**
```
Invalid input: File 'doc-issues.json' not found. Ensure --input points to a valid file.
```

**Solutions:**
- Verify the input file path exists: `ls -l doc-issues.json`
- Validate JSON syntax: `jq . doc-issues.json`
- Check file permissions: Ensure the file is readable

---

### Exit Code 2: Adapter Error (SPEC.md §3.1.2)

**Error Prefix:** `Adapter error:`

**Common Causes:**
- No compatible adapter found: `metadata.generator.name` does not match any known producer
- Missing metadata: Input lacks `metadata.generator` section

**Example:**
```
Adapter error: No compatible adapter found for input. Check metadata.generator.name field.
```

**Solutions:**
- Inspect `metadata.generator.name`: `jq .metadata.generator.name doc-issues.json`
- Verify input is from `AbsaOSS/living-doc-collector-gh`
- Use `--source collector-gh` to explicitly select adapter

---

### Exit Code 3: Schema Validation Failed (SPEC.md §3.1.2)

**Error Prefix:** `Schema validation failed:`

**Common Causes:**
- Missing required fields in output (e.g., `schema_version`, `meta.document_title`)
- Invalid data types (e.g., string where integer expected)
- **This indicates a builder bug** — output generation logic failed

**Example:**
```
Schema validation failed: Missing required field 'schema_version' in output. This is a builder bug.
```

**Solutions:**
- **Report the issue**: This is a bug in the toolkit
- Include the input file and error message in the bug report
- Check if a newer version of the toolkit fixes the issue

---

### Exit Code 4: Normalization Failed (SPEC.md §3.1.2)

**Error Prefix:** `Normalization failed:`

**Common Causes:**
- Malformed markdown in issue body (e.g., unclosed tags, broken tables)
- Extremely large markdown content causing parser issues

**Example:**
```
Normalization failed: Unable to parse markdown in issue #42 body. Check for malformed content.
```

**Solutions:**
- Review the issue body markdown: `jq '.issues[] | select(.number == 42) | .body' doc-issues.json`
- Fix markdown syntax errors (unclosed tags, broken links)
- Simplify complex markdown (split large tables, reduce nesting)

---

### Exit Code 5: File I/O Error (SPEC.md §3.1.2)

**Error Prefix:** `File I/O error:`

**Common Causes:**
- Permission denied: Cannot write to output path
- Disk full: No space available
- Invalid output path: Directory does not exist

**Example:**
```
File I/O error: Cannot write to 'outputs/pdf_ready.json'. Ensure output directory exists and is writable.
```

**Solutions:**
- Check output directory exists: `mkdir -p outputs/`
- Verify write permissions: `ls -ld outputs/`
- Check disk space: `df -h`

---

## Markdown Normalization Rules

### Heading Synonym Mapping (SPEC.md §3.3.3)

The service normalizes issue body headings to canonical section keys using case-insensitive matching:

| Input Headings | Canonical Section |
|----------------|-------------------|
| `Description`, `Overview`, `Summary` | `description` |
| `Business Value`, `Value`, `Why` | `business_value` |
| `Preconditions`, `Prerequisites`, `Setup` | `preconditions` |
| `Acceptance Criteria`, `AC`, `Done Criteria` | `acceptance_criteria` |
| `User Guide`, `How To`, `Instructions` | `user_guide` |
| `Connections`, `Related`, `Links` | `connections` |
| `Last Edited`, `History`, `Changes` | `last_edited` |

### Example Markdown Normalization

**Input (Issue Body):**
```markdown
## Description
As a user, I want to log in using SSO.

## Business Value
Reduces friction for enterprise users.

## Acceptance Criteria
- User can click SSO button
- Redirect to SSO provider
- Return with session token
```

**Output (Normalized Sections):**
```json
{
  "sections": {
    "description": "As a user, I want to log in using SSO.",
    "business_value": "Reduces friction for enterprise users.",
    "acceptance_criteria": "- User can click SSO button\n- Redirect to SSO provider\n- Return with session token"
  }
}
```

### Unknown Headings

Headings that don't match known synonyms are appended to `description` in structured form:

**Input:**
```markdown
## Description
Main content here.

## Custom Section
Additional information.
```

**Output:**
```json
{
  "sections": {
    "description": "Main content here.\n\n### Custom Section\nAdditional information."
  }
}
```

### Content Before First Heading

Content appearing before the first `##` heading is assigned to `description`:

**Input:**
```markdown
Initial content without heading.

## Business Value
Important value statement.
```

**Output:**
```json
{
  "sections": {
    "description": "Initial content without heading.",
    "business_value": "Important value statement."
  }
}
```

---

## Best Practices

### 1. Use Verbose Mode for Debugging

Enable verbose logging to see detailed processing steps:

```bash
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --verbose
```

### 2. Validate Input Before Processing

Use `jq` to validate JSON syntax and inspect structure:

```bash
# Validate JSON syntax
jq empty doc-issues.json

# Check generator name
jq .metadata.generator.name doc-issues.json

# Count issues
jq '.issues | length' doc-issues.json
```

### 3. Review Audit Trail

After processing, inspect the audit trace for warnings:

```bash
jq .meta.audit.trace pdf_ready.json
```

### 4. Version Pinning

Pin collector and toolkit versions in CI/CD to ensure reproducibility:

```yaml
- name: Install living-doc-toolkit
  run: pip install living-doc-toolkit==0.1.0
```

---

## Additional Resources

- **SPEC.md**: Full system specification
- **Troubleshooting Guide**: `docs/troubleshooting.md`
- **Local Usage Recipe**: `docs/recipes/local-normalize-issues.md`
- **GitHub Actions Recipe**: `docs/recipes/github-actions-normalize-issues.yml`
- **Architecture Overview**: `docs/architecture.md`
