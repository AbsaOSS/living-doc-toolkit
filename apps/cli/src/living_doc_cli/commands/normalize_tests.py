# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""The `normalize-tests` command: its options, output summary, and error lines and exit codes."""

import logging
from typing import cast, get_args

import click
from living_doc_core.logging_config import setup_logging
from living_doc_service_normalize_tests import service
from living_doc_utilities.contracts.common import View

from living_doc_cli.failures import exit_on_failure

logger = logging.getLogger("living_doc.normalize_tests")


@click.command("normalize-tests")
@click.option(
    "--doc-input",
    "doc_inputs",
    required=True,
    multiple=True,
    type=click.Path(),
    help="The documentation input, doc-source.json, read for each criterion's state. A run reads exactly one, so a "
    "second one fails it.",
)
@click.option("--tests-input", required=True, type=click.Path(), help="The tests input, ui-tests.json.")
@click.option("--output", "output_path", required=True, type=click.Path(), help="The ui-test-catalog.json to write.")
@click.option(
    "--view",
    type=click.Choice(get_args(View)),
    default="inner",
    show_default=True,
    help="document.view; the release view drops each link to a planned or in_review criterion.",
)
@click.pass_context
def normalize_tests(
    ctx: click.Context,
    doc_inputs: tuple[str, ...],
    tests_input: str,
    output_path: str,
    view: str,
) -> None:
    """Normalize one ui-tests.json into ui-test-catalog.json, with each link's state from one doc-source.json."""
    setup_logging(verbose=bool((ctx.obj or {}).get("verbose")))
    with exit_on_failure(logger, "normalize-tests"):
        result = service.normalize_tests(doc_inputs, tests_input, output_path, view=cast(View, view))

    scenarios = result.metadata.source_inputs[1].selected_stats.cardinality.scenarios
    logger.info(
        "normalize-tests - written: `%s` (%s view; %d feature files, %d scenarios).",
        output_path,
        view,
        len(result.feature_files),
        scenarios,
    )
