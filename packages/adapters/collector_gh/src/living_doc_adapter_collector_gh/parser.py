# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Input parser for the collector-gh adapter.

This module provides functions to parse collector-gh output into
AdapterResult format with schema validation and comprehensive error reporting.
"""

import logging
from jsonschema import validate, ValidationError  # type: ignore[import-untyped]
from pydantic import ValidationError as PydanticValidationError

from living_doc_core.errors import AdapterError  # type: ignore[import-untyped]

from living_doc_adapter_collector_gh.compatibility import check_compatibility
from living_doc_adapter_collector_gh.detector import extract_version
from living_doc_adapter_collector_gh.models import (
    AdapterItem,
    AdapterItemTimestamps,
    AdapterMetadata,
    AdapterMetadataProducer,
    AdapterMetadataRun,
    AdapterMetadataSource,
    AdapterResult,
)

logger = logging.getLogger(__name__)


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
    errors = []

    # Check top-level structure
    if not isinstance(payload, dict):
        errors.append(f"Payload must be a dict, got {type(payload).__name__}")
        return errors

    # Check required root keys
    if "metadata" not in payload:
        errors.append("Missing required key: 'metadata'")
    if "items" not in payload:
        errors.append("Missing required key: 'items'")

    # Validate metadata structure
    if "metadata" in payload:
        metadata = payload["metadata"]
        if not isinstance(metadata, dict):
            errors.append(f"'metadata' must be a dict, got {type(metadata).__name__}")
        else:
            # Check metadata sub-keys
            for key in ["producer", "run", "source"]:
                if key not in metadata:
                    errors.append(f"Missing metadata.{key}")
                elif not isinstance(metadata[key], dict):
                    errors.append(
                        f"metadata.{key} must be a dict, got {type(metadata[key]).__name__}"
                    )

            # Validate producer
            producer = metadata.get("producer", {})
            if isinstance(producer, dict):
                for key in ["name", "version"]:
                    if key not in producer:
                        errors.append(f"Missing metadata.producer.{key}")
                    elif not isinstance(producer.get(key), str):
                        errors.append(
                            f"metadata.producer.{key} must be a string, "
                            f"got {type(producer.get(key)).__name__}"
                        )

            # Validate source
            source = metadata.get("source", {})
            if isinstance(source, dict):
                if "repositories" not in source:
                    errors.append("Missing metadata.source.repositories")
                elif not isinstance(source["repositories"], list):
                    errors.append(
                        f"metadata.source.repositories must be a list, "
                        f"got {type(source['repositories']).__name__}"
                    )
                elif not source["repositories"]:
                    errors.append("metadata.source.repositories cannot be empty")

    # Validate items structure
    if "items" in payload:
        items = payload["items"]
        if not isinstance(items, list):
            errors.append(
                f"'items' must be a list, got {type(items).__name__}"
            )
            return errors
        item_count = len(items)
        
        # Sample validation of first few items
        for idx, item in enumerate(items[:5]):
            if not isinstance(item, dict):
                errors.append(
                    f"Item {idx} must be a dict, got {type(item).__name__}"
                )
                continue
            
            # Check required item fields
            for field in ["id", "title", "state", "url", "timestamps"]:
                if field not in item:
                    item_id = item.get("id", f"[{idx}]")
                    errors.append(f"Item {item_id} missing required field: '{field}'")
        
        if item_count > 5:
            logger.info(
                "Schema validation checked first 5 of %d items; "
                "full validation deferred to item parsing",
                item_count,
            )

    return errors


def parse(payload: dict) -> AdapterResult:
    """
    Parse collector-gh output into AdapterResult format.

    Performs schema validation before parsing to catch issues early
    with detailed error reporting.

    Args:
        payload: Input payload from collector-gh

    Returns:
        AdapterResult with parsed items and metadata

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

        # Extract metadata
        logger.debug("Extracting metadata")
        metadata_dict = payload.get("metadata", {})
        producer = metadata_dict.get("producer", {})
        run = metadata_dict.get("run", {})
        source = metadata_dict.get("source", {})

        # Create metadata
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

        # Parse items
        logger.debug("Parsing items")
        items_data = payload.get("items", [])
        if not isinstance(items_data, list):
            items_data = []
        logger.debug("Items provided as array with %d items", len(items_data))

        items = []
        parse_errors = []

        for idx, raw_item in enumerate(items_data):
            try:
                # Validate required fields
                missing_fields = []
                for field in ["id", "title", "state", "url", "timestamps"]:
                    if field not in raw_item:
                        missing_fields.append(field)

                if missing_fields:
                    raise KeyError(f"Missing required fields: {', '.join(missing_fields)}")

                item = AdapterItem(
                    id=raw_item["id"],
                    title=raw_item["title"],
                    state=raw_item["state"],
                    tags=raw_item.get("tags", []),
                    url=raw_item["url"],
                    timestamps=AdapterItemTimestamps(
                        created=raw_item["timestamps"]["created"],
                        updated=raw_item["timestamps"]["updated"],
                    ),
                    body=raw_item.get("body"),
                )
                items.append(item)
                logger.debug("Parsed item %s: %s", raw_item["id"], raw_item["title"][:50])

            except (KeyError, TypeError, PydanticValidationError) as e:
                item_id = raw_item.get("id", f"[{idx}]")
                error_msg = f"Failed to parse item {item_id}: {e}"
                logger.error(error_msg)
                parse_errors.append(error_msg)

        if parse_errors:
            error_summary = f"Failed to parse {len(parse_errors)} item(s):\n"
            for error in parse_errors:
                error_summary += f"  - {error}\n"
            logger.error(error_summary.strip())
            raise AdapterError(error_summary.strip())

        logger.info("Parsing input with collector-gh adapter...")
        logger.info("Parsed %d items", len(items))

        return AdapterResult(items=items, metadata=metadata, warnings=warnings)

    except AdapterError:
        raise
    except Exception as e:
        error_msg = f"Failed to parse collector-gh payload: {e}"
        logger.exception(error_msg)
        raise AdapterError(error_msg) from e

