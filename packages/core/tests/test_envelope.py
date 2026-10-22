# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the shared envelope identity and warning forwarding."""

from importlib.metadata import version

import pytest
from living_doc_core.envelope import PRODUCER_NAME, TOOLKIT_VERSION, forwarded
from living_doc_utilities.contracts.envelope import ContractWarning


def test_the_producer_identity_uses_the_installed_core_version():
    assert PRODUCER_NAME == "AbsaOSS/living-doc-toolkit"
    assert TOOLKIT_VERSION == version("living-doc-core") == "0.1.0"


def test_a_forwarded_warning_names_the_input_before_its_own_context():
    warning = ContractWarning(code="UNRESOLVED_RELATION", message="m", context="entity_id='FEAT-003' target='FEAT-002'")

    result = forwarded(warning, "doc-source-v1.0.0")

    assert result.context == "source_input='doc-source-v1.0.0' entity_id='FEAT-003' target='FEAT-002'"
    assert result.model_dump(exclude={"context"}) == warning.model_dump(exclude={"context"})


@pytest.mark.parametrize("context", [None, ""])
def test_a_forwarded_warning_without_a_context_gets_the_input_as_its_context(context):
    result = forwarded(ContractWarning(code="EMPTY_SOURCE", message="m", context=context), "doc-source-v1.0.0")

    assert result.context == "source_input='doc-source-v1.0.0'"
