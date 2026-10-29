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
"""
The promises of `local-integration.sh`, an operator's run of the real toolkit outside any workflow, and of
`tools/local_integration.py`, its Python half: every output is re-read with `read_artifact` and reported, and forwards
every warning of the inputs it read; the configuration is read as data and never sourced; a misconfiguration or a
failed command stops the run with one actionable stderr line; no token reaches anything the script prints, starts or
writes; and no workflow runs it.

The script runs end to end here in a copy whose venv is seeded: its interpreter is this test's, which has the packages
installed already, so the run builds no venv and needs no network. Everything after the install runs for real.
"""

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Optional

import pytest
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.envelope import ContractWarning
from living_doc_utilities.contracts.io import read_artifact

from tools.local_integration import FIRST_OCCURRENCES, NotForwarded, main, report, warnings_by_code

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "local-integration.sh"
EXAMPLE_CONFIG = REPO_ROOT / ".env.local.example"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
DOC_SOURCE = REPO_ROOT / "tests" / "fixtures" / "collector-gh" / "doc-source.json"
UI_TESTS = REPO_ROOT / "tests" / "fixtures" / "collector-gh" / "ui-tests.json"

# A token-shaped value no real credential has; the script must print it nowhere, hand it to no child and write it to
# no output.
TOKEN = "ghp_dummy_local_integration_token"

# Per output contract: the command that writes it, its CLI arguments over the fixture pair, and the inputs it reads.
COMMANDS = {
    "generator-ready": ("normalize-docs", [f"--input={DOC_SOURCE}"], [DOC_SOURCE]),
    "ui-test-catalog": ("normalize-tests", [f"--input={UI_TESTS}"], [UI_TESTS]),
    "coverage-matrix": (
        "coverage-matrix",
        [f"--doc-input={DOC_SOURCE}", f"--tests-input={UI_TESTS}"],
        [DOC_SOURCE, UI_TESTS],
    ),
}


def _inputs(contract: str) -> list[str]:
    return [os.fspath(path) for path in COMMANDS[contract][2]]


# --- warnings by code ----------------------------------------------------------------------------------------------


def _warning(message: str, code: str = "UNRESOLVED_RELATION", **where) -> ContractWarning:
    return ContractWarning(code=code, message=message, **where)


def test_no_warnings_is_the_header_alone():
    # Act & Assert
    assert warnings_by_code([]) == ["  warnings: 0"]


def test_warnings_are_grouped_by_sorted_code_each_in_output_order():
    # Arrange
    warnings = [
        _warning("z first", code="ZETA_CODE"),
        _warning("a only", code="ALPHA_CODE"),
        _warning("z second", code="ZETA_CODE"),
    ]

    # Act & Assert
    assert warnings_by_code(warnings) == [
        "  warnings: 3",
        "    ALPHA_CODE: 1",
        "      - a only",
        "    ZETA_CODE: 2",
        "      - z first",
        "      - z second",
    ]


def test_ten_occurrences_of_a_code_are_listed_and_the_rest_counted():
    # Arrange
    warnings = [_warning(f"w{n:02d}") for n in range(12)] + [_warning("ten", code="TEN")] * 10

    # Act & Assert: a code with exactly ten is listed whole.
    assert FIRST_OCCURRENCES == 10
    assert warnings_by_code(warnings) == [
        "  warnings: 22",
        "    TEN: 10",
        *["      - ten"] * 10,
        "    UNRESOLVED_RELATION: 12",
        *(f"      - w{n:02d}" for n in range(10)),
        "      ... and 2 more",
    ]


@pytest.mark.parametrize(
    ("where", "expected"),
    [
        (
            {"path": "us/loans.feature", "line_no": 12, "entity_id": "US-7", "ac_id": "US-7-02"},
            "us/loans.feature:12 US-7/US-7-02 msg",
        ),
        (
            {"context": "source_input='doc-source-v1.0.0' entity_id='FEAT-3'", "entity_id": "FEAT-3"},
            "source_input='doc-source-v1.0.0' entity_id='FEAT-3' FEAT-3 msg",
        ),
        ({"path": "us/loans.feature", "context": "not shown when a path is known"}, "us/loans.feature msg"),
        ({}, "- msg"),
    ],
    ids=["everything", "context", "path-over-context", "none"],
)
def test_an_occurrence_says_where_and_about_what(where, expected):
    # Act & Assert: `<path or context or ->[:line] <entity>/<ac> <message>`, empty parts dropped.
    assert warnings_by_code([_warning("msg", **where)]) == [
        "  warnings: 1",
        "    UNRESOLVED_RELATION: 1",
        f"      {expected}",
    ]


