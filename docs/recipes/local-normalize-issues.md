# Recipe: Local Normalize-Issues Usage

**Goal:** Run the `normalize-issues` service locally to convert collector output into PDF-ready JSON.

**Estimated Time:** 10 minutes

---

## Prerequisites

### Required

- **Python 3.14** or later
- **pip** package manager
- **Git** for cloning the repository

### Verify Prerequisites

```bash
# Check Python version
python --version
# Expected: Python 3.14.x or later

# Check pip
pip --version

# Check Git
git --version
```

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/AbsaOSS/living-doc-toolkit.git
cd living-doc-toolkit
```

### Step 2: Install Core Package

```bash
# Install core utilities
pip install -e packages/core
```

### Step 3: Install Dataset Package

```bash
# Install PDF dataset models
pip install -e packages/datasets_pdf
```

### Step 4: Install Adapter Package

```bash
# Install collector-gh adapter
pip install -e packages/adapters/collector_gh
```

### Step 5: Install Service Package

```bash
# Install normalize-issues service
pip install -e packages/services/normalize_issues
```

### Step 6: Install CLI

```bash
# Install CLI wrapper
pip install -e apps/cli
```

### Verify Installation

```bash
# Check that the CLI is available
living-doc --version

# View help for normalize-issues command
living-doc normalize-issues --help
```

**Expected Output:**
```
Usage: living-doc normalize-issues [OPTIONS]

  Normalize collector output into PDF-ready JSON format.

Options:
  --input PATH                Path to input JSON file  [required]
  --output PATH               Path for output JSON file  [required]
  --source [auto|collector-gh]
                              Producer adapter selection
  --document-title TEXT       Override document title in meta.document_title
  --document-version TEXT     Override document version in meta.document_version
  --verbose                   Enable verbose logging
  --help                      Show this message and exit.
```

---

## Example CLI Invocation

### Basic Usage (SPEC.md §3.1.1)

Convert `doc-issues.json` to `pdf_ready.json` with auto-detection:

```bash
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json
```

### With Custom Document Metadata

Override document title and version:

```bash
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --document-title "Product Requirements - Release 2.1" \
  --document-version "2.1.0"
```

### With Explicit Adapter Selection

Explicitly specify the collector-gh adapter:

```bash
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --source collector-gh
```

### With Verbose Logging

Enable detailed logging for debugging:

```bash
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --verbose
```

### Complete Example with All Options

```bash
living-doc normalize-issues \
  --input /path/to/input/doc-issues.json \
  --output /path/to/output/pdf_ready.json \
  --source auto \
  --document-title "Sprint 5 User Stories" \
  --document-version "1.5.0" \
  --verbose
```

---

## Expected Output

### Success Message

When processing completes successfully:

```
Successfully normalized /path/to/input/doc-issues.json -> /path/to/output/pdf_ready.json
```

**Exit Code:** `0`

### Output File Structure (SPEC.md §3.3.4)

The generated `pdf_ready.json` follows this structure:

```json
{
  "schema_version": "1.0",
  "meta": {
    "document_title": "Product Requirements - Release 2.1",
    "document_version": "2.1.0",
    "generated_at": "2026-02-18T10:30:00Z",
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
          "started_at": "2026-02-18T10:25:00Z",
          "finished_at": "2026-02-18T10:28:00Z",
          "warnings": []
        },
        {
          "step": "normalization",
          "tool": "living-doc-toolkit",
          "tool_version": "0.1.0",
          "started_at": "2026-02-18T10:30:00Z",
          "finished_at": "2026-02-18T10:30:05Z",
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

---

## How to Verify Output

### Method 1: Manual Inspection

Use `jq` to inspect the output:

```bash
# View schema version
jq .schema_version pdf_ready.json

# View document metadata
jq .meta pdf_ready.json

# Count user stories
jq '.content.user_stories | length' pdf_ready.json

# View first user story
jq '.content.user_stories[0]' pdf_ready.json
```

### Method 2: Schema Validation (Python)

Validate the output against the `PdfReadyV1` model:

```python
from living_doc_datasets_pdf.pdf_ready.v1.models import PdfReadyV1
import json

# Load the output
with open('pdf_ready.json', 'r') as f:
    data = json.load(f)

# Validate against schema
try:
    model = PdfReadyV1.model_validate(data)
    print("✅ Output is valid!")
    print(f"Document: {model.meta.document_title} v{model.meta.document_version}")
    print(f"User stories: {len(model.content.user_stories)}")
except Exception as e:
    print(f"❌ Validation failed: {e}")
```

### Method 3: Check Audit Trail

Verify the audit trace contains normalization step:

```bash
# View audit trace
jq .meta.audit.trace pdf_ready.json

# Check for warnings
jq '.meta.audit.trace[].warnings' pdf_ready.json
```

**Expected Trace:**
```json
[
  {
    "step": "collection",
    "tool": "living-doc-collector-gh",
    "tool_version": "1.2.0",
    ...
  },
  {
    "step": "normalization",
    "tool": "living-doc-toolkit",
    "tool_version": "0.1.0",
    ...
  }
]
```

---

## Common Issues and Solutions

### Issue: "Command not found: living-doc"

**Cause:** CLI not installed or not in PATH

**Solution:**
```bash
# Reinstall CLI
pip install -e apps/cli

# Or add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

---

### Issue: "Invalid input: File not found"

**Cause:** Input file path is incorrect

**Solution:**
```bash
# Verify file exists
ls -l doc-issues.json

# Use absolute path
living-doc normalize-issues \
  --input "$(pwd)/doc-issues.json" \
  --output pdf_ready.json
```

---

### Issue: "Adapter error: No compatible adapter found"

**Cause:** Input file is not from a recognized collector

**Solution:**
```bash
# Check generator name
jq .metadata.generator.name doc-issues.json

# Should output: "AbsaOSS/living-doc-collector-gh"

# If missing, input is not from collector-gh
```

---

### Issue: Version mismatch warning

**Output:**
```
[WARNING] Producer version 2.1.0 is outside confirmed range >=1.0.0,<2.0.0
```

**Cause:** Collector version is outside confirmed range

**Solution:**
- Check the output is still valid: `jq .meta.audit.trace pdf_ready.json`
- Review warnings: `jq '.meta.audit.trace[].warnings' pdf_ready.json`
- Update collector to compatible version if needed

---

## Next Steps

### Chain with PDF Generator

After normalization, generate a PDF document:

```bash
# Run normalize-issues
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json

# Use output with living-doc-generator-pdf
# (See living-doc-generator-pdf documentation)
```

### Integrate into CI/CD

See `docs/recipes/github-actions-normalize-issues.yml` for GitHub Actions integration.

### Customize Document Metadata

Override title and version to match your release cycle:

```bash
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --document-title "Sprint $(date +%Y-%m) User Stories" \
  --document-version "$(git describe --tags)"
```

---

## Additional Resources

- **Cookbook**: `docs/cookbooks/normalize-issues.md` — Detailed service documentation
- **Troubleshooting**: `docs/troubleshooting.md` — Common errors and solutions
- **SPEC.md**: Full system specification
- **GitHub Actions Recipe**: `docs/recipes/github-actions-normalize-issues.yml`
