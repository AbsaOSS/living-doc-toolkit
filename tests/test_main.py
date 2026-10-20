#
# Copyright 2026 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from main import run

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_ISSUES = REPO_ROOT / "tests" / "fixtures" / "collector_gh" / "v1.2.0" / "input" / "doc-issues.json"
GOLDEN = REPO_ROOT / "packages" / "services" / "coverage_matrix" / "tests" / "fixtures" / "golden"
CLI = [sys.executable, "-I", "-m", "living_doc_cli.main"]


def _errors(err: str) -> list[str]:
    return [line for line in err.splitlines() if line.startswith("[ERROR]")]


def _set_inputs(monkeypatch, **inputs: str) -> None:
    for name, value in inputs.items():
        monkeypatch.setenv(f"INPUT_{name.upper()}", value)


class _FakeCli:
    """Records each CLI command line instead of running it; `returncode` is what each run exits with."""

    def __init__(self) -> None:
        self.runs: list[list[str]] = []
        self.returncode = 0

    def run(self, command_line: list[str], check: bool) -> subprocess.CompletedProcess:
        assert check is False
        self.runs.append(command_line)
        return subprocess.CompletedProcess(command_line, self.returncode)


@pytest.fixture(name="cli")
def _cli(monkeypatch, tmp_path) -> _FakeCli:
    """Run from `tmp_path`, with the CLI replaced by a `_FakeCli`."""
    monkeypatch.chdir(tmp_path)
    fake = _FakeCli()
    monkeypatch.setattr(subprocess, "run", fake.run)
    return fake


def _run_failing(capsys) -> tuple[int, list[str]]:
    with pytest.raises(SystemExit) as exit_info:
        run()
    return exit_info.value.code, _errors(capsys.readouterr().err)


def test_an_empty_command_fails_with_one_line_listing_the_valid_commands(cli, capsys):
    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [
        "[ERROR] Input `command` is required; valid commands: normalize-issues, normalize-tests, coverage-matrix."
    ]
    assert cli.runs == []


def test_an_unknown_command_fails_with_one_line_listing_the_valid_commands(cli, monkeypatch, capsys):
    # Arrange
    _set_inputs(monkeypatch, command="normalize\nissues", input="in.json", output="out.json")

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [
        "[ERROR] Input `command` is 'normalize\\nissues', not a valid command; "
        "valid commands: normalize-issues, normalize-tests, coverage-matrix."
    ]
    assert cli.runs == []


def test_normalize_tests_fails_with_one_line_saying_it_is_not_available_yet(cli, monkeypatch, capsys):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-tests", input="in.json", output="out.json")

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [
        "[ERROR] Command `normalize-tests` is not available yet; "
        "the commands available now: normalize-issues, coverage-matrix."
    ]
    assert cli.runs == []


@pytest.mark.parametrize(
    ("inputs", "untaken"),
    [
        ({"command": "coverage-matrix", "tests_input": "tests.json", "view": "release"}, "view"),
        ({"command": "coverage-matrix", "tests_input": "tests.json", "document_title": "Title"}, "document-title"),
        ({"command": "normalize-issues", "tests_input": "tests.json"}, "tests-input"),
        ({"command": "normalize-issues", "fail_under": "80"}, "fail-under"),
    ],
)
def test_an_input_the_command_does_not_take_fails_with_one_line_naming_it(cli, monkeypatch, capsys, inputs, untaken):
    # Arrange
    _set_inputs(monkeypatch, input="in.json", output="out.json", **inputs)

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [f"[ERROR] Input `{untaken}` is not taken by command `{inputs['command']}`; leave it empty."]
    assert cli.runs == []


def test_an_empty_input_the_command_does_not_take_is_not_passed(cli, monkeypatch, capsys):
    # Arrange: `action.yml` passes every input, an unset optional one as its empty default.
    _set_inputs(
        monkeypatch,
        command="coverage-matrix",
        input="doc.json",
        tests_input="tests.json",
        output="out.json",
        view="",
        document_title="",
    )

    # Act
    run()

    # Assert
    assert _errors(capsys.readouterr().err) == []
    assert cli.runs[0][len(CLI) :][:2] == ["coverage-matrix", "--doc-input=doc.json"]
    assert not [argument for argument in cli.runs[0] if argument.startswith(("--view", "--document-title"))]


@pytest.mark.parametrize(
    ("command", "missing"),
    [
        ("normalize-issues", "input"),
        ("normalize-issues", "output"),
        ("coverage-matrix", "input"),
        ("coverage-matrix", "output"),
        ("coverage-matrix", "tests-input"),
    ],
)
def test_a_required_input_left_empty_fails_with_one_line_naming_it(cli, monkeypatch, capsys, command, missing):
    # Arrange
    _set_inputs(monkeypatch, command=command, input="in.json", output="out.json")
    if command == "coverage-matrix":
        _set_inputs(monkeypatch, tests_input="tests.json")
    monkeypatch.setenv(f"INPUT_{missing.replace('-', '_').upper()}", "  ")

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [f"[ERROR] Input `{missing}` is required by command `{command}`."]
    assert cli.runs == []