# --- report: one output re-read with read_artifact -----------------------------------------------------------------


@pytest.fixture(name="written", scope="module")
def _written(tmp_path_factory) -> dict[str, str]:
    """Each output contract's file, written by the real CLI over the fixture pair."""
    root = tmp_path_factory.mktemp("toolkit")
    written = {}
    for contract, (command, arguments, _) in COMMANDS.items():
        written[contract] = os.fspath(root / f"{contract}.json")
        subprocess.run(
            [sys.executable, "-I", "-m", "living_doc_cli.main", command, *arguments, f"--output={written[contract]}"],
            capture_output=True,
            check=True,
            timeout=120,
        )
    return written


def test_the_report_describes_the_output_it_re_read_and_its_input(written):
    # Arrange
    path = written["generator-ready"]
    output = read_artifact(path, "generator-ready")
    source = read_artifact(DOC_SOURCE, "doc-source")
    producer = output.metadata.producer
    cardinality = output.metadata.stats.cardinality

    # Act
    lines = report(path, "generator-ready", 1234, _inputs("generator-ready"))

    # Assert: what was read, that it is valid, who wrote it, how long it took and how big it is.
    assert lines[:5] == [
        f"generator-ready: {path}",
        "  contract: generator-ready-v1.0.0, valid (read_artifact)",
        f"  producer: AbsaOSS/living-doc-toolkit {producer.version}, living-doc-utilities {version('living-doc-utilities')}",
        "  time: 1.23 s",
        f"  size: {os.path.getsize(path)} bytes",
    ]
    # Assert: every cardinality counter in the model's order, a mapping as sorted pairs.
    source_inputs_at = lines.index("  source_inputs: 1")
    assert lines[5] == "  stats.cardinality:"
    assert [line.split(":")[0].strip() for line in lines[6:source_inputs_at]] == list(cardinality.model_dump())
    assert "    entities_by_type: DocumentedFeature=2, DocumentedFunctionality=2, DocumentedUserStory=1" in lines
    # Assert: the input it records - the producer that wrote it and what it documents - then its warnings, all
    # forwarded from the one input.
    warnings_at = source_inputs_at + 5
    assert lines[source_inputs_at + 1 : warnings_at] == [
        "    doc-source-v1.0.0",
        f"      producer: AbsaOSS/living-doc-collector-gh {source.metadata.producer.version}, "
        f"living-doc-utilities {source.metadata.producer.utilities_version}",
        "      project_id: living-doc-examples",
        "      repositories: AbsaOSS/living-doc",
    ]
    assert lines[warnings_at:-1] == warnings_by_code(output.warnings)
    assert lines[-1] == "  forwarded: 2 of 2 from doc-source-v1.0.0"


def test_the_coverage_matrix_report_adds_the_root_summary_and_counts_each_input(written):
    # Act
    lines = report(written["coverage-matrix"], "coverage-matrix", 0, _inputs("coverage-matrix"))

    # Assert: both inputs recorded, the matrix's own totals, and each input's warnings counted on their own.
    assert "  source_inputs: 2" in lines
    assert [line.strip() for line in lines if line.startswith("    ") and line.strip().endswith("-v1.0.0")] == [
        "doc-source-v1.0.0",
        "ui-tests-v1.0.0",
    ]
    summary_at = lines.index("  summary:")
    assert lines[summary_at + 1 : summary_at + 6] == [
        "    counted_acs: 6",
        "    covered_acs: 3",
        "    partially_covered_acs: 1",
        "    not_covered_acs: 2",
        "    coverage_pct: 55.6",
    ]
    assert lines[summary_at + 6] == "  warnings: 2"
    assert lines[-2:] == ["  forwarded: 2 of 2 from doc-source-v1.0.0", "  forwarded: 0 of 0 from ui-tests-v1.0.0"]


