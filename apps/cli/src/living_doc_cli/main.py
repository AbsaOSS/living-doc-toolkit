# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Main CLI entrypoint for the Living Documentation Toolkit.
"""

import click

from living_doc_cli import __version__
from living_doc_cli.commands.normalize_issues import normalize_issues


@click.group()
@click.version_option(version=__version__, prog_name="living-doc")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """
    Living Documentation Toolkit CLI.

    A unified CLI for transforming and enriching machine-readable artifacts.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    # Store verbose flag in context for subcommands
    ctx.obj["verbose"] = verbose


cli.add_command(normalize_issues)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