def test_an_output_with_a_line_break_fails_with_one_line_naming_it(cli, monkeypatch, capsys):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-issues", input="in.json", output="out\nput.json")

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [
        "[ERROR] Input `output` is 'out\\nput.json', a path with a line break, which the `output-path` output "
        "cannot carry."
    ]
    assert cli.runs == []


@pytest.mark.parametrize("value", ["eighty", "80%", "nan", "inf"])
def test_a_fail_under_that_is_not_a_number_fails_with_one_line_naming_it(cli, monkeypatch, capsys, value):
    # Arrange
    _set_inputs(monkeypatch, command="coverage-matrix", input="doc.json", tests_input="tests.json", output="out.json")
    _set_inputs(monkeypatch, fail_under=value)

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [f"[ERROR] Input `fail-under` is {value!r}, not a number."]
    assert cli.runs == []


def test_coverage_matrix_gets_each_input_as_its_option_and_the_output_as_an_absolute_path(cli, monkeypatch):
    # Arrange
    _set_inputs(
        monkeypatch,
        command="coverage-matrix",
        input="doc_source.json",
        tests_input="ui_tests.json",
        output="coverage-matrix.json",
        fail_under="72.5",
    )

    # Act
    run()

    # Assert
    assert cli.runs == [
        [
            *CLI,
            "coverage-matrix",
            "--doc-input=doc_source.json",
            f"--output={Path.cwd() / 'coverage-matrix.json'}",
            "--tests-input=ui_tests.json",
            "--fail-under=72.5",
        ]
    ]


def test_normalize_issues_gets_each_input_as_its_option_and_the_output_as_an_absolute_path(cli, monkeypatch):
    # Arrange
    _set_inputs(
        monkeypatch,
        command="normalize-issues",
        input="doc-issues.json",
        output="out/generator-ready.json",
        view="release",
        document_title="-Release notes",
    )

    # Act
    run()

    # Assert: `--option=value` keeps a value starting with `-` the option's value.
    assert cli.runs == [
        [
            *CLI,
            "normalize-issues",
            "--input=doc-issues.json",
            f"--output={Path.cwd() / 'out' / 'generator-ready.json'}",
            "--view=release",
            "--document-title=-Release notes",
        ]
    ]


def test_an_optional_input_left_empty_is_not_passed_so_the_cli_default_applies(cli, monkeypatch):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-issues", input="doc-issues.json", output="generator-ready.json")

    # Act
    run()

    # Assert
    assert cli.runs == [
        [*CLI, "normalize-issues", "--input=doc-issues.json", f"--output={Path.cwd() / 'generator-ready.json'}"]
    ]


@pytest.mark.parametrize("value", ["true", "TRUE", " True "])
def test_verbose_logging_true_passes_verbose_and_logs_the_command_line_at_debug(cli, monkeypatch, capsys, value):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-issues", input="in.json", output="out.json", verbose_logging=value)

    # Act
    run()

    # Assert
    assert cli.runs[0][-1] == "--verbose"
    debug = [line for line in capsys.readouterr().err.splitlines() if line.startswith("[DEBUG]")]
    assert len(debug) == 1
    assert debug[0].startswith("[DEBUG] Living Documentation Toolkit action - command line: ")
    assert debug[0].endswith(" --verbose")


@pytest.mark.parametrize("value", ["false", "", "yes"])
def test_verbose_logging_off_passes_no_verbose_and_logs_no_debug_line(cli, monkeypatch, capsys, value):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-issues", input="in.json", output="out.json", verbose_logging=value)

    # Act
    run()

    # Assert
    assert "--verbose" not in cli.runs[0]
    assert not [line for line in capsys.readouterr().err.splitlines() if line.startswith("[DEBUG]")]


def test_a_successful_run_sets_the_output_path_to_the_absolute_output(cli, monkeypatch, tmp_path):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-issues", input="in.json", output="out/generator-ready.json")
    monkeypatch.setenv("GITHUB_OUTPUT", os.fspath(tmp_path / "github-output"))

    # Act
    run()

    # Assert
    assert (tmp_path / "github-output").read_text(encoding="utf-8") == (
        f"output-path={tmp_path / 'out' / 'generator-ready.json'}\n"
    )


def test_a_failed_command_ends_the_run_with_its_exit_code_and_sets_no_output(cli, monkeypatch, capsys, tmp_path):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-issues", input="in.json", output="out.json")
    monkeypatch.setenv("GITHUB_OUTPUT", os.fspath(tmp_path / "github-output"))
    cli.returncode = 3

    # Act
    code, errors = _run_failing(capsys)

    # Assert: the CLI prints its own error line.
    assert code == 3
    assert errors == []
    assert not (tmp_path / "github-output").exists()


def test_a_run_outside_github_actions_sets_no_output_and_says_so_once(cli, monkeypatch, capsys):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-issues", input="in.json", output="out.json")

    # Act
    run()

    # Assert
    err = capsys.readouterr().err
    assert err.count("no `GITHUB_OUTPUT`: the `output-path` output is not set.") == 1
    assert _errors(err) == []