def test_an_output_with_no_warnings_shows_an_empty_mapping_as_a_dash(written):
    # Act
    lines = report(written["ui-test-catalog"], "ui-test-catalog", 0, _inputs("ui-test-catalog"))

    # Assert
    assert "    warnings_by_code: -" in lines
    assert "  summary:" not in lines
    assert lines[-2:] == ["  warnings: 0", "  forwarded: 0 of 0 from ui-tests-v1.0.0"]


@pytest.mark.parametrize(("elapsed_ms", "shown"), [(0, "0.00"), (125600, "125.60")])
def test_the_time_is_shown_in_seconds_to_two_decimals(written, elapsed_ms, shown):
    # Act & Assert
    assert report(written["ui-test-catalog"], "ui-test-catalog", elapsed_ms, _inputs("ui-test-catalog"))[3] == (
        f"  time: {shown} s"
    )


def test_main_prints_the_report_and_exits_zero(written, capsys):
    # Arrange
    arguments = [written["coverage-matrix"], "coverage-matrix", "1234", *_inputs("coverage-matrix")]

    # Act
    code = main(["report", *arguments])

    # Assert
    out, err = capsys.readouterr()
    assert code == 0
    assert err == ""
    assert out == "\n".join(report(written["coverage-matrix"], "coverage-matrix", 1234, arguments[3:])) + "\n"


def _main_fails(capsys, path, contract: str, *inputs: str) -> str:
    """Run `main` on one output, expecting the one-line failure; return that line."""
    code = main(["report", os.fspath(path), contract, "5", *(inputs or [os.fspath(DOC_SOURCE)])])
    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    [line] = err.splitlines()
    return line


def test_main_reports_a_missing_output_and_a_file_that_is_not_json_with_one_line(tmp_path, capsys):
    # Arrange
    missing = tmp_path / "generator-ready.json"
    not_json = tmp_path / "not-json.json"
    not_json.write_text("{ not json", encoding="utf-8")

    # Act & Assert: the missing file is named.
    line = _main_fails(capsys, missing, "generator-ready")
    assert line.startswith("generator-ready: the output is not valid: ")
    assert "generator-ready.json" in line
    assert _main_fails(capsys, not_json, "generator-ready").startswith("generator-ready: the output is not valid: ")


def test_an_output_of_another_contract_fails_validation(written, capsys):
    # Act & Assert: `report` raises the contract's own error...
    with pytest.raises(ContractError) as raised:
        report(written["ui-test-catalog"], "generator-ready", 5, [os.fspath(DOC_SOURCE)])
    assert raised.value.code is Code.CONTRACT_MISMATCH

    # ...and `main` turns it into one stderr line and exit 1.
    assert _main_fails(capsys, written["ui-test-catalog"], "generator-ready") == (
        "generator-ready: the output is not valid: [CONTRACT_MISMATCH] expected one of ['generator-ready'], "
        "got 'ui-test-catalog'"
    )


def test_an_output_that_drops_an_input_warning_fails(written, tmp_path, capsys):
    # Arrange: the output as written, less its first forwarded warning; it still passes its contract.
    payload = json.loads(Path(written["generator-ready"]).read_text(encoding="utf-8"))
    payload["warnings"] = payload["warnings"][1:]
    dropped = tmp_path / "generator-ready.json"
    dropped.write_text(json.dumps(payload), encoding="utf-8")
    read_artifact(dropped, "generator-ready")

    # Act & Assert
    with pytest.raises(NotForwarded):
        report(os.fspath(dropped), "generator-ready", 5, [os.fspath(DOC_SOURCE)])
    assert _main_fails(capsys, dropped, "generator-ready") == (
        f"generator-ready: forwards 1 of the 2 warnings of its doc-source-v1.0.0 input '{DOC_SOURCE}'; "
        "a command forwards every input warning"
    )


