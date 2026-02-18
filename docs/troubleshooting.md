# Troubleshooting Guide

**Purpose:** Comprehensive guide for diagnosing and resolving common issues with the Living Documentation Toolkit.

---

## Table of Contents

1. [Exit Codes Reference](#exit-codes-reference)
2. [Common Errors](#common-errors)
3. [Version Mismatch Warnings](#version-mismatch-warnings)
4. [Verbose Logging](#verbose-logging)
5. [FAQ](#faq)

---

## Exit Codes Reference

All toolkit services follow the exit code convention defined in SPEC.md §3.1.2:

| Exit Code | Condition | Error Prefix | Description |
|-----------|-----------|--------------|-------------|
| **0** | Success | - | Operation completed successfully |
| **1** | Invalid input | `Invalid input:` | File not found, malformed JSON, missing required fields |
| **2** | Adapter error | `Adapter error:` | No compatible adapter found for input |
| **3** | Schema validation | `Schema validation failed:` | Output validation failure (builder bug) |
| **4** | Normalization error | `Normalization failed:` | Markdown parsing or section mapping failure |
| **5** | File I/O error | `File I/O error:` | Cannot write output file |

---

## Common Errors

### Exit 0: Success ✅

**Message:**
```
Successfully normalized {input} -> {output}
```

**What it means:**
- Input file was successfully parsed
- All sections were normalized
- Output file was written and validated
- No errors or critical warnings

**What to do:**
- Review the output file: `jq . {output}`
- Check audit trail for any warnings: `jq .meta.audit.trace[].warnings {output}`
- Proceed to the next pipeline stage (e.g., PDF generation)

---

### Exit 1: Invalid Input ❌

**Error Prefix:** `Invalid input:`

#### Error: File Not Found

**Message:**
```
Invalid input: File 'doc-issues.json' not found. Ensure --input points to a valid file.
```

**Causes:**
- Input file path is incorrect
- File does not exist
- Permission denied (cannot read file)

**Solutions:**

1. **Verify file exists:**
   ```bash
   ls -l doc-issues.json
   ```

2. **Use absolute path:**
   ```bash
   living-doc normalize-issues \
     --input "$(pwd)/doc-issues.json" \
     --output pdf_ready.json
   ```

3. **Check file permissions:**
   ```bash
   chmod +r doc-issues.json
   ```

#### Error: Malformed JSON

**Message:**
```
Invalid input: Malformed JSON in 'doc-issues.json'. Ensure the file contains valid JSON.
```

**Causes:**
- Syntax errors in JSON (missing commas, brackets, quotes)
- Non-UTF-8 encoding
- Truncated file (incomplete download or write)

**Solutions:**

1. **Validate JSON syntax:**
   ```bash
   jq empty doc-issues.json
   ```

2. **Check for syntax errors:**
   ```bash
   # View error location
   python3 -m json.tool doc-issues.json
   ```

3. **Verify file is complete:**
   ```bash
   # Check file size is non-zero
   du -h doc-issues.json
   
   # View last few lines
   tail doc-issues.json
   ```

4. **Re-download or regenerate the input file**

#### Error: Missing Required Fields

**Message:**
```
Invalid input: Missing required field 'metadata.generator.name'. Check input structure.
```

**Causes:**
- Input file is not from a recognized collector
- Collector output is corrupted or incomplete
- Wrong file provided as input

**Solutions:**

1. **Inspect input structure:**
   ```bash
   jq keys doc-issues.json
   jq .metadata doc-issues.json
   ```

2. **Verify generator metadata:**
   ```bash
   jq .metadata.generator doc-issues.json
   ```
   
   Expected output:
   ```json
   {
     "name": "AbsaOSS/living-doc-collector-gh",
     "version": "1.2.0",
     "build": "abc123"
   }
   ```

3. **Regenerate input file with correct collector**

---

### Exit 2: Adapter Error ❌

**Error Prefix:** `Adapter error:`

#### Error: No Compatible Adapter Found

**Message:**
```
Adapter error: No compatible adapter found for input. Check metadata.generator.name field.
```

**Causes:**
- Input file is not from `AbsaOSS/living-doc-collector-gh`
- `metadata.generator.name` field is missing or incorrect
- Input format is unrecognized

**Solutions:**

1. **Check generator name:**
   ```bash
   jq .metadata.generator.name doc-issues.json
   ```
   
   Expected: `"AbsaOSS/living-doc-collector-gh"`

2. **Use explicit adapter selection:**
   ```bash
   living-doc normalize-issues \
     --input doc-issues.json \
     --output pdf_ready.json \
     --source collector-gh
   ```

3. **Verify input is from the correct collector:**
   - Re-run the collector action
   - Check collector version is supported (`>=1.0.0,<2.0.0`)

---

### Exit 3: Schema Validation Failed ❌

**Error Prefix:** `Schema validation failed:`

#### Error: Missing Required Field

**Message:**
```
Schema validation failed: Missing required field 'schema_version' in output. This is a builder bug.
```

**Causes:**
- **This is a builder bug** — the toolkit failed to generate valid output
- Internal logic error in the service
- Pydantic model validation failure

**Solutions:**

1. **This is a bug — report it:**
   - Go to: https://github.com/AbsaOSS/living-doc-toolkit/issues
   - Create a new issue with:
     - Error message
     - Input file (if possible)
     - Toolkit version: `living-doc --version`
     - Operating system and Python version

2. **Check if a newer version fixes the issue:**
   ```bash
   pip install --upgrade living-doc-toolkit
   ```

3. **Workaround (temporary):**
   - Use an older version of the toolkit
   - Manually edit the output file to add missing fields

**Note:** Schema validation failures indicate a bug in the toolkit, not in your input. Please report these issues.

---

### Exit 4: Normalization Failed ❌

**Error Prefix:** `Normalization failed:`

#### Error: Unable to Parse Markdown

**Message:**
```
Normalization failed: Unable to parse markdown in issue #42 body. Check for malformed content.
```

**Causes:**
- Malformed markdown in issue body (unclosed tags, broken tables)
- Extremely large markdown content
- Special characters causing parser issues

**Solutions:**

1. **Identify the problematic issue:**
   ```bash
   jq '.issues[] | select(.number == 42)' doc-issues.json
   ```

2. **Review the issue body:**
   ```bash
   jq '.issues[] | select(.number == 42) | .body' doc-issues.json
   ```

3. **Check for common markdown errors:**
   - Unclosed HTML tags: `<div>` without `</div>`
   - Broken tables: Misaligned columns
   - Invalid heading syntax: `##Heading` (missing space)

4. **Fix markdown in GitHub:**
   - Edit the issue in GitHub
   - Fix syntax errors
   - Re-run the collector

5. **Enable verbose logging for more details:**
   ```bash
   living-doc normalize-issues \
     --input doc-issues.json \
     --output pdf_ready.json \
     --verbose
   ```

#### Error: Section Mapping Failed

**Message:**
```
Normalization failed: Section mapping failed for issue #42. Unknown heading format.
```

**Causes:**
- Unexpected heading format
- Special characters in heading names
- Nested headings causing conflicts

**Solutions:**

1. **Review heading structure:**
   ```bash
   # Extract headings from issue body
   jq '.issues[] | select(.number == 42) | .body' doc-issues.json | \
     grep "^##"
   ```

2. **Simplify headings:**
   - Use standard heading names (Description, Acceptance Criteria, etc.)
   - Avoid special characters in headings
   - Use consistent heading levels (##, not ###)

3. **Check SPEC.md §3.3.3 for supported heading synonyms**

---

### Exit 5: File I/O Error ❌

**Error Prefix:** `File I/O error:`

#### Error: Cannot Write Output

**Message:**
```
File I/O error: Cannot write to 'outputs/pdf_ready.json'. Ensure output directory exists and is writable.
```

**Causes:**
- Output directory does not exist
- Permission denied (cannot write to directory)
- Disk full
- Invalid path (e.g., `/invalid/path/file.json`)

**Solutions:**

1. **Create output directory:**
   ```bash
   mkdir -p outputs
   ```

2. **Check directory permissions:**
   ```bash
   ls -ld outputs
   chmod +w outputs
   ```

3. **Check disk space:**
   ```bash
   df -h
   ```
   
   If disk is full, free up space or use a different location.

4. **Use absolute path:**
   ```bash
   living-doc normalize-issues \
     --input doc-issues.json \
     --output "$(pwd)/pdf_ready.json"
   ```

5. **Test write permissions:**
   ```bash
   touch outputs/test.txt
   rm outputs/test.txt
   ```

---

## Version Mismatch Warnings

### Warning: Producer Version Outside Range

**Message:**
```
[WARNING] Producer version 2.1.0 is outside confirmed range >=1.0.0,<2.0.0
```

**What it means:**
- The collector version is outside the confirmed compatible range
- The service will **still attempt processing** with newest adapter logic
- A warning is added to `audit.trace[].warnings[]`

**What to do:**

1. **Check the output is valid:**
   ```bash
   jq .meta.audit.trace pdf_ready.json
   ```

2. **Review warnings in audit trail:**
   ```bash
   jq '.meta.audit.trace[].warnings' pdf_ready.json
   ```
   
   Expected warning structure:
   ```json
   [
     {
       "code": "VERSION_MISMATCH",
       "message": "Producer version 2.1.0 is outside confirmed range >=1.0.0,<2.0.0",
       "context": "metadata.generator.version"
     }
   ]
   ```

3. **Verify normalized output:**
   - Check that user stories are correctly mapped
   - Verify sections are normalized properly
   - Test with downstream generator

4. **Consider updating:**
   - Update collector to a compatible version (`1.x.x`)
   - Or update toolkit to support newer collector versions
   - Report compatibility issues to maintainers

**Note:** Version warnings are **informational**, not errors. Processing continues unless fundamentally incompatible.

---

## Verbose Logging

### Enable Verbose Mode

Use the `--verbose` flag to see detailed processing steps:

```bash
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --verbose
```

### Verbose Output Example

```
[INFO] Loading input file: doc-issues.json
[INFO] Input file size: 2.4 MB
[INFO] Detected producer: AbsaOSS/living-doc-collector-gh v1.2.0
[INFO] Checking version compatibility...
[INFO] Version 1.2.0 is within confirmed range >=1.0.0,<2.0.0
[INFO] Parsing input with collector-gh adapter
[INFO] Found 42 issues to normalize
[INFO] Normalizing sections for issue #1: User login with SSO
[DEBUG] Mapped heading "Description" -> "description"
[DEBUG] Mapped heading "Acceptance Criteria" -> "acceptance_criteria"
[INFO] Normalizing sections for issue #2: Dashboard redesign
...
[INFO] Building PDF-ready JSON structure
[INFO] Augmenting audit envelope with normalization trace
[INFO] Validating output against schema
[INFO] Writing output file: pdf_ready.json
[INFO] Successfully processed 42 user stories
[INFO] Total processing time: 3.2 seconds
```

### When to Use Verbose Mode

- **Debugging:** When an error occurs and you need more context
- **Development:** When testing new collectors or adapters
- **CI/CD:** When you want detailed logs for audit purposes
- **Performance:** When you need to identify bottlenecks

---

## FAQ

### Q: How do I check which adapter was used?

**A:** Inspect the audit trace in the output:

```bash
jq '.meta.audit.producer' pdf_ready.json
```

Expected output:
```json
{
  "name": "AbsaOSS/living-doc-collector-gh",
  "version": "1.2.0",
  "build": "abc123"
}
```

---

### Q: What if I have issues from multiple sources?

**A:** Currently, the toolkit only supports `collector-gh`. For multiple sources:

1. Run collector separately for each source
2. Normalize each output separately
3. Merge outputs manually or use a custom script

Future versions may support multi-source input.

---

### Q: Can I customize the section mapping?

**A:** Not directly. The section mapping is defined by SPEC.md §3.3.3. However, you can:

1. Use standard heading names in issue bodies
2. Unknown headings are appended to `description`
3. Request new heading synonyms via GitHub issues

---

### Q: How do I verify the output is correct?

**A:** Use these validation steps:

```bash
# 1. Check schema version
jq .schema_version pdf_ready.json

# 2. Count user stories
jq '.content.user_stories | length' pdf_ready.json

# 3. View first user story
jq '.content.user_stories[0]' pdf_ready.json

# 4. Check for warnings
jq '.meta.audit.trace[].warnings' pdf_ready.json

# 5. Validate with Python
python3 << EOF
from living_doc_datasets_pdf.pdf_ready.v1.models import PdfReadyV1
import json

with open('pdf_ready.json') as f:
    data = json.load(f)

model = PdfReadyV1.model_validate(data)
print(f"✅ Valid! {len(model.content.user_stories)} user stories")
EOF
```

---

### Q: What Python version is required?

**A:** Python **3.14** or later is required. Check your version:

```bash
python --version
```

If you need to install Python 3.14, see: https://www.python.org/downloads/

---

### Q: Can I run the toolkit offline?

**A:** Yes, once installed. The toolkit does not make network requests during processing. However, installation requires internet access to download packages from PyPI.

---

### Q: How do I update the toolkit?

**A:** Use pip to upgrade:

```bash
pip install --upgrade living-doc-toolkit
```

Or reinstall from source:

```bash
cd living-doc-toolkit
git pull
pip install -e packages/core packages/datasets_pdf packages/adapters/collector_gh packages/services/normalize_issues apps/cli
```

---

### Q: Where are logs stored?

**A:** Logs are written to stdout/stderr. To save logs to a file:

```bash
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --verbose 2>&1 | tee normalize.log
```

---

### Q: How do I report a bug?

**A:** Create an issue on GitHub:

1. Go to: https://github.com/AbsaOSS/living-doc-toolkit/issues
2. Click "New Issue"
3. Include:
   - Error message
   - Toolkit version: `living-doc --version`
   - Python version: `python --version`
   - Operating system
   - Input file (if possible)
   - Steps to reproduce

---

### Q: What if processing is very slow?

**A:** Performance depends on input size. For large inputs:

1. **Check input size:**
   ```bash
   du -h doc-issues.json
   jq '.issues | length' doc-issues.json
   ```

2. **Expected performance (SPEC.md §5.5):**
   - 100 issues: < 10 seconds
   - 1000 issues: < 60 seconds

3. **If slower than expected:**
   - Check for extremely large issue bodies
   - Check for complex markdown (nested tables, large lists)
   - Report performance issues to maintainers

---

### Q: Can I use the toolkit in a Docker container?

**A:** Yes. Example Dockerfile:

```dockerfile
FROM python:3.14-slim

WORKDIR /app

# Install toolkit
RUN pip install living-doc-toolkit

# Set entrypoint
ENTRYPOINT ["living-doc", "normalize-issues"]
```

Usage:
```bash
docker build -t living-doc-toolkit .
docker run -v $(pwd):/data living-doc-toolkit \
  --input /data/doc-issues.json \
  --output /data/pdf_ready.json
```

---

## Additional Resources

- **Cookbook**: `docs/cookbooks/normalize-issues.md` — Service documentation
- **Local Recipe**: `docs/recipes/local-normalize-issues.md` — Local usage guide
- **GitHub Actions Recipe**: `docs/recipes/github-actions-normalize-issues.yml` — CI/CD integration
- **SPEC.md**: Full system specification
- **GitHub Issues**: https://github.com/AbsaOSS/living-doc-toolkit/issues