def test_an_output_file_that_cannot_be_written_fails_with_one_line(cli, monkeypatch, capsys, tmp_path):
    # Arrange: a directory where the output file should be.
    _set_inputs(monkeypatch, command="normalize-issues", input="in.json", output="out.json")
    (tmp_path / "github-output").mkdir()
    monkeypatch.setenv("GITHUB_OUTPUT", os.fspath(tmp_path / "github-output"))

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert len(errors) == 1
    assert errors[0].startswith(
        "[ERROR] Living Documentation Toolkit action - the `output-path` output cannot be set: "
    )


def _run_entry_point(tmp_path: Path, inputs: dict[str, str]) -> subprocess.CompletedProcess:
    # Only the run step's inputs reach the entry point: no inherited `INPUT_*` and no CI job's `GITHUB_OUTPUT`.
    env = {name: value for name, value in os.environ.items() if not name.startswith("INPUT_")}
    env.update({f"INPUT_{name.replace('-', '_').upper()}": value for name, value in inputs.items()})
    env["GITHUB_OUTPUT"] = os.fspath(tmp_path / "github-output")
    return subprocess.run(
        [sys.executable, "-E", os.fspath(REPO_ROOT / "main.py")],
        capture_output=True,
        check=False,
        cwd=tmp_path,
        env=env,
        text=True,
    )


def test_the_entry_point_runs_normalize_issues_over_the_fixture_and_sets_the_output(tmp_path):
    # Act
    result = _run_entry_point(
        tmp_path,
        {
            "command": "normalize-issues",
            "input": os.fspath(DOC_ISSUES),
            "output": "out/generator-ready.json",
            "view": "release",
            "document-title": "Release notes",
        },
    )

    # Assert
    assert result.returncode == 0, result.stderr
    written = tmp_path / "out" / "generator-ready.json"
    meta = json.loads(written.read_text(encoding="utf-8"))["meta"]
    assert (meta["document_title"], meta["view"]["view"]) == ("Release notes", "release")
    assert (tmp_path / "github-output").read_text(encoding="utf-8") == f"output-path={written}\n"
    assert "[DEBUG]" not in result.stderr


def test_the_entry_point_runs_coverage_matrix_over_the_fixtures_and_sets_the_output(tmp_path):
    # Act: the fixtures' coverage is 75 %.
    result = _run_entry_point(
        tmp_path,
        {
            "command": "coverage-matrix",
            "input": os.fspath(GOLDEN / "doc_source.json"),
            "tests-input": os.fspath(GOLDEN / "ui_tests.json"),
            "output": "coverage-matrix.json",
            "fail-under": "75",
        },
    )

    # Assert
    assert result.returncode == 0, result.stderr
    written = tmp_path / "coverage-matrix.json"
    assert json.loads(written.read_text(encoding="utf-8"))["summary"]["coverage_pct"] == 75.0
    assert (tmp_path / "github-output").read_text(encoding="utf-8") == f"output-path={written}\n"


def test_the_entry_point_fails_a_coverage_below_fail_under_and_sets_no_output(tmp_path):
    # Act
    result = _run_entry_point(
        tmp_path,
        {
            "command": "coverage-matrix",
            "input": os.fspath(GOLDEN / "doc_source.json"),
            "tests-input": os.fspath(GOLDEN / "ui_tests.json"),
            "output": "coverage-matrix.json",
            "fail-under": "80",
        },
    )

    # Assert
    assert result.returncode == 1
    assert "Error: Coverage 75.0% is below threshold 80.0%" in result.stderr
    assert not (tmp_path / "github-output").exists()


def test_the_entry_point_with_verbose_logging_logs_debug_lines(tmp_path):
    # Act
    result = _run_entry_point(
        tmp_path,
        {
            "command": "normalize-issues",
            "input": os.fspath(DOC_ISSUES),
            "output": "generator-ready.json",
            "verbose-logging": "true",
        },
    )

    # Assert
    assert result.returncode == 0, result.stderr
    assert "[DEBUG] Living Documentation Toolkit action - command line: " in result.stderr


def test_a_module_in_the_callers_working_directory_does_not_shadow_the_clis(tmp_path):
    # Arrange: the run step runs in the caller's checkout, which may hold a module named like one the CLI imports.
    (tmp_path / "click.py").write_text("import sys\nsys.exit(42)\n", encoding="utf-8")

    # Act
    result = _run_entry_point(
        tmp_path, {"command": "normalize-issues", "input": os.fspath(DOC_ISSUES), "output": "generator-ready.json"}
    )

    # Assert
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "generator-ready.json").is_file()


def test_the_entry_point_passes_a_failed_commands_exit_code_through(tmp_path):
    # Act
    result = _run_entry_point(
        tmp_path, {"command": "normalize-issues", "input": "missing.json", "output": "generator-ready.json"}
    )

    # Assert: 4 is the CLI's exit code for a `NormalizationError`, which a missing input file raises today.
    assert result.returncode == 4, result.stderr
    assert "Error: " in result.stderr
    assert not (tmp_path / "github-output").exists()
