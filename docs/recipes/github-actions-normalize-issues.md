# Recipe: GitHub Actions Integration

**Goal:** Integrate the `normalize-issues` service into a GitHub Actions workflow.

**Estimated Time:** 15 minutes

---

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Basic Workflow Setup](#basic-workflow-setup)
- [Customization Options](#customization-options)
- [Complete Pipeline: Collector → Builder → Generator](#complete-pipeline-collector--builder--generator)
- [Pipeline Orchestration Patterns](#pipeline-orchestration-patterns)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

---

## Overview

This recipe shows how to run the `normalize-issues` service in GitHub Actions, either as a standalone job or as part of a complete living documentation pipeline (Collector → Builder → Generator).

Each run is one step of the toolkit's action, `AbsaOSS/living-doc-toolkit@<ref>`. The action installs the toolkit into a venv of its own, so the job needs no `pip install` step. [README § GitHub Action](../../README.md#github-action) lists its inputs and its output.

**Workflow File:** `docs/recipes/github-actions-normalize-issues.yml`

---

## Prerequisites

- GitHub repository with Actions enabled
- A Linux runner, such as `ubuntu-latest`
- Python 3.10 or later on `PATH`, set up with `actions/setup-python` before the action
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

Edit `.github/workflows/normalize-issues.yml` to match your needs, and replace `<ref>` with a release tag or a commit SHA of `living-doc-toolkit`:

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

      - name: Normalize issues
        uses: AbsaOSS/living-doc-toolkit@<ref>
        with:
          command: normalize-issues
          input: doc-issues.json
          output: generator-ready.json
          document-title: Product Requirements

      - name: Upload generator-ready JSON
        uses: actions/upload-artifact@v4
        with:
          name: generator-ready-json
          path: generator-ready.json
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
5. Download the `generator-ready-json` artifact to verify output

---

## Customization Options

### Option 1: Custom Document Title

Set the title from a workflow input:

```yaml
on:
  workflow_dispatch:
    inputs:
      document_title:
        description: 'Document title'
        required: true
        default: 'Product Requirements'

jobs:
  normalize-issues:
    steps:
      - name: Normalize issues
        uses: AbsaOSS/living-doc-toolkit@<ref>
        with:
          command: normalize-issues
          input: doc-issues.json
          output: generator-ready.json
          document-title: ${{ inputs.document_title }}
```

### Option 2: Release View

`view: release` drops planned and in-review entities and ACs. The default view is `inner`:

```yaml
- name: Normalize issues for the release document
  uses: AbsaOSS/living-doc-toolkit@<ref>
  with:
    command: normalize-issues
    input: doc-issues.json
    output: generator-ready.json
    view: release
```

### Option 3: Multiple Input Files

One step runs one command over one file. For several files, run one step per file, or a matrix ([Pattern 2](#pattern-2-parallel-processing)):

```yaml
- name: Normalize the team A issues
  uses: AbsaOSS/living-doc-toolkit@<ref>
  with:
    command: normalize-issues
    input: outputs/team-a.json
    output: normalized/team-a.json

- name: Normalize the team B issues
  uses: AbsaOSS/living-doc-toolkit@<ref>
  with:
    command: normalize-issues
    input: outputs/team-b.json
    output: normalized/team-b.json
```

---

## Complete Pipeline: Collector → Builder → Generator

The full living documentation pipeline consists of three stages:

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  COLLECTOR  │──────>│   BUILDER   │──────>│  GENERATOR  │
│  (GitHub)   │       │  (Toolkit)  │       │    (PDF)    │
└─────────────┘       └─────────────┘       └─────────────┘
 doc-issues.json      generator-ready.json      living-doc.pdf
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
      - name: Download collector output
        uses: actions/download-artifact@v4
        with:
          name: collector-output

      - name: Set up Python 3.14
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Normalize issues
        uses: AbsaOSS/living-doc-toolkit@<ref>
        with:
          command: normalize-issues
          input: doc-issues.json
          output: generator-ready.json
          document-title: Product Requirements - Sprint ${{ github.run_number }}

      - name: Upload generator-ready JSON
        uses: actions/upload-artifact@v4
        with:
          name: generator-ready-json
          path: generator-ready.json
```

### Stage 3: Generator (Generate PDF)

```yaml
  generate:
    name: Generate PDF
    needs: normalize
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Download generator-ready JSON
        uses: actions/download-artifact@v4
        with:
          name: generator-ready-json
      
      - name: Generate PDF
        uses: AbsaOSS/living-doc-generator-pdf@v1
        with:
          input-file: generator-ready.json
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
    runs-on: ubuntu-latest
    strategy:
      matrix:
        repo: [repo1, repo2, repo3]
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Normalize ${{ matrix.repo }}
        uses: AbsaOSS/living-doc-toolkit@<ref>
        with:
          command: normalize-issues
          input: doc-issues-${{ matrix.repo }}.json
          output: generator-ready-${{ matrix.repo }}.json
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

A failed command fails the step with the CLI's own error line and exit code. Add error handling to continue on non-critical failures:

```yaml
- name: Normalize issues
  id: normalize
  continue-on-error: true
  uses: AbsaOSS/living-doc-toolkit@<ref>
  with:
    command: normalize-issues
    input: doc-issues.json
    output: generator-ready.json

- name: Check normalization result
  if: steps.normalize.outcome == 'failure'
  run: |
    echo "❌ Normalization failed"
    echo "Check logs for details"
    exit 1
```

---

## Best Practices

### 1. Pin Python Version

The action needs Python 3.10 or later on `PATH`. Pin the version you test with:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.14'
```

### 2. Pin the Toolkit's Ref

Use a release tag or a commit SHA, not a branch, so a toolkit change does not change your documents unannounced:

```yaml
uses: AbsaOSS/living-doc-toolkit@<release tag or commit SHA>
```

### 3. Store Artifacts

Always upload artifacts for debugging:

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: generator-ready-json
    path: generator-ready.json
    retention-days: 30
```

### 4. Enable Verbose Logging

Set `verbose-logging: 'true'` for detailed logs:

```yaml
- name: Normalize issues
  uses: AbsaOSS/living-doc-toolkit@<ref>
  with:
    command: normalize-issues
    input: doc-issues.json
    output: generator-ready.json
    verbose-logging: 'true'
```

---

## Troubleshooting

### Issue: "living-doc-toolkit needs Python >= 3.10 on PATH"

**Cause:** No `actions/setup-python` before the action, or a Python older than 3.10 on `PATH`

**Solution:**
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.14'
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
  uses: AbsaOSS/living-doc-toolkit@<ref>
  with:
    command: normalize-issues
    input: doc-issues.json
    output: generator-ready.json
```

---

## Additional Resources

- **[Workflow YAML](github-actions-normalize-issues.yml)** — Ready-to-use workflow file
- **[README § GitHub Action](../../README.md#github-action)** — The action's inputs and output
- **[Cookbook: normalize-issues](../cookbooks/normalize-issues.md)** — How detection, compatibility, and normalization work
- **[Troubleshooting](../troubleshooting.md)** — Exit codes, common errors, FAQ
- **[GitHub Actions Documentation](https://docs.github.com/en/actions)** — Official GitHub Actions docs
