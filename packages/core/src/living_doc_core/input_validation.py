# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The shared input validation every transform command runs before it transforms. It runs the steps of
`living-doc-utilities`' shared input validation order (`docs/contracts/errors.md`) over a command's inputs by role,
reports every occurrence of the first step that fails, and returns the inputs as contract models.
"""

import json
import os
import re
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.envelope import CONTRACT_ID_PATTERN
from living_doc_utilities.contracts.registry import record_roots

from living_doc_core.readers import READERS, DocumentationResult, Role, TestsResult, read_documentation, read_tests

# The roles each command takes, one input each (`living-doc-utilities` `docs/contracts/pipeline-rules.md` § One
# project, one pipeline, one documentation source).
COMMAND_ROLES: dict[str, tuple[Role, ...]] = {
    "normalize-docs": (Role.DOCUMENTATION,),
    "normalize-tests": (Role.TESTS,),
    "coverage-matrix": (Role.DOCUMENTATION, Role.TESTS),
}

_READ: dict[Role, Callable[[str | Path], DocumentationResult | TestsResult]] = {
    Role.DOCUMENTATION: read_documentation,
    Role.TESTS: read_tests,
}

_CONTRACT_ID_RE = re.compile(CONTRACT_ID_PATTERN)


@dataclass(frozen=True)
class InputProblem:
    """
    One occurrence of a failing step: its code, the input it is in, and what is wrong, ending in a hint. The code is
    None only for a file that is not JSON.
    """

    code: Code | None
    location: str
    message: str

    def __str__(self) -> str:
        line = f"{self.location}: {self.message}"
        return line if self.code is None else f"[{self.code.name}] {line}"


class InputValidationError(Exception):
    """
    Every occurrence of the first step that failed, and nothing from a later step. Its text is the problems in order,
    each starting a line; an R5 message from `living-doc-utilities` may run over several.
    """

    def __init__(self, problems: Sequence[InputProblem]) -> None:
        self.problems = tuple(problems)
        super().__init__("\n".join(str(problem) for problem in self.problems))


@dataclass(frozen=True)
class ValidatedInputs:
    """A command's inputs once every step passed, as contract models; a role the command does not take is None."""

    documentation: DocumentationResult | None = None
    tests: TestsResult | None = None


@dataclass(frozen=True)
class _Input:
    """One input file read as its contract model."""

    role: Role
    path: str
    result: DocumentationResult | TestsResult

    @property
    def location(self) -> str:
        """The input as a problem names it: its role and path."""
        return _location(self.role, self.path)

    @property
    def contract_name(self) -> str:
        """The contract the file declares, its `schema_version` without the version."""
        match = _CONTRACT_ID_RE.match(self.result.schema_version)
        assert match is not None  # R5 step 1 passed
        return match.group(1)


def _location(role: Role, path: str | None = None) -> str:
    return f"{role.value} input" if path is None else f"{role.value} input {path!r}"


def _stop_on(problems: Sequence[InputProblem]) -> None:
    if problems:
        raise InputValidationError(problems)


def _roles(command: str, inputs: Mapping[Role, Sequence[str | Path]]) -> tuple[Role, ...]:
    if command not in COMMAND_ROLES:
        raise ValueError(f"unknown command {command!r}; the commands: {', '.join(COMMAND_ROLES)}")
    roles = COMMAND_ROLES[command]
    for role, paths in inputs.items():
        if paths and role not in roles:
            raise ValueError(f"`{command}` takes no {role.value} input")
    if len(inputs.get(Role.TESTS, ())) > 1:
        raise ValueError(f"`{command}` takes one tests input")
    return roles


def _missing_inputs(command: str, roles: Sequence[Role], paths: Mapping[Role, Sequence[str]]) -> list[InputProblem]:
    # A path that names no file is a needed input that is absent, as decided on issue #85.
    takes = " and ".join(f"one {role.value} input" for role in roles)
    problems = []
    for role in roles:
        if not paths[role]:
            problems.append(InputProblem(Code.MISSING_INPUT, _location(role), f"none given; `{command}` takes {takes}"))
        problems.extend(
            InputProblem(
                Code.MISSING_INPUT,
                _location(role, path),
                "no such file; check the path, or run the step that writes it first",
            )
            for path in paths[role]
            if not Path(path).is_file()
        )
    return problems


def _read_inputs(paths: Mapping[Role, Sequence[str]]) -> tuple[list[_Input], list[InputProblem]]:
    inputs: list[_Input] = []
    problems: list[InputProblem] = []
    for role, role_paths in paths.items():
        for path in role_paths:
            try:
                inputs.append(_Input(role, path, _READ[role](path)))
            except ContractError as error:
                message = error.message if error.context is None else f"{error.message} ({error.context})"
                problems.append(InputProblem(error.code, _location(role, path), message))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                # Not one of R5's failures, so no code names it (decided on issue #85).
                problems.append(InputProblem(None, _location(role, path), f"not JSON: {error}"))
    return inputs, problems


