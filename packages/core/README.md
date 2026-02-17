# Living Documentation Core Utilities

Core utilities package for the Living Documentation Toolkit.

## Overview

This package provides reusable, service-agnostic helper utilities including:

- **Error types**: Common exception hierarchy with exit codes
- **JSON utilities**: Reading, writing, and validating JSON files
- **Logging configuration**: Consistent logging setup across services
- **Markdown utilities**: Parsing and normalizing markdown text

## Installation

```bash
pip install -e packages/core
```

## Usage

```python
from living_doc_core import read_json, write_json, setup_logging
from living_doc_core import split_by_headings, normalize_heading
from living_doc_core.errors import FileIOError, InvalidInputError

# Set up logging
logger = setup_logging(verbose=True)

# Read and write JSON
data = read_json("input.json")
write_json("output.json", data)

# Parse markdown
sections = split_by_headings(markdown_text, level=2)
```

## License

Apache License, Version 2.0