def test_a_tests_input_warning_is_counted_against_that_input_and_must_be_forwarded(tmp_path, capsys):
    # Arrange: the fixture's tests input with a warning of its own, and the catalog the real CLI writes from it.
    payload = json.loads(UI_TESTS.read_text(encoding="utf-8"))
    payload["warnings"].append({"code": "EMPTY_SOURCE", "message": "no feature file", "path": "features"})
    tests_input = tmp_path / "ui-tests.json"
    tests_input.write_text(json.dumps(payload), encoding="utf-8")
    catalog = tmp_path / "ui-test-catalog.json"
    subprocess.run(
        [sys.executable, "-I", "-m", "living_doc_cli.main", "normalize-tests", f"--input={tests_input}"]
        + [f"--output={catalog}"],
        capture_output=True,
        check=True,
        timeout=120,
    )

    # Act & Assert: the warning is forwarded and counted...
    assert report(os.fspath(catalog), "ui-test-catalog", 5, [os.fspath(tests_input)])[-1] == (
        "  forwarded: 1 of 1 from ui-tests-v1.0.0"
    )

    # ...and an output without it fails.
    output = json.loads(catalog.read_text(encoding="utf-8"))
    output["warnings"] = []
    catalog.write_text(json.dumps(output), encoding="utf-8")
    assert _main_fails(capsys, catalog, "ui-test-catalog", os.fspath(tests_input)).startswith(
        "ui-test-catalog: forwards 0 of the 1 warnings of its ui-tests-v1.0.0 input "
    )


def test_main_spells_out_the_control_characters_a_file_carries(written, tmp_path, capsys):
    # Arrange: a forwarded warning whose message would clear the terminal and forge a report line.
    payload = json.loads(Path(written["generator-ready"]).read_text(encoding="utf-8"))
    payload["warnings"][0]["message"] = "\x1b[2J\n  forwarded: 9 of 9 from doc-source-v1.0.0"
    crafted = tmp_path / "generator-ready.json"
    crafted.write_text(json.dumps(payload), encoding="utf-8")

    # Act
    code = main(["report", os.fspath(crafted), "generator-ready", "5", os.fspath(DOC_SOURCE)])

    # Assert: the message stays on its own line, its control characters spelled out.
    out, _ = capsys.readouterr()
    assert code == 0
    assert "\x1b" not in out
    assert "  forwarded: 9 of 9 from doc-source-v1.0.0" not in out.splitlines()
    assert "\\x1b[2J\\n  forwarded: 9 of 9 from doc-source-v1.0.0" in out


# --- static promises over the script and its configuration --------------------------------------------------------


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", os.fspath(REPO_ROOT), *args], capture_output=True, check=False, text=True, timeout=60
    )


def _shell_code() -> list[str]:
    """The script's lines without comments: in bash a `#` that starts a word starts a comment."""
    return [re.sub(r"(?:^|\s)#.*", "", line).strip() for line in SCRIPT.read_text(encoding="utf-8").splitlines()]


def _script_list(name: str) -> list[str]:
    """A whitespace-separated list the script assigns in double quotes, e.g. `KEYS`."""
    match = re.search(rf'^{name}="([^"]*)"', SCRIPT.read_text(encoding="utf-8"), re.MULTILINE)
    assert match, f"{name} is not assigned in {SCRIPT.name}"
    return match.group(1).split()


def _example_settings() -> dict[str, str]:
    settings = {}
    for line in EXAMPLE_CONFIG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, separator, value = line.partition("=")
            assert separator, f"not a KEY=value line in {EXAMPLE_CONFIG.name}: {line!r}"
            settings[key] = value
    return settings


def test_the_script_is_committed_executable():
    # Assert: `./local-integration.sh` runs on a fresh clone with no `chmod`.
    entry = _git("ls-files", "-s", SCRIPT.name).stdout
    assert entry.startswith("100755 "), f"{SCRIPT.name} is not committed with mode 100755: {entry!r}"


def test_the_script_keeps_lf_line_ends_on_every_checkout():
    # Assert: bash, Git Bash on Windows included, fails on a CRLF line.
    assert _git("check-attr", "eol", "--", SCRIPT.name).stdout.strip() == f"{SCRIPT.name}: eol: lf"
    assert b"\r" not in SCRIPT.read_bytes()


def test_no_workflow_runs_the_script():
    # Arrange
    workflows = [path for path in WORKFLOWS.rglob("*") if path.is_file()]

    # Assert: the script is an operator's tool; CI keeps `integration.yml`.
    assert workflows
    assert [
        path.name for path in workflows if re.search(r"local[-_]integration", path.read_text(encoding="utf-8"))
    ] == []


def test_the_example_documents_exactly_the_settings_the_script_reads():
    # Assert: a setting added to the script is added to the example the operator copies, and the example names
    # nothing else - no token.
    assert set(_example_settings()) == set(_script_list("KEYS"))


