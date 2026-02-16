# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Common error types for the Living Documentation Toolkit.

Based on SPEC.md section 3.1.2.
"""


class ToolkitError(Exception):
    """Base exception for all toolkit errors."""

    exit_code: int = 1

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidInputError(ToolkitError):
    """Invalid input (missing file, malformed JSON). Exit code 1."""

    exit_code = 1


class AdapterError(ToolkitError):
    """Adapter detection failed. Exit code 2."""

    exit_code = 2


class SchemaValidationError(ToolkitError):
    """Schema validation failure (output). Exit code 3."""

    exit_code = 3


class NormalizationError(ToolkitError):
    """Normalization error (parsing failure). Exit code 4."""

    exit_code = 4


class FileIOError(ToolkitError):
    """File I/O error (write failure). Exit code 5."""

    exit_code = 5
