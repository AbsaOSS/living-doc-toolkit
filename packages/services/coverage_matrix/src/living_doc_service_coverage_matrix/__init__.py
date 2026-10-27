# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `coverage-matrix` transform: one `doc-source.json` and one `ui-tests.json` input to `coverage-matrix.json`.

`builder` counts each acceptance criterion's linked scenarios, `lineage` holds the command's lineage table over both
inputs, and `service` runs validation, field-loss checking, and the write.
"""

__version__ = "0.1.0"

__all__ = [
    "__version__",
]
