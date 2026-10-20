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
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_MANIFESTS = ("packages/**/pyproject.toml", "apps/**/pyproject.toml")


def _lines(path: Path) -> list[str]:
    lines = (raw.split("#", 1)[0].strip() for raw in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line]


def test_requirements_txt_lists_every_package_of_the_repository():
    # Arrange
    packages = {manifest.parent for pattern in PACKAGE_MANIFESTS for manifest in REPO_ROOT.glob(pattern)}

    # Act
    listed = {(REPO_ROOT / line).resolve() for line in _lines(REPO_ROOT / "requirements.txt")}

    # Assert
    unlisted = sorted(package.relative_to(REPO_ROOT).as_posix() for package in packages - listed)
    assert unlisted == [], f"requirements.txt does not list {unlisted}; add each as `./<path>`."


def test_requirements_txt_lists_each_package_as_a_plain_relative_directory():
    # Assert: no `-e`, no extra, read from the repository root as pip reads it from the directory it runs in.
    assert all(
        line.startswith("./") and (REPO_ROOT / line / "pyproject.toml").is_file()
        for line in _lines(REPO_ROOT / "requirements.txt")
    )


def test_requirements_dev_txt_opens_with_the_runtime_set():
    # Assert
    assert _lines(REPO_ROOT / "requirements-dev.txt")[0] == "-r requirements.txt"
