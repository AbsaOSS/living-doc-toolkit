# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for the CI run context.
"""

import pytest
from living_doc_utilities.contracts.envelope import Run

from living_doc_core.run_context import RUN_VARIABLES, run_context

RUN = {
    "GITHUB_RUN_ID": "4242",
    "GITHUB_RUN_ATTEMPT": "2",
    "GITHUB_ACTOR": "octocat",
    "GITHUB_WORKFLOW": "docs",
    "GITHUB_REF": "refs/heads/master",
    "GITHUB_SHA": "3f2c1ab",
}


@pytest.fixture(autouse=True)
def _no_run(monkeypatch):
    # The CI job running the tests sets every variable.
    for variable in RUN_VARIABLES.values():
        monkeypatch.delenv(variable, raising=False)


def _set(monkeypatch, variables: dict[str, str]) -> None:
    for variable, value in variables.items():
        monkeypatch.setenv(variable, value)


def test_it_reads_one_variable_per_run_field():
    assert sorted(RUN_VARIABLES) == sorted(Run.model_fields)
    assert sorted(RUN_VARIABLES.values()) == sorted(RUN)


def test_every_variable_set_fills_every_field(monkeypatch):
    # Arrange
    _set(monkeypatch, RUN)

    # Act
    run = run_context()

    # Assert
    assert run == Run(
        run_id="4242", run_attempt="2", actor="octocat", workflow="docs", ref="refs/heads/master", sha="3f2c1ab"
    )


def test_an_unset_variable_is_none(monkeypatch):
    # Arrange
    _set(monkeypatch, {"GITHUB_RUN_ID": "4242", "GITHUB_SHA": "3f2c1ab"})

    # Act
    run = run_context()

    # Assert
    assert run == Run(run_id="4242", sha="3f2c1ab")


def test_an_empty_variable_is_none(monkeypatch):
    # Arrange
    _set(monkeypatch, {**RUN, "GITHUB_ACTOR": ""})

    # Act
    run = run_context()

    # Assert
    assert run.actor is None
    assert run.run_id == "4242"


def test_outside_github_actions_every_field_is_none():
    assert run_context() == Run()
