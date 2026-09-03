# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Schema validation for coverage-matrix inputs.

Validates the doc-source envelope against the bundled ``doc-source-v1.0.0`` JSON
Schema before the matcher consumes it.
"""

import json
from functools import lru_cache
from importlib import resources

from jsonschema import Draft7Validator  # type: ignore[import-untyped]
from living_doc_core.errors import InvalidInputError  # type: ignore[import-untyped]

_DOC_SOURCE_SCHEMA_FILE = "doc-source-v1.0.0-schema.json"


@lru_cache(maxsize=1)
def _doc_source_validator() -> Draft7Validator:
    """Build (and cache) the Draft-07 validator for the doc-source schema."""
    schema_text = (
        resources.files("living_doc_service_coverage_matrix")
        .joinpath("schema")
        .joinpath(_DOC_SOURCE_SCHEMA_FILE)
        .read_text(encoding="utf-8")
    )
    return Draft7Validator(json.loads(schema_text))


def is_doc_source_envelope(payload: object) -> bool:
    """Return ``True`` when the payload is a full doc-source envelope."""
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("user_stories"), list)
        and "metadata" in payload
        and "warnings" in payload
    )


def validate_doc_source(payload: dict) -> None:
    """
    Validate a doc-source envelope against the bundled JSON Schema.

    Args:
        payload: The parsed doc-source JSON object

    Raises:
        InvalidInputError: If the payload violates the doc-source schema
    """
    validator = _doc_source_validator()
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.path))
    if errors:
        details = "; ".join(f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}" for err in errors)
        raise InvalidInputError(f"doc-source input failed schema validation: {details}")
