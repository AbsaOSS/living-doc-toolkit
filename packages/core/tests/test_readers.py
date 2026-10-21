# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for the reader table and its readers.
"""

import pytest
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.ui_tests import UITestsResult

from living_doc_core import readers
from living_doc_core.readers import READERS, Reader, Role, contract_names, read_documentation, read_tests


def test_the_table_maps_each_contract_name_to_its_role_and_known_producer():
    assert READERS == {
        "doc-source": Reader(Role.DOCUMENTATION, frozenset({"AbsaOSS/living-doc-collector-gh"})),
        "ui-tests": Reader(Role.TESTS, frozenset({"AbsaOSS/living-doc-collector-gh"})),
    }


@pytest.mark.parametrize(("role", "names"), [(Role.DOCUMENTATION, {"doc-source"}), (Role.TESTS, {"ui-tests"})])
def test_each_role_reads_the_contracts_the_table_gives_it(role, names):
    assert contract_names(role) == names


def test_read_documentation_returns_the_doc_source_model(doc_source):
    # Act
    result = read_documentation(doc_source)

    # Assert
    assert isinstance(result, DocSourceResult)
    assert [entity.entity_id for entity in result.user_stories] == ["US-001"]


def test_read_tests_returns_the_ui_tests_model(ui_tests):
    # Act
    result = read_tests(ui_tests)

    # Assert
    assert isinstance(result, UITestsResult)
    assert len(result.scenarios) == 6


def test_every_read_goes_through_read_artifact_with_its_roles_contract_names(monkeypatch, doc_source, ui_tests):
    # Arrange
    calls = []
    read_artifact = readers.read_artifact

    def recording_read_artifact(path, expected):
        calls.append((path, expected))
        return read_artifact(path, expected)

    monkeypatch.setattr(readers, "read_artifact", recording_read_artifact)

    # Act
    read_documentation(doc_source)
    read_tests(ui_tests)

    # Assert
    assert calls == [(doc_source, {"doc-source"}), (ui_tests, {"ui-tests"})]


@pytest.mark.parametrize(
    ("read", "fixture", "message"),
    [
        (read_documentation, "ui_tests", "expected one of ['doc-source'], got 'ui-tests'"),
        (read_tests, "doc_source", "expected one of ['ui-tests'], got 'doc-source'"),
    ],
)
def test_a_reader_given_another_roles_file_fails_r5_naming_the_expected_set(request, read, fixture, message):
    # Act
    with pytest.raises(ContractError) as error:
        read(request.getfixturevalue(fixture))

    # Assert
    assert (error.value.code, error.value.message) == (Code.CONTRACT_MISMATCH, message)
