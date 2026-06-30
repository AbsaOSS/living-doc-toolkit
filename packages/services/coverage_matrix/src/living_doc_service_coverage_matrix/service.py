# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Service orchestration for the coverage-matrix generator.

Loads the doc and tests inputs, builds the coverage matrix, writes the output JSON,
and enforces an optional ``--fail-under`` threshold.
"""

from datetime import datetime, timezone

from living_doc_core.errors import ToolkitError  # type: ignore[import-untyped]
from living_doc_core.json_utils import write_json  # type: ignore[import-untyped]
from living_doc_core.logging_config import setup_logging  # type: ignore[import-untyped]

from living_doc_service_coverage_matrix.loader import load_doc_input, load_tests_input
from living_doc_service_coverage_matrix.matcher import build_coverage_matrix
from living_doc_service_coverage_matrix.model.coverage_item import CoverageMatrix


class CoverageThresholdError(ToolkitError):
    """Coverage percentage below the configured ``--fail-under`` threshold. Exit code 1."""

    exit_code = 1


def _filter_valid_user_stories(doc_items: list[dict], logger) -> list[dict]:
    """Drop User Stories missing ``id`` or ``acceptance_criteria``, logging each skip."""
    valid: list[dict] = []
    for us in doc_items:
        if not isinstance(us, dict) or not us.get("id") or us.get("acceptance_criteria") is None:
            skipped_id = us.get("id") if isinstance(us, dict) else us
            logger.warning("Skipping user story missing 'id' or 'acceptance_criteria': %s", skipped_id)
            continue
        valid.append(us)
    return valid


def run_service(doc_input: str, tests_input: str, output_path: str, options: dict) -> CoverageMatrix:
    """
    Run the coverage-matrix generation pipeline.

    Args:
        doc_input: Path to the doc JSON file (doc-source.json / doc-issues.json)
        tests_input: Path to the ui-tests JSON file
        output_path: Destination path for coverage-matrix.json
        options: Configuration options (``verbose``, ``fail_under``)

    Returns:
        The generated :class:`CoverageMatrix`.

    Raises:
        FileIOError: If an input file is missing or the output cannot be written
        InvalidInputError: If an input file is malformed or has the wrong shape
        CoverageThresholdError: If coverage is below ``--fail-under``
    """
    verbose = options.get("verbose", False)
    fail_under = options.get("fail_under")
    logger = setup_logging(verbose=verbose)

    logger.info("Starting coverage matrix generation")
    logger.info("Doc input: %s", doc_input)
    logger.info("Tests input: %s", tests_input)
    logger.info("Output: %s", output_path)

    doc_items = load_doc_input(doc_input)
    test_items = load_tests_input(tests_input)

    valid_doc = _filter_valid_user_stories(doc_items, logger)

    generated_at = datetime.now(timezone.utc).isoformat()
    matrix = build_coverage_matrix(valid_doc, test_items, generated_at)

    logger.info("Writing coverage matrix JSON...")
    write_json(output_path, matrix.to_dict(), indent=2, sort_keys=True)

    summary = matrix.summary
    logger.info("Coverage matrix written successfully")
    logger.info("  - User stories: %d", summary.total_user_stories)
    logger.info("  - Total ACs: %d", summary.total_acs)
    logger.info("  - Active ACs: %d", summary.active_acs)
    logger.info("  - Covered ACs: %d", summary.covered_acs)
    logger.info("  - Coverage: %s%%", summary.coverage_pct)
    if matrix.unlinked_tests:
        logger.warning("Unlinked tests: %d", len(matrix.unlinked_tests))
    if matrix.stale_ac_refs:
        logger.warning("Stale AC references: %d", len(matrix.stale_ac_refs))

    if fail_under is not None:
        effective_pct = summary.coverage_pct if summary.coverage_pct is not None else 0.0
        if effective_pct < fail_under:
            raise CoverageThresholdError(f"Coverage {effective_pct}% is below threshold {fail_under}%")

    return matrix
