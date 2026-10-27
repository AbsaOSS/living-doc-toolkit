# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `normalize-docs` command: its options, and the error lines and exit code of a run that fails.
"""

import logging
from typing import cast, get_args

import click
from living_doc_core.logging_config import setup_logging
from living_doc_service_normalize_docs import service
from living_doc_utilities.contracts.common import View

from living_doc_cli.failures import exit_on_failure

logger = logging.getLogger("living_doc.normalize_docs")


@click.command("normalize-docs")
@click.option(
    "--input", "input_path", required=True, type=click.Path(), help="The documentation input, doc-source.json."
)
@click.option("--output", "output_path", required=True, type=click.Path(), help="The generator-ready.json to write.")
@click.option(
    "--view",
    type=click.Choice(get_args(View)),
    default="inner",
    show_default=True,
    help="The records the output holds: every one, or the release view's.",
)
@click.option("--document-title", help="The document title; the input's project id when not given.")
@click.option("--document-version", help="The document version; 1.0.0 when not given.")
@click.pass_context
def normalize_docs(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    ctx: click.Context,
    input_path: str,
    output_path: str,
    view: str,
    document_title: str | None,
    document_version: str | None,
) -> None:
    """
    Normalize one doc-source.json into generator-ready.json.
    """
    setup_logging(verbose=bool((ctx.obj or {}).get("verbose")))
    with exit_on_failure(logger, "normalize-docs"):
        result = service.normalize_docs(
            input_path,
            output_path,
            view=cast(View, view),
            document_title=document_title,
            document_version=document_version,
        )

    summary = result.document.selection_summary
    logger.info(
        "normalize-docs - written: `%s` (%s view; %d of %d entities, %d of %d acceptance criteria).",
        output_path,
        view,
        summary.included_entities,
        summary.total_entities,
        summary.included_acceptance_criteria,
        summary.total_acceptance_criteria,
    )
