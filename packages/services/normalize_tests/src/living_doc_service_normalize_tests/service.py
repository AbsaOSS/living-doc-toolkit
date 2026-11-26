# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `normalize-tests` command: read one documentation input and one tests input through the shared input validation,
build the catalog, record the CI run, check that no field was lost, and write the file.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from living_doc_core.input_validation import validate_inputs
from living_doc_core.readers import Role
from living_doc_core.run_context import run_context
from living_doc_utilities.contracts import ui_test_catalog
from living_doc_utilities.contracts.common import View
from living_doc_utilities.contracts.envelope import Stats
from living_doc_utilities.contracts.io import write_artifact
from living_doc_utilities.contracts.lineage import check_field_loss
from living_doc_utilities.contracts.stats import compute_stats
from living_doc_utilities.contracts.ui_test_catalog import UiTestCatalogResult

from living_doc_service_normalize_tests.builder import build_ui_test_catalog
from living_doc_service_normalize_tests.lineage import (
    FUNCTIONALITY_SCENARIO_ROOT,
    LINEAGE_TABLE,
    UNLINKED_SCENARIO_ROOT,
    USER_STORY_SCENARIO_ROOT,
)

COMMAND = "normalize-tests"


def _field_loss_stats(result: UiTestCatalogResult) -> Stats:
    """Add the three mutually exclusive scenario groups for the check without changing the catalog's own stats."""
    output_stats = compute_stats(result, ui_test_catalog.RECORD_ROOTS, result.metadata.stats.cardinality)
    field_occupancy = dict(output_stats.field_occupancy)
    group_roots = (USER_STORY_SCENARIO_ROOT, FUNCTIONALITY_SCENARIO_ROOT, UNLINKED_SCENARIO_ROOT)
    for mapped_output_path in LINEAGE_TABLE.entries.values():
        if isinstance(mapped_output_path, str) and mapped_output_path.startswith(USER_STORY_SCENARIO_ROOT):
            field_path = mapped_output_path.removeprefix(USER_STORY_SCENARIO_ROOT)
            field_occupancy[mapped_output_path] = sum(
                field_occupancy.get(f"{root}{field_path}", 0) for root in group_roots
            )
    return output_stats.model_copy(update={"field_occupancy": field_occupancy})


def check_no_field_loss(result: UiTestCatalogResult) -> None:
    """
    R11 at run time, against the tests input, whose scenarios the catalog carries: a field the lineage table maps, with
    data in the links the view keeps, must have data in the union of the three scenario groups, or on a feature file.

    @param result: The built output; its second `source_inputs[]` entry is the tests input's.
    @raise ContractError: `FIELD_LOSS`, naming every lost path.
    """
    check_field_loss(LINEAGE_TABLE, result.metadata.source_inputs[1].selected_stats, _field_loss_stats(result))


def normalize_tests(
    doc_inputs: Sequence[str | Path],
    tests_input: str | Path,
    output_path: str | Path,
    *,
    view: View = "inner",
) -> UiTestCatalogResult:
    """
    Run `normalize-tests`: nothing is built before the inputs pass the shared input validation, and nothing is
    written when a field was lost.

    @param doc_inputs: The documentation inputs given, `doc-source.json`; the shared input validation takes one.
    @param tests_input: The tests input, `ui-tests.json`.
    @param output_path: The `ui-test-catalog.json` to write.
    @param view: `document.view`, `inner` or `release`; `release` drops the links to `planned` and `in_review` criteria.
    @return: The output as built, before `write_artifact` filled its stats.
    @raise TypeError: `doc_inputs` is one path, not a sequence of them.
    @raise InputValidationError: The inputs failed a step of the shared input validation.
    @raise RuntimeError: The shared input validation passed but returned no documentation or no tests input, a
        defect in it.
    @raise ContractError: `FIELD_LOSS`, or the output failed validation on write; no file is written either way.
    @raise OSError: The output file cannot be written.
    """
    # A `str` is a `Sequence[str]` too, and `list()` would read each of its characters as a path.
    if isinstance(doc_inputs, (str, Path)):
        raise TypeError(f"{COMMAND} - doc_inputs is one path, {str(doc_inputs)!r}; pass a sequence of paths")
    inputs = validate_inputs(COMMAND, {Role.DOCUMENTATION: list(doc_inputs), Role.TESTS: [tests_input]})
    # `validate_inputs` returns an input for every role the command takes, or raises.
    if inputs.documentation is None:
        raise RuntimeError(f"{COMMAND} - the shared input validation returned no documentation input")
    if inputs.tests is None:
        raise RuntimeError(f"{COMMAND} - the shared input validation returned no tests input")

    result = build_ui_test_catalog(
        inputs.documentation,
        inputs.tests,
        view=view,
        generated_at=datetime.now(timezone.utc).replace(microsecond=0),
    )
    # The CI run this file is written in; each `source_inputs[]` entry keeps its input's own.
    result.metadata.run = run_context()
    check_no_field_loss(result)
    write_artifact(result, output_path)
    return result
