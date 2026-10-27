# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""The `normalize-tests` command: validate, build, record the CI run, check lineage, and write the catalog."""

from datetime import datetime, timezone
from pathlib import Path

from living_doc_core.input_validation import validate_inputs
from living_doc_core.readers import Role
from living_doc_core.run_context import run_context
from living_doc_utilities.contracts import ui_test_catalog
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
        if isinstance(mapped_output_path, str):
            field_path = mapped_output_path.removeprefix(USER_STORY_SCENARIO_ROOT)
            field_occupancy[mapped_output_path] = sum(
                field_occupancy.get(f"{root}{field_path}", 0) for root in group_roots
            )
    return output_stats.model_copy(update={"field_occupancy": field_occupancy})


def check_no_field_loss(result: UiTestCatalogResult) -> None:
    """Apply R11 to the union of the User Story, Functionality, and unlinked scenario groups."""
    input_stats = result.metadata.source_inputs[0].selected_stats
    check_field_loss(LINEAGE_TABLE, input_stats, _field_loss_stats(result))


def normalize_tests(input_path: str | Path, output_path: str | Path) -> UiTestCatalogResult:
    """Run `normalize-tests`: validate one input before building, fail on field loss, and write one catalog."""
    tests = validate_inputs(COMMAND, {Role.TESTS: [input_path]}).tests
    if tests is None:
        raise RuntimeError(f"{COMMAND} - the shared input validation returned no tests input")

    result = build_ui_test_catalog(
        tests,
        generated_at=datetime.now(timezone.utc).replace(microsecond=0),
    )
    result.metadata.run = run_context()
    check_no_field_loss(result)
    write_artifact(result, output_path)
    return result
