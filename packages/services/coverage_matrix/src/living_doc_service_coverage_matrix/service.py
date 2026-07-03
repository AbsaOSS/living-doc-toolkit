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


def _filter_valid_entities(items: list[dict], kind: str, logger) -> list[dict]:
    """Drop entities missing ``id`` or ``acceptance_criteria``, logging each skip."""
    valid: list[dict] = []
    for entity in items:
        if not isinstance(entity, dict) or not entity.get("id") or entity.get("acceptance_criteria") is None:
            skipped_id = entity.get("id") if isinstance(entity, dict) else entity
            logger.warning("Skipping %s missing 'id' or 'acceptance_criteria': %s", kind, skipped_id)
            continue
        valid.append(entity)
    return valid


def _filter_valid_features(items: list[dict], logger) -> list[dict]:
    """Drop features missing ``id``, logging each skip."""
    valid: list[dict] = []
    for feature in items:
        if not isinstance(feature, dict) or not feature.get("id"):
            skipped_id = feature.get("id") if isinstance(feature, dict) else feature
            logger.warning("Skipping feature missing 'id': %s", skipped_id)
            continue
        valid.append(feature)
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

    doc_groups = load_doc_input(doc_input)
    test_items = load_tests_input(tests_input)

    valid_doc = {
        "user_stories": _filter_valid_entities(doc_groups["user_stories"], "user story", logger),
        "functionalities": _filter_valid_entities(doc_groups["functionalities"], "functionality", logger),
        "features": _filter_valid_features(doc_groups["features"], logger),
    }

    generated_at = datetime.now(timezone.utc).isoformat()
    matrix = build_coverage_matrix(valid_doc, test_items, generated_at)

    logger.info("Writing coverage matrix JSON...")
    write_json(output_path, matrix.to_dict(), indent=2, sort_keys=True)

    summary = matrix.summary
    logger.info("Coverage matrix written successfully")
    logger.info("  - User stories: %d", summary.total_user_stories)
    logger.info("  - Functionalities: %d", summary.total_functionalities)
    logger.info("  - Features: %d", summary.total_features)
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
