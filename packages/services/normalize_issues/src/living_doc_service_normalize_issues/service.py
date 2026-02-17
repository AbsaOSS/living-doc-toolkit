# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Service orchestration for normalize_issues.

This module provides the main service entry point for normalizing collector-gh output
into PDF-ready JSON format.
"""

from living_doc_adapter_collector_gh.detector import can_handle  # type: ignore[import-untyped]
from living_doc_adapter_collector_gh.parser import parse  # type: ignore[import-untyped]
from living_doc_core.errors import AdapterError, InvalidInputError, NormalizationError  # type: ignore[import-untyped]
from living_doc_core.json_utils import read_json, write_json  # type: ignore[import-untyped]
from living_doc_core.logging_config import setup_logging  # type: ignore[import-untyped]

from living_doc_service_normalize_issues.builder import build_pdf_ready


def run_service(input_path: str, output_path: str, options: dict) -> None:
    """
    Run the normalization service pipeline.

    This function orchestrates the complete normalization pipeline:
    1. Load input JSON
    2. Detect adapter (collector-gh)
    3. Parse into AdapterResult
    4. Build PdfReadyV1 with normalized sections
    5. Validate output (via Pydantic)
    6. Write output JSON
    7. Log summary

    Args:
        input_path: Path to input JSON file (collector-gh output)
        output_path: Path to output JSON file (pdf_ready.json)
        options: Configuration options (document_title, document_version, source, etc.)

    Raises:
        InvalidInputError: If input file is missing or malformed
        AdapterError: If adapter detection fails
        NormalizationError: If parsing or building fails
        FileIOError: If write operation fails
    """
    # Set up logging
    verbose = options.get("verbose", False)
    logger = setup_logging(verbose=verbose)

    logger.info("Starting normalization service")
    logger.info("Input: %s", input_path)
    logger.info("Output: %s", output_path)

    try:
        # Step 1: Load input JSON
        logger.info("Loading input JSON...")
        payload = read_json(input_path)

        # Step 2: Detect adapter
        source_option = options.get("source", "auto")
        if source_option == "auto":
            logger.info("Detecting adapter...")
            if not can_handle(payload):
                raise AdapterError("Input does not match collector-gh format")
            logger.info("Detected adapter: collector-gh")
        elif source_option == "collector-gh":
            logger.info("Using explicit adapter: collector-gh")
        else:
            raise AdapterError(f"Unsupported adapter: {source_option}")

        # Step 3: Parse into AdapterResult (includes compatibility check)
        logger.info("Parsing input with collector-gh adapter...")
        try:
            adapter_result = parse(payload)
        except Exception as e:
            raise NormalizationError(f"Failed to parse input: {e}") from e

        logger.info("Parsed %d items", len(adapter_result.items))
        if adapter_result.warnings:
            logger.warning("Adapter reported %d warnings", len(adapter_result.warnings))
            for warning in adapter_result.warnings:
                logger.warning("  - [%s] %s", warning.code, warning.message)

        # Step 4: Build PdfReadyV1
        logger.info("Building PDF-ready output...")
        try:
            pdf_ready = build_pdf_ready(adapter_result, options)
        except Exception as e:
            raise NormalizationError(f"Failed to build PDF-ready output: {e}") from e

        # Step 5: Validate output (Pydantic model already validates)
        logger.info("Output validated successfully")

        # Step 6: Write output JSON
        logger.info("Writing output JSON...")
        output_data = pdf_ready.model_dump(mode="json")
        write_json(output_path, output_data, indent=2, sort_keys=True)

        # Step 7: Log summary
        logger.info("Normalization completed successfully")
        logger.info("  - User stories: %d", len(pdf_ready.content.user_stories))  # pylint: disable=no-member
        logger.info("  - Document title: %s", pdf_ready.meta.document_title)  # pylint: disable=no-member
        logger.info("  - Document version: %s", pdf_ready.meta.document_version)  # pylint: disable=no-member
        logger.info("  - Generated at: %s", pdf_ready.meta.generated_at)  # pylint: disable=no-member

    except (InvalidInputError, AdapterError, NormalizationError) as e:
        logger.error("Normalization failed: %s", e.message)
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        raise NormalizationError(f"Unexpected error during normalization: {e}") from e
