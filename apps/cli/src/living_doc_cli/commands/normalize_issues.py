# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
normalize-issues CLI command.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from living_doc_core.errors import (  # type: ignore[import-untyped]
    AdapterError,
    FileIOError,
    InvalidInputError,
    NormalizationError,
    SchemaValidationError,
    ToolkitError,
)
from living_doc_service_normalize_issues.service import run_service  # type: ignore[import-untyped]

# The canonical output name is generator-ready.json; pdf_ready.json is still
# accepted for one or two minor versions and emits a deprecation notice.
DEPRECATED_OUTPUT_NAME = "pdf_ready.json"
CANONICAL_OUTPUT_NAME = "generator-ready.json"

# Error prefix mapping per SPEC.md 3.1.2
ERROR_PREFIXES = {
    InvalidInputError: "Invalid input:",
    AdapterError: "Adapter error:",
    SchemaValidationError: "Schema validation failed:",
    NormalizationError: "Normalization failed:",
    FileIOError: "File I/O error:",
}


def format_error_message(error: ToolkitError) -> str:
    """
    Format error message according to SPEC.md 3.1.2: {prefix} {detail}. {guidance}

    Args:
        error: The toolkit error to format

    Returns:
        Formatted error message string
    """
    error_class = type(error)
    prefix = ERROR_PREFIXES.get(error_class, "Error:")

    # Extract detail from the error message
    detail = error.message

    # Add actionable guidance based on error type
    guidance_map = {
        InvalidInputError: "Ensure --input points to a valid file.",
        AdapterError: "Check metadata.producer.name field.",
        SchemaValidationError: "Review the output schema requirements.",
        NormalizationError: "Check input data format and content.",
        FileIOError: "Ensure output directory exists and is writable.",
    }

    guidance = guidance_map.get(error_class, "Please check the logs for more details.")

    return f"{prefix} {detail}. {guidance}"


@click.command("normalize-issues")
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=False),
    help="Path to input JSON file",
)
@click.option(
    "--output",
    "output_path",
    required=True,
    type=click.Path(),
    help="Path for output JSON file (e.g. generator-ready.json; pdf_ready.json still accepted, deprecated)",
)
@click.option(
    "--source",
    type=click.Choice(["auto", "collector-gh"], case_sensitive=False),
    default="auto",
    help="Producer adapter selection",
)
@click.option(
    "--document-title",
    type=str,
    help="Override document title in meta.document_title",
)
@click.option(
    "--document-version",
    type=str,
    help="Override document version in meta.document_version",
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def normalize_issues(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    ctx: click.Context,
    input_path: str,
    output_path: str,
    source: str,
    document_title: Optional[str],
    document_version: Optional[str],
    verbose: bool,
) -> None:
    """
    Normalize collector output into the canonical generator-ready JSON dataset.

    Converts collector-gh output (doc-issues.json) into generator-ready.json, the
    canonical dataset consumed by living-doc generators. The legacy output name
    pdf_ready.json is still accepted but deprecated.
    """
    # Merge verbose flag: local overrides global
    global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
    effective_verbose = verbose or global_verbose

    if Path(output_path).name == DEPRECATED_OUTPUT_NAME:
        click.echo(
            f"Warning: '{DEPRECATED_OUTPUT_NAME}' is a deprecated output name; use '{CANONICAL_OUTPUT_NAME}'.",
            err=True,
        )

    # Build options dictionary
    options = {
        "verbose": effective_verbose,
        "source": source,
    }

    if document_title:
        options["document_title"] = document_title
    if document_version:
        options["document_version"] = document_version

    try:
        # Call the service
        run_service(input_path, output_path, options)
        click.echo(f"Successfully normalized {input_path} -> {output_path}")

    except ToolkitError as e:
        # Map toolkit errors to exit codes and format message
        error_message = format_error_message(e)
        click.echo(f"Error: {error_message}", err=True)
        sys.exit(e.exit_code)

    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch any unexpected errors
        click.echo(
            f"Error: Unexpected error: {str(e)}. Please check the logs for more details.",
            err=True,
        )
        sys.exit(1)
