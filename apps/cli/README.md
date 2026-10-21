# living-doc-cli

CLI wrapper for the Living Documentation Toolkit: the `living-doc` command group.

No command is registered yet. `normalize-docs`, `normalize-tests` and `coverage-matrix` are added to the group as each
lands; until then the group offers only `--help`, `--version` and `--verbose`.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Show help; it lists no command yet
living-doc --help

# Show version
living-doc --version
```

- `--verbose` is a group option: the group keeps it in its context object for the commands it will run.
- A command name the group does not register yet, such as `living-doc normalize-docs`, fails with click's
  "No such command" and exit code 2.

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
