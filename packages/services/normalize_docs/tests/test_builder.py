# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for the builder: its contract types, the entity order, the envelope, the document block and the forwarded
warnings.
"""

from datetime import datetime, timezone
from importlib.metadata import version
from typing import get_type_hints

import pytest
from living_doc_core.readers import read_documentation
from living_doc_utilities.contracts.compat import installed_utilities_version
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.envelope import AuditStats, ContractWarning, Run
from living_doc_utilities.contracts.generator_ready import GeneratorReadyResult

from living_doc_service_normalize_docs.builder import build_generator_ready, forwarded

GENERATED_AT = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(name="documentation")
def _documentation(doc_source) -> DocSourceResult:
    return read_documentation(doc_source)


def _build(documentation: DocSourceResult, view="inner", **options) -> GeneratorReadyResult:
    return build_generator_ready(documentation, view=view, generated_at=GENERATED_AT, **options)


# --- Typed on the contract models (R12 check 2) ---


def test_the_builder_is_typed_on_the_contract_models_in_and_out():
    hints = get_type_hints(build_generator_ready)
    assert hints["documentation"] is DocSourceResult
    assert hints["return"] is GeneratorReadyResult


def test_the_builder_takes_and_returns_contract_model_instances(documentation):
    # Act
    result = _build(documentation)

    # Assert
    assert isinstance(documentation, DocSourceResult)
    assert isinstance(result, GeneratorReadyResult)


# --- Content ---


def test_the_entity_lists_are_concatenated_user_stories_then_features_then_functionalities(documentation):
    # Act
    result = _build(documentation)

    # Assert
    assert [entity.entity_id for entity in result.content.entities] == [
        "US-001",
        "FEAT-001",
        "FEAT-003",
        "FUNC-001",
        "FUNC-002",
    ]


def test_the_inner_view_carries_every_entity_unchanged(documentation):
    # Act
    result = _build(documentation)

    # Assert
    assert result.content.entities == [
        *documentation.user_stories,
        *documentation.features,
        *documentation.functionalities,
    ]


def test_the_release_view_keeps_the_released_records_in_the_same_order(documentation):
    # Act
    result = _build(documentation, view="release")

    # Assert: FEAT-003 and FUNC-002 are planned; so is US-001-03.
    assert [entity.entity_id for entity in result.content.entities] == ["US-001", "FEAT-001", "FUNC-001"]
    assert [criterion.id for criterion in result.content.entities[0].acceptance_criteria] == [
        "US-001-01",
        "US-001-02",
        "US-001-04",
    ]


# --- The document block ---


@pytest.mark.parametrize("view", ["inner", "release"])
def test_the_document_declares_the_view_it_holds(documentation, view):
    assert _build(documentation, view=view).document.view == view


def test_the_title_and_version_default_to_the_project_id_and_1_0_0(documentation):
    # Act
    document = _build(documentation).document

    # Assert
    assert (document.title, document.version) == ("living-doc-examples", "1.0.0")


def test_a_given_title_and_version_are_the_documents(documentation):
    # Act
    document = _build(documentation, title="Checkout tests", version="2.3.0").document

    # Assert
    assert (document.title, document.version) == ("Checkout tests", "2.3.0")


# --- The envelope ---


def test_the_producer_is_the_toolkit_at_the_version_of_living_doc_core(documentation):
    # Act
    producer = _build(documentation).metadata.producer

    # Assert
    assert producer.name == "AbsaOSS/living-doc-toolkit"
    assert producer.version == version("living-doc-core") == "0.1.0"
    assert producer.build is None
    assert producer.utilities_version == installed_utilities_version()


def test_the_builder_leaves_the_run_empty_for_the_caller_to_set(documentation):
    # Act
    metadata = _build(documentation).metadata

    # Assert
    assert metadata.run == Run()


def test_the_source_is_the_inputs_and_generated_at_is_the_given_time(documentation):
    # Act
    metadata = _build(documentation).metadata

    # Assert
    assert metadata.source == documentation.metadata.source
    assert metadata.generated_at == GENERATED_AT


def test_one_source_inputs_entry_names_the_input_and_carries_its_stats(documentation):
    # Act
    entries = _build(documentation).metadata.source_inputs

    # Assert
    assert len(entries) == 1
    entry = entries[0]
    assert entry.schema_version == "doc-source-v1.0.0"
    assert entry.producer == documentation.metadata.producer
    assert entry.run == documentation.metadata.run
    assert entry.source == documentation.metadata.source
    assert entry.stats == AuditStats.model_validate(documentation.metadata.stats.model_dump())
    cardinality = entry.stats.cardinality
    assert (cardinality.sources_configured, cardinality.sources_failed, cardinality.entities_skipped) == (1, 0, 0)
    assert cardinality.unresolved_refs == 1


def test_the_inner_selected_stats_count_every_record_of_the_input(documentation):
    # Act
    entry = _build(documentation).metadata.source_inputs[0]

    # Assert
    assert entry.selected_stats.field_occupancy == entry.stats.field_occupancy
    assert (entry.selected_stats.cardinality.entities, entry.selected_stats.cardinality.acceptance_criteria) == (5, 8)


def test_the_release_selected_stats_count_the_kept_records_only(documentation):
    # Act
    entry = _build(documentation, view="release").metadata.source_inputs[0]

    # Assert: FUNC-002, the one functionality with a `not_in_scope`, is not kept.
    selected = entry.selected_stats
    assert (selected.cardinality.entities, selected.cardinality.acceptance_criteria) == (3, 6)
    assert selected.cardinality.sources_configured == 1
    assert entry.stats.field_occupancy["functionalities[].not_in_scope[]"] == 1
    assert selected.field_occupancy["functionalities[].not_in_scope[]"] == 0
    assert selected.field_occupancy["features[].stub_reason"] == 1
    assert selected.field_occupancy["user_stories[].acceptance_criteria[].version"] == 3


def test_the_outputs_own_reported_counts_are_left_at_0(documentation):
    # Act: a transform configures no source, so the four counts a caller reports do not apply to its output.
    cardinality = _build(documentation).metadata.stats.cardinality

    # Assert
    assert (
        cardinality.sources_configured,
        cardinality.sources_failed,
        cardinality.unresolved_refs,
        cardinality.entities_skipped,
    ) == (0, 0, 0, 0)


# --- Forwarded warnings ---


def test_a_forwarded_warning_names_the_input_before_its_own_context():
    # Arrange
    warning = ContractWarning(code="UNRESOLVED_RELATION", message="m", context="entity_id='FEAT-003' target='FEAT-002'")

    # Act
    result = forwarded(warning, "doc-source-v1.0.0")

    # Assert
    assert result.context == "source_input='doc-source-v1.0.0' entity_id='FEAT-003' target='FEAT-002'"
    assert result.model_dump(exclude={"context"}) == warning.model_dump(exclude={"context"})


@pytest.mark.parametrize("context", [None, ""])
def test_a_forwarded_warning_without_a_context_gets_the_input_as_its_context(context):
    # Act
    result = forwarded(ContractWarning(code="EMPTY_SOURCE", message="m", context=context), "doc-source-v1.0.0")

    # Assert
    assert result.context == "source_input='doc-source-v1.0.0'"


def test_every_input_warning_is_forwarded_in_order_naming_the_inputs_source_inputs_entry(documentation):
    # Act
    result = _build(documentation, view="release")

    # Assert: the name in each context is the id of the input's own `source_inputs[]` entry. FEAT-003, which both
    # warnings name, is not kept; its warnings still are.
    assert result.metadata.source_inputs[0].schema_version == "doc-source-v1.0.0"
    assert result.warnings == [forwarded(warning, "doc-source-v1.0.0") for warning in documentation.warnings]
    assert [warning.code for warning in result.warnings] == ["FEATURE_WITHOUT_FUNCTIONALITY", "UNRESOLVED_RELATION"]
