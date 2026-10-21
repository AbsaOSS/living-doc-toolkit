# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The reader table: each contract the toolkit reads, by contract name, with the role it plays in a command and the
producers known to write it. Every read goes through `living-doc-utilities`' `read_artifact`, which runs R5, and
returns the contract's own model.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.io import read_artifact
from living_doc_utilities.contracts.ui_tests import UITestsResult


class Role(str, Enum):
    """What an input file is to a command."""

    DOCUMENTATION = "documentation"
    TESTS = "tests"


@dataclass(frozen=True)
class Reader:
    """One contract's row: the role its file plays and the producers known to write it."""

    role: Role
    producers: frozenset[str]


COLLECTOR_GH = "AbsaOSS/living-doc-collector-gh"

# By contract name, never by producer: the file's own `schema_version` says how it is read (R5). The issue-tracker
# documentation contract, `doc-entities`, joins the documentation role in a later release.
READERS: dict[str, Reader] = {
    "doc-source": Reader(Role.DOCUMENTATION, frozenset({COLLECTOR_GH})),
    "ui-tests": Reader(Role.TESTS, frozenset({COLLECTOR_GH})),
}

# The contract models a read returns, per role.
DocumentationResult = DocSourceResult
TestsResult = UITestsResult


def contract_names(role: Role) -> set[str]:
    """
    The contracts a role reads.

    @param role: The input's role.
    @return: The contract names `READERS` gives that role, the `expected` set of `read_artifact`.
    """
    return {name for name, reader in READERS.items() if reader.role is role}


def read_documentation(path: str | Path) -> DocumentationResult:
    """
    Read a documentation input.

    @param path: The documentation file.
    @return: Its contract model.
    @raise ContractError: R5's `INVALID_CONTRACT_ID`, `CONTRACT_MISMATCH` or `SCHEMA_VALIDATION_FAILED`.
    """
    result = read_artifact(path, expected=contract_names(Role.DOCUMENTATION))
    assert isinstance(result, DocSourceResult)  # R12 check 2: a contract model, never a dict
    return result


def read_tests(path: str | Path) -> TestsResult:
    """
    Read a tests input.

    @param path: The tests file.
    @return: Its contract model.
    @raise ContractError: R5's `INVALID_CONTRACT_ID`, `CONTRACT_MISMATCH` or `SCHEMA_VALIDATION_FAILED`.
    """
    result = read_artifact(path, expected=contract_names(Role.TESTS))
    assert isinstance(result, UITestsResult)  # R12 check 2: a contract model, never a dict
    return result
