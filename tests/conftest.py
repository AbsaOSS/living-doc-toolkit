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

import pytest


@pytest.fixture(autouse=True)
def _clear_action_inputs(monkeypatch):
    # No action input leaks in from the shell, so every input a test does not set reads as unset; no run appends an
    # output to the `GITHUB_OUTPUT` of the CI job running the tests; and a CI re-run with debug logging does not turn
    # verbose logging on.
    for name in [name for name in os.environ if name.startswith("INPUT_")]:
        monkeypatch.delenv(name)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.delenv("RUNNER_DEBUG", raising=False)