def _unknown_producers(inputs: Sequence[_Input]) -> list[InputProblem]:
    problems = []
    for item in inputs:
        known = READERS[item.contract_name].producers
        producer = item.result.metadata.producer.name
        if producer not in known:
            problems.append(
                InputProblem(
                    Code.UNKNOWN_PRODUCER,
                    item.location,
                    f"producer {producer!r} is not a known producer of {item.contract_name}; "
                    f"the known ones: {_quoted(sorted(known))}",
                )
            )
    return problems


def _project_mismatches(inputs: Sequence[_Input]) -> list[InputProblem]:
    projects = sorted({item.result.metadata.source.project_id for item in inputs})
    if len(projects) < 2:
        return []
    return [
        InputProblem(
            Code.PROJECT_MISMATCH,
            item.location,
            f"project {item.result.metadata.source.project_id!r}, where the inputs name {_quoted(projects)}; "
            "a run documents one project, so collect every input for it",
        )
        for item in inputs
    ]


def _multiple_documentation_sources(inputs: Sequence[_Input]) -> list[InputProblem]:
    documentation = [item for item in inputs if item.role is Role.DOCUMENTATION]
    if len(documentation) < 2:
        return []
    return [
        InputProblem(
            Code.MULTIPLE_DOCUMENTATION_SOURCES,
            item.location,
            f"one of {len(documentation)} documentation files; a run reads exactly one, so pass one",
        )
        for item in documentation
    ]


def _duplicate_ids(inputs: Sequence[_Input]) -> list[InputProblem]:
    entity_problems: list[InputProblem] = []
    ac_problems: list[InputProblem] = []
    for item in inputs:
        if item.role is not Role.DOCUMENTATION:
            continue
        entities = list(_entities(item.result))
        for entity_id, at in _repeated((entity.entity_id, path) for path, entity in entities):
            entity_problems.append(
                InputProblem(
                    Code.DUPLICATE_ENTITY_ID,
                    item.location,
                    f"entity id {entity_id!r} at {', '.join(at)}; one id names one entity, "
                    "so renumber all but one at the source",
                )
            )
        for path, entity in entities:
            criteria = (
                (criterion.id, f"{path}.acceptance_criteria[{index}]")
                for index, criterion in enumerate(entity.acceptance_criteria)
            )
            for ac_id, at in _repeated(criteria):
                ac_problems.append(
                    InputProblem(
                        Code.DUPLICATE_AC_ID,
                        item.location,
                        f"acceptance criterion id {ac_id!r} at {', '.join(at)}; one id names one criterion of its "
                        "entity, so renumber all but one at the source",
                    )
                )
    return entity_problems + ac_problems


def _entities(result: DocumentationResult | TestsResult) -> Iterator[tuple[str, Any]]:
    """Each entity of a documentation input, with its path: `<record root>[<index>]`."""
    for root in record_roots(result.schema_version):
        for index, entity in enumerate(getattr(result, root)):
            yield f"{root}[{index}]", entity


def _repeated(occurrences: Iterable[tuple[str, str]]) -> list[tuple[str, list[str]]]:
    """Each id met more than once, in the order first met, with every path it was met at."""
    paths_by_id: defaultdict[str, list[str]] = defaultdict(list)
    for identifier, path in occurrences:
        paths_by_id[identifier].append(path)
    return [(identifier, paths) for identifier, paths in paths_by_id.items() if len(paths) > 1]


def _quoted(values: Iterable[str]) -> str:
    return ", ".join(repr(value) for value in values)


def validate_inputs(command: str, inputs: Mapping[Role, Sequence[str | Path]]) -> ValidatedInputs:
    """
    Run the shared input validation over one command's inputs, step by step, stopping at the first that fails.

    @param command: The command the inputs are for, a key of `COMMAND_ROLES`.
    @param inputs: The paths given per role; a role the command takes with no path is a missing input.
    @return: The inputs as contract models.
    @raise InputValidationError: A step failed. It carries every occurrence of that step, and only that step.
    @raise ValueError: The command is unknown, a role is given that it does not take, or more than one tests path
        is given. A command's own options rule these out, so they are a caller's error, not an input's.
    """
    roles = _roles(command, inputs)
    paths = {role: [os.fspath(path) for path in inputs.get(role, ())] for role in roles}

    # 1. MISSING_INPUT
    _stop_on(_missing_inputs(command, roles, paths))
    # 2. R5 steps 1 to 3, per input, through `read_artifact`
    read, problems = _read_inputs(paths)
    _stop_on(problems)
    # 3. UNKNOWN_PRODUCER
    _stop_on(_unknown_producers(read))
    # 4. PROJECT_MISMATCH
    _stop_on(_project_mismatches(read))
    # 5. MULTIPLE_DOCUMENTATION_SOURCES. MIXED_DOCUMENTATION_SOURCES needs a second documentation contract, so it
    # arrives with `doc-entities`.
    _stop_on(_multiple_documentation_sources(read))
    # 6. DUPLICATE_ENTITY_ID, DUPLICATE_AC_ID
    _stop_on(_duplicate_ids(read))

    documentation = next((item.result for item in read if item.role is Role.DOCUMENTATION), None)
    tests = next((item.result for item in read if item.role is Role.TESTS), None)
    assert documentation is None or isinstance(documentation, DocumentationResult)
    assert tests is None or isinstance(tests, TestsResult)
    return ValidatedInputs(documentation, tests)
