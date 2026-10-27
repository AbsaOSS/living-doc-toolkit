# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""The `normalize-tests` command: its options, output summary, and error lines and exit codes."""

import logging

import click
from living_doc_core.logging_config import setup_logging
from living_doc_service_normalize_tests import service

from living_doc_cli.failures import exit_on_failure

logger = logging.getLogger("living_doc.normalize_tests")


@click.command("normalize-tests")
@click.option("--input", "input_path", required=True, type=click.Path(), help="The tests input, ui-tests.json.")
@click.option("--output", "output_path", required=True, type=click.Path(), help="The ui-test-catalog.json to write.")
@click.pass_context
def normalize_tests(ctx: click.Context, input_path: str, output_path: str) -> None:
    """Normalize one ui-tests.json into ui-test-catalog.json."""
    setup_logging(verbose=bool((ctx.obj or {}).get("verbose")))
    with exit_on_failure(logger, "normalize-tests"):
        result = service.normalize_tests(input_path, output_path)

    scenarios = result.metadata.source_inputs[0].selected_stats.cardinality.scenarios
    logger.info(
        "normalize-tests - written: `%s` (%d feature files, %d scenarios).",
        output_path,
        len(result.feature_files),
        scenarios,
    )
