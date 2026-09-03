# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Input parser for the collector-gh adapter.

This module provides functions to parse collector-gh output into
AdapterResult format with schema validation and comprehensive error reporting.
"""

import logging

from living_doc_core.errors import AdapterError  # type: ignore[import-untyped]
from pydantic import ValidationError as PydanticValidationError

from living_doc_adapter_collector_gh.compatibility import check_compatibility
from living_doc_adapter_collector_gh.detector import extract_version
from living_doc_adapter_collector_gh.models import (
    AcceptanceCriterion,
    AdapterItem,
    AdapterItemTimestamps,
    AdapterMetadata,
    AdapterMetadataProducer,
    AdapterMetadataRun,
    AdapterMetadataSource,
    AdapterResult,
)

logger = logging.getLogger(__name__)


def _validate_metadata(metadata: dict, errors: list[str]) -> None:
    """Validate the metadata section of the payload."""
    for key in ["producer", "run", "source"]:
        if key not in metadata:
            errors.append(f"Missing metadata.{key}")
        elif not isinstance(metadata[key], dict):
            errors.append(f"metadata.{key} must be a dict, got {type(metadata[key]).__name__}")

    producer = metadata.get("producer", {})
    if isinstance(producer, dict):
        for key in ["name", "version"]:
            if key not in producer:
                errors.append(f"Missing metadata.producer.{key}")
            elif not isinstance(producer.get(key), str):
                errors.append(f"metadata.producer.{key} must be a string, got {type(producer.get(key)).__name__}")

    source = metadata.get("source", {})
    if isinstance(source, dict):
        if "repositories" not in source:
            errors.append("Missing metadata.source.repositories")
        elif not isinstance(source["repositories"], list):
            errors.append(f"metadata.source.repositories must be a list, got {type(source['repositories']).__name__}")
        elif not source["repositories"]:
            errors.append("metadata.source.repositories cannot be empty")


def _validate_items(items: list, errors: list[str]) -> None:
    """Validate the user_stories section of the payload."""
    item_count = len(items)
    for idx, item in enumerate(items[:5]):
        if not isinstance(item, dict):
            errors.append(f"User story {idx} must be a dict, got {type(item).__name__}")
            continue
        for field in ["id", "title", "state", "url", "timestamps"]:
            if field not in item:
                item_id = item.get("id", f"[{idx}]")
                errors.append(f"User story {item_id} missing required field: '{field}'")

    if item_count > 5:
        logger.info(
            "Schema validation checked first 5 of %d user stories; full validation deferred to item parsing",
            item_count,
        )


def _validate_schema(payload: dict) -> list[str]:
    """
    Validate incoming payload against expected schema structure.

    Performs pre-parsing validation to catch structural issues early
    and provide actionable error messages.

    Args:
        payload: Input payload to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors: list[str] = []

    if not isinstance(payload, dict):
        errors.append(f"Payload must be a dict, got {type(payload).__name__}")
        return errors

    if "metadata" not in payload:
        errors.append("Missing required key: 'metadata'")
    if "user_stories" not in payload:
        errors.append("Missing required key: 'user_stories'")

    if "metadata" in payload:
        metadata = payload["metadata"]
        if not isinstance(metadata, dict):
            errors.append(f"'metadata' must be a dict, got {type(metadata).__name__}")
        else:
            _validate_metadata(metadata, errors)

    if "user_stories" in payload:
        items = payload["user_stories"]
        if not isinstance(items, list):
            errors.append(f"'user_stories' must be a list, got {type(items).__name__}")
            return errors
        _validate_items(items, errors)

    return errors


def _build_metadata(payload: dict) -> AdapterMetadata:
    """Build AdapterMetadata from the parsed payload dict."""
    metadata_dict = payload.get("metadata", {})
    producer = metadata_dict.get("producer", {})
    run = metadata_dict.get("run", {})
    source = metadata_dict.get("source", {})
    metadata = AdapterMetadata(
        producer=AdapterMetadataProducer(
            name=producer.get("name", ""),
            version=producer.get("version", ""),
            build=producer.get("build"),
        ),
        run=AdapterMetadataRun(
            run_id=run.get("run_id"),
            run_attempt=run.get("run_attempt"),
            actor=run.get("actor"),
            workflow=run.get("workflow"),
            ref=run.get("ref"),
            sha=run.get("sha"),
        ),
        source=AdapterMetadataSource(
            systems=source.get("systems", []),
            repositories=source.get("repositories", []),
            organization=source.get("organization"),
            enterprise=source.get("enterprise"),
        ),
        original_metadata=metadata_dict,
    )
    logger.info("Metadata extracted: producer=%s v%s", producer.get("name"), producer.get("version"))
    return metadata