def test_the_example_runs_over_the_fixture_pair_as_committed():
    # Arrange
    required = _script_list("REQUIRED")
    example = _example_settings()

    # Assert: a copied example passes the required-key check, and both inputs exist relative to the repository root.
    assert required == ["DOC_INPUT", "TESTS_INPUT"]
    assert set(required) <= set(_script_list("KEYS"))
    assert (REPO_ROOT / example["DOC_INPUT"]).resolve() == DOC_SOURCE
    assert (REPO_ROOT / example["TESTS_INPUT"]).resolve() == UI_TESTS


def test_the_only_install_is_the_runtime_requirements_into_the_scripts_venv():
    # Assert: pip is always the venv's own, and installs `requirements.txt` alone - what the action installs.
    installs = [line for line in _shell_code() if re.search(r"\bpip\b", line) and re.search(r"\binstall\b", line)]
    assert installs == ['run "$VPY" -m pip install --disable-pip-version-check -r requirements.txt']
    assert "requirements-dev" not in SCRIPT.read_text(encoding="utf-8")


def test_the_script_unsets_the_pip_variables_action_yml_unsets():
    # Assert: the install lands in the venv as the action's does (DEVELOPER.md § Action venv).
    assert "unset PIP_TARGET PIP_PREFIX PIP_USER PIP_ROOT PIP_PYTHON PYTHONPATH" in _shell_code()


def test_the_script_never_sources_or_evaluates_a_file():
    # Arrange: the first word of every command, a line split at `;`, `&&` and `||`.
    commands = [
        segment.split()[0] for line in _shell_code() for segment in re.split(r";|&&|\|\|", line) if segment.split()
    ]

    # Assert: `.env.local` is read as data; a sourced file runs whatever it holds and exports any token in it.
    assert commands
    assert {"source", ".", "eval"} & set(commands) == set()


@pytest.mark.parametrize(
    "path", [".env.local", ".venv-local-integration/x", "output/toolkit/x"], ids=["config", "venv", "output"]
)
def test_what_the_script_reads_and_writes_locally_is_git_ignored(path):
    # Assert
    assert _git("check-ignore", "-q", "--no-index", path).returncode == 0, f"{path} is not git-ignored"


def test_the_example_config_is_not_git_ignored():
    # Assert: the pattern for `.env.local` does not swallow the committed example.
    assert _git("check-ignore", "-q", "--no-index", EXAMPLE_CONFIG.name).returncode == 1


# --- the script's behaviour, run with bash in a copy ---------------------------------------------------------------


def _bash() -> Optional[str]:
    """bash to run the script with: Git Bash on Windows, never `System32\\bash.exe`, the WSL launcher."""
    bash = shutil.which("bash")
    if bash and sys.platform == "win32" and "system32" in (part.lower() for part in Path(bash).parts):
        return None
    return bash


BASH = _bash()
needs_bash = pytest.mark.skipif(BASH is None, reason="no bash to run local-integration.sh with (Git Bash on Windows)")

# Process start-up is slow on Git Bash for Windows; a `--check` there takes seconds, a run tens of seconds.
TIMEOUT = 300

# A configuration the `workspace` fixture satisfies: the inputs are in `../inputs`, relative to the script's copy.
VALID_CONFIG = {
    "DOC_INPUT": "../inputs/doc-source.json",
    "TESTS_INPUT": "../inputs/ui-tests.json",
    "VIEW": "inner",
    "OUT_DIR": "./output",
    "PYTHON": Path(sys.executable).as_posix(),
}


@pytest.fixture(name="workspace")
def _workspace(tmp_path):
    """A copy of the script in a directory of its own, beside a copy of the fixture pair."""
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copyfile(SCRIPT, repo / SCRIPT.name)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    shutil.copyfile(DOC_SOURCE, inputs / DOC_SOURCE.name)
    shutil.copyfile(UI_TESTS, inputs / UI_TESTS.name)
    return repo


