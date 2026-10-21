# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Living Documentation Core package: logging, the reader table and the shared input validation.

Only logging is exported here. `living_doc_core.readers` and `living_doc_core.input_validation` load the contract
models, so they are imported by name, by the code that reads inputs.
"""

__version__ = "1.0.0"

from living_doc_core.logging_config import setup_logging

__all__ = [
    "__version__",
    "setup_logging",
]
