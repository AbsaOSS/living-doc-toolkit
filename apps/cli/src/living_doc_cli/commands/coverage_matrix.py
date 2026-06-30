# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
coverage-matrix CLI command.
"""

import sys

import click

from living_doc_core.errors import ToolkitError  # type: ignore[import-untyped]
from living_doc_service_coverage_matrix.service import run_service  # type: ignore[import-untyped]


@click.command("coverage-matrix")
@click.option(
    "--doc-input",
    "doc_input",
    required=True,
    type=click.Path(exists=False),
    help="Path to the US+AC doc JSON file (doc-source.json / doc-issues.json)",
)
@click.option(
    "--tests-input",
    "tests_input",
    required=True,
    type=click.Path(exists=False),
    help="Path to the ui-tests JSON file",
)
@click.option(
    "--output",
    "output_path",
    required=True,
    type=click.Path(),
    help="Destination path for coverage-matrix.json",
)
@click.option(
    "--fail-under",
    "fail_under",
    type=float,
    default=None,
    help="Exit with code 1 if coverage_pct is below this threshold",
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def coverage_matrix(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    ctx: click.Context,
    doc_input: str,
    tests_input: str,
    output_path: str,
    fail_under: float | None,
    verbose: bool,
) -> None:
    """
    Generate an AC-level test coverage matrix.

    Cross-references doc-source output (User Stories + acceptance criteria) with
    ui-tests output (test scenarios) into coverage-matrix.json.
    """
    global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
    options = {
        "verbose": verbose or global_verbose,
        "fail_under": fail_under,
    }

    try:
        run_service(doc_input, tests_input, output_path, options)
        click.echo(f"Successfully generated coverage matrix -> {output_path}")

    except ToolkitError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(1)

    except Exception as e:  # pylint: disable=broad-exception-caught
        click.echo(f"Error: Unexpected error: {e}", err=True)
        sys.exit(1)