def _write_config(repo: Path, config: dict, extra_lines: tuple = ()) -> None:
    lines = [*(f"{key}={value}" for key, value in config.items()), *extra_lines]
    (repo / ".env.local").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _executable(path: Path, body: str) -> str:
    """A `/bin/sh` script at `path`, executable; its path as `.env.local`'s `PYTHON` takes it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/bin/sh\n{body}", encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path.as_posix()


def _run(repo: Path, *args: str, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    assert BASH is not None
    return subprocess.run(
        [BASH, f"./{SCRIPT.name}", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT,
        check=False,
    )


@needs_bash
def test_check_passes_on_a_valid_configuration_and_builds_nothing(workspace):
    # Arrange
    _write_config(workspace, VALID_CONFIG)

    # Act
    result = _run(workspace, "--check")

    # Assert: one line naming the Python found; no venv, no output directory, nothing else written.
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.startswith(f"local-integration.sh: check passed - Python {platform.python_version()} ")
    assert len(result.stdout.splitlines()) == 1
    assert sorted(path.name for path in workspace.iterdir()) == [".env.local", SCRIPT.name]


@needs_bash
def test_the_config_reads_comments_blank_lines_export_quotes_and_crlf(workspace):
    # Arrange: `.env.local` as an editor on Windows may leave it - CRLF line ends and no final one.
    lines = [
        "# a comment",
        "",
        *(f"{key}={value}" for key, value in VALID_CONFIG.items() if key not in ("DOC_INPUT", "TESTS_INPUT")),
        'export DOC_INPUT="../inputs/doc-source.json"',
        "  TESTS_INPUT='../inputs/ui-tests.json'   ",
    ]
    (workspace / ".env.local").write_bytes("\r\n".join(lines).encode("utf-8"))

    # Act
    result = _run(workspace, "--check")

    # Assert
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "check passed" in result.stdout


@needs_bash
@pytest.mark.parametrize(
    ("setting", "says"),
    [
        ({"DOC_INPUT": None}, "DOC_INPUT is not set in .env.local"),
        ({"TESTS_INPUT": ""}, "TESTS_INPUT is not set in .env.local"),
        ({"DOC_INPUT": "../inputs/missing.json"}, "DOC_INPUT not found: "),
        ({"TESTS_INPUT": "../inputs"}, "TESTS_INPUT is not a file: "),
        ({"VIEW": "draft"}, "VIEW 'draft' is not inner or release"),
        ({"OUT_DIR": "../inputs/ui-tests.json"}, "OUT_DIR is not a directory: "),
    ],
    ids=["absent", "empty", "missing-input", "input-not-a-file", "view", "output-a-file"],
)
def test_a_misconfiguration_fails_with_one_line_naming_it(workspace, setting, says):
    # Arrange
    config = {**VALID_CONFIG, **setting}
    _write_config(workspace, {key: value for key, value in config.items() if value is not None})

    # Act
    result = _run(workspace, "--check")

    # Assert
    assert result.returncode == 1
    assert result.stdout == ""
    [line] = result.stderr.splitlines()
    assert line.startswith(f"local-integration.sh: {says}")


@needs_bash
@pytest.mark.parametrize(("python", "says"), [("missing", "does not run"), ("3.9", "is 3.9.18")])
def test_a_python_that_does_not_run_or_is_older_than_3_10_fails_with_one_line(workspace, tmp_path, python, says):
    # Arrange: no file at all, or a Python 3.9 - it prints its version when asked and fails every other check.
    if python == "missing":
        interpreter = (tmp_path / "no-such-python").as_posix()
    else:
        interpreter = _executable(
            tmp_path / "python3.9", 'case "$2" in\n  *print*) echo 3.9.18 ;;\n  *) exit 1 ;;\nesac\n'
        )
    _write_config(workspace, {**VALID_CONFIG, "PYTHON": interpreter})

    # Act
    result = _run(workspace, "--check")

    # Assert
    assert result.returncode == 1
    assert result.stderr.splitlines() == [
        f"local-integration.sh: needs Python >= 3.10, and '{interpreter}' {says}; set PYTHON in .env.local"
    ]


@needs_bash
def test_a_line_that_is_no_setting_is_reported_by_its_number_alone(workspace):
    # Arrange: a pasted secret, no `=` in it.
    _write_config(workspace, VALID_CONFIG, (TOKEN,))

    # Act
    result = _run(workspace, "--check")

    # Assert
    assert result.returncode == 1
    assert result.stderr.splitlines() == [
        f"local-integration.sh: .env.local:{len(VALID_CONFIG) + 1}: not a KEY=value line"
    ]
    assert TOKEN not in result.stdout + result.stderr


@needs_bash
@pytest.mark.parametrize(
    ("args", "message"),
    [(["--bogus"], "unknown argument '--bogus'"), (["--check", "--check"], "too many arguments")],
    ids=["unknown", "too-many"],
)
def test_an_unknown_argument_fails_with_one_line_of_usage(workspace, args, message):
    # Act
    result = _run(workspace, *args)

    # Assert
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.splitlines() == [f"local-integration.sh: {message}; usage: ./local-integration.sh [--check]"]


@needs_bash
def test_help_prints_the_usage_and_reads_no_config(workspace):
    # Act: the workspace has no `.env.local`, so a help that read it would fail.
    result = _run(workspace, "--help")

    # Assert
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.startswith("usage: ./local-integration.sh [--check]\n")


# --- a whole run, in a copy whose venv is seeded -------------------------------------------------------------------

# Every interpreter the script starts, `PYTHON` and the venv's own: it appends its environment to a record, then runs
# this test's interpreter, which has the toolkit installed. As the venv's, it skips pip: the seeded venv needs no
# install, and the static test above pins the one the script runs.
RECORDING_PYTHON = """env >> "{record}"
case "$1 $2" in "-m pip") exit 0 ;; esac
exec "{python}" "$@"
"""


@pytest.fixture(name="seeded")
def _seeded(workspace, tmp_path):
    """
    The workspace with what a run reads beside the script, and a venv the script reuses: built by the configured
    interpreter, from the `requirements.txt` beside it.
    """
    for name in ("main.py", "requirements.txt", "tools/__init__.py", "tools/local_integration.py"):
        (workspace / name).parent.mkdir(exist_ok=True)
        shutil.copyfile(REPO_ROOT / name, workspace / name)
    body = RECORDING_PYTHON.format(
        record=(tmp_path / "child-environment.txt").as_posix(), python=Path(sys.executable).as_posix()
    )
    _executable(workspace / ".venv-local-integration" / "bin" / "python", body)
    shutil.copyfile(REPO_ROOT / "requirements.txt", workspace / ".venv-local-integration" / "requirements.txt")
    python = _executable(tmp_path / "bin" / "python", body)
    _write_config(workspace, {**VALID_CONFIG, "PYTHON": python})
    return workspace


def _run_env(**variables: str) -> dict:
    # A rebuilt venv would install from the network; with no index it fails at once instead.
    return {**os.environ, "PIP_NO_INDEX": "1", **variables}


def _native(path: Path) -> str:
    """A path as the script hands it to the venv's Python: `C:/...` on Windows, a POSIX path elsewhere."""
    return path.resolve().as_posix()


