# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for the `normalize-docs` command: its options, the file it writes, and the error lines and exit code of a
run that fails.
"""

import logging

import pytest
from click.testing import CliRunner
from living_doc_service_normalize_docs import service
from living_doc_utilities.contracts.generator_ready import GeneratorReadyResult
from living_doc_utilities.contracts.io import read_artifact

from living_doc_cli.main import cli


@pytest.fixture(name="runner")
def _runner() -> CliRunner:
    return CliRunner()


def _errors(stderr: str) -> list[str]:
    return [line for line in stderr.splitlines() if line.startswith("[ERROR]")]


def _read(path) -> GeneratorReadyResult:
    result = read_artifact(path, expected="generator-ready")
    assert isinstance(result, GeneratorReadyResult)
    return result


def _no_build(*_args, **_kwargs):
    raise AssertionError("the builder ran")


def test_the_help_lists_the_options_and_the_view_default(runner):
    # Act
    result = runner.invoke(cli, ["normalize-docs", "--help"])

    # Assert
    assert result.exit_code == 0
    for option in ("--input", "--output", "--view", "--document-title", "--document-version", "--verbose"):
        assert option in result.output
    assert "[default: inner]" in result.output


@pytest.mark.parametrize("missing", ["--input", "--output"])
def test_input_and_output_are_required(runner, doc_source, tmp_path, missing):
    # Arrange
    options = {"--input": str(doc_source), "--output": str(tmp_path / "generator-ready.json")}
    del options[missing]

    # Act
    result = runner.invoke(cli, ["normalize-docs", *[item for pair in options.items() for item in pair]])

    # Assert
    assert result.exit_code == 2
    assert f"Missing option '{missing}'" in result.output


def test_over_the_fixture_it_writes_generator_ready_in_the_inner_view(runner, doc_source, tmp_path):
    # Arrange
    output = tmp_path / "out" / "generator-ready.json"

    # Act
    result = runner.invoke(cli, ["normalize-docs", "--input", str(doc_source), "--output", str(output)])

    # Assert
    assert result.exit_code == 0, result.output
    document = _read(output).document
    assert (document.view, document.title, document.version) == ("inner", "living-doc-examples", "1.0.0")
    assert (
        f"[INFO] normalize-docs - written: `{output}` (inner view; 5 of 5 entities, 8 of 8 acceptance criteria)."
        in (result.stderr.splitlines())
    )


def test_the_view_title_and_version_options_reach_the_document(runner, doc_source, tmp_path):
    # Arrange
    output = tmp_path / "generator-ready.json"

    # Act
    result = runner.invoke(
        cli,
        [
            "normalize-docs",
            f"--input={doc_source}",
            f"--output={output}",
            "--view=release",
            "--document-title=Checkout tests",
            "--document-version=2.3.0",
        ],
    )

    # Assert
    assert result.exit_code == 0, result.output
    document = _read(output).document
    assert (document.view, document.title, document.version) == ("release", "Checkout tests", "2.3.0")
    assert (document.selection_summary.included_entities, document.selection_summary.total_entities) == (3, 5)


def test_a_view_that_is_not_inner_or_release_is_a_usage_error(runner, doc_source, tmp_path):
    # Act
    result = runner.invoke(
        cli, ["normalize-docs", f"--input={doc_source}", f"--output={tmp_path / 'out.json'}", "--view=Release"]
    )

    # Assert
    assert result.exit_code == 2
    assert "'Release' is not one of 'inner', 'release'" in result.output


@pytest.mark.parametrize(
    "arguments",
    [
        ["--verbose", "normalize-docs"],
        # As the action passes it: after the command's own options.
        ["normalize-docs", "--verbose"],
    ],
)
def test_verbose_is_taken_by_the_group_and_by_the_command(runner, doc_source, tmp_path, arguments):
    # Act
    result = runner.invoke(cli, [*arguments, f"--input={doc_source}", f"--output={tmp_path / 'out.json'}"])

    # Assert
    assert result.exit_code == 0, result.output
    assert logging.getLogger("living_doc").level == logging.DEBUG


def test_a_missing_input_fails_with_one_missing_input_line_before_any_transform(runner, monkeypatch, tmp_path):
    # Arrange
    monkeypatch.setattr(service, "build_generator_ready", _no_build)
    missing = tmp_path / "doc-source.json"
    output = tmp_path / "generator-ready.json"

    # Act
    result = runner.invoke(cli, ["normalize-docs", f"--input={missing}", f"--output={output}"])

    # Assert
    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        f"[ERROR] [MISSING_INPUT] documentation input {str(missing)!r}: no such file; check the path, or run the step "
        "that writes it first"
    ]
    assert not output.exists()


def test_an_input_that_is_not_json_fails_with_one_line_without_a_code(runner, monkeypatch, tmp_path):
    # Arrange
    monkeypatch.setattr(service, "build_generator_ready", _no_build)
    broken = tmp_path / "doc-source.json"
    broken.write_text("{not json", encoding="utf-8")

    # Act
    result = runner.invoke(cli, ["normalize-docs", f"--input={broken}", f"--output={tmp_path / 'out.json'}"])

    # Assert
    assert result.exit_code == 1
    errors = _errors(result.stderr)
    assert len(errors) == 1
    assert errors[0].startswith(f"[ERROR] documentation input {str(broken)!r}: not JSON: ")


def test_a_lost_field_fails_with_one_field_loss_line_and_writes_no_file(runner, monkeypatch, doc_source, tmp_path):
    # Arrange: the builder loses every entity's `purpose`, which both Features fill.
    build = service.build_generator_ready

    def dropping(*args, **kwargs):
        result = build(*args, **kwargs)
        result.content.entities = [entity.model_copy(update={"purpose": None}) for entity in result.content.entities]
        return result

    monkeypatch.setattr(service, "build_generator_ready", dropping)
    output = tmp_path / "generator-ready.json"

    # Act
    result = runner.invoke(cli, ["normalize-docs", f"--input={doc_source}", f"--output={output}"])

    # Assert
    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        "[ERROR] [FIELD_LOSS] 'features[].purpose' had occupancy 2 on input but its mapped output path "
        "'content.entities[].purpose' has occupancy 0"
    ]
    assert not output.exists()


def test_an_output_that_cannot_be_written_fails_with_one_line(runner, doc_source, tmp_path):
    # Arrange: a directory where the output file should be.
    output = tmp_path / "generator-ready.json"
    output.mkdir()

    # Act
    result = runner.invoke(cli, ["normalize-docs", f"--input={doc_source}", f"--output={output}"])

    # Assert
    assert result.exit_code == 1
    errors = _errors(result.stderr)
    assert len(errors) == 1
    assert errors[0].startswith("[ERROR] normalize-docs - the output cannot be written: ")
