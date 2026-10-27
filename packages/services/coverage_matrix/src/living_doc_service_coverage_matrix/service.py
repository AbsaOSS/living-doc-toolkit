# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `coverage-matrix` command: read one documentation input and one tests input through the shared input validation,
build the coverage matrix from them, record the CI run, check that no field was lost, and write the file.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from living_doc_core.input_validation import validate_inputs
from living_doc_core.readers import Role
from living_doc_core.run_context import run_context
from living_doc_utilities.contracts import coverage_matrix as coverage_matrix_contract
from living_doc_utilities.contracts.common import View
from living_doc_utilities.contracts.coverage_matrix import CoverageMatrixResult
from living_doc_utilities.contracts.io import write_artifact
from living_doc_utilities.contracts.lineage import check_field_loss
from living_doc_utilities.contracts.stats import compute_stats

from living_doc_service_coverage_matrix.builder import build_coverage_matrix
from living_doc_service_coverage_matrix.lineage import LINEAGE_TABLE

COMMAND = "coverage-matrix"


def check_no_field_loss(result: CoverageMatrixResult) -> None:
    """
    R11 at run time, against the documentation input only: a field the lineage table maps, with data in the records
    the matrix counts, must have data in the output. The tests input is never compared.

    @param result: The built output; its first `source_inputs[]` entry is the documentation input's.
    @raise ContractError: `FIELD_LOSS`, naming every lost path.
    """
    # `write_artifact` recomputes the output's stats on write, so they are computed here the same way first.
    output_stats = compute_stats(result, coverage_matrix_contract.RECORD_ROOTS, result.metadata.stats.cardinality)
    check_field_loss(LINEAGE_TABLE, result.metadata.source_inputs[0].selected_stats, output_stats)


def coverage_matrix(
    doc_inputs: Sequence[str | Path],
    tests_input: str | Path,
    output_path: str | Path,
    *,
    view: View = "inner",
) -> CoverageMatrixResult:
    """
    Run `coverage-matrix`: nothing is built before the inputs pass the shared input validation, and nothing is
    written when a field was lost.

    @param doc_inputs: The documentation inputs given, `doc-source.json`; the shared input validation takes one.
    @param tests_input: The tests input, `ui-tests.json`.
    @param output_path: The `coverage-matrix.json` to write.
    @param view: `document.view`, `inner` or `release`.
    @return: The output as built, before `write_artifact` filled its stats.
    @raise InputValidationError: The inputs failed a step of the shared input validation.
    @raise RuntimeError: The shared input validation passed but returned no documentation or no tests input, a
        defect in it.
    @raise ContractError: `FIELD_LOSS`, or the output failed validation on write; no file is written either way.
    @raise OSError: The output file cannot be written.
    """
    inputs = validate_inputs(COMMAND, {Role.DOCUMENTATION: list(doc_inputs), Role.TESTS: [tests_input]})
    # `validate_inputs` returns an input for every role the command takes, or raises.
    if inputs.documentation is None:
        raise RuntimeError(f"{COMMAND} - the shared input validation returned no documentation input")
    if inputs.tests is None:
        raise RuntimeError(f"{COMMAND} - the shared input validation returned no tests input")
    result = build_coverage_matrix(
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