@needs_bash
def test_a_run_writes_validates_and_reports_the_three_outputs(seeded, tmp_path):
    # Act
    result = _run(seeded, env=_run_env())

    # Assert: the venv was reused, and the header says what ran on what.
    assert result.returncode == 0, result.stderr
    assert " -m venv " not in result.stderr
    output = f"{_native(seeded / 'output')}/toolkit"
    assert result.stdout.splitlines()[:8] == [
        "== local-integration.sh",
        "toolkit:               unknown (not a git checkout)",
        f"living-doc-utilities:  {version('living-doc-utilities')}",
        f"python:                {platform.python_version()} (.venv-local-integration/bin/python)",
        f"documentation input:   {_native(tmp_path / 'inputs' / 'doc-source.json')}",
        f"tests input:           {_native(tmp_path / 'inputs' / 'ui-tests.json')}",
        "view:                  inner",
        f"output:                {output}",
    ]
    # Assert: each command ran through `main.py` with its own inputs only, and its output is valid and reported.
    runs = [line for line in result.stderr.splitlines() if line.startswith("+ env ")]
    assert [sorted(set(re.findall(r"\bINPUT_[A-Z_]+(?==)", run))) for run in runs] == [
        ["INPUT_COMMAND", "INPUT_INPUT", "INPUT_OUTPUT", "INPUT_VIEW"],
        ["INPUT_COMMAND", "INPUT_INPUT", "INPUT_OUTPUT"],
        ["INPUT_COMMAND", "INPUT_INPUT", "INPUT_OUTPUT", "INPUT_TESTS_INPUT", "INPUT_VIEW"],
    ]
    assert all(run.endswith(" -E main.py") for run in runs)
    for contract, (command, _, _) in COMMANDS.items():
        path = f"{output}/{command}/{contract}.json"
        assert read_artifact(path, contract).schema_version == f"{contract}-v1.0.0"
        assert f"{contract}: {path}" in result.stdout
    assert "    coverage_pct: 55.6" in result.stdout
    assert result.stdout.count("  forwarded: 2 of 2 from doc-source-v1.0.0") == 2
    assert (
        result.stdout.splitlines()[-1]
        == f"local-integration.sh: the three outputs are written and valid under {output}"
    )


