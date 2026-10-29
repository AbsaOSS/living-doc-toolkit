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
import os
import subprocess
import sys
from pathlib import Path

import pytest
from living_doc_utilities.contracts.coverage_matrix import CoverageMatrixResult
from living_doc_utilities.contracts.envelope import Run
from living_doc_utilities.contracts.generator_ready import GeneratorReadyResult
from living_doc_utilities.contracts.io import read_artifact
from living_doc_utilities.contracts.ui_test_catalog import UiTestCatalogResult

import main
from main import run

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_SOURCE = REPO_ROOT / "tests" / "fixtures" / "collector-gh" / "doc-source.json"
UI_TESTS = REPO_ROOT / "tests" / "fixtures" / "collector-gh" / "ui-tests.json"
CLI = [sys.executable, "-I", "-m", "living_doc_cli.main"]
COMMANDS = ["normalize-docs", "normalize-tests", "coverage-matrix"]
# The CI run the entry point runs in, as GitHub Actions sets it.
RUN_CONTEXT = {
    "GITHUB_RUN_ID": "4242",
    "GITHUB_RUN_ATTEMPT": "2",
    "GITHUB_ACTOR": "octocat",
    "GITHUB_WORKFLOW": "docs",
    "GITHUB_REF": "refs/heads/master",
    "GITHUB_SHA": "3f2c1ab",
}


def _errors(err: str) -> list[str]:
    return [line for line in err.splitlines() if line.startswith("[ERROR]")]


def _set_inputs(monkeypatch, **inputs: str) -> None:
    for name, value in inputs.items():
        monkeypatch.setenv(f"INPUT_{name.upper()}", value)


def _set_required_inputs(monkeypatch, command: str) -> None:
    _set_inputs(monkeypatch, command=command, input="in.json", output="out.json")
    if command == "coverage-matrix":
        _set_inputs(monkeypatch, tests_input="tests.json")


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
        "[ERROR] Input `command` is required; valid commands: normalize-docs, normalize-tests, coverage-matrix."
    ]
    assert cli.runs == []


def test_an_unknown_command_fails_with_one_line_listing_the_valid_commands(cli, monkeypatch, capsys):
    # Arrange
    _set_inputs(monkeypatch, command="normalize\ndocs", input="in.json", output="out.json")

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [
        "[ERROR] Input `command` is 'normalize\\ndocs', not a valid command; "
        "valid commands: normalize-docs, normalize-tests, coverage-matrix."
    ]
    assert cli.runs == []


def test_the_action_runs_the_three_commands_it_declares():
    # Assert
    assert list(main.COMMAND_INPUTS) == COMMANDS


@pytest.mark.parametrize(
    ("inputs", "untaken"),
    [
        ({"command": "normalize-docs", "tests_input": "tests.json"}, "tests-input"),
        ({"command": "normalize-docs", "fail_under": "80"}, "fail-under"),
        ({"command": "normalize-tests", "view": "release"}, "view"),
        ({"command": "normalize-tests", "document_title": "Title"}, "document-title"),
        ({"command": "normalize-tests", "tests_input": "tests.json"}, "tests-input"),
        ({"command": "normalize-tests", "fail_under": "80"}, "fail-under"),
        ({"command": "coverage-matrix", "tests_input": "tests.json", "document_title": "Title"}, "document-title"),
    ],
)
def test_an_input_the_command_does_not_take_fails_with_one_line_naming_it(cli, monkeypatch, capsys, inputs, untaken):
    # Arrange: the untaken input is rejected before the command runs.
    _set_inputs(monkeypatch, input="in.json", output="out.json", **inputs)

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [f"[ERROR] Input `{untaken}` is not taken by command `{inputs['command']}`; leave it empty."]
    assert cli.runs == []


@pytest.mark.parametrize(
    ("command", "missing"),
    [
        ("normalize-docs", "input"),
        ("normalize-docs", "output"),
        ("normalize-tests", "input"),
        ("normalize-tests", "output"),
        ("coverage-matrix", "input"),
        ("coverage-matrix", "output"),
        ("coverage-matrix", "tests-input"),
    ],
)
def test_a_required_input_left_empty_fails_with_one_line_naming_it(cli, monkeypatch, capsys, command, missing):
    # Arrange
    _set_required_inputs(monkeypatch, command)
    monkeypatch.setenv(f"INPUT_{missing.replace('-', '_').upper()}", "  ")

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [f"[ERROR] Input `{missing}` is required by command `{command}`."]
    assert cli.runs == []


