# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for the `normalize-docs` command: over the fixture against the committed goldens, the shared input
validation before any transform, the forwarded warnings, and `FIELD_LOSS` stopping the write.
"""

import json
from pathlib import Path

import pytest
from living_doc_core.input_validation import InputValidationError
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.envelope import ContractWarning
from living_doc_utilities.contracts.generator_ready import SelectionSummary

from living_doc_service_normalize_docs import service
from living_doc_service_normalize_docs.service import normalize_docs

# The committed goldens: what the command writes over the fixture, per view.
EXPECTED = Path(__file__).resolve().parent / "expected"

# What the fixture's two warnings are forwarded as.
FIXTURE_CONTEXTS = [
    "input='doc-source-v1.0.0' entity_id='FEAT-003'",
    "input='doc-source-v1.0.0' entity_id='FEAT-003' target='FEAT-002'",
]


def _masked(payload: dict) -> dict:
    payload["metadata"]["generated_at"] = "<masked>"
    return payload


def _written(path: Path) -> dict:
    return _masked(json.loads(path.read_text(encoding="utf-8")))


# --- Over the fixture ---


@pytest.mark.parametrize("view", ["inner", "release"])
def test_over_the_fixture_the_command_writes_the_committed_golden(doc_source, tmp_path, view):
    # Act
    normalize_docs(doc_source, tmp_path / "generator-ready.json", view=view)

    # Assert
    assert _written(tmp_path / "generator-ready.json") == _written(EXPECTED / f"generator-ready-{view}.json")


@pytest.mark.parametrize(
    ("view", "summary"),
    [
        ("inner", (5, 5, 0, 8, 8, 0)),
        # FEAT-003 and FUNC-002 are dropped; of the kept entities' 7 criteria, US-001-03 is.
        ("release", (5, 3, 2, 7, 6, 1)),
    ],
)
def test_over_the_fixture_the_selection_summary_counts_what_the_view_kept(doc_source, run_command, view, summary):
    # Act
    result = run_command(doc_source, view=view)

    # Assert
    names = list(SelectionSummary.model_fields)
    assert result.document.selection_summary == SelectionSummary(**dict(zip(names, summary, strict=True)))


def test_over_the_fixture_the_release_view_holds_no_planned_record(doc_source, run_command):
    # Act
    result = run_command(doc_source, view="release")

    # Assert
    states = {entity.state for entity in result.content.entities}
    criteria = {criterion.state for entity in result.content.entities for criterion in entity.acceptance_criteria}
    assert states == {"active"}
    assert criteria == {"active", "deprecated"}


@pytest.mark.parametrize("view", ["inner", "release"])
def test_over_the_fixture_the_two_warnings_arrive_naming_the_input(doc_source, run_command, view):
    # Act
    result = run_command(doc_source, view=view)

    # Assert
    assert [warning.context for warning in result.warnings] == FIXTURE_CONTEXTS
    assert [warning.entity_id for warning in result.warnings] == ["FEAT-003", "FEAT-003"]


def test_the_document_title_and_version_options_reach_the_document(doc_source, run_command):
    # Act
    document = run_command(doc_source, document_title="Checkout tests", document_version="2.3.0").document

    # Assert
    assert (document.title, document.version) == ("Checkout tests", "2.3.0")


def test_without_the_options_the_title_is_the_project_id_and_the_version_1_0_0(doc_source, run_command):
    # Act
    document = run_command(doc_source).document

    # Assert
    assert (document.view, document.title, document.version) == ("inner", "living-doc-examples", "1.0.0")


# --- The shared input validation comes first ---


def _no_build(*_args, **_kwargs):
    raise AssertionError("the builder ran")


def test_a_missing_input_fails_with_missing_input_before_any_transform(monkeypatch, tmp_path):
    # Arrange
    monkeypatch.setattr(service, "build_generator_ready", _no_build)
    missing = tmp_path / "doc-source.json"

    # Act
    with pytest.raises(InputValidationError) as error:
        normalize_docs(missing, tmp_path / "generator-ready.json")

    # Assert
    assert [problem.code for problem in error.value.problems] == [Code.MISSING_INPUT]
    assert not (tmp_path / "generator-ready.json").exists()


def test_an_input_of_an_unknown_producer_fails_with_its_code_before_any_transform(
    monkeypatch, doc_source, changed_copy, tmp_path
):
    # Arrange
    monkeypatch.setattr(service, "build_generator_ready", _no_build)
    unknown = changed_copy(doc_source, lambda payload: payload["metadata"]["producer"].update(name="Acme/doc-tool"))

    # Act
    with pytest.raises(InputValidationError) as error:
        normalize_docs(unknown, tmp_path / "generator-ready.json")

    # Assert
    assert [problem.code for problem in error.value.problems] == [Code.UNKNOWN_PRODUCER]
    assert not (tmp_path / "generator-ready.json").exists()


def test_a_tests_file_as_the_input_fails_with_contract_mismatch(monkeypatch, doc_source, tmp_path):
    # Arrange
    monkeypatch.setattr(service, "build_generator_ready", _no_build)

    # Act
    with pytest.raises(InputValidationError) as error:
        normalize_docs(doc_source.with_name("ui-tests.json"), tmp_path / "generator-ready.json")

    # Assert
    assert [problem.code for problem in error.value.problems] == [Code.CONTRACT_MISMATCH]


# --- Forwarded warnings (`living-doc-utilities` `docs/contracts/errors.md` § Forwarded warnings) ---

BUILT_WARNINGS = [
    ContractWarning(
        code="SOURCE_UNAVAILABLE",
        message="Repository could not be fetched after retries; collected in partial mode.",
        context="repository='AbsaOSS/living-doc-examples'",
    ),
    ContractWarning(code="MISSING_STATUS", message="The header has no status.", entity_id="US-001"),
    ContractWarning(code="NO_SOURCE_URL", message="The source has no URL to link."),
    ContractWarning(
        code="MALFORMED_AC",
        message="Acceptance criterion declares its variants more than once; keep one.",
        context="entity='US-001' line_no=31 header='#   AC:US-001-05 (v1.0.0 - active)'",
        entity_id="US-001",
        ac_id="US-001-05",
        line_no=31,
        path="docs/examples/gherkin/liv_doc_us/us-001-customer-login.feature",
        source_url="https://github.com/AbsaOSS/living-doc/blob/972dba3/docs/examples/gherkin/liv_doc_us/"
        "us-001-customer-login.feature",
    ),
]


def _with_built_warnings(payload: dict) -> None:
    payload["warnings"] = [warning.model_dump(mode="json") for warning in BUILT_WARNINGS]
    payload["metadata"]["stats"]["cardinality"]["warnings_by_code"] = {warning.code: 1 for warning in BUILT_WARNINGS}


@pytest.mark.parametrize("view", ["inner", "release"])
def test_every_input_warning_is_forwarded_unchanged_but_for_its_context(doc_source, changed_copy, run_command, view):
    # Arrange: the context names the input by its contract id, so its file name does not show.
    warned = changed_copy(doc_source, _with_built_warnings, name="warned-doc-source.json")

    # Act
    result = run_command(warned, view=view)

    # Assert
    assert [warning.model_dump(exclude={"context"}) for warning in result.warnings] == [
        warning.model_dump(exclude={"context"}) for warning in BUILT_WARNINGS
    ]
    assert [warning.context for warning in result.warnings] == [
        "input='doc-source-v1.0.0' repository='AbsaOSS/living-doc-examples'",
        "input='doc-source-v1.0.0'",
        "input='doc-source-v1.0.0'",
        "input='doc-source-v1.0.0' entity='US-001' line_no=31 header='#   AC:US-001-05 (v1.0.0 - active)'",
    ]


def test_a_forwarded_warning_keeps_all_five_location_fields(doc_source, changed_copy, run_command):
    # Arrange
    warned = changed_copy(doc_source, _with_built_warnings)

    # Act
    malformed = run_command(warned).warnings[3]

    # Assert
    assert (malformed.code, malformed.entity_id, malformed.ac_id, malformed.line_no) == (
        "MALFORMED_AC",
        "US-001",
        "US-001-05",
        31,
    )
    assert malformed.path == "docs/examples/gherkin/liv_doc_us/us-001-customer-login.feature"
    assert malformed.source_url == BUILT_WARNINGS[3].source_url


# --- FIELD_LOSS stops the run before the write ---


def test_a_builder_that_drops_a_mapped_field_fails_with_field_loss_and_writes_no_file(
    monkeypatch, doc_source, tmp_path
):
    # Arrange: the builder loses every entity's `business_value`, which US-001 fills.
    build = service.build_generator_ready

    def dropping(*args, **kwargs):
        result = build(*args, **kwargs)
        result.content.entities = [
            entity.model_copy(update={"business_value": []}) for entity in result.content.entities
        ]
        return result

    monkeypatch.setattr(service, "build_generator_ready", dropping)
    output = tmp_path / "generator-ready.json"

    # Act
    with pytest.raises(ContractError) as error:
        normalize_docs(doc_source, output)

    # Assert
    assert error.value.code is Code.FIELD_LOSS
    assert "'user_stories[].business_value[]' had occupancy 1 on input" in error.value.message
    assert not output.exists()


def test_a_field_loss_leaves_an_existing_output_untouched(monkeypatch, doc_source, tmp_path):
    # Arrange
    output = tmp_path / "generator-ready.json"
    output.write_text("previous run", encoding="utf-8")
    monkeypatch.setattr(service, "check_no_field_loss", _raise_field_loss)

    # Act
    with pytest.raises(ContractError):
        normalize_docs(doc_source, output)

    # Assert
    assert output.read_text(encoding="utf-8") == "previous run"


def _raise_field_loss(_result):
    raise ContractError(Code.FIELD_LOSS, "lost")


def test_the_release_view_removing_every_planned_criterion_is_no_field_loss(doc_source, run_command):
    # Act: US-001-03 and FUNC-002-01, the only planned criteria, go, and with FUNC-002 its `not_in_scope`.
    result = run_command(doc_source, view="release")

    # Assert
    criteria = [criterion.id for entity in result.content.entities for criterion in entity.acceptance_criteria]
    assert "US-001-03" not in criteria
    assert "FUNC-002-01" not in criteria
    assert all(not entity.not_in_scope for entity in result.content.entities)
