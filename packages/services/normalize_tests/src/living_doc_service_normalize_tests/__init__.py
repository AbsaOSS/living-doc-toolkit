# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `normalize-tests` transform: one `ui-tests.json` input to `ui-test-catalog.json`.

`builder` groups the validated scenarios, `lineage` holds the command's lineage table, and `service` runs validation,
field-loss checking, and the write.
"""

__version__ = "0.1.0"

__all__ = [
    "__version__",
]