def test_an_output_with_a_line_break_fails_with_one_line_naming_it(cli, monkeypatch, capsys):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-docs", input="in.json", output="out\nput.json")

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
    _set_required_inputs(monkeypatch, "coverage-matrix")
    _set_inputs(monkeypatch, fail_under=value)

    # Act
    code, errors = _run_failing(capsys)

    # Assert
    assert code == 1
    assert errors == [f"[ERROR] Input `fail-under` is {value!r}, not a number."]
    assert cli.runs == []


def test_an_empty_input_the_command_does_not_take_is_not_passed(cli, monkeypatch, capsys):
    # Arrange: `action.yml` passes every input, an unset optional one as its empty default.
    _set_inputs(
        monkeypatch,
        command="normalize-tests",
        input="ui-tests.json",
        output="out.json",
        view="",
        document_title="",
        tests_input="",
        fail_under="",
    )

    # Act
    run()

    # Assert
    assert _errors(capsys.readouterr().err) == []
    assert cli.runs == [[*CLI, "normalize-tests", "--input=ui-tests.json", f"--output={Path.cwd() / 'out.json'}"]]


def test_coverage_matrix_gets_each_input_as_its_option_and_the_output_as_an_absolute_path(cli, monkeypatch):
    # Arrange
    _set_inputs(
        monkeypatch,
        command="coverage-matrix",
        input="doc-source.json",
        tests_input="ui-tests.json",
        output="coverage-matrix.json",
        view="release",
        fail_under="72.5",
    )

    # Act
    run()

    # Assert
    assert cli.runs == [
        [
            *CLI,
            "coverage-matrix",
            "--doc-input=doc-source.json",
            f"--output={Path.cwd() / 'coverage-matrix.json'}",
            "--view=release",
            "--tests-input=ui-tests.json",
            "--fail-under=72.5",
        ]
    ]


def test_normalize_docs_gets_each_input_as_its_option_and_the_output_as_an_absolute_path(cli, monkeypatch):
    # Arrange
    _set_inputs(
        monkeypatch,
        command="normalize-docs",
        input="doc-source.json",
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
            "normalize-docs",
            "--input=doc-source.json",
            f"--output={Path.cwd() / 'out' / 'generator-ready.json'}",
            "--view=release",
            "--document-title=-Release notes",
        ]
    ]


def test_an_optional_input_left_empty_is_not_passed_so_the_cli_default_applies(cli, monkeypatch):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-docs", input="doc-source.json", output="generator-ready.json")

    # Act
    run()

    # Assert
    assert cli.runs == [
        [*CLI, "normalize-docs", "--input=doc-source.json", f"--output={Path.cwd() / 'generator-ready.json'}"]
    ]


def _assert_verbose_run(cli: _FakeCli, err: str) -> None:
    # `--verbose` is the group's option, so it comes before the command name.
    assert cli.runs[0][len(CLI) :] == [
        "--verbose",
        "normalize-docs",
        "--input=in.json",
        f"--output={Path.cwd() / 'out.json'}",
    ]
    debug = [line for line in err.splitlines() if line.startswith("[DEBUG]")]
    assert len(debug) == 1
    assert debug[0].startswith("[DEBUG] Living Documentation Toolkit action - command line: ")
    assert " living_doc_cli.main --verbose normalize-docs " in debug[0]


@pytest.mark.parametrize("value", ["true", "TRUE", " True "])
def test_verbose_logging_true_passes_verbose_before_the_command_and_logs_the_command_line_at_debug(
    cli, monkeypatch, capsys, value
):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-docs", input="in.json", output="out.json", verbose_logging=value)

    # Act
    run()

    # Assert
    _assert_verbose_run(cli, capsys.readouterr().err)


@pytest.mark.parametrize("value", ["false", ""])
def test_a_rerun_with_debug_logging_turns_verbose_on_without_verbose_logging(cli, monkeypatch, capsys, value):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-docs", input="in.json", output="out.json", verbose_logging=value)
    monkeypatch.setenv("RUNNER_DEBUG", "1")

    # Act
    run()

    # Assert
    _assert_verbose_run(cli, capsys.readouterr().err)


@pytest.mark.parametrize("value", ["false", "", "yes"])
def test_verbose_logging_off_passes_no_verbose_and_logs_no_debug_line(cli, monkeypatch, capsys, value):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-docs", input="in.json", output="out.json", verbose_logging=value)

    # Act
    run()

    # Assert
    assert "--verbose" not in cli.runs[0]
    assert not [line for line in capsys.readouterr().err.splitlines() if line.startswith("[DEBUG]")]


