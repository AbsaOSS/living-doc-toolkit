# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Living Documentation Core package: logging, the reader table, the shared input validation and the view filter.

Only logging is exported here. `living_doc_core.readers`, `living_doc_core.input_validation` and
`living_doc_core.views` load the contract models, so they are imported by name, by the code that reads inputs.
"""

__version__ = "0.1.0"

from living_doc_core.logging_config import setup_logging

__all__ = [
    "__version__",
    "setup_logging",
]
