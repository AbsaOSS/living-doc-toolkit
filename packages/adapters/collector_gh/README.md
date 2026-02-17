# Living Doc Adapter - Collector-GH

**Version:** 1.0.0  
**License:** Apache-2.0  
**Author:** AbsaOSS

## Overview

The `living-doc-adapter-collector-gh` package provides adapter functionality to detect and parse input from the [living-doc-collector-gh](https://github.com/AbsaOSS/living-doc-collector-gh) GitHub Action.

This adapter is part of the Living Documentation Toolkit and is used by the normalize-issues service to transform collector output into a standardized format.

## Features

- **Producer Detection**: Automatically detects if input is from collector-gh
- **Version Compatibility**: Validates producer version against confirmed range (>=1.0.0, <2.0.0)
- **Input Parsing**: Transforms collector-gh output into structured `AdapterResult` format
- **Metadata Preservation**: Maintains original metadata for audit trail
- **Type Safety**: Full Pydantic model validation with type hints

## Installation

```bash
pip install -e packages/adapters/collector_gh
```

Or as a dependency:

```toml
[project]
dependencies = [
    "living-doc-adapter-collector-gh @ file://packages/adapters/collector_gh"
]
```

## Usage

### Basic Usage

```python
from living_doc_adapter_collector_gh import can_handle, parse

# Load collector-gh output
import json
with open('doc-issues.json') as f:
    payload = json.load(f)

# Check if adapter can handle this input
if can_handle(payload):
    # Parse the input
    result = parse(payload)
    
    # Access parsed items
    for item in result.items:
        print(f"ID: {item.id}")
        print(f"Title: {item.title}")
        print(f"State: {item.state}")
        print(f"Tags: {', '.join(item.tags)}")
        print(f"URL: {item.url}")
        print()
    
    # Check for warnings
    if result.warnings:
        for warning in result.warnings:
            print(f"Warning [{warning.code}]: {warning.message}")
```

### Version Checking

```python
from living_doc_adapter_collector_gh import check_compatibility

version = "1.5.0"
warnings = check_compatibility(version)

if warnings:
    for warning in warnings:
        print(f"Compatibility issue: {warning.message}")
else:
    print("Version is compatible")
```

### Extracting Version

```python
from living_doc_adapter_collector_gh import extract_version
from living_doc_core.errors import AdapterError

try:
    version = extract_version(payload)
    print(f"Producer version: {version}")
except AdapterError as e:
    print(f"Error: {e.message}")
```

## Data Models

### AdapterResult

Complete output from the adapter:

```python
@dataclass
class AdapterResult:
    items: list[AdapterItem]           # Parsed items/issues
    metadata: AdapterMetadata          # Producer metadata
    warnings: list[CompatibilityWarning]  # Compatibility warnings
```

### AdapterItem

Represents a single parsed item (issue):

```python
@dataclass
class AdapterItem:
    id: str                           # Format: "github:owner/repo#123"
    title: str                        # Issue title
    state: str                        # "open" or "closed"
    tags: list[str]                   # Labels/tags
    url: str                          # GitHub issue URL
    timestamps: AdapterItemTimestamps # Created/updated times
    body: str | None                  # Issue body content
```

### AdapterMetadata

Metadata from the collector:

```python
@dataclass
class AdapterMetadata:
    producer: AdapterMetadataProducer  # Generator info
    run: AdapterMetadataRun           # CI run info
    source: AdapterMetadataSource     # Source repository info
    original_metadata: dict           # Full original metadata
```

### CompatibilityWarning

Warning about version compatibility:

```python
@dataclass
class CompatibilityWarning:
    code: str                # "VERSION_MISMATCH" or "INVALID_VERSION"
    message: str             # Human-readable description
    context: str | None      # Context (e.g., field path)
```

## Version Compatibility

The adapter is confirmed compatible with:
- **collector-gh versions**: `>=1.0.0, <2.0.0`

Versions outside this range will generate a `VERSION_MISMATCH` warning, but parsing will still be attempted.

## Error Handling

The adapter uses `AdapterError` from `living-doc-core` for error reporting:

```python
from living_doc_core.errors import AdapterError

try:
    result = parse(payload)
except AdapterError as e:
    print(f"Adapter error: {e.message}")
    exit(e.exit_code)  # Exit code: 2
```

## Testing

Run the test suite:

```bash
pytest tests/ --cov=src --cov-report=term
```

Current test coverage: **98%**

## Development

### Requirements

- Python 3.11+
- pydantic >= 2.10.0
- packaging

### Code Quality

```bash
# Format code
black src/ tests/ --line-length 120

# Lint code
pylint src/living_doc_adapter_collector_gh/*.py --fail-under=9.5

# Type checking
mypy src/living_doc_adapter_collector_gh --python-version 3.14
```

## License

Copyright 2026 ABSA Group Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Contributing

Please refer to the main repository's CONTRIBUTING guidelines.

## Related Packages

- `living-doc-core` - Core utilities and error types
- `living-doc-service-normalize-issues` - Service that uses this adapter
- [living-doc-collector-gh](https://github.com/AbsaOSS/living-doc-collector-gh) - Produces input for this adapter
