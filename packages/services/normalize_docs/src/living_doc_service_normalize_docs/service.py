# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `normalize-docs` command: read one documentation input through the shared input validation, build
`generator-ready` from it, record the CI run, check that no field was lost, and write the file.
"""

from datetime import datetime, timezone
from pathlib import Path

from living_doc_core.input_validation import validate_inputs
from living_doc_core.readers import Role
from living_doc_core.run_context import run_context
from living_doc_utilities.contracts import generator_ready
from living_doc_utilities.contracts.common import View
from living_doc_utilities.contracts.generator_ready import GeneratorReadyResult
from living_doc_utilities.contracts.io import write_artifact
from living_doc_utilities.contracts.lineage import check_field_loss
from living_doc_utilities.contracts.stats import compute_stats

from living_doc_service_normalize_docs.builder import build_generator_ready
from living_doc_service_normalize_docs.lineage import LINEAGE_TABLE

COMMAND = "normalize-docs"


def check_no_field_loss(result: GeneratorReadyResult) -> None:
    """
    R11 at run time: a field the lineage table maps, with data in the records the view kept, must have data in the
    output. It compares the table's mapped paths only, so a field the table does not know never stops a run.

    @param result: The built output, with its one `source_inputs[]` entry.
    @raise ContractError: `FIELD_LOSS`, naming every lost path.
    """
    # `write_artifact` recomputes the output's stats on write, so they are computed here the same way first.
    output_stats = compute_stats(result, generator_ready.RECORD_ROOTS, result.metadata.stats.cardinality)
    check_field_loss(LINEAGE_TABLE, result.metadata.source_inputs[0].selected_stats, output_stats)


def normalize_docs(
    input_path: str | Path,
    output_path: str | Path,
    *,
    view: View = "inner",
    document_title: str | None = None,
    document_version: str | None = None,
) -> GeneratorReadyResult:
    """
    Run `normalize-docs`: nothing is built before the input passes the shared input validation, and nothing is
    written when a field was lost.

    @param input_path: The documentation input, `doc-source.json`.
    @param output_path: The `generator-ready.json` to write.
    @param view: The view the output holds, `inner` or `release`.
    @param document_title: `document.title`; the input's project id when not given.
    @param document_version: `document.version`; `1.0.0` when not given.
    @return: The output as built, before `write_artifact` filled its stats.
    @raise InputValidationError: The input failed a step of the shared input validation.
    @raise ContractError: `FIELD_LOSS`, or the output failed validation on write; no file is written either way.
    @raise OSError: The output file cannot be written.
    """
    documentation = validate_inputs(COMMAND, {Role.DOCUMENTATION: [input_path]}).documentation
    assert documentation is not None  # the command takes one documentation input
    result = build_generator_ready(
        documentation,
        view=view,
        generated_at=datetime.now(timezone.utc).replace(microsecond=0),
        title=document_title,
        version=document_version,
    )
    # The CI run this file is written in; `source_inputs[0].run` stays the input's own.
    result.metadata.run = run_context()
    check_no_field_loss(result)
    write_artifact(result, output_path)
    return result
