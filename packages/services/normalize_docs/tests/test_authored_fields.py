# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Every authored field reaches the inner `generator-ready.json` at its authored level: the fields named one by one, and
`living-doc-utilities`' six golden entities compared field by field.
"""

import json
from pathlib import Path

import pytest
from living_doc_core.readers import read_documentation
from living_doc_utilities.contracts.common import AcceptanceCriterion
from living_doc_utilities.contracts.doc_entities import Entity

# --- The named fields ---


def _author_the_fields_the_fixture_lacks(payload: dict) -> None:
    """The fixture authors every named field but these: entity deprecation, criterion `not_in_scope` and `rationale`,
    and a Functionality's `rationale`."""
    criterion = payload["user_stories"][0]["acceptance_criteria"][1]
    criterion["not_in_scope"] = ["Single sign-on through a social account."]
    criterion["rationale"] = "The customer must not lose the typed email when the credentials are wrong."
    functionality = payload["functionalities"][0]
    functionality["state"] = "deprecated"
    functionality["deprecated_at"] = "2026-09-30"
    functionality["deprecation_reason"] = "The account complexity policy moved to the identity service."
    functionality["rationale"] = "Customers get feedback before submitting rather than after."


# (entity id, criterion id or None, field): one row per authored field the output must carry.
NAMED_FIELDS = [
    ("US-001", None, "state"),
    ("US-001", None, "state_origin"),
    ("FEAT-001", None, "state"),
    ("FEAT-001", None, "state_origin"),
    ("FUNC-002", None, "not_in_scope"),
    ("FUNC-001", None, "deprecated_at"),
    ("FUNC-001", None, "deprecation_reason"),
    ("FUNC-001", None, "rationale"),
    ("FEAT-001", None, "stub_reason"),
    ("FUNC-001", "FUNC-001-01", "aspect"),
    ("US-001", "US-001-01", "preconditions"),
    ("US-001", "US-001-02", "not_in_scope"),
    ("US-001", "US-001-04", "removal_planned"),
    ("US-001", "US-001-02", "rationale"),
    ("FUNC-001", "FUNC-001-03", "placeholder_values"),
    ("US-001", "US-001-03", "version"),
]


def _record(entities: list[Entity], entity_id: str, ac_id: str | None) -> Entity | AcceptanceCriterion:
    entity = next(entity for entity in entities if entity.entity_id == entity_id)
    if ac_id is None:
        return entity
    return next(criterion for criterion in entity.acceptance_criteria if criterion.id == ac_id)


@pytest.fixture(name="authored")
def _authored(doc_source, changed_copy) -> Path:
    return changed_copy(doc_source, _author_the_fields_the_fixture_lacks)


def test_the_named_fields_include_derived_state_and_a_planned_criterions_version(authored):
    # Assert: the rows above cover what they claim.
    documentation = read_documentation(authored)
    entities = [*documentation.user_stories, *documentation.features, *documentation.functionalities]
    feature = _record(entities, "FEAT-001", None)
    planned = _record(entities, "US-001", "US-001-03")
    assert (feature.type, feature.state_origin) == ("DocumentedFeature", "derived")
    assert (planned.state, planned.version) == ("planned", "1.1.0")


@pytest.mark.parametrize(("entity_id", "ac_id", "field"), NAMED_FIELDS)
def test_each_named_field_reaches_the_inner_output(authored, run_command, entity_id, ac_id, field):
    # Arrange
    documentation = read_documentation(authored)
    expected = getattr(
        _record(
            [*documentation.user_stories, *documentation.features, *documentation.functionalities], entity_id, ac_id
        ),
        field,
    )

    # Act
    result = run_command(authored)

    # Assert
    assert expected not in (None, "", [], {})
    assert getattr(_record(result.content.entities, entity_id, ac_id), field) == expected


# --- living-doc-utilities' golden entities ---

# The lists of `doc-source.json` each golden entity goes into, by its type.
_LISTS = {
    "DocumentedUserStory": "user_stories",
    "DocumentedFeature": "features",
    "DocumentedFunctionality": "functionalities",
}


def _goldens(directory: Path) -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(directory.glob("*.json"))]


def _source_ref(entity_id: str) -> dict:
    """The `source_ref` a collector adds; the goldens carry none."""
    return {
        "system": "GitHub",
        "native_id": entity_id,
        "native_type": "issue",
        "url": f"https://github.com/AbsaOSS/living-doc-utilities/issues/{entity_id}",
        "tracker_state": "open",
        "area_path": None,
        "iteration_path": None,
    }


@pytest.fixture(name="golden_doc_source")
def _golden_doc_source(doc_source, changed_copy, utilities_golden) -> Path:
    """The fixture with its entities replaced by the six golden ones, and no warnings."""

    def with_goldens(payload: dict) -> None:
        payload["warnings"] = []
        for name in _LISTS.values():
            payload[name] = []
        for golden in _goldens(utilities_golden):
            payload[_LISTS[golden["type"]]].append({**golden, "source_ref": _source_ref(golden["entity_id"])})

    return changed_copy(doc_source, with_goldens, name="golden-doc-source.json")


def test_the_six_golden_entities_are_read(utilities_golden):
    assert sorted(golden["entity_id"] for golden in _goldens(utilities_golden)) == [
        "FEAT-001",
        "FEAT-002",
        "FEAT-003",
        "FUNC-001",
        "FUNC-002",
        "US-001",
    ]


def test_every_authored_field_of_each_golden_entity_reaches_the_inner_output(
    golden_doc_source, utilities_golden, run_command
):
    # Act
    result = run_command(golden_doc_source)

    # Assert: field by field, and no field beyond the golden's and the added `source_ref`.
    by_id = {entity.entity_id: entity.model_dump(mode="json") for entity in result.content.entities}
    assert len(by_id) == 6
    for golden in _goldens(utilities_golden):
        written = by_id[golden["entity_id"]]
        assert written.pop("source_ref") == _source_ref(golden["entity_id"])
        assert set(written) == set(golden), golden["entity_id"]
        for field, value in golden.items():
            assert written[field] == value, f"{golden['entity_id']}.{field}"
