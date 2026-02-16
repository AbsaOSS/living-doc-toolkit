# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for error classes.
"""

import pytest

from living_doc_core.errors import (
    AdapterError,
    FileIOError,
    InvalidInputError,
    NormalizationError,
    SchemaValidationError,
    ToolkitError,
)


def test_toolkit_error_can_be_raised():
    """Test that ToolkitError can be raised and caught."""
    with pytest.raises(ToolkitError) as exc_info:
        raise ToolkitError("Test error")
    assert str(exc_info.value) == "Test error"
    assert exc_info.value.exit_code == 1


def test_invalid_input_error_can_be_raised():
    """Test that InvalidInputError can be raised and caught."""
    with pytest.raises(InvalidInputError) as exc_info:
        raise InvalidInputError("Invalid input")
    assert str(exc_info.value) == "Invalid input"
    assert exc_info.value.exit_code == 1


def test_adapter_error_can_be_raised():
    """Test that AdapterError can be raised and caught."""
    with pytest.raises(AdapterError) as exc_info:
        raise AdapterError("Adapter failed")
    assert str(exc_info.value) == "Adapter failed"
    assert exc_info.value.exit_code == 2


def test_schema_validation_error_can_be_raised():
    """Test that SchemaValidationError can be raised and caught."""
    with pytest.raises(SchemaValidationError) as exc_info:
        raise SchemaValidationError("Schema invalid")
    assert str(exc_info.value) == "Schema invalid"
    assert exc_info.value.exit_code == 3


def test_normalization_error_can_be_raised():
    """Test that NormalizationError can be raised and caught."""
    with pytest.raises(NormalizationError) as exc_info:
        raise NormalizationError("Normalization failed")
    assert str(exc_info.value) == "Normalization failed"
    assert exc_info.value.exit_code == 4


def test_file_io_error_can_be_raised():
    """Test that FileIOError can be raised and caught."""
    with pytest.raises(FileIOError) as exc_info:
        raise FileIOError("File error")
    assert str(exc_info.value) == "File error"
    assert exc_info.value.exit_code == 5


def test_all_errors_inherit_from_toolkit_error():
    """Test that all error classes inherit from ToolkitError."""
    assert issubclass(InvalidInputError, ToolkitError)
    assert issubclass(AdapterError, ToolkitError)
    assert issubclass(SchemaValidationError, ToolkitError)
    assert issubclass(NormalizationError, ToolkitError)
    assert issubclass(FileIOError, ToolkitError)


def test_error_exit_codes():
    """Test that error classes have correct exit codes."""
    assert ToolkitError.exit_code == 1
    assert InvalidInputError.exit_code == 1
    assert AdapterError.exit_code == 2
    assert SchemaValidationError.exit_code == 3
    assert NormalizationError.exit_code == 4
    assert FileIOError.exit_code == 5


def test_error_messages_are_preserved():
    """Test that error messages are preserved correctly."""
    error_message = "Detailed error information"
    error = InvalidInputError(error_message)
    assert error.message == error_message
    assert str(error) == error_message


def test_can_catch_specific_error_as_base_class():
    """Test that specific errors can be caught as ToolkitError."""
    with pytest.raises(ToolkitError):
        raise InvalidInputError("Test error")

    with pytest.raises(ToolkitError):
        raise AdapterError("Test error")