@pytest.mark.parametrize("value", ["0", "", "true"])
def test_runner_debug_other_than_1_leaves_verbose_off(cli, monkeypatch, value):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-docs", input="in.json", output="out.json")
    monkeypatch.setenv("RUNNER_DEBUG", value)

    # Act
    run()

    # Assert
    assert "--verbose" not in cli.runs[0]


def test_a_successful_run_sets_the_output_path_to_the_absolute_output(cli, monkeypatch, tmp_path):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-docs", input="in.json", output="out/generator-ready.json")
    monkeypatch.setenv("GITHUB_OUTPUT", os.fspath(tmp_path / "github-output"))

    # Act
    run()

    # Assert
    assert (tmp_path / "github-output").read_text(encoding="utf-8") == (
        f"output-path={tmp_path / 'out' / 'generator-ready.json'}\n"
    )


def test_a_run_outside_github_actions_sets_no_output_and_says_so(cli, monkeypatch, capsys):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-docs", input="in.json", output="out.json")

    # Act
    run()

    # Assert
    assert "[INFO] Living Documentation Toolkit action - no `GITHUB_OUTPUT`" in capsys.readouterr().err


def test_a_failed_command_ends_the_run_with_its_exit_code_and_sets_no_output(cli, monkeypatch, capsys, tmp_path):
    # Arrange
    _set_inputs(monkeypatch, command="normalize-docs", input="in.json", output="out.json")
    monkeypatch.setenv("GITHUB_OUTPUT", os.fspath(tmp_path / "github-output"))
    cli.returncode = 3

    # Act
    code, errors = _run_failing(capsys)

    # Assert: the CLI prints its own error line.
    assert code == 3
    assert errors == []
    assert not (tmp_path / "github-output").exists()


def test_an_output_file_that_cannot_be_written_fails_with_one_line(cli, monkeypatch, capsys, tmp_path):
    # Arrange: a directory where the output file should be.
    _set_inputs(monkeypatch, command="normalize-docs", input="in.json", output="out.json")
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
    env.update(RUN_CONTEXT)
    env["GITHUB_OUTPUT"] = os.fspath(tmp_path / "github-output")
    return subprocess.run(
        [sys.executable, "-E", os.fspath(REPO_ROOT / "main.py")],
        capture_output=True,
        check=False,
        cwd=tmp_path,
        env=env,
        text=True,
    )


@pytest.mark.parametrize(
    ("inputs", "view"),
    [
        ({}, "inner"),
        ({"view": "release", "document-title": "Checkout tests"}, "release"),
        # `--verbose` comes before the command name, as the group takes it.
        ({"verbose-logging": "true"}, "inner"),
    ],
)
def test_the_entry_point_runs_normalize_docs_over_the_fixture_and_sets_the_output_path(tmp_path, inputs, view):
    # Act
    result = _run_entry_point(
        tmp_path,
        {"command": "normalize-docs", "input": os.fspath(DOC_SOURCE), "output": "out/generator-ready.json", **inputs},
    )

    # Assert
    assert result.returncode == 0, result.stderr
    assert _errors(result.stderr) == []
    written = read_artifact(tmp_path / "out" / "generator-ready.json", expected="generator-ready")
    assert isinstance(written, GeneratorReadyResult)
    assert written.document.view == view
    assert written.document.title == inputs.get("document-title", "living-doc-examples")
    # `-I` drops no `GITHUB_*` variable, so the CLI records the run.
    assert written.metadata.run == Run(
        run_id="4242", run_attempt="2", actor="octocat", workflow="docs", ref="refs/heads/master", sha="3f2c1ab"
    )
    assert (tmp_path / "github-output").read_text(encoding="utf-8") == (
        f"output-path={tmp_path / 'out' / 'generator-ready.json'}\n"
    )


def test_the_entry_point_ends_a_failed_normalize_docs_with_the_clis_line_and_exit_code(tmp_path):
    # Act
    result = _run_entry_point(
        tmp_path, {"command": "normalize-docs", "input": "missing.json", "output": "generator-ready.json"}
    )

    # Assert
    assert result.returncode == 1, result.stderr
    assert _errors(result.stderr) == [
        "[ERROR] [MISSING_INPUT] documentation input 'missing.json': no such file; check the path, or run the step "
        "that writes it first"
    ]
    assert not (tmp_path / "generator-ready.json").exists()
    assert not (tmp_path / "github-output").exists()


