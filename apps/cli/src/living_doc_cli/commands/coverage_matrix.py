# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `coverage-matrix` command: its options, the `--fail-under` gate, and the error lines and exit code of a run that
fails.
"""

import logging
import math
import sys
from typing import cast, get_args

import click
from living_doc_core.logging_config import setup_logging
from living_doc_service_coverage_matrix import service
from living_doc_utilities.contracts.common import View
from living_doc_utilities.contracts.coverage_matrix import CoverageSummary

from living_doc_cli.failures import exit_on_failure

logger = logging.getLogger("living_doc.coverage_matrix")


def _percentage(summary: CoverageSummary) -> str:
    """The matrix's coverage percentage as the success line names it."""
    return "no coverage percentage" if summary.coverage_pct is None else f"{summary.coverage_pct}%"


def _finite(_ctx: click.Context, _param: click.Parameter, value: float | None) -> float | None:
    """
    `--fail-under` as a finite number, as the action takes it: click's float reads `nan` and `inf` too, and no
    percentage is below `nan`, so the gate would never fail.
    """
    if value is not None and not math.isfinite(value):
        raise click.BadParameter(f"{value} is not a finite number.")
    return value


@click.command("coverage-matrix")
@click.option(
    "--doc-input",
    "doc_inputs",
    required=True,
    multiple=True,
    type=click.Path(),
    help="The documentation input, doc-source.json. A run reads exactly one, so a second one fails it.",
)
@click.option("--tests-input", required=True, type=click.Path(), help="The tests input, ui-tests.json.")
@click.option("--output", "output_path", required=True, type=click.Path(), help="The coverage-matrix.json to write.")
@click.option(
    "--view",
    type=click.Choice(get_args(View)),
    default="inner",
    show_default=True,
    help="document.view; the same criteria are counted in both views.",
)
@click.option(
    "--fail-under",
    type=float,
    callback=_finite,
    help="Fail the run when the matrix's coverage percentage is below this number, or there is none; "
    "the file is written first.",
)
@click.pass_context
def coverage_matrix(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    ctx: click.Context,
    doc_inputs: tuple[str, ...],
    tests_input: str,
    output_path: str,
    view: str,
    fail_under: float | None,
) -> None:
    """
    Compute coverage-matrix.json from one doc-source.json and one ui-tests.json.
    """
    setup_logging(verbose=bool((ctx.obj or {}).get("verbose")))
    with exit_on_failure(logger, "coverage-matrix"):
        result = service.coverage_matrix(doc_inputs, tests_input, output_path, view=cast(View, view))

    summary = result.summary
    logger.info(
        "coverage-matrix - written: `%s` (%s view; %d counted acceptance criteria, %d covered, %s).",
        output_path,
        view,
        summary.counted_acs,
        summary.covered_acs,
        _percentage(summary),
    )

    if fail_under is None:
        return
    if summary.coverage_pct is None:
        logger.error(
            "coverage-matrix - no acceptance criterion is counted, so the matrix has no coverage percentage, which "
            "fails --fail-under %g.",
            fail_under,
        )
        sys.exit(1)
    if summary.coverage_pct < fail_under:
        logger.error(
            "coverage-matrix - the coverage percentage, %s, is below --fail-under %g.", summary.coverage_pct, fail_under
        )
        sys.exit(1)
