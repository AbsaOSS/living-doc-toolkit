# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `normalize-docs` transform: one documentation input, `doc-source.json`, to `generator-ready.json`.

`builder` builds the output from the input's contract model, `lineage` holds the command's lineage table, and
`service` runs the command: the shared input validation, the builder, the field-loss check and the write.
"""

__version__ = "0.1.0"

__all__ = [
    "__version__",
]