def _coverage_matrix_inputs(**inputs: str) -> dict[str, str]:
    return {
        "command": "coverage-matrix",
        "input": os.fspath(DOC_SOURCE),
        "tests-input": os.fspath(UI_TESTS),
        "output": "out/coverage-matrix.json",
        **inputs,
    }


@pytest.mark.parametrize(
    ("inputs", "view"),
    [
        ({}, "inner"),
        # At the matrix's own percentage, the gate passes.
        ({"view": "release", "fail-under": "55.6"}, "release"),
    ],
)
def test_the_entry_point_runs_coverage_matrix_over_the_fixture_pair_and_sets_the_output_path(tmp_path, inputs, view):
    # Act
    result = _run_entry_point(tmp_path, _coverage_matrix_inputs(**inputs))

    # Assert
    assert result.returncode == 0, result.stderr
    assert _errors(result.stderr) == []
    written = read_artifact(tmp_path / "out" / "coverage-matrix.json", expected="coverage-matrix")
    assert isinstance(written, CoverageMatrixResult)
    assert written.document.view == view
    assert [entity.entity_id for entity in written.entities] == ["US-001", "FUNC-001", "FUNC-002"]
    summary = written.summary
    assert (summary.counted_acs, summary.covered_acs, summary.not_covered_acs, summary.coverage_pct) == (6, 3, 2, 55.6)
    assert written.metadata.run.run_id == RUN_CONTEXT["GITHUB_RUN_ID"]
    assert written.metadata.producer.build is None
    assert (tmp_path / "github-output").read_text(encoding="utf-8") == (
        f"output-path={tmp_path / 'out' / 'coverage-matrix.json'}\n"
    )


def test_the_entry_point_ends_a_coverage_matrix_below_fail_under_with_the_clis_line_and_sets_no_output(tmp_path):
    # Act
    result = _run_entry_point(tmp_path, _coverage_matrix_inputs(**{"fail-under": "55.7"}))

    # Assert: the matrix is written before the gate, and the step fails.
    assert result.returncode == 1, result.stderr
    assert _errors(result.stderr) == [
        "[ERROR] coverage-matrix - the coverage percentage, 55.6, is below --fail-under 55.7."
    ]
    assert (tmp_path / "out" / "coverage-matrix.json").exists()
    assert not (tmp_path / "github-output").exists()


def test_the_entry_point_runs_normalize_tests_over_the_fixture_and_sets_the_output_path(tmp_path):
    output_path = "out/ui-test-catalog.json"

    result = _run_entry_point(
        tmp_path,
        {"command": "normalize-tests", "input": os.fspath(UI_TESTS), "output": output_path},
    )

    assert result.returncode == 0, result.stderr
    assert _errors(result.stderr) == []
    written = read_artifact(tmp_path / output_path, expected="ui-test-catalog")
    assert isinstance(written, UiTestCatalogResult)
    assert written.document.view == "inner"
    assert [feature_file.feature_file for feature_file in written.feature_files] == [
        "AbsaOSS/living-doc/docs/examples/gherkin/liv_doc_func/func-001-validate-password-strength.feature",
        "AbsaOSS/living-doc/docs/examples/gherkin/liv_doc_us/us-001-customer-login.feature",
    ]
    assert [(group.entity_id, len(group.scenarios)) for group in written.feature_files[0].linked_to_functionality] == [
        ("FUNC-001", 4)
    ]
    assert [(group.entity_id, len(group.scenarios)) for group in written.feature_files[1].linked_to_user_story] == [
        ("US-001", 2)
    ]
    assert written.metadata.run.run_id == RUN_CONTEXT["GITHUB_RUN_ID"]
    assert written.metadata.producer.build is None
    assert (tmp_path / "github-output").read_text(encoding="utf-8") == (f"output-path={tmp_path / output_path}\n")


def test_a_module_in_the_callers_working_directory_does_not_shadow_the_clis(tmp_path):
    # Arrange: the run step runs in the caller's checkout, which may hold a module named like one the CLI imports.
    (tmp_path / "click.py").write_text("import sys\nsys.exit(42)\n", encoding="utf-8")

    def cli_help(*flags: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, *flags, "-m", "living_doc_cli.main", "--help"],
            capture_output=True,
            check=False,
            cwd=tmp_path,
            text=True,
        )

    # Act
    isolated = cli_help("-I")
    shadowed = cli_help()

    # Assert: `-I`, as the entry point runs the CLI, keeps the working directory off `sys.path`; without it the
    # `click.py` there is what the CLI imports.
    assert isolated.returncode == 0, isolated.stderr
    assert "Living Documentation Toolkit CLI" in isolated.stdout
    assert shadowed.returncode == 42
