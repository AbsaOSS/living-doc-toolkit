# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Living Documentation Core package: logging, the shared envelope, the reader table, the shared input validation, the
view filter and the CI run context.

Only logging is exported here. `living_doc_core.envelope`, `living_doc_core.readers`,
`living_doc_core.input_validation`, `living_doc_core.views` and `living_doc_core.run_context` load the contract models,
so they are imported by name, by the code that uses them.
"""

__version__ = "0.1.0"

from living_doc_core.logging_config import setup_logging

__all__ = [
    "__version__",
    "setup_logging",
]
