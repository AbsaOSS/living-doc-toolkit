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
The Python half of `local-integration.sh`: the report on one output a toolkit command wrote - re-read with
`read_artifact`, then who wrote it, the time the run took, the file's size, its `metadata.stats` counts, each input
it records in `metadata.source_inputs[]`, its warnings by code, and per input how many of that input's warnings it
forwards. Runs in the script's venv, which holds `requirements.txt` alone, so it imports `living_doc_utilities` and
the standard library only.
"""

import argparse
import json
import os
import sys
from collections import Counter
from collections.abc import Sequence
from typing import Any, Optional

from living_doc_utilities.contracts.codes import ContractError
from living_doc_utilities.contracts.coverage_matrix import CoverageMatrixResult
from living_doc_utilities.contracts.envelope import ContractWarning, SourceInputEntry
from living_doc_utilities.contracts.io import read_artifact

# How many occurrences of each warning code the report lists; the count covers them all.
FIRST_OCCURRENCES = 10

# The contracts a toolkit command reads; every input of a report is one of them.
INPUT_CONTRACTS = {"doc-source", "ui-tests"}


class NotForwarded(Exception):
    """The output does not carry every warning of an input unchanged."""


def _printable(line: str) -> str:
    """
    One report line as the terminal shows it, a control character spelled out (`\\n`, `\\x1b`): an input is another
    component's file, and its text must neither forge a report line nor drive the terminal.
    """
    return "".join(char if char.isprintable() else char.encode("unicode_escape").decode("ascii") for char in line)


def _counts(value: Any) -> str:
    """A `metadata.stats` value on one line: a number as it is, a mapping as sorted `key=count` pairs."""
    if isinstance(value, dict):
        return ", ".join(f"{key}={count}" for key, count in sorted(value.items())) or "-"
    return str(value)


def _occurrence(warning: ContractWarning) -> str:
    """Where one warning was raised and what it says: `<path>:<line> <entity>/<ac> <message>`."""
    where = warning.path or warning.context or "-"
    if warning.line_no is not None:
        where = f"{where}:{warning.line_no}"
    subject = "/".join(part for part in (warning.entity_id, warning.ac_id) if part)
    return " ".join(part for part in (where, subject, warning.message) if part)


def warnings_by_code(warnings: Sequence[ContractWarning], first: int = FIRST_OCCURRENCES) -> list[str]:
    """
    The warnings grouped by code, codes sorted: each code's count, then its first occurrences in output order.

    @param warnings: The output's warnings.
    @param first: How many occurrences of each code to list.
    @return: The report lines.
    """
    grouped: dict[str, list[ContractWarning]] = {}
    for warning in warnings:
        grouped.setdefault(warning.code, []).append(warning)
    lines = [f"  warnings: {len(warnings)}"]
    for code in sorted(grouped):
        occurrences = grouped[code]
        lines.append(f"    {code}: {len(occurrences)}")
        lines.extend(f"      {_occurrence(warning)}" for warning in occurrences[:first])
        if len(occurrences) > first:
            lines.append(f"      ... and {len(occurrences) - first} more")
    return lines


def _source_input(entry: SourceInputEntry) -> list[str]:
    """One `metadata.source_inputs[]` entry: the input's contract, the producer that wrote it and what it documents."""
    producer = entry.producer
    return [
        f"    {entry.schema_version}",
        f"      producer: {producer.name} {producer.version}, living-doc-utilities {producer.utilities_version}",
        f"      project_id: {entry.source.project_id}",
        f"      repositories: {', '.join(entry.source.repositories) or '-'}",
    ]


def _key(warning: ContractWarning) -> str:
    """Every field of one warning, as one comparable value."""
    return json.dumps(warning.model_dump(mode="json"), sort_keys=True)


def _forwarded(warnings: Sequence[ContractWarning], input_path: str) -> str:
    """
    How many of one input's warnings the output carries unchanged, as a command forwards one: every field the same,
    its context naming the input's contract first. Each output warning stands for one input warning at most, so a
    duplicate cannot stand in for one the output dropped.

    @param warnings: The output's warnings.
    @param input_path: One input the command read.
    @return: The report line.
    @raise NotForwarded: When an input warning is not among them.
    """
    source = read_artifact(input_path, INPUT_CONTRACTS)
    named = f"source_input={source.schema_version!r}"
    carried = Counter(_key(warning) for warning in warnings)
    count = 0
    for warning in source.warnings:
        key = _key(warning.model_copy(update={"context": f"{named} {warning.context}" if warning.context else named}))
        if carried[key]:
            carried[key] -= 1
            count += 1
    if count < len(source.warnings):
        raise NotForwarded(
            f"forwards {count} of the {len(source.warnings)} warnings of its {source.schema_version} input "
            f"'{input_path}'; a command forwards every input warning"
        )
    return f"  forwarded: {count} of {len(source.warnings)} from {source.schema_version}"


def report(path: str, contract: str, elapsed_ms: int, inputs: Sequence[str]) -> list[str]:
    """
    Re-read one command's output with `read_artifact` and describe it.

    @param path: The output file.
    @param contract: The contract the output must carry, e.g. `generator-ready`.
    @param elapsed_ms: How long the command's run took, in milliseconds.
    @param inputs: The input files the command read.
    @return: The report lines.
    @raise ContractError: When the output or an input fails its contract.
    @raise NotForwarded: When the output does not forward every warning of an input.
    @raise OSError: When a file cannot be read.
    @raise ValueError: When a file is not JSON.
    """
    result = read_artifact(path, contract)
    metadata = result.metadata
    lines = [
        f"{contract}: {path}",
        f"  contract: {result.schema_version}, valid (read_artifact)",
        f"  producer: {metadata.producer.name} {metadata.producer.version}, "
        f"living-doc-utilities {metadata.producer.utilities_version}",
        f"  time: {elapsed_ms / 1000:.2f} s",
        f"  size: {os.path.getsize(path)} bytes",
        "  stats.cardinality:",
        *(f"    {name}: {_counts(value)}" for name, value in metadata.stats.cardinality.model_dump().items()),
        f"  source_inputs: {len(metadata.source_inputs)}",
        *(line for entry in metadata.source_inputs for line in _source_input(entry)),
    ]
    if isinstance(result, CoverageMatrixResult):
        lines += ["  summary:", *(f"    {name}: {value}" for name, value in result.summary.model_dump().items())]
    lines += warnings_by_code(result.warnings)
    lines += [_forwarded(result.warnings, input_path) for input_path in inputs]
    return lines


def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    The command line `local-integration.sh` calls: `report` prints the report on one output.

    @param argv: The arguments; the process's own when None.
    @return: The process exit code: 0 on success, 1 when the output fails validation or drops an input warning.
    """
    parser = argparse.ArgumentParser(prog="python -m tools.local_integration")
    commands = parser.add_subparsers(dest="command", required=True)
    output = commands.add_parser("report", help="validate one output and print its report")
    output.add_argument("path")
    output.add_argument("contract")
    output.add_argument("elapsed_ms", type=int)
    output.add_argument("inputs", nargs="+", metavar="input")
    args = parser.parse_args(argv)

    try:
        lines = report(args.path, args.contract, args.elapsed_ms, args.inputs)
    except NotForwarded as e:
        print(_printable(f"{args.contract}: {e}"), file=sys.stderr)
        return 1
    except (ContractError, OSError, ValueError) as e:
        print(_printable(f"{args.contract}: the output is not valid: {e}"), file=sys.stderr)
        return 1
    print("\n".join(_printable(line) for line in lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
