# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for the shared input validation.
"""

import json
import logging
from importlib.metadata import version

import pytest
from living_doc_utilities.contracts.codes import Code
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.ui_tests import UITestsResult

from living_doc_core import readers
from living_doc_core.input_validation import (
    COMMAND_ROLES,
    InputProblem,
    InputValidationError,
    ValidatedInputs,
    validate_inputs,
)
from living_doc_core.readers import Role

DOCUMENTATION = Role.DOCUMENTATION
TESTS = Role.TESTS
PIN_HINT = "the components run different utilities versions — align the pins"
RUNNING_UTILITIES = version("living-doc-utilities")
_MAJOR, _MINOR, _ = RUNNING_UTILITIES.split(".", 2)
NEWER_UTILITIES = f"{_MAJOR}.{int(_MINOR) + 1}.0"


def _fails(command, inputs) -> list[InputProblem]:
    with pytest.raises(InputValidationError) as error:
        validate_inputs(command, inputs)
    return list(error.value.problems)


def _codes(problems: list[InputProblem]) -> list[Code | None]:
    return [problem.code for problem in problems]


def _set_producer(payload, name="Acme/doc-tool"):
    payload["metadata"]["producer"]["name"] = name


def _set_project(payload, project_id="another-project"):
    payload["metadata"]["source"]["project_id"] = project_id


def _repeat_first_user_story(payload):
    payload["user_stories"].append(payload["user_stories"][0])


# --- Each command's roles, and the inputs once every step passed ---


def test_each_command_declares_the_roles_it_takes():
    assert COMMAND_ROLES == {
        "normalize-docs": (DOCUMENTATION,),
        "normalize-tests": (TESTS,),
        "coverage-matrix": (DOCUMENTATION, TESTS),
    }


def test_the_example_documentation_and_tests_pass_together_as_contract_models(doc_source, ui_tests):
    # Act
    validated = validate_inputs("coverage-matrix", {DOCUMENTATION: [doc_source], TESTS: [ui_tests]})

    # Assert
    assert isinstance(validated.documentation, DocSourceResult)
    assert isinstance(validated.tests, UITestsResult)
    assert validated.documentation.metadata.source.project_id == "living-doc-examples"
    assert validated.tests.metadata.source.project_id == "living-doc-examples"


def test_normalize_docs_returns_only_its_documentation(doc_source):
    # Act
    validated = validate_inputs("normalize-docs", {DOCUMENTATION: [doc_source]})

    # Assert
    assert isinstance(validated.documentation, DocSourceResult)
    assert validated.tests is None


def test_normalize_tests_returns_only_its_tests(ui_tests):
    # Act
    validated = validate_inputs("normalize-tests", {TESTS: [ui_tests], DOCUMENTATION: []})

    # Assert
    assert validated == ValidatedInputs(tests=validated.tests)
    assert isinstance(validated.tests, UITestsResult)


def test_an_unfamiliar_producer_version_passes_without_a_warning(changed_copy, doc_source, caplog, recwarn):
    # Arrange: `metadata.producer.version` is audit information, never compared.
    caplog.set_level(logging.DEBUG)
    unfamiliar = changed_copy(doc_source, lambda payload: payload["metadata"]["producer"].update(version="99.0.0"))

    # Act
    validated = validate_inputs("normalize-docs", {DOCUMENTATION: [unfamiliar]})

    # Assert
    assert validated.documentation is not None
    assert validated.documentation.metadata.producer.version == "99.0.0"
    assert caplog.records == []
    assert len(recwarn) == 0


# --- Step 1: MISSING_INPUT ---


def test_every_input_the_command_needs_and_was_not_given_is_listed():
    # Act
    problems = _fails("coverage-matrix", {})

    # Assert
    assert [str(problem) for problem in problems] == [
        "[MISSING_INPUT] documentation input: none given; "
        "`coverage-matrix` takes one documentation input and one tests input",
        "[MISSING_INPUT] tests input: none given; "
        "`coverage-matrix` takes one documentation input and one tests input",
    ]


@pytest.mark.parametrize("names_no_file", ["missing/doc-source.json", "."])
def test_a_path_that_names_no_file_is_a_missing_input_naming_the_input_and_the_path(
    monkeypatch, tmp_path, ui_tests, names_no_file
):
    # Arrange: a path that does not exist, or one that names a directory.
    monkeypatch.chdir(tmp_path)

    # Act
    problems = _fails("coverage-matrix", {DOCUMENTATION: [names_no_file], TESTS: [ui_tests]})

    # Assert
    assert [str(problem) for problem in problems] == [
        f"[MISSING_INPUT] documentation input {names_no_file!r}: no such file; check the path, or run the step that "
        "writes it first"
    ]


def test_a_path_that_names_no_file_is_listed_with_an_input_not_given(tmp_path):
    # Act
    problems = _fails("coverage-matrix", {DOCUMENTATION: [tmp_path / "doc-source.json"]})

    # Assert
    assert [(problem.code, problem.location) for problem in problems] == [
        (Code.MISSING_INPUT, f"documentation input {str(tmp_path / 'doc-source.json')!r}"),
        (Code.MISSING_INPUT, "tests input"),
    ]


def test_a_missing_input_is_reported_before_the_given_one_is_read(changed_copy, doc_source):
    # Arrange: the documentation input would also fail R5.
    unreadable = changed_copy(doc_source, lambda payload: payload.update(schema_version="nonsense"))

    # Act
    problems = _fails("coverage-matrix", {DOCUMENTATION: [unreadable]})

    # Assert
    assert _codes(problems) == [Code.MISSING_INPUT]
    assert problems[0].location == "tests input"


# --- Step 2: R5 through `read_artifact`, per input ---


def test_a_file_of_another_contract_fails_with_contract_mismatch_naming_the_expected_set(ui_tests):
    # Act
    problems = _fails("normalize-docs", {DOCUMENTATION: [ui_tests]})

    # Assert
    assert problems == [
        InputProblem(
            Code.CONTRACT_MISMATCH,
            f"documentation input {str(ui_tests)!r}",
            "expected one of ['doc-source'], got 'ui-tests'",
        )
    ]


@pytest.mark.parametrize(
    ("utilities_version", "hint"),
    [
        # A newer utilities wrote the file.
        (NEWER_UTILITIES, f"; {PIN_HINT}"),
        # The running utilities wrote it, so it was edited by hand.
        (RUNNING_UTILITIES, f"; the file was edited by hand, or {PIN_HINT}"),
    ],
)
def test_an_unshipped_contract_version_fails_with_invalid_contract_id_and_the_pin_hint(
    changed_copy, doc_source, utilities_version, hint
):
    # Arrange
    def unshipped(payload):
        payload["schema_version"] = "doc-source-v1.1.0"
        payload["metadata"]["producer"]["utilities_version"] = utilities_version

    path = changed_copy(doc_source, unshipped)

    # Act
    problems = _fails("normalize-docs", {DOCUMENTATION: [path]})

    # Assert
    assert _codes(problems) == [Code.INVALID_CONTRACT_ID]
    assert problems[0].message.startswith(
        "schema_version 'doc-source-v1.1.0' is not a contract version this utilities ships "
        f"(file written by utilities {utilities_version!r}, this is utilities {RUNNING_UTILITIES!r})"
    )
    assert problems[0].message.endswith(hint)


def test_a_file_that_fails_its_schema_fails_with_schema_validation_failed_naming_the_path(changed_copy, ui_tests):
    # Arrange: the fixture was written by an older utilities than the running one, so the message ends with the hint.
    written = json.loads(ui_tests.read_text(encoding="utf-8"))["metadata"]["producer"]["utilities_version"]
    path = changed_copy(ui_tests, lambda payload: payload["metadata"]["source"].pop("project_id"))

    # Act
    problems = _fails("normalize-tests", {TESTS: [path]})

    # Assert
    assert _codes(problems) == [Code.SCHEMA_VALIDATION_FAILED]
    assert problems[0].location == f"tests input {str(path)!r}"
    assert problems[0].message == (
        "$.metadata.source: 'project_id' is a required property "
        f"(file written by utilities {written!r}, this is utilities {RUNNING_UTILITIES!r}); {PIN_HINT}"
    )


def test_a_file_that_is_not_json_fails_with_one_line_without_a_code_naming_the_file_and_the_parse_error(
    tmp_path, doc_source
):
    # Arrange: the first 400 characters of the example documentation.
    text = doc_source.read_text(encoding="utf-8")[:400]
    truncated = tmp_path / "doc-source.json"
    truncated.write_text(text, encoding="utf-8")
    with pytest.raises(json.JSONDecodeError) as parse_error:
        json.loads(text)

    # Act
    problems = _fails("normalize-docs", {DOCUMENTATION: [truncated]})

    # Assert
    assert problems == [InputProblem(None, f"documentation input {str(truncated)!r}", f"not JSON: {parse_error.value}")]
    assert str(problems[0]) == f"documentation input {str(truncated)!r}: not JSON: {parse_error.value}"


def test_a_file_that_is_not_utf8_text_is_not_json(tmp_path):
    # Arrange
    binary = tmp_path / "ui-tests.json"
    binary.write_bytes(b"\xff\xfe{}")

    # Act
    problems = _fails("normalize-tests", {TESTS: [binary]})

    # Assert
    assert [str(problem) for problem in problems] == [
        f"tests input {str(binary)!r}: not JSON: 'utf-8' codec can't decode byte 0xff in position 0: "
        "invalid start byte"
    ]


def test_a_file_that_is_not_json_is_listed_with_the_r5_failures_of_the_other_inputs(tmp_path, changed_copy, ui_tests):
    # Arrange
    not_json = tmp_path / "doc-source.json"
    not_json.write_text("{", encoding="utf-8")
    tests = changed_copy(ui_tests, lambda payload: payload.update(unexpected=True))

    # Act
    problems = _fails("coverage-matrix", {DOCUMENTATION: [not_json], TESTS: [tests]})

    # Assert
    assert _codes(problems) == [None, Code.SCHEMA_VALIDATION_FAILED]


def test_every_input_failing_r5_is_listed(changed_copy, doc_source, ui_tests):
    # Arrange
    tests = changed_copy(ui_tests, lambda payload: payload.update(unexpected=True))

    # Act
    problems = _fails("coverage-matrix", {DOCUMENTATION: [ui_tests], TESTS: [tests]})

    # Assert
    assert _codes(problems) == [Code.CONTRACT_MISMATCH, Code.SCHEMA_VALIDATION_FAILED]
    assert [problem.location for problem in problems] == [
        f"documentation input {str(ui_tests)!r}",
        f"tests input {str(tests)!r}",
    ]


# --- Step 3: UNKNOWN_PRODUCER ---


def test_every_input_from_an_unknown_producer_is_listed_with_the_known_ones(changed_copy, doc_source, ui_tests):
    # Arrange
    documentation = changed_copy(doc_source, _set_producer)
    tests = changed_copy(ui_tests, _set_producer)

    # Act
    problems = _fails("coverage-matrix", {DOCUMENTATION: [documentation], TESTS: [tests]})

    # Assert
    assert [str(problem) for problem in problems] == [
        f"[UNKNOWN_PRODUCER] documentation input {str(documentation)!r}: producer 'Acme/doc-tool' is not a known "
        "producer of doc-source; the known ones: 'AbsaOSS/living-doc-collector-gh'",
        f"[UNKNOWN_PRODUCER] tests input {str(tests)!r}: producer 'Acme/doc-tool' is not a known producer of "
        "ui-tests; the known ones: 'AbsaOSS/living-doc-collector-gh'",
    ]


# --- Step 4: PROJECT_MISMATCH ---


def test_inputs_of_different_projects_are_each_listed_with_their_project(changed_copy, doc_source, ui_tests):
    # Arrange
    tests = changed_copy(ui_tests, _set_project)

    # Act
    problems = _fails("coverage-matrix", {DOCUMENTATION: [doc_source], TESTS: [tests]})

    # Assert
    assert [str(problem) for problem in problems] == [
        f"[PROJECT_MISMATCH] documentation input {str(doc_source)!r}: project 'living-doc-examples', where the "
        "inputs name 'another-project', 'living-doc-examples'; a run documents one project, so collect every "
        "input for it",
        f"[PROJECT_MISMATCH] tests input {str(tests)!r}: project 'another-project', where the inputs name "
        "'another-project', 'living-doc-examples'; a run documents one project, so collect every input for it",
    ]


# --- Step 5: MULTIPLE_DOCUMENTATION_SOURCES ---


def test_every_documentation_file_beyond_one_is_listed(changed_copy, doc_source):
    # Arrange: the same documentation twice, whatever wrote it.
    second = changed_copy(doc_source, lambda payload: None, name="second-doc-source.json")

    # Act
    problems = _fails("normalize-docs", {DOCUMENTATION: [doc_source, second]})

    # Assert
    assert [str(problem) for problem in problems] == [
        f"[MULTIPLE_DOCUMENTATION_SOURCES] documentation input {str(doc_source)!r}: one of 2 documentation files; "
        "a run reads exactly one, so pass one",
        f"[MULTIPLE_DOCUMENTATION_SOURCES] documentation input {str(second)!r}: one of 2 documentation files; "
        "a run reads exactly one, so pass one",
    ]


# --- Step 6: DUPLICATE_ENTITY_ID, DUPLICATE_AC_ID ---


def test_every_repeated_entity_id_is_listed_with_every_place_it_is_at(changed_copy, doc_source):
    # Arrange
    def repeat_entities(payload):
        _repeat_first_user_story(payload)
        payload["functionalities"].append(payload["functionalities"][1])

    path = changed_copy(doc_source, repeat_entities)

    # Act
    problems = _fails("normalize-docs", {DOCUMENTATION: [path]})

    # Assert
    location = f"documentation input {str(path)!r}"
    assert problems == [
        InputProblem(
            Code.DUPLICATE_ENTITY_ID,
            location,
            "entity id 'US-001' at user_stories[0], user_stories[1]; one id names one entity, so renumber all but "
            "one at the source",
        ),
        InputProblem(
            Code.DUPLICATE_ENTITY_ID,
            location,
            "entity id 'FUNC-002' at functionalities[1], functionalities[2]; one id names one entity, so renumber "
            "all but one at the source",
        ),
    ]


def test_every_repeated_criterion_id_under_one_entity_is_listed_with_every_place_it_is_at(changed_copy, doc_source):
    # Arrange
    def repeat_criteria(payload):
        criteria = payload["user_stories"][0]["acceptance_criteria"]
        criteria.extend([criteria[1], criteria[1]])
        functionality_criteria = payload["functionalities"][0]["acceptance_criteria"]
        functionality_criteria.append(functionality_criteria[0])

    path = changed_copy(doc_source, repeat_criteria)

    # Act
    problems = _fails("normalize-docs", {DOCUMENTATION: [path]})

    # Assert
    assert [(problem.code, problem.message) for problem in problems] == [
        (
            Code.DUPLICATE_AC_ID,
            "acceptance criterion id 'US-001-02' at user_stories[0].acceptance_criteria[1], "
            "user_stories[0].acceptance_criteria[4], user_stories[0].acceptance_criteria[5]; one id names one "
            "criterion of its entity, so renumber all but one at the source",
        ),
        (
            Code.DUPLICATE_AC_ID,
            "acceptance criterion id 'FUNC-001-01' at functionalities[0].acceptance_criteria[0], "
            "functionalities[0].acceptance_criteria[3]; one id names one criterion of its entity, so renumber all "
            "but one at the source",
        ),
    ]


def test_repeated_entity_and_criterion_ids_are_reported_together(changed_copy, doc_source):
    # Arrange
    def repeat_both(payload):
        payload["functionalities"][1]["acceptance_criteria"].append(
            payload["functionalities"][1]["acceptance_criteria"][0]
        )
        _repeat_first_user_story(payload)

    path = changed_copy(doc_source, repeat_both)

    # Act
    problems = _fails("normalize-docs", {DOCUMENTATION: [path]})

    # Assert
    assert _codes(problems) == [Code.DUPLICATE_ENTITY_ID, Code.DUPLICATE_AC_ID]


# --- The order: only the first failing step is reported ---


@pytest.mark.parametrize(
    ("fixed", "reported"),
    [
        ((), Code.UNKNOWN_PRODUCER),
        (("producer",), Code.PROJECT_MISMATCH),
        (("producer", "project"), Code.MULTIPLE_DOCUMENTATION_SOURCES),
        (("producer", "project", "one documentation file"), Code.DUPLICATE_ENTITY_ID),
    ],
)
def test_inputs_failing_several_steps_report_only_the_first_failing_steps_code(
    changed_copy, doc_source, ui_tests, fixed, reported
):
    # Arrange: documentation failing steps 3 to 6 at once, then one fewer per case.
    def documentation_change(payload):
        _repeat_first_user_story(payload)
        if "producer" not in fixed:
            _set_producer(payload)
        if "project" not in fixed:
            _set_project(payload)

    documentation = [changed_copy(doc_source, documentation_change)]
    if "one documentation file" not in fixed:
        documentation.append(changed_copy(doc_source, documentation_change, name="second-doc-source.json"))

    # Act
    problems = _fails("coverage-matrix", {DOCUMENTATION: documentation, TESTS: [ui_tests]})

    # Assert
    assert set(_codes(problems)) == {reported}


def test_the_error_text_lists_every_problem_in_order(ui_tests, doc_source):
    # Act
    with pytest.raises(InputValidationError) as error:
        validate_inputs("coverage-matrix", {DOCUMENTATION: [ui_tests], TESTS: [doc_source]})

    # Assert
    assert str(error.value).splitlines() == [
        f"[CONTRACT_MISMATCH] documentation input {str(ui_tests)!r}: expected one of ['doc-source'], got 'ui-tests'",
        f"[CONTRACT_MISMATCH] tests input {str(doc_source)!r}: expected one of ['ui-tests'], got 'doc-source'",
    ]


# --- A caller's errors ---


@pytest.mark.parametrize(
    ("command", "inputs", "message"),
    [
        ("normalize-everything", {}, "unknown command 'normalize-everything'"),
        ("normalize-tests", {DOCUMENTATION: ["doc-source.json"]}, "`normalize-tests` takes no documentation input"),
        ("coverage-matrix", {TESTS: ["a.json", "b.json"]}, "`coverage-matrix` takes one tests input"),
    ],
)
def test_a_call_no_command_can_make_is_a_value_error(command, inputs, message):
    with pytest.raises(ValueError, match=message):
        validate_inputs(command, inputs)


# --- A defect in `read_artifact` ---


def test_a_read_model_whose_schema_version_is_no_contract_id_is_a_value_error(monkeypatch, doc_source):
    # Arrange: R5 step 1 lets only a contract id through, so only a defect in it gets here.
    read = readers.read_artifact(doc_source, expected={"doc-source"})
    broken = read.model_copy(update={"schema_version": "doc-source"})
    monkeypatch.setattr(readers, "read_artifact", lambda *_args, **_kwargs: broken)

    # Act / Assert
    with pytest.raises(ValueError, match="^schema_version 'doc-source' is not a contract id$"):
        validate_inputs("normalize-docs", {DOCUMENTATION: [doc_source]})
