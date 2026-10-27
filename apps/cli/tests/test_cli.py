# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for the CLI group.
"""

import click
import pytest
from click.testing import CliRunner

from living_doc_cli.main import cli


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


def test_cli_help(runner):
    """Test that --help displays usage information."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Living Documentation Toolkit CLI" in result.output


def test_cli_version(runner):
    """Test that --version displays version information."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_registers_every_command_the_action_runs(runner):
    """`normalize-docs`, `normalize-tests` and `coverage-matrix` are registered; another name is not a command."""
    assert list(cli.commands) == ["normalize-docs", "normalize-tests", "coverage-matrix"]
    result = runner.invoke(cli, ["generate"])
    assert result.exit_code == 2
    assert "No such command 'generate'" in result.output


@pytest.mark.parametrize("verbose", [True, False])
def test_cli_stores_the_verbose_flag_for_its_commands(verbose):
    """The group's callback keeps --verbose in the context object its commands read."""
    with click.Context(cli) as ctx:
        cli.callback(verbose=verbose)
    assert ctx.obj == {"verbose": verbose}
