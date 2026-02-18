# Recipe: GitHub Actions Integration

**Goal:** Integrate the `normalize-issues` service into a GitHub Actions workflow.

**Estimated Time:** 15 minutes

---

## Overview

This recipe shows how to run the `normalize-issues` service in GitHub Actions, either as a standalone job or as part of a complete living documentation pipeline (Collector → Builder → Generator).

**Workflow File:** `docs/recipes/github-actions-normalize-issues.yml`

---

## Prerequisites

- GitHub repository with Actions enabled
- Input file (`doc-issues.json`) available in the repository or from a previous job
- Write access to repository settings (for workflow configuration)

---

## Basic Workflow Setup

### Step 1: Copy the Workflow File

Copy `docs/recipes/github-actions-normalize-issues.yml` to your repository:

```bash
mkdir -p .github/workflows
cp docs/recipes/github-actions-normalize-issues.yml \
   .github/workflows/normalize-issues.yml
```

### Step 2: Customize the Workflow

Edit `.github/workflows/normalize-issues.yml` to match your needs:

```yaml
name: Normalize Issues

on:
  push:
    branches:
      - main  # Trigger on push to main
  workflow_dispatch:  # Allow manual trigger

jobs:
  normalize-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python 3.14
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
          cache: 'pip'
      
      - name: Install living-doc-toolkit
        run: |
          pip install -e packages/core
          pip install -e packages/datasets_pdf
          pip install -e packages/adapters/collector_gh
          pip install -e packages/services/normalize_issues
          pip install -e apps/cli
      
      - name: Normalize issues
        run: |
          living-doc normalize-issues \
            --input doc-issues.json \
            --output pdf_ready.json \
            --document-title "Product Requirements" \
            --document-version "${{ github.ref_name }}"
      
      - name: Upload PDF-ready JSON
        uses: actions/upload-artifact@v4
        with:
          name: pdf-ready-json
          path: pdf_ready.json
```

### Step 3: Commit and Push

```bash
git add .github/workflows/normalize-issues.yml
git commit -m "Add normalize-issues workflow"
git push
```

### Step 4: Verify Workflow Runs

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Find the "Normalize Issues" workflow
4. Check that it runs successfully
5. Download the `pdf-ready-json` artifact to verify output

---

## Customization Options

### Option 1: Custom Document Title and Version

Override document metadata using workflow inputs:

```yaml
on:
  workflow_dispatch:
    inputs:
      document_title:
        description: 'Document title'
        required: true
        default: 'Product Requirements'
      document_version:
        description: 'Document version'
        required: true
        default: '1.0.0'

jobs:
  normalize-issues:
    steps:
      - name: Normalize issues
        run: |
          living-doc normalize-issues \
            --input doc-issues.json \
            --output pdf_ready.json \
            --document-title "${{ inputs.document_title }}" \
            --document-version "${{ inputs.document_version }}"
```

### Option 2: Dynamic Versioning

Use Git tags or branch names for versioning:

```yaml
- name: Get version from Git
  id: version
  run: echo "version=$(git describe --tags --always)" >> $GITHUB_OUTPUT

- name: Normalize issues
  run: |
    living-doc normalize-issues \
      --input doc-issues.json \
      --output pdf_ready.json \
      --document-version "${{ steps.version.outputs.version }}"
```

### Option 3: Multiple Input Files

Process multiple collector outputs:

```yaml
- name: Normalize multiple files
  run: |
    for input in outputs/*.json; do
      output="normalized/$(basename $input)"
      living-doc normalize-issues \
        --input "$input" \
        --output "$output"
    done
```

---

## Complete Pipeline: Collector → Builder → Generator

The full living documentation pipeline consists of three stages:

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  COLLECTOR  │──────>│   BUILDER   │──────>│  GENERATOR  │
│  (GitHub)   │       │  (Toolkit)  │       │    (PDF)    │
└─────────────┘       └─────────────┘       └─────────────┘
 doc-issues.json      pdf_ready.json      living-doc.pdf
```

### Stage 1: Collector (Collect Issues from GitHub)

```yaml
jobs:
  collect:
    name: Collect Issues
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Collect issues
        uses: AbsaOSS/living-doc-collector-gh@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          output-file: doc-issues.json
          labels: 'documentation'
      
      - name: Upload collector output
        uses: actions/upload-artifact@v4
        with:
          name: collector-output
          path: doc-issues.json
