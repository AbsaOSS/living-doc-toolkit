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
import pytest

from tools.check_runtime_requirements import REPO_ROOT, RUNTIME_REQUIREMENTS, denied_requirements, main


@pytest.fixture(name="repo")
def _repo(tmp_path):
    """A repository root holding one package, `packages/demo`, and a directory without a `pyproject.toml`."""
    root = tmp_path / "repo"
    (root / "packages" / "demo").mkdir(parents=True)
    (root / "packages" / "demo" / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (root / "packages" / "no_manifest").mkdir()
    (tmp_path / "outside").mkdir()
    (tmp_path / "outside" / "pyproject.toml").write_text("[project]\nname = 'outside'\n", encoding="utf-8")
    return root


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("pytest==9.1.1", "pytest"),
        ("pytest-cov==7.1.0", "pytest-cov"),
        ("black==26.5.1", "black"),
        ("mypy==2.3.1", "mypy"),
        ("ruff==0.16.9", "ruff"),
        ("types-requests==2.33.0", "types-requests"),
        ("pyright==1.1.0", "pyright"),
        ("hypothesis==6.0.0", "hypothesis"),
        # PEP 503: pip installs the same distribution for every spelling.
        ("PyTest==9.1.1", "pytest"),
        ("pytest_cov==7.1.0", "pytest-cov"),
        ("pytest.cov==7.1.0", "pytest-cov"),
        ("pytest..cov==7.1.0", "pytest-cov"),
        ("mypy.extensions==1.1.0", "mypy-extensions"),
    ],
)
def test_a_development_tool_in_the_runtime_file_is_reported(repo, line, expected):
    # Arrange
    planted = repo / "requirements.txt"
    planted.write_text(f"./packages/demo\n{line}\n", encoding="utf-8")

    # Act & Assert
    assert denied_requirements(planted, repo) == [expected]
    assert main(planted, repo) == 1


@pytest.mark.parametrize(
    "line",
    [
        "-r requirements-dev.txt",
        "--requirement requirements-dev.txt",
        "-e ./packages/demo",
        "--editable ./packages/demo",
        "./packages/demo[dev]",
        "git+https://github.com/psf/black@main",
        "https://example.invalid/pytest-9.1.1-py3-none-any.whl",
        "./wheels/pytest-9.1.1-py3-none-any.whl",
        # A directory below the root without a `pyproject.toml`, the root itself, and a package outside it.
        "./packages/no_manifest",
        ".",
        "../outside",
    ],
)
def test_a_line_naming_neither_a_plain_requirement_nor_a_repository_package_is_reported(repo, line):
    # Arrange
    planted = repo / "requirements.txt"
    planted.write_text(f"./packages/demo\n{line}\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[tool.black]\n", encoding="utf-8")

    # Act & Assert
    assert denied_requirements(planted, repo) == [line]
    assert main(planted, repo) == 1


def test_an_absolute_path_to_a_repository_package_is_reported(repo):
    # Arrange: pip reads it on the machine that installs, where the path does not exist.
    line = str(repo / "packages" / "demo")
    planted = repo / "requirements.txt"
    planted.write_text(f"{line}\n", encoding="utf-8")

    # Act & Assert
    assert denied_requirements(planted, repo) == [line]


@pytest.mark.parametrize(
    "line",
    [
        "./packages/demo",
        "packages/demo",
        "./packages/demo/",
        "living-doc-utilities==0.6.0",
        'tomli==2.4.1; python_version < "3.11"',
        "living-doc-utilities[html]==0.6.0",
        "living-doc-utilities>=0.6.0,<0.7",
        "pydantic ~= 2.13",
    ],
)
def test_a_repository_package_or_a_plain_runtime_pin_is_not_reported(repo, line):
    # Arrange
    planted = repo / "requirements.txt"
    planted.write_text(f"{line}\n", encoding="utf-8")

    # Act & Assert
    assert denied_requirements(planted, repo) == []
    assert main(planted, repo) == 0


def test_a_commented_out_development_tool_is_not_reported(repo):
    # Arrange
    planted = repo / "requirements.txt"
    planted.write_text("./packages/demo\n# pytest==9.1.1\n", encoding="utf-8")

    # Act & Assert
    assert denied_requirements(planted, repo) == []


def test_a_denied_line_is_reported_on_stderr(repo, capsys):
    # Arrange
    planted = repo / "requirements.txt"
    planted.write_text("-e ./packages/demo\npytest==9.1.1\n", encoding="utf-8")

    # Act
    main(planted, repo)

    # Assert
    assert capsys.readouterr().err.splitlines()[1:] == ["  -e ./packages/demo", "  pytest"]


def test_the_repositorys_requirements_txt_is_runtime_only():
    # Act & Assert
    assert denied_requirements(RUNTIME_REQUIREMENTS, REPO_ROOT) == []
    assert main() == 0
