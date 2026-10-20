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
The entry point `action.yml` runs. It validates the action inputs, builds the `living-doc <command>` command line
from them, runs it on this interpreter with `-E`, and sets the `output-path` output to the file the command wrote.
"""

import logging
import math
import os
import shlex
import subprocess
import sys

from living_doc_core.logging_config import setup_logging  # type: ignore[import-untyped]

logger = logging.getLogger("living_doc.action")

COMMAND = "command"
OUTPUT = "output"
FAIL_UNDER = "fail-under"
VERBOSE_LOGGING = "verbose-logging"
OUTPUT_PATH = "output-path"

# Per command, the inputs it takes, in `action.yml` order, each with the CLI option it becomes and whether the
# command requires it. `verbose-logging` is taken by every command and becomes `--verbose`.
COMMAND_INPUTS: dict[str, dict[str, tuple[str, bool]]] = {
    "normalize-issues": {
        "input": ("--input", True),
        OUTPUT: ("--output", True),
        "view": ("--view", False),
        "document-title": ("--document-title", False),
    },
    "coverage-matrix": {
        "input": ("--doc-input", True),
        OUTPUT: ("--output", True),
        "tests-input": ("--tests-input", True),
        FAIL_UNDER: ("--fail-under", False),
    },
}
# Declared by `action.yml`, run by no CLI yet.
NOT_AVAILABLE_YET = ("normalize-tests",)

VALID_COMMANDS = ", ".join(("normalize-issues", "normalize-tests", "coverage-matrix"))
AVAILABLE_COMMANDS = ", ".join(COMMAND_INPUTS)
# Every input a command can take, in `action.yml` order.
COMMAND_INPUT_NAMES = list(dict.fromkeys(name for inputs in COMMAND_INPUTS.values() for name in inputs))


class ActionInputError(Exception):
    """A missing, invalid or untaken input; the message is the one line the run fails with, naming the input."""


def get_input(name: str) -> str:
    """
    Read one action input as `action.yml` passes it to the run step.

    @param name: The input's name as `action.yml` declares it.
    @return: The `INPUT_<NAME>` variable, stripped; empty when it is not set.
    """
    return os.environ.get(f"INPUT_{name.replace('-', '_').upper()}", "").strip()


def _command() -> str:
    """
    Read and validate `command`.

    @return: A command the CLI runs.
    @raise ActionInputError: `command` is empty, unknown or not available yet.
    """
    command = get_input(COMMAND)
    if not command:
        raise ActionInputError(f"Input `{COMMAND}` is required; valid commands: {VALID_COMMANDS}.")
    if command in NOT_AVAILABLE_YET:
        raise ActionInputError(
            f"Command `{command}` is not available yet; the commands available now: {AVAILABLE_COMMANDS}."
        )
    if command not in COMMAND_INPUTS:
        # `!r` keeps a value with a line break on the one line the run fails with.
        raise ActionInputError(
            f"Input `{COMMAND}` is {command!r}, not a valid command; valid commands: {VALID_COMMANDS}."
        )
    return command


def _is_number(value: str) -> bool:
    """
    Whether a value reads as a finite number, as the CLI's `--fail-under` takes it.

    @param value: The input value.
    @return: True for a finite number such as `80` or `72.5`.
    """
    try:
        return math.isfinite(float(value))
    except ValueError:
        return False


def build_command_line(verbose: bool) -> tuple[list[str], str]:
    """
    Validate the inputs, stopping at the first invalid one, and build the CLI's arguments from them.

    @param verbose: Whether `verbose-logging` is on, which adds `--verbose`.
    @return: The arguments after `python -E -m living_doc_cli.main`, and the absolute path of the file the command
        writes.
    @raise ActionInputError: `command` is empty, unknown or not available yet; an input the command does not take
        is set; an input the command requires is empty; `output` holds a line break; or `fail-under` is not a
        number.
    """
    command = _command()
    taken = COMMAND_INPUTS[command]

    for name in COMMAND_INPUT_NAMES:
        if name not in taken and get_input(name):
            raise ActionInputError(f"Input `{name}` is not taken by command `{command}`; leave it empty.")
    for name, (_, required) in taken.items():
        if required and not get_input(name):
            raise ActionInputError(f"Input `{name}` is required by command `{command}`.")

    output = get_input(OUTPUT)
    if "\n" in output or "\r" in output:
        # The run sets the `output-path` output to this path, one `name=value` line in `$GITHUB_OUTPUT`.
        raise ActionInputError(
            f"Input `{OUTPUT}` is {output!r}, a path with a line break, which the `{OUTPUT_PATH}` output cannot carry."
        )
    output_path = os.path.abspath(output)

    fail_under = get_input(FAIL_UNDER)
    if fail_under and not _is_number(fail_under):
        raise ActionInputError(f"Input `{FAIL_UNDER}` is {fail_under!r}, not a number.")

    arguments = [command]
    for name, (option, _) in taken.items():
        value = output_path if name == OUTPUT else get_input(name)
        if value:
            # `--option=value`: a value that starts with `-` stays the option's value.
            arguments.append(f"{option}={value}")
    if verbose:
        arguments.append("--verbose")
    return arguments, output_path


def set_output(name: str, value: str) -> None:
    """
    Append one output to the step's `$GITHUB_OUTPUT` file.

    @param name: The output's name as `action.yml` declares it.
    @param value: The output's value, on one line.
    @raise KeyError: `GITHUB_OUTPUT` is not set, as outside GitHub Actions.
    @raise OSError: The file cannot be written.
    """
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as github_output:
        github_output.write(f"{name}={value}\n")


def run() -> None:
    """
    Run the Living Documentation Toolkit as the action: validate the inputs, run the command, set its output.

    @return: None; the run ends with exit code 1 on an invalid input or an output it cannot set, with the command's
        own exit code when the command fails, and with exit code 0 once the file is written and the output set.
    """
    verbose = get_input(VERBOSE_LOGGING).lower() == "true"
    setup_logging(verbose=verbose)

    try:
        arguments, output_path = build_command_line(verbose)
    except ActionInputError as error:
        logger.error("%s", error)
        sys.exit(1)

    command_line = [sys.executable, "-E", "-m", "living_doc_cli.main", *arguments]
    logger.info("Living Documentation Toolkit action - running `%s`.", arguments[0])
    logger.debug("Living Documentation Toolkit action - command line: %s", shlex.join(command_line))
    completed = subprocess.run(command_line, check=False)
    if completed.returncode != 0:
        # The CLI has already printed its own error line.
        sys.exit(completed.returncode)

    try:
        set_output(OUTPUT_PATH, output_path)
    except KeyError:
        # A run outside GitHub Actions has no `GITHUB_OUTPUT` to append to.
        logger.info(
            "Living Documentation Toolkit action - no `GITHUB_OUTPUT`: the `%s` output is not set.", OUTPUT_PATH
        )
    except OSError as error:
        logger.error("Living Documentation Toolkit action - the `%s` output cannot be set: %s.", OUTPUT_PATH, error)
        sys.exit(1)

    logger.info("Living Documentation Toolkit action - written: `%s`.", output_path)


if __name__ == "__main__":
    run()
