# living-doc-cli

CLI wrapper for the Living Documentation Toolkit.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Show help
living-doc --help

# Show version
living-doc --version

# Normalize issues
living-doc normalize-issues --input doc-issues.json --output pdf_ready.json

# With options
living-doc normalize-issues \
  --input doc-issues.json \
  --output pdf_ready.json \
  --source collector-gh \
  --document-title "My Document" \
  --document-version "1.0.0" \
  --verbose
```

## Exit Codes

- 0: Success
- 1: Invalid input (missing file, malformed JSON)
- 2: Adapter detection failed
- 3: Schema validation failure (output)
- 4: Normalization error (parsing failure)
- 5: File I/O error (write failure)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
pylint src/living_doc_cli

# Run type checking
mypy src/living_doc_cli

# Format code
black src/ tests/
```