@needs_bash
def test_a_documentation_input_of_another_contract_stops_the_run_with_the_toolkits_line(seeded, tmp_path):
    # Arrange: the tests input where the documentation input belongs, and a previous run's output.
    python = (tmp_path / "bin" / "python").as_posix()
    _write_config(seeded, {**VALID_CONFIG, "DOC_INPUT": "../inputs/ui-tests.json", "PYTHON": python})
    stale = seeded / "output" / "toolkit" / "coverage-matrix" / "coverage-matrix.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}", encoding="utf-8")

    # Act
    result = _run(seeded, env=_run_env())

    # Assert: the toolkit's own line, then the script's one line naming the command; nothing after it ran.
    assert result.returncode == 1
    errors = result.stderr.splitlines()
    assert [line for line in errors if line.startswith("[ERROR]")] == [
        f"[ERROR] [CONTRACT_MISMATCH] documentation input '{_native(seeded.parent / 'inputs' / 'ui-tests.json')}': "
        "expected one of ['doc-source'], got 'ui-tests'"
    ]
    assert errors[-1] == "local-integration.sh: the toolkit failed in 'normalize-docs' (exit 1); its log is above"
    assert "== normalize-tests" not in result.stdout
    # Assert: the output holds nothing - the previous run's files were cleared, and the failed command wrote none.
    assert [path for path in (seeded / "output").rglob("*") if path.is_file()] == []


@needs_bash
def test_an_output_that_fails_its_report_stops_the_run_with_one_line_naming_the_command(seeded):
    # Arrange: a report that fails, as it does on an output that is not valid or drops an input warning.
    (seeded / "tools" / "local_integration.py").write_text(
        'import sys\nprint("generator-ready: the output is not valid: stub", file=sys.stderr)\nsys.exit(1)\n',
        encoding="utf-8",
    )

    # Act
    result = _run(seeded, env=_run_env())

    # Assert: the report's line, then the script's; no later command ran.
    assert result.returncode == 1
    assert result.stderr.splitlines()[-2:] == [
        "generator-ready: the output is not valid: stub",
        "local-integration.sh: the 'normalize-docs' output failed validation",
    ]
    assert "== normalize-tests" not in result.stdout


@needs_bash
def test_a_token_in_the_shell_or_the_config_reaches_no_output_no_child_and_no_file(seeded, tmp_path):
    # Arrange: the token everywhere an operator's may be - the shell, an inherited action input the toolkit would
    # write into an output, and `.env.local`.
    config = (seeded / ".env.local").read_text(encoding="utf-8")
    (seeded / ".env.local").write_text(f"{config}GITHUB_TOKEN={TOKEN}\n", encoding="utf-8", newline="\n")
    env = _run_env(GITHUB_TOKEN=TOKEN, GH_TOKEN=TOKEN, INPUT_GITHUB_TOKEN=TOKEN, INPUT_DOCUMENT_TITLE=TOKEN)

    # Act
    result = _run(seeded, env=env)

    # Assert: the run passed, and the `.env.local` line was reported by its number - neither its key nor its value.
    assert result.returncode == 0, result.stderr
    assert f".env.local:{len(VALID_CONFIG) + 1}: ignored, not a setting of this script" in result.stderr
    assert TOKEN not in result.stdout + result.stderr
    # Assert: no output file holds it.
    written = [path for path in (seeded / "output").rglob("*") if path.is_file()]
    assert len(written) == 3
    assert [path.name for path in written if TOKEN in path.read_text(encoding="utf-8")] == []
    # Assert: what the script starts inherits neither the token nor any action input from the shell.
    child_environment = (tmp_path / "child-environment.txt").read_text(encoding="utf-8", errors="replace")
    assert "PATH=" in child_environment
    assert TOKEN not in child_environment
    assert {line.split("=")[0] for line in child_environment.splitlines() if line.startswith("INPUT_")} == {
        "INPUT_COMMAND",
        "INPUT_INPUT",
        "INPUT_OUTPUT",
        "INPUT_TESTS_INPUT",
        "INPUT_VIEW",
    }