def _parse_single_item(raw_item: dict) -> AdapterItem:
    """Parse a single raw User Story dict into an AdapterItem."""
    missing_fields = [f for f in ["id", "title", "state", "url", "timestamps"] if f not in raw_item]
    if missing_fields:
        raise KeyError(f"Missing required fields: {', '.join(missing_fields)}")

    raw_bv = raw_item.get("business_value")
    raw_pc = raw_item.get("preconditions")
    raw_ac = raw_item.get("acceptance_criteria")

    acceptance_criteria = None
    if raw_ac is not None:
        acceptance_criteria = [
            AcceptanceCriterion(
                id=ac["id"],
                state=ac["state"],
                version=ac["version"],
                description=ac["description"],
            )
            for ac in raw_ac
        ]

    return AdapterItem(
        id=raw_item["id"],
        title=raw_item["title"],
        state=raw_item["state"],
        tags=raw_item.get("tags", []),
        url=raw_item["url"],
        timestamps=AdapterItemTimestamps(
            created=raw_item["timestamps"]["created"],
            updated=raw_item["timestamps"]["updated"],
        ),
        description=raw_item.get("description"),
        business_value=raw_bv if isinstance(raw_bv, list) else None,
        preconditions=raw_pc if isinstance(raw_pc, list) else None,
        acceptance_criteria=acceptance_criteria,
    )


def parse(payload: dict) -> AdapterResult:
    """
    Parse collector-gh output into AdapterResult format.

    Performs schema validation before parsing to catch issues early
    with detailed error reporting.

    Args:
        payload: Input payload from collector-gh

    Returns:
        AdapterResult with parsed user stories and metadata

    Raises:
        AdapterError: If validation or parsing fails
    """
    try:
        # Perform schema validation
        logger.debug("Starting schema validation for collector-gh payload")
        validation_errors = _validate_schema(payload)

        if validation_errors:
            error_message = "Schema validation failed with the following issues:\n"
            for idx, error in enumerate(validation_errors, 1):
                error_message += f"  [{idx}] {error}\n"
            logger.error(error_message.strip())
            raise AdapterError(error_message.strip())

        logger.debug("Schema validation passed")

        # Extract version and check compatibility
        logger.debug("Extracting version from payload")
        version = extract_version(payload)
        logger.info("Detected collector-gh version: %s", version)

        warnings = check_compatibility(version)
        if warnings:
            logger.warning("Compatibility warnings detected: %s", len(warnings))
            for warning in warnings:
                logger.warning("  - [%s] %s", warning.code, warning.message)

        logger.debug("Extracting metadata")
        metadata = _build_metadata(payload)

        logger.debug("Parsing user stories")
        items_data = payload.get("user_stories", [])
        if not isinstance(items_data, list):
            items_data = []
        logger.debug("User stories provided as array with %d items", len(items_data))

        items = []
        parse_errors = []

        for idx, raw_item in enumerate(items_data):
            try:
                item = _parse_single_item(raw_item)
                items.append(item)
                logger.debug("Parsed user story %s: %s", raw_item["id"], raw_item["title"][:50])
            except (KeyError, TypeError, PydanticValidationError) as e:
                item_id = raw_item.get("id", f"[{idx}]")
                error_msg = f"Failed to parse user story {item_id}: {e}"
                logger.error(error_msg)
                parse_errors.append(error_msg)

        if parse_errors:
            error_summary = f"Failed to parse {len(parse_errors)} user story(ies):\n"
            for error in parse_errors:
                error_summary += f"  - {error}\n"
            logger.error(error_summary.strip())
            raise AdapterError(error_summary.strip())

        logger.info("Parsing input with collector-gh adapter...")
        logger.info("Parsed %d user stories", len(items))

        return AdapterResult(user_stories=items, metadata=metadata, warnings=warnings)

    except AdapterError:
        raise
    except Exception as e:
        error_msg = f"Failed to parse collector-gh payload: {e}"
        logger.exception(error_msg)
        raise AdapterError(error_msg) from e