```

### Stage 2: Builder (Normalize Issues)

```yaml
  normalize:
    name: Normalize Issues
    needs: collect
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Download collector output
        uses: actions/download-artifact@v4
        with:
          name: collector-output
      
      - name: Set up Python 3.14
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
          cache: 'pip'
      
      - name: Install living-doc-toolkit
        run: |
          pip install living-doc-toolkit
      
      - name: Normalize issues
        run: |
          living-doc normalize-issues \
            --input doc-issues.json \
            --output pdf_ready.json \
            --document-title "Product Requirements - Sprint ${{ github.run_number }}" \
            --document-version "${{ github.ref_name }}"
      
      - name: Upload PDF-ready JSON
        uses: actions/upload-artifact@v4
        with:
          name: pdf-ready-json
          path: pdf_ready.json
```

### Stage 3: Generator (Generate PDF)

```yaml
  generate:
    name: Generate PDF
    needs: normalize
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Download PDF-ready JSON
        uses: actions/download-artifact@v4
        with:
          name: pdf-ready-json
      
      - name: Generate PDF
        uses: AbsaOSS/living-doc-generator-pdf@v1
        with:
          input-file: pdf_ready.json
          output-file: living-documentation.pdf
      
      - name: Upload PDF
        uses: actions/upload-artifact@v4
        with:
          name: living-documentation
          path: living-documentation.pdf
```

---

## Pipeline Orchestration Patterns

### Pattern 1: Sequential Pipeline (Recommended)

Run stages sequentially with `needs` dependencies:

```yaml
jobs:
  collect:
    # ... collector job
  
  normalize:
    needs: collect
    # ... builder job
  
  generate:
    needs: normalize
    # ... generator job
```

**Pros:**
- Clear dependency chain
- Artifacts passed between stages
- Easy to debug

**Cons:**
- Longer total runtime (sequential execution)

### Pattern 2: Parallel Processing

Process multiple inputs in parallel:

```yaml
jobs:
  collect:
    # ... collect issues from multiple repositories
  
  normalize:
    needs: collect
    strategy:
      matrix:
        repo: [repo1, repo2, repo3]
    steps:
      - name: Normalize ${{ matrix.repo }}
        run: |
          living-doc normalize-issues \
            --input doc-issues-${{ matrix.repo }}.json \
            --output pdf_ready-${{ matrix.repo }}.json
```

### Pattern 3: Scheduled Pipeline

Run the pipeline on a schedule:

```yaml
on:
  schedule:
    - cron: '0 2 * * 1'  # Every Monday at 2 AM UTC
  workflow_dispatch:
```

---

## Error Handling

### Handling Workflow Failures

Add error handling to continue on non-critical failures:

```yaml
- name: Normalize issues
  id: normalize
  continue-on-error: true
  run: |
    living-doc normalize-issues \
      --input doc-issues.json \
      --output pdf_ready.json

- name: Check normalization result
  if: steps.normalize.outcome == 'failure'
  run: |
    echo "❌ Normalization failed"
    echo "Check logs for details"
    exit 1
```

### Retry Logic

Add retries for transient failures:

```yaml
- name: Normalize issues
  uses: nick-fields/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    command: |
      living-doc normalize-issues \
        --input doc-issues.json \
        --output pdf_ready.json
```

---

## Best Practices

### 1. Pin Python Version

Always pin Python to 3.14 to ensure compatibility:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.14'
```

### 2. Cache Dependencies

Enable pip caching to speed up workflow:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.14'
    cache: 'pip'
```

### 3. Use Semantic Versioning

Version your documents using semantic versioning:

```yaml
--document-version "1.2.3"
```

### 4. Store Artifacts

Always upload artifacts for debugging:

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: pdf-ready-json
    path: pdf_ready.json
    retention-days: 30
```

### 5. Enable Verbose Logging

Use `--verbose` flag in workflows for detailed logs:

```yaml
- name: Normalize issues
  run: |
    living-doc normalize-issues \
      --input doc-issues.json \
      --output pdf_ready.json \
      --verbose
```

---

## Troubleshooting

### Issue: "Command not found: living-doc"

**Cause:** Toolkit not installed correctly

**Solution:**
```yaml
- name: Install living-doc-toolkit
  run: |
    pip install --upgrade pip
    pip install living-doc-toolkit
```

### Issue: "File not found: doc-issues.json"

**Cause:** Input file not available from previous job

**Solution:**
```yaml
- name: Download artifact
  uses: actions/download-artifact@v4
  with:
    name: collector-output

- name: Verify input file
  run: ls -l doc-issues.json
```

### Issue: Workflow times out

**Cause:** Large input file or slow processing

**Solution:**
```yaml
- name: Normalize issues
  timeout-minutes: 15
  run: |
    living-doc normalize-issues \
      --input doc-issues.json \
      --output pdf_ready.json
```

---

## Additional Resources

- **Workflow YAML**: `docs/recipes/github-actions-normalize-issues.yml`
- **Cookbook**: `docs/cookbooks/normalize-issues.md`
- **Troubleshooting**: `docs/troubleshooting.md`
- **GitHub Actions Documentation**: https://docs.github.com/en/actions
